import streamlit as st

from evidence_pipeline import execute_inquiry

st.set_page_config(
    page_title="Research Evidence Agent",
    page_icon="🔬",
    layout="wide",
)
st.title("Research Evidence Agent")
st.markdown("**面向科研问题的多源文献检索、证据抽取与跨论文分析系统**")
st.caption("问题拆解 → 多源检索 → 相关性筛选 → Evidence Card → 跨论文对比 → Claim-Evidence 校验")

with st.sidebar:
    st.header("关于项目")
    st.write(
        "本项目聚焦科研检索分散、跨论文结论难比较和生成式模型引用错配问题，"
        "通过可回溯的证据片段约束研究结论。"
    )
    st.info("当前版本使用论文摘要进行分析；摘要未披露的信息会标记为“未报告”。")
question = st.text_area("科研问题", placeholder="例如：哪些实验支持某机制？不同研究条件为何导致不同结论？")
limit = st.slider("最多分析论文", 2, 12, 6)
if st.button("开始分析", type="primary"):
    with st.spinner("正在检索与分析…"):
        try:
            st.session_state.result = execute_inquiry(question, limit)
        except Exception as exc:
            st.error(str(exc))

if "result" in st.session_state:
    result = st.session_state.result
    st.subheader("检索计划")
    st.write(result.get("plan", []))
    if result.get("errors"):
        st.warning(f"部分阶段失败：{result['errors']}")
    st.write(f"候选 {len(result.get('papers', []))} 篇；筛选 {len(result.get('selected', []))} 篇")
    st.subheader("Evidence Cards · 摘要级")
    for card in result.get("cards", []):
        with st.expander(f"{card['title']} ({card['year']}) · {card['source']}"):
            st.markdown(f"[原文入口]({card['url']}) · 引用 ID `{card['paper_id']}`")
            for key, label in (("method", "研究方法"), ("mechanism", "核心机制"), ("conditions", "实验条件"),
                               ("key_evidence", "关键证据"), ("limitations", "局限")):
                st.write(f"**{label}：** {card[key]}")
            st.write("**原文证据片段：**", card["evidence_snippets"])
            st.write("**摘要：**", card["abstract"])
    st.subheader("跨论文对比矩阵")
    st.dataframe(result.get("matrix", []), use_container_width=True)
    st.subheader("通过引用校验的结论")
    for claim in result.get("verified", []):
        st.markdown(f"{claim['text']} **[{claim['paper_id']}]**")
        st.caption(f"证据：{claim['evidence_quote']} · {claim['check']}")
    if not result.get("verified"):
        st.info("当前没有通过校验的结论。")
    if result.get("rejected"):
        with st.expander("未通过校验的结论"):
            st.json(result["rejected"])

