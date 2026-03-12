# -*- coding: utf-8 -*-
"""
Agent 与 RAG - LLM 应用
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from src.agents.marketing_agent import MarketingAgent
from src.ai_analysis.llm_client import LLMClient
from src.rag.knowledge_base import RAGKnowledgeBase

st.set_page_config(page_title="Agent 与 RAG", page_icon="🤖", layout="wide")
st.title("🤖 Agent 与 RAG")

tab1, tab2, tab3 = st.tabs(["Agent 对话", "RAG 知识库", "数据分析"])

with tab1:
    st.subheader("营销 Agent")
    st.caption("输入任务，Agent 将调用工具（热门榜、爆款模型、知识库检索等）并给出回答")
    task = st.text_input("任务", placeholder="例如：分析今日热门趋势、检索搞笑类创意案例")
    if st.button("执行"):
        agent = MarketingAgent(LLMClient())
        with st.spinner("执行中..."):
            result = agent.run(task)
        st.write(result)

with tab2:
    st.subheader("RAG 知识库")
    rag = RAGKnowledgeBase()
    if st.button("从爆款内容库同步到 RAG"):
        n = rag.sync_from_viral_library()
        st.success(f"已同步 {n} 条文档")
    query = st.text_input("检索", placeholder="输入关键词检索知识库")
    if query and st.button("检索"):
        docs = rag.retrieve(query, top_k=5)
        for i, d in enumerate(docs, 1):
            st.markdown(f"**{i}** {d.get('content', '')[:200]}...")

with tab3:
    st.subheader("数据分析（Agent 驱动）")
    if st.button("生成今日趋势分析"):
        agent = MarketingAgent(LLMClient())
        with st.spinner("分析中..."):
            result = agent.analyze_trends()
        st.write(result)
