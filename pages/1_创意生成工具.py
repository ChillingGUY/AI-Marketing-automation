# -*- coding: utf-8 -*-
"""
创意中心 - 企业使用流程
1. 输入产品 2. 选择行业 3. AI 生成脚本 | 历史记录保留
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from config import PROCESSED_DATA_DIR
from src.ai_analysis.analyzer import LLMAnalyzer
from src.ai_analysis.llm_client import LLMClient
from src.employees.store import EmployeeStore
from src.models.employee import CreativeRecord
from src.creative.history import CreativeHistoryStore

st.set_page_config(page_title="创意中心", page_icon="💡", layout="wide")
st.title("💡 创意中心")
st.caption("企业流程：输入产品 → 选择行业 → AI 生成脚本 | 历史记录保留")

analyzer = LLMAnalyzer(LLMClient())
store = EmployeeStore()
employees = store.list_all()

if not analyzer.llm.is_available():
    st.info("配置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 后启用 LLM 创意生成，当前使用规则模板。")

# 企业流程：步骤 1 输入产品、步骤 2 选择行业
st.subheader("步骤 1：输入产品")
product = st.text_input("产品/服务", placeholder="例如：智能手环、职场培训课程、护肤精华", key="product")
st.subheader("步骤 2：选择行业")
INDUSTRIES = ["营销", "职场", "美食", "美妆", "数码", "教育", "电商", "金融", "房产", "其他"]
industry = st.selectbox("行业", INDUSTRIES, key="industry")
topic_extra = st.text_input("补充主题（可选）", placeholder="例如：新品上市、节日促销、痛点解决", key="topic_extra")

# 组合主题：产品 + 行业（企业流程）
topic_parts = []
if product and product.strip():
    topic_parts.append(product.strip())
topic_parts.append(industry)
if topic_extra and topic_extra.strip():
    topic_parts.append(topic_extra.strip())
topic = " - ".join(topic_parts)

# 选择员工（可选）
st.subheader("可选：员工数字人")
employee_options = [("（不指定，通用风格）", None)] + [
    (f"{e.name} - {e.ai_assistant_type}", e) for e in employees
]
selected_label = st.selectbox(
    "选择员工数字人（AI 将按该员工风格生成）",
    [o[0] for o in employee_options],
    key="employee",
)
selected_employee = next((o[1] for o in employee_options if o[0] == selected_label), None)
if selected_employee:
    st.caption(f"风格：{selected_employee.content_style} | 擅长：{', '.join(selected_employee.expertise) or '-'}")
num_ideas = st.slider("生成创意数量", 1, 5, 3)
use_rag = st.checkbox("使用 RAG 知识库增强", value=True, help="从爆款内容库检索以增强创意")
gen_script = st.checkbox("为第一个创意生成拍摄脚本", value=True)

if st.button("🚀 生成创意", type="primary"):
    with st.spinner("生成中..."):
        viral = {}
        ai_files = sorted(PROCESSED_DATA_DIR.glob("ai_analysis_*.json"), reverse=True)
        if ai_files:
            import json
            with open(ai_files[0], "r", encoding="utf-8") as f:
                viral = json.load(f).get("viral_model", {})

        rag_ctx = None
        if use_rag:
            try:
                from src.rag.knowledge_base import RAGKnowledgeBase
                r = RAGKnowledgeBase()
                if r.is_available():
                    rag_ctx = r.retrieve_for_prompt(topic, top_k=3)
            except Exception:
                pass

        ideas = analyzer.generate_ideas(
            viral, topic=topic, employee=selected_employee, rag_context=rag_ctx
        )
        ideas = ideas[:num_ideas] if isinstance(ideas, list) else [ideas]

        script = ""
        if gen_script and ideas:
            script = analyzer.generate_script(ideas[0], employee=selected_employee)

        # 统一保存到创意历史（无论是否选员工）
        history_store = CreativeHistoryStore()
        history_store.add(
            topic=topic,
            ideas=ideas,
            script=script or "",
            product=product or "",
            industry=industry,
            employee_id=selected_employee.id if selected_employee else "",
        )
        # 员工画像创意记录（若选了员工）
        if selected_employee and ideas:
            record = CreativeRecord(
                employee_id=selected_employee.id,
                topic=topic,
                ideas=ideas,
                script=script or None,
            )
            store.add_creative_record(record)

    st.subheader("步骤 3：AI 推荐创意")
    for i, idea in enumerate(ideas, 1):
        idea = idea if isinstance(idea, dict) else {}
        with st.expander(f"创意 {i}: {idea.get('title', '')}", expanded=True):
            st.write("**钩子**:", idea.get("hook", ""))
            st.write("**标签**:", idea.get("tags", []))
            st.write("**建议时长**:", f"{idea.get('duration', 0)}s")
            st.write("**切入角度**:", idea.get("angle", ""))

    if gen_script and ideas and script:
        st.subheader("拍摄脚本（可发送到内容分析进行评分、编辑后传输视频生成）")
        st.code(script, language=None)
        if st.button("📤 发送到内容分析", key="send_new"):
            if "pending_analyze" not in st.session_state:
                st.session_state["pending_analyze"] = []
            st.session_state["pending_analyze"].append({
                "title": ideas[0].get("title", ""),
                "hook": ideas[0].get("hook", ""),
                "script": script,
                "industry": industry,
                "source": "creative_center",
            })
            st.success("已加入内容分析待处理列表，请切换到「内容分析」页面")
            st.rerun()

# 历史记录
st.divider()
st.subheader("📋 创意历史记录")
history_store = CreativeHistoryStore()
history_list = history_store.list_all(limit=20)
if not history_list:
    st.caption("暂无历史记录，生成创意后将在此展示")
else:
    for h in history_list:
        title = h.get("ideas", [{}])[0].get("title", h.get("topic", "")) if h.get("ideas") else h.get("topic", "")
        with st.expander(f"📌 {h.get('topic', '')[:50]} | {h.get('created_at', '')[:19]}", expanded=False):
            st.write("**主题**", h.get("topic", ""))
            st.write("**产品**", h.get("product", "-"))
            st.write("**行业**", h.get("industry", "-"))
            if h.get("ideas"):
                for i, idea in enumerate(h["ideas"][:3], 1):
                    st.write(f"- 创意{i}:", idea.get("title", ""))
            script_text = h.get("script", "")
            if script_text:
                st.code(script_text[:500] + ("..." if len(script_text) > 500 else ""), language=None)
                if st.button("📤 发送到内容分析", key=f"send_{h['id']}"):
                    if "pending_analyze" not in st.session_state:
                        st.session_state["pending_analyze"] = []
                    st.session_state["pending_analyze"].append({
                        "title": (h.get("ideas") or [{}])[0].get("title", h.get("topic", "")),
                        "hook": (h.get("ideas") or [{}])[0].get("hook", ""),
                        "script": script_text,
                        "industry": h.get("industry", ""),
                        "source": "history",
                    })
                    st.success("已加入内容分析待处理列表")
                    st.rerun()
