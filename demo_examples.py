"""Curated, source-linked examples used for instant product demonstrations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _card(
    paper_id: str,
    title: str,
    year: int,
    abstract: str,
    *,
    method: str,
    mechanism: str,
    conditions: str,
    key_evidence: str,
    limitations: str,
) -> dict[str, Any]:
    return {
        "paper_id": paper_id,
        "title": title,
        "year": year,
        "url": f"https://arxiv.org/abs/{paper_id}",
        "source": "arXiv",
        "abstract": abstract,
        "method": method,
        "mechanism": mechanism,
        "conditions": conditions,
        "key_evidence": key_evidence,
        "limitations": limitations,
        "evidence_snippets": [key_evidence],
    }


def _result(question: str, cards: list[dict[str, Any]], claims: list[dict[str, str]]) -> dict[str, Any]:
    papers = [{"id": c["paper_id"], "title": c["title"]} for c in cards]
    matrix = [
        {
            "论文": c["title"],
            "年份": c["year"],
            "研究方法": c["method"],
            "核心机制": c["mechanism"],
            "实验条件": c["conditions"],
            "关键证据": c["key_evidence"],
            "局限": c["limitations"],
            "引用ID": c["paper_id"],
        }
        for c in cards
    ]
    verified = [
        {**claim, "check": "预置样例：引用编号与 arXiv 摘要原文片段已人工核对"}
        for claim in claims
    ]
    return {
        "question": question,
        "plan": [question],
        "papers": papers,
        "selected": papers,
        "cards": cards,
        "matrix": matrix,
        "claims": claims,
        "verified": verified,
        "rejected": [],
        "errors": {},
        "demo": True,
    }


_rag_a = (
    "Large pre-trained language models have been shown to store factual knowledge in their parameters, and achieve state-of-the-art results when fine-tuned on downstream NLP tasks. "
    "However, their ability to access and precisely manipulate knowledge is still limited. We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG) -- models which combine pre-trained parametric and non-parametric memory for language generation. "
    "We fine-tune and evaluate our models on a wide range of knowledge-intensive NLP tasks and set the state-of-the-art on three open domain QA tasks. "
    "For language generation tasks, we find that RAG models generate more specific, diverse and factual language than a state-of-the-art parametric-only seq2seq baseline."
)
_rag_b = (
    "Retrieval-Augmented Generation (RAG) has recently emerged as a paradigm to address such challenges. "
    "In particular, RAG introduces the information retrieval process, which enhances the generation process by retrieving relevant objects from available data stores, leading to higher accuracy and better robustness. "
    "We also summarize additional enhancements methods for RAG, facilitating effective engineering and implementation of RAG systems. "
    "Furthermore, we introduce the benchmarks for RAG, discuss the limitations of current RAG systems, and suggest potential directions for future research."
)

_uav_a = (
    "Uncrewed aerial vehicle (UAV) swarms are pivotal in the applications such as disaster relief, aerial base station (BS) and logistics transportation. "
    "These scenarios require the capabilities in accurate sensing, efficient communication and flexible control for real-time and reliable task execution. "
    "We propose a deeply coupled scheme of integrated sensing, communication and control (ISCC) for UAV swarms. "
    "Simulation results validate the performance of the proposed ISCC framework, demonstrating its application potential in the future."
)
_uav_b = (
    "This paper first provides a comprehensive portrayal of the 6G vision, technical requirements, and application scenarios, covering the current common understanding of 6G. "
    "Then, a critical appraisal of the 6G network architecture and key technologies is presented. "
    "Furthermore, existing testbeds and advanced 6G verification platforms are detailed for the first time. "
    "In addition, future research directions and open challenges are identified for stimulating the on-going global debate."
)

_mol_a = (
    "In this paper, we reformulate existing models into a single common framework we call Message Passing Neural Networks (MPNNs) and explore additional novel variations within this framework. "
    "Using MPNNs we demonstrate state of the art results on an important molecular property prediction benchmark; these results are strong enough that we believe future work should focus on datasets with larger molecules or more accurate ground truth labels."
)
_mol_b = (
    "We introduce a convolutional neural network that operates directly on graphs. "
    "These networks allow end-to-end learning of prediction pipelines whose inputs are graphs of arbitrary size and shape. "
    "The architecture we present generalizes standard molecular feature extraction methods based on circular fingerprints. "
    "We show that these data-driven features are more interpretable, and have better predictive performance on a variety of tasks."
)


SAMPLE_CASES: dict[str, dict[str, Any]] = {
    "RAG 与事实性": {
        "question": "检索增强生成为什么可能改善知识密集型任务中的事实性？",
        "description": "比较经典 RAG 方法与后续综述对检索增强作用的证据。",
        "result": _result(
            "检索增强生成为什么可能改善知识密集型任务中的事实性？",
            [
                _card("2005.11401", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", 2020, _rag_a,
                      method="在多类知识密集型 NLP 任务上微调并评估两种 RAG 形式。",
                      mechanism="将参数化 seq2seq 记忆与 Wikipedia 稠密向量索引结合。",
                      conditions="开放域问答与语言生成任务；对照参数化 seq2seq 基线。",
                      key_evidence="For language generation tasks, we find that RAG models generate more specific, diverse and factual language than a state-of-the-art parametric-only seq2seq baseline.",
                      limitations="摘要未报告长期知识更新成本、检索失败传播或生产部署约束。"),
                _card("2402.19473", "Retrieval-Augmented Generation for AI-Generated Content: A Survey", 2024, _rag_b,
                      method="系统梳理 RAG 的基础、增强方法、应用、基准与研究方向。",
                      mechanism="从外部数据存储检索相关对象以增强生成。",
                      conditions="覆盖不同模态和任务的 RAG/AIGC 文献。",
                      key_evidence="RAG introduces the information retrieval process, which enhances the generation process by retrieving relevant objects from available data stores, leading to higher accuracy and better robustness.",
                      limitations="综述性证据不能替代特定系统、数据集上的直接对照实验。"),
            ],
            [
                {"text": "经典实验表明，RAG 在所评估的生成任务上比参数化基线产生了更事实性的语言。", "paper_id": "2005.11401", "evidence_quote": "For language generation tasks, we find that RAG models generate more specific, diverse and factual language than a state-of-the-art parametric-only seq2seq baseline."},
                {"text": "后续综述将性能改善归因于从外部数据存储检索相关对象来增强生成过程。", "paper_id": "2402.19473", "evidence_quote": "RAG introduces the information retrieval process, which enhances the generation process by retrieving relevant objects from available data stores, leading to higher accuracy and better robustness."},
            ],
        ),
    },
    "无人机 ISAC": {
        "question": "无人机集群中的感知、通信与控制一体化有哪些主要应用与证据？",
        "description": "查看灾害救援、空中基站和物流等场景中的一体化需求。",
        "result": _result(
            "无人机集群中的感知、通信与控制一体化有哪些主要应用与证据？",
            [
                _card("2601.14783", "Integrated Sensing, Communication and Control enabled Agile UAV Swarm", 2026, _uav_a,
                      method="提出深度耦合的 ISCC 框架，并用仿真验证。",
                      mechanism="联合优化感知、通信和控制，形成闭环协同。",
                      conditions="无人机集群；灾害救援、空中基站和物流运输场景。",
                      key_evidence="Simulation results validate the performance of the proposed ISCC framework, demonstrating its application potential in the future.",
                      limitations="摘要未提供仿真参数、量化增益和真实飞行试验。"),
                _card("2302.14536", "On the Road to 6G: Visions, Requirements, Key Technologies and Testbeds", 2023, _uav_b,
                      method="综述 6G 愿景、需求、关键技术和试验平台。",
                      mechanism="从网络架构与关键技术层面支撑通信、感知和计算融合。",
                      conditions="面向广义 6G 应用与验证平台，并非只针对无人机。",
                      key_evidence="In addition, future research directions and open challenges are identified for stimulating the on-going global debate.",
                      limitations="宏观综述不能直接证明某个 UAV ISAC 实现的性能。"),
            ],
            [
                {"text": "无人机 ISCC 已有框架级仿真证据，但摘要尚不足以判断真实部署增益。", "paper_id": "2601.14783", "evidence_quote": "Simulation results validate the performance of the proposed ISCC framework, demonstrating its application potential in the future."},
                {"text": "6G 综述仍将相关方向描述为包含开放挑战的持续研究议题。", "paper_id": "2302.14536", "evidence_quote": "In addition, future research directions and open challenges are identified for stimulating the on-going global debate."},
            ],
        ),
    },
    "分子图学习": {
        "question": "图神经网络如何用于分子性质预测，现有证据边界是什么？",
        "description": "比较分子指纹图卷积与消息传递框架的研究证据。",
        "result": _result(
            "图神经网络如何用于分子性质预测，现有证据边界是什么？",
            [
                _card("1704.01212", "Neural Message Passing for Quantum Chemistry", 2017, _mol_a,
                      method="统一既有模型为 MPNN 框架，并探索新变体。",
                      mechanism="在分子图节点间传递消息，再通过聚合得到图级表示。",
                      conditions="重要的分子性质预测基准。",
                      key_evidence="Using MPNNs we demonstrate state of the art results on an important molecular property prediction benchmark",
                      limitations="作者指出后续应使用更大分子或更准确的真实标签。"),
                _card("1509.09292", "Convolutional Networks on Graphs for Learning Molecular Fingerprints", 2015, _mol_b,
                      method="在图结构上直接运行卷积网络，端到端学习分子指纹。",
                      mechanism="把传统圆形指纹特征推广为可学习的数据驱动表示。",
                      conditions="多种分子预测任务；输入为任意大小和形状的图。",
                      key_evidence="We show that these data-driven features are more interpretable, and have better predictive performance on a variety of tasks.",
                      limitations="摘要没有列出各任务的数据规模和统计显著性。"),
            ],
            [
                {"text": "MPNN 在所报告的分子性质预测基准上达到当时的先进结果。", "paper_id": "1704.01212", "evidence_quote": "Using MPNNs we demonstrate state of the art results on an important molecular property prediction benchmark"},
                {"text": "早期图卷积工作报告了可解释性和多任务预测性能方面的优势。", "paper_id": "1509.09292", "evidence_quote": "We show that these data-driven features are more interpretable, and have better predictive performance on a variety of tasks."},
            ],
        ),
    },
}


def get_sample(name: str) -> dict[str, Any]:
    return deepcopy(SAMPLE_CASES[name]["result"])
