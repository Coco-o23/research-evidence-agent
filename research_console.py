from __future__ import annotations

import html
import os
from typing import Any

import streamlit as st

from demo_examples import SAMPLE_CASES, get_sample
from evidence_pipeline import execute_inquiry


st.set_page_config(page_title="Research Evidence Agent", page_icon="🔎", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 35%);}
    .block-container {max-width: 1160px; padding-top: 2rem; padding-bottom: 4rem;}
    .hero {padding: 2.1rem 2.2rem; border-radius: 24px; color: white;
      background: radial-gradient(circle at 85% 15%, #2563eb 0%, #13213c 36%, #0b1220 76%);
      box-shadow: 0 18px 48px rgba(15, 23, 42, .18); margin-bottom: 1.3rem;}
    .eyebrow {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase; color: #93c5fd; font-weight: 700;}
    .hero h1 {font-size: 2.55rem; line-height: 1.08; margin: .55rem 0 .7rem; color: white;}
    .hero p {max-width: 760px; color: #dbeafe; font-size: 1.05rem; line-height: 1.7; margin: 0;}
    .flow {margin-top: 1.25rem; color: #bfdbfe; font-size: .88rem;}
    .section-kicker {color: #2563eb; font-weight: 750; font-size: .82rem; letter-spacing: .08em; text-transform: uppercase;}
    .sample-card {height: 155px; padding: 1.15rem 1.15rem .8rem; border: 1px solid #e2e8f0;
      border-radius: 18px; background: rgba(255,255,255,.9); box-shadow: 0 8px 24px rgba(15,23,42,.05);}
    .sample-card h3 {font-size: 1.03rem; margin: .35rem 0 .55rem; color: #0f172a;}
    .sample-card p {font-size: .87rem; line-height: 1.5; color: #64748b;}
    .result-banner {padding: 1rem 1.2rem; border: 1px solid #bfdbfe; border-radius: 16px;
      background: #eff6ff; margin: .5rem 0 1.2rem;}
    .claim {padding: 1rem 1.15rem; border-left: 4px solid #16a34a; border-radius: 12px;
      background: #f0fdf4; margin-bottom: .7rem; color: #14532d;}
    .quote {padding: .85rem 1rem; border-radius: 10px; background: #f8fafc; color: #475569;
      font-size: .88rem; line-height: 1.55; border: 1px solid #e2e8f0;}
    .muted {color:#64748b; font-size:.88rem;}
    div[data-testid="stMetric"] {background:white; border:1px solid #e2e8f0; padding:.8rem 1rem; border-radius:14px;}
    div[data-testid="stForm"] {background:white; border:1px solid #e2e8f0; padding:1.25rem; border-radius:18px;}
    .stButton > button, .stFormSubmitButton > button {border-radius: 12px; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_results(result: dict[str, Any]) -> None:
    cards = result.get("cards", [])
    accepted = result.get("verified", [])
    rejected = result.get("rejected", [])
    evidence_count = sum(bool(card.get("evidence_snippets")) for card in cards)

    label = "预置演示结果" if result.get("demo") else "实时研究结果"
    st.markdown(
        f'<div class="result-banner"><b>{label}</b><br><span class="muted">'
        f'{html.escape(result.get("question", "分析已完成"))}</span></div>',
        unsafe_allow_html=True,
    )

    a, b, c, d = st.columns(4)
    a.metric("候选文献", len(result.get("papers", [])))
    b.metric("进入分析", len(result.get("selected", [])))
    c.metric("有效证据卡", evidence_count)
    d.metric("通过校验结论", len(accepted))

    overview, evidence, comparison, diagnostics = st.tabs(
        ["结论概览", "证据卡", "跨论文比较", "过程与诊断"]
    )

    with overview:
        st.subheader("通过来源检查的结论")
        if not accepted:
            st.info("当前没有结论通过来源检查。请查看诊断信息或更换问题。")
        for claim in accepted:
            st.markdown(
                f'<div class="claim">{html.escape(str(claim.get("text", "")))} '
                f'<b>[{html.escape(str(claim.get("paper_id", "")))}]</b></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="quote"><b>原文锚点</b><br>{html.escape(str(claim.get("evidence_quote", "")))}'
                f'<br><br><span class="muted">{html.escape(str(claim.get("check", "")))}</span></div>',
                unsafe_allow_html=True,
            )
        st.caption("通过表示论文编号和原文片段能够对应；语义蕴含和研究质量仍需人工判断。")

    with evidence:
        if not cards:
            st.info("尚未生成证据卡。")
        for index, card in enumerate(cards, 1):
            with st.expander(f"P{index} · {card.get('title', 'Untitled')} · {card.get('year', '—')}", expanded=index == 1):
                head_left, head_right = st.columns([4, 1])
                with head_left:
                    st.caption(f"来源：{card.get('source', '—')} · 引用 ID：{card.get('paper_id', '—')}")
                with head_right:
                    if card.get("url"):
                        st.link_button("查看论文 ↗", card["url"], width="stretch")
                fields = [
                    ("研究方法", "method"), ("核心机制", "mechanism"), ("实验条件", "conditions"),
                    ("关键证据", "key_evidence"), ("局限", "limitations"),
                ]
                left, right = st.columns(2)
                for position, (title, key) in enumerate(fields):
                    with left if position % 2 == 0 else right:
                        st.markdown(f"**{title}**")
                        st.write(card.get(key) or "未报告")
                st.markdown("**可核对原文片段**")
                for snippet in card.get("evidence_snippets", []):
                    st.markdown(f"> {snippet}")
                with st.expander("查看摘要"):
                    st.write(card.get("abstract", ""))

    with comparison:
        rows = result.get("matrix", [])
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True)
        else:
            st.info("没有可比较的论文记录。")

    with diagnostics:
        st.markdown("**检索角度**")
        for query in result.get("plan", []):
            st.code(query, language=None)
        if result.get("errors"):
            st.warning("部分来源或模型调用未完成，系统已保留其他可用结果。")
            st.json(result["errors"])
        else:
            st.success("本次流程没有记录到来源或模型错误。")
        if rejected:
            st.markdown("**未通过来源检查的候选结论**")
            st.json(rejected)


with st.sidebar:
    st.markdown("### Research Evidence Agent")
    st.caption("摘要级、多来源、可回溯")
    st.divider()
    st.markdown("**运行状态**")
    st.write("🟢 样例演示可用")
    st.write("🟢 arXiv / Semantic Scholar")
    if os.getenv("OPENAI_API_KEY"):
        st.write("🟢 结构化模型已配置")
    else:
        st.write("🟡 未配置云端模型，实时分析将使用保守模式")
    st.divider()
    st.caption("证据范围：当前版本以论文摘要为分析边界。")
    st.markdown("[查看 GitHub 源码](https://github.com/Coco-o23/research-evidence-agent)")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Evidence-first research workflow</div>
      <h1>把科研问题变成<br>可核对的证据链</h1>
      <p>自动拆解问题、检索真实论文、抽取统一证据字段并比较跨论文结论。每条输出都保留论文编号和摘要原文锚点，方便快速判断，也方便回到来源复核。</p>
      <div class="flow">问题拆解&nbsp; → &nbsp;多源检索&nbsp; → &nbsp;相关性筛选&nbsp; → &nbsp;证据映射&nbsp; → &nbsp;跨论文比较&nbsp; → &nbsp;引用检查</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-kicker">Instant demos</div>', unsafe_allow_html=True)
st.subheader("先用一个准备好的问题体验结果")
st.caption("样例结果已人工核对来源，点击后立即展示，不消耗 API 配额。")

columns = st.columns(len(SAMPLE_CASES))
for column, (name, case) in zip(columns, SAMPLE_CASES.items()):
    with column:
        st.markdown(
            f'<div class="sample-card"><span class="section-kicker">Sample</span>'
            f'<h3>{html.escape(name)}</h3><p>{html.escape(case["description"])}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button(f"体验 {name}", key=f"sample-{name}", width="stretch"):
            st.session_state.result = get_sample(name)
            st.session_state.active_question = case["question"]

st.divider()
st.markdown('<div class="section-kicker">Live research</div>', unsafe_allow_html=True)
st.subheader("研究你自己的问题")

with st.form("research-form"):
    question = st.text_area(
        "科研问题",
        value=st.session_state.get("active_question", ""),
        height=110,
        placeholder="例如：无人机集群中的感知、通信与控制一体化有哪些主要应用与证据？",
        help="尽量写明研究对象、希望比较的机制或实验条件。",
    )
    left, right = st.columns([1, 2])
    with left:
        limit = st.slider("分析论文数量", 2, 10, 5)
    with right:
        st.caption("实时模式会访问 Semantic Scholar 与 arXiv。匿名接口可能限流，系统会保留仍可访问来源的结果。")
    submitted = st.form_submit_button("开始构建证据链 →", type="primary", width="stretch")

if submitted:
    if not question.strip():
        st.warning("请先输入一个明确的科研问题。")
    else:
        with st.status("正在构建证据链…", expanded=True) as status:
            st.write("拆解问题并生成检索角度")
            st.write("访问论文来源并进行摘要相关性排序")
            try:
                st.session_state.result = execute_inquiry(question, limit)
                st.session_state.result["question"] = question
                st.session_state.active_question = question
                status.update(label="分析完成", state="complete", expanded=False)
            except Exception as exc:
                status.update(label="分析未完成", state="error", expanded=True)
                st.error(f"运行失败：{exc}")

if "result" in st.session_state:
    st.divider()
    render_results(st.session_state.result)

st.divider()
st.caption("Research Evidence Agent · 公开演示版 · 数据来源归属于各论文与检索服务提供方")
