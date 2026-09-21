from unittest.mock import patch

from evidence_pipeline import check_source_binding, execute_inquiry, retain_unique_abstracts
from demo_examples import SAMPLE_CASES


def paper(identifier="p1"):
    return {"id": identifier, "doi": None, "title": "A Study of Catalysis", "abstract": "The catalyst increased conversion under mild conditions.",
            "year": 2024, "authors": [], "url": "https://example.org/p1", "source": "arXiv"}


def test_retain_unique_abstracts_by_title():
    assert len(retain_unique_abstracts([paper("p1"), paper("p2")])) == 1


def test_claim_evidence_guards():
    card = {"paper_id": "p1", "abstract": paper()["abstract"]}
    valid = {"text": "Conversion increased", "paper_id": "p1", "evidence_quote": "increased conversion under mild conditions"}
    assert check_source_binding(valid, [card])[0]
    assert not check_source_binding({**valid, "paper_id": "other"}, [card])[0]
    assert not check_source_binding({**valid, "evidence_quote": "unreported numerical breakthrough"}, [card])[0]
    assert not check_source_binding({**valid, "text": ""}, [card])[0]


def test_offline_graph(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with patch("evidence_pipeline.query_s2_catalog", return_value=[paper()]), patch("evidence_pipeline.query_arxiv_feed", return_value=[paper("p2")]):
        result = execute_inquiry("catalyst conversion", 3)
    assert len(result["papers"]) == 1
    assert len(result["cards"]) == 1
    assert result["matrix"][0]["引用ID"] == "p1"
    assert len(result["verified"]) == 1


def test_curated_examples_keep_quotes_bound_to_their_sources():
    for case in SAMPLE_CASES.values():
        result = case["result"]
        assert len(result["cards"]) >= 2
        for claim in result["verified"]:
            card = next(card for card in result["cards"] if card["paper_id"] == claim["paper_id"])
            assert claim["evidence_quote"].casefold() in card["abstract"].casefold()

