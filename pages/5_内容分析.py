# -*- coding: utf-8 -*-
"""
内容分析 - 分析、评分、编辑脚本，传输给视频生成
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(page_title="内容分析", page_icon="📊", layout="wide")
st.title("📊 内容分析")
st.caption("分析脚本、评分（创意/营销价值/传播潜力）、编辑内容，传输给视频生成制作")

# 初始化 session
if "pending_analyze" not in st.session_state:
    st.session_state["pending_analyze"] = []
if "pending_video" not in st.session_state:
    st.session_state["pending_video"] = []

tab1, tab2, tab3 = st.tabs(["待分析（创意中心发送）", "工作流脚本库", "已传输视频生成"])

def _render_script_card(item: dict, source: str, key_prefix: str):
    """渲染单个脚本卡片：分析、编辑、传输"""
    title = item.get("title", "(无标题)")
    hook = item.get("hook", "")
    script = item.get("script", "")
    industry = item.get("industry", "")
    score_data = item.get("score_data")
    script_id = item.get("id")

    with st.expander(f"📄 {title[:50]} | 评分: {score_data.get('score', '-') if score_data else '待分析'}", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**标题**", title)
            st.write("**钩子**", hook)
            st.write("**行业**", industry)
        with col2:
            if score_data:
                s = score_data.get("score", 0)
                st.metric("综合评分", f"{s:.0f}", "/ 100")
                st.caption(f"创意 {score_data.get('creative_score', 0)} | 营销 {score_data.get('marketing_value', 0)} | 传播 {score_data.get('spread_potential', 0)}")

        edited = st.text_area("脚本内容（可编辑，含完整 0-26 秒分镜）", script, height=280, key=f"{key_prefix}_ta")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("🔍 分析评分", key=f"{key_prefix}_analyze"):
                try:
                    from src.agents.score_agent import ScoreAgent
                    agent = ScoreAgent()
                    score_result = agent._score_script(title, hook, edited)
                    item["score_data"] = score_result
                    if script_id and source == "workflow":
                        from src.db.models import update_script_score, update_script_content
                        update_script_score(script_id, score_result["score"])
                        update_script_content(script_id, script=edited)
                    else:
                        item["script"] = edited
                    st.success(f"评分: {score_result['score']} 分")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        with btn_col2:
            if st.button("📤 传输给视频生成", key=f"{key_prefix}_send"):
                st.session_state["pending_video"].append({
                    "title": title,
                    "hook": hook,
                    "script": edited,
                    "industry": industry,
                    "score": item.get("score_data", {}).get("score") if item.get("score_data") else None,
                })
                st.success("已传输到视频生成，请在「视频生成」页面查看")
                st.rerun()
        if source == "workflow" and script_id:
            with btn_col3:
                if st.button("保存修改", key=f"{key_prefix}_save"):
                    try:
                        from src.db.models import update_script_content
                        update_script_content(script_id, script=edited)
                        st.success("已保存")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

with tab1:
    st.write("从创意中心「发送到内容分析」的脚本将在此展示")
    pending = st.session_state.get("pending_analyze", [])
    if not pending:
        st.info("暂无待分析脚本。请在创意中心生成创意后点击「发送到内容分析」")
    else:
        for i, item in enumerate(pending):
            _render_script_card(item, "pending", f"p{i}")

with tab2:
    try:
        from src.db.models import list_scripts_with_scores, init_tables
        init_tables()
        scripts = list_scripts_with_scores(limit=30)
    except ImportError:
        scripts = []
    if not scripts:
        st.info("暂无工作流脚本。请先运行 `python run_all.py` 完成工作流编排。")
    else:
        for s in scripts:
            item = {
                "id": s["id"],
                "title": s.get("title", ""),
                "hook": s.get("hook", ""),
                "script": s.get("script", ""),
                "industry": s.get("industry", ""),
                "score_data": {"score": s.get("score")} if s.get("score") is not None else None,
            }
            if item["score_data"]:
                item["score_data"]["creative_score"] = item["score_data"]["marketing_value"] = item["score_data"]["spread_potential"] = s.get("score")
            _render_script_card(item, "workflow", f"w{s['id']}")

with tab3:
    st.write("已传输给视频生成的脚本，可在「视频生成」页面进行制作")
    pending_v = st.session_state.get("pending_video", [])
    if not pending_v:
        st.info("暂无已传输脚本。在待分析或工作流库中点击「传输给视频生成」")
    else:
        for i, p in enumerate(pending_v):
            with st.expander(f"🎬 {p.get('title', '')[:50]}"):
                st.text_area("脚本", p.get("script", ""), height=200, disabled=True, key=f"sent_script_{i}", label_visibility="collapsed")
                if st.button("移除", key=f"rm_{i}"):
                    st.session_state["pending_video"] = [x for j, x in enumerate(pending_v) if j != i]
                    st.rerun()
