# -*- coding: utf-8 -*-
"""
爆款内容库 - 营销知识库
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from config import PROCESSED_DATA_DIR
from src.knowledge.viral_library import ViralContentLibrary

st.set_page_config(page_title="爆款内容库", page_icon="📚", layout="wide")
st.title("📚 爆款内容库")
st.caption("趋势分析·爆款结构 | 支持创意中心 RAG 增强检索")

lib = ViralContentLibrary()

# 同步按钮
ai_files = sorted(PROCESSED_DATA_DIR.glob("ai_analysis_*.json"), reverse=True)
if ai_files and st.button("从最新分析同步到知识库"):
    n = lib.sync_from_analysis(ai_files[0])
    st.success(f"已同步 {n} 条记录")

st.subheader("爆款模型")
models = lib.list_viral_models(limit=10)
if not models:
    st.info("暂无爆款模型，请先运行数据分析并同步。")
else:
    for m in models:
        with st.expander(f"📌 {m.get('_date', '')}", expanded=False):
            st.json({k: v for k, v in m.items() if not k.startswith("_")})

st.subheader("按标签检索拆解")
tags_input = st.text_input("输入标签（逗号分隔）", placeholder="例如：开箱, 测评, 美食")
if tags_input and st.button("检索"):
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    results = lib.search_by_tags(tags, limit=10)
    if not results:
        st.warning("未找到匹配的拆解")
    for r in results:
        st.write("**视频**:", r.get("title", r.get("video_id", "")))
        st.caption(str(r.get("tags", "")))
