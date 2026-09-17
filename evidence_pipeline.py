"""Research question -> retrieved abstracts -> checked claims."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, TypedDict
from xml.etree import ElementTree as ET

import httpx
from langgraph.graph import END, START, StateGraph
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()


class ResearchState(TypedDict, total=False):
    question: str
    limit: int
    plan: list[str]
    papers: list[dict[str, Any]]
    selected: list[dict[str, Any]]
    cards: list[dict[str, Any]]
    matrix: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    verified: list[dict[str, Any]]
    rejected: list[dict[str, Any]]
    errors: dict[str, str]


def request_json_result(system: str, payload: Any) -> Any:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL") or None)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    return json.loads(response.choices[0].message.content or "{}")


def draft_search_angles(state: ResearchState) -> ResearchState:
    question = state["question"].strip()
    if not question:
        raise ValueError("请输入科研问题")
    if os.getenv("OPENAI_API_KEY"):
        try:
            data = request_json_result("Return JSON {queries:[2-3 short English scholarly search queries]}. Preserve the user's research intent.", question)
            queries = [str(x).strip() for x in data.get("queries", []) if str(x).strip()][:3]
            if queries:
                return {"plan": queries}
        except Exception as exc:
            return {"plan": [question], "errors": {"draft_search_angles": str(exc)}}
    return {"plan": [question]}


def query_s2_catalog(query: str, limit: int, client: httpx.Client) -> list[dict[str, Any]]:
    headers = {"User-Agent": "research-evidence-console/0.1"}
    if os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
    params = {"query": query, "limit": limit,
              "fields": "title,abstract,year,authors,url,externalIds,openAccessPdf"}
    response = None
    for attempt in range(3):
        response = client.get("https://api.semanticscholar.org/graph/v1/paper/search",
                              params=params, headers=headers)
        if response.status_code != 429:
            break
        retry_after = response.headers.get("Retry-After", "")
        try:
            delay = min(float(retry_after), 10.0)
        except ValueError:
            delay = float(2 ** attempt)
        time.sleep(max(delay, 1.0))
    assert response is not None
    response.raise_for_status()
    result = []
    for item in response.json().get("data", []):
        ids = item.get("externalIds") or {}
        result.append({"id": ids.get("DOI") or ids.get("ArXiv") or item.get("paperId"),
                       "doi": ids.get("DOI"), "title": item.get("title", ""), "abstract": item.get("abstract") or "",
                       "year": item.get("year"), "authors": [a.get("name", "") for a in item.get("authors") or []],
                       "url": item.get("url") or "", "source": "Semantic Scholar"})
    return result


def query_arxiv_feed(query: str, limit: int, client: httpx.Client) -> list[dict[str, Any]]:
    # arXiv query syntax is strict; quote a short plain-text phrase.
    terms = re.findall(r"[\w-]+", query, flags=re.UNICODE)[:8]
    expression = " AND ".join(f'all:"{term}"' for term in terms) or 'all:"research"'
    response = client.get("https://export.arxiv.org/api/query", params={
        "search_query": expression, "start": 0, "max_results": limit, "sortBy": "relevance"
    }, headers={"User-Agent": "research-evidence-console/0.1"})
    response.raise_for_status()
    root = ET.fromstring(response.text)
    atom = "{http://www.w3.org/2005/Atom}"
    result = []
    for entry in root.findall(f"{atom}entry"):
        url = entry.findtext(f"{atom}id", default="").strip()
        identifier = url.rsplit("/", 1)[-1].split("v")[0]
        result.append({"id": identifier, "doi": None, "title": " ".join(entry.findtext(f"{atom}title", default="").split()),
                       "abstract": " ".join(entry.findtext(f"{atom}summary", default="").split()),
                       "year": int(entry.findtext(f"{atom}published", default="0000")[:4]),
                       "authors": [a.findtext(f"{atom}name", default="") for a in entry.findall(f"{atom}author")],
                       "url": url, "source": "arXiv"})
    return result


def retain_unique_abstracts(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output = []
    for paper in papers:
        key = (paper.get("doi") or paper.get("title") or "").strip().lower()
        key = re.sub(r"\W+", "", key)
        if key and key not in seen and paper.get("id") and paper.get("abstract"):
            seen.add(key)
            output.append(paper)
    return output


def gather_literature(state: ResearchState) -> ResearchState:
    papers: list[dict[str, Any]] = []
    errors = dict(state.get("errors", {}))
    with httpx.Client(timeout=20) as client:
        queries = state["plan"]
        # Anonymous Semantic Scholar traffic is tightly rate-limited. One broad query is
        # enough for the MVP; API-key users may execute the complete query plan.
        semantic_queries = queries if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else queries[:1]
        for query in semantic_queries:
            try:
                papers.extend(query_s2_catalog(query, min(max(state.get("limit", 6), 1), 20), client))
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    errors["semantic_scholar"] = "Semantic Scholar 暂时限流；本次已自动使用其他来源的结果。"
                else:
                    errors["semantic_scholar"] = str(exc)
            except Exception as exc:
                errors["semantic_scholar"] = str(exc)
        for query in queries:
            try:
                papers.extend(query_arxiv_feed(query, min(max(state.get("limit", 6), 1), 20), client))
            except Exception as exc:
                errors["arxiv"] = str(exc)
    return {"papers": retain_unique_abstracts(papers), "errors": errors}


def prioritize_abstracts(state: ResearchState) -> ResearchState:
    papers = state.get("papers", [])
    if not papers:
        return {"selected": []}
    texts = [state["question"]] + [p["title"] + " " + p["abstract"] for p in papers]
    vectors = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=15000).fit_transform(texts)
    scores = cosine_similarity(vectors[0], vectors[1:]).ravel()
    ranked = sorted(zip(papers, scores), key=lambda x: x[1], reverse=True)
    selected = [{**p, "relevance": round(float(score), 3)} for p, score in ranked[:state.get("limit", 6)]]
    return {"selected": selected}


CARD_DIMENSIONS = ("method", "mechanism", "conditions", "key_evidence", "limitations")


def extract_supported_facts(state: ResearchState) -> ResearchState:
    cards = []
    errors = dict(state.get("errors", {}))
    for paper in state.get("selected", []):
        fields = {key: "未报告" for key in CARD_DIMENSIONS}
        snippets = []
        if os.getenv("OPENAI_API_KEY"):
            try:
                data = request_json_result(
                    "Extract ONLY from the supplied abstract. Return JSON with method, mechanism, conditions, key_evidence, limitations and evidence_snippets (exact short substrings of abstract). For absent facts use '未报告'. Do not invent details.",
                    {"title": paper["title"], "abstract": paper["abstract"]})
                fields.update({k: str(data.get(k) or "未报告") for k in CARD_DIMENSIONS})
                snippets = [str(x) for x in data.get("evidence_snippets", []) if isinstance(x, str)]
            except Exception as exc:
                errors[f"extract:{paper['id']}"] = str(exc)
        if not snippets:
            snippets = [paper["abstract"][:300]]
        snippets = [s for s in snippets if s and s.casefold() in paper["abstract"].casefold()]
        # Discard extracted details if the model supplied no valid textual anchor.
        if not snippets:
            fields = {key: "未报告" for key in CARD_DIMENSIONS}
        cards.append({"paper_id": paper["id"], "title": paper["title"], "year": paper["year"],
                      "url": paper["url"], "source": paper["source"], "abstract": paper["abstract"],
                      "evidence_snippets": snippets, **fields})
    return {"cards": cards, "errors": errors}


def compose_evidence_table(state: ResearchState) -> ResearchState:
    cards = state.get("cards", [])
    matrix = [{"论文": c["title"], "年份": c["year"], "研究方法": c["method"], "核心机制": c["mechanism"],
               "实验条件": c["conditions"], "关键证据": c["key_evidence"], "局限": c["limitations"],
               "引用ID": c["paper_id"]} for c in cards]
    claims = []
    if cards and os.getenv("OPENAI_API_KEY"):
        try:
            data = request_json_result("Return JSON {claims:[{text, paper_id, evidence_quote}]}. Each claim must be directly supported by an EXACT substring from that paper's abstract. Compare papers when possible. No unsupported synthesis.",
                            [{"paper_id": c["paper_id"], "abstract": c["abstract"], "fields": {k: c[k] for k in CARD_DIMENSIONS}} for c in cards])
            claims = [x for x in data.get("claims", []) if isinstance(x, dict)]
        except Exception:
            pass
    else:
        claims = [{"text": f"{c['title']} 的摘要报告：{c['evidence_snippets'][0]}", "paper_id": c["paper_id"],
                   "evidence_quote": c["evidence_snippets"][0]} for c in cards if c["evidence_snippets"]]
    return {"matrix": matrix, "claims": claims}


def check_source_binding(claim: dict[str, Any], cards: list[dict[str, Any]]) -> tuple[bool, str]:
    card = next((c for c in cards if c["paper_id"] == claim.get("paper_id")), None)
    if not card:
        return False, "引用 ID 不存在"
    quote = str(claim.get("evidence_quote") or "").strip()
    if len(quote) < 12 or quote.casefold() not in card["abstract"].casefold():
        return False, "证据片段不在被引论文摘要中"
    text = str(claim.get("text") or "").strip()
    if not text:
        return False, "结论为空"
    # Structural checks cannot prove semantic entailment. Require the exact evidence in the displayed claim.
    return True, "摘要证据与引用匹配；语义仍需人工复核"


def review_generated_claims(state: ResearchState) -> ResearchState:
    verified, rejected = [], []
    for claim in state.get("claims", []):
        ok, reason = check_source_binding(claim, state.get("cards", []))
        (verified if ok else rejected).append({**claim, "check": reason})
    return {"verified": verified, "rejected": rejected}


def create_inquiry_graph():
    graph = StateGraph(ResearchState)
    for name, node in (("question_frame", draft_search_angles), ("source_harvest", gather_literature), ("abstract_ranking", prioritize_abstracts),
                       ("evidence_mapping", extract_supported_facts), ("cross_study_view", compose_evidence_table), ("citation_audit", review_generated_claims)):
        graph.add_node(name, node)
    graph.add_edge(START, "question_frame")
    graph.add_edge("question_frame", "source_harvest")
    graph.add_edge("source_harvest", "abstract_ranking")
    graph.add_edge("abstract_ranking", "evidence_mapping")
    graph.add_edge("evidence_mapping", "cross_study_view")
    graph.add_edge("cross_study_view", "citation_audit")
    graph.add_edge("citation_audit", END)
    return graph.compile()


def execute_inquiry(question: str, limit: int = 6) -> ResearchState:
    return create_inquiry_graph().invoke({"question": question, "limit": limit})

