# -*- coding: utf-8 -*-
"""
热门趋势看板 - Streamlit 可视化
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR

st.set_page_config(page_title="营销数据分析", page_icon="📊", layout="wide")
st.title("📊 趋势分析")
st.caption("平台 5 大模块：趋势分析 | 创意中心 | 脚本中心 | 视频生成 | 数据分析")

# 价值展示
with st.container():
    v1, v2, v3 = st.columns(3)
    with v1:
        st.metric("核心价值", "AI 内容工厂", "全流程自动化")
    with v2:
        st.metric("效率", "约 10 分钟", "完成一个视频")
    with v3:
        st.metric("产能", "1 天约 100 条", "内容生产")

# 读取最新处理后的数据
processed_files = sorted(PROCESSED_DATA_DIR.glob("hot_rank_*.csv"), reverse=True)
raw_files = sorted(RAW_DATA_DIR.glob("tiktok_hot_*.csv"), reverse=True)

if not processed_files:
    st.warning("暂无处理后数据，请先运行 `python main.py` 进行数据采集。")
    st.stop()

@st.cache_data(ttl=300)
def load_latest():
    df = pd.read_csv(processed_files[0], encoding="utf-8-sig")
    return df, processed_files[0].name

df, fname = load_latest()

# 判断是否为真实 TikHub 数据
def _is_real_data(df):
    if df.empty:
        return False
    if "source" in df.columns and (df["source"] == "tikhub").any():
        return True
    return not df["video_id"].astype(str).str.match(r"^(sample_|demo_)").any()

def _is_demo_data(df):
    return df["video_id"].astype(str).str.startswith("demo_").any()

is_real_data = _is_real_data(df)
is_demo_data = _is_demo_data(df)

if not is_real_data:
    if is_demo_data:
        st.info("**演示模式**：使用预置演示数据，适合公司展示。数据涵盖职场、营销、带货、美食等热门场景。")
    else:
        st.info(
            "**当前为演示数据**：链接为占位符，播放量/点赞为模拟值。"
            "公司演示建议设置 `DEMO_MODE=true` 使用 `data/raw/demo_tiktok_hot.csv`。"
        )

st.caption(f"数据来源: {fname}")

# 今日热门视频榜（模块 1：趋势分析 - 热门视频）
st.subheader("今日热门视频榜")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    top_n = st.slider("显示条数", 5, 50, 10)
with col2:
    sort_by = st.selectbox("排序", ["play_count", "like_count", "engagement_rate"], format_func=lambda x: {"play_count": "播放量", "like_count": "点赞数", "engagement_rate": "互动率"}[x])
with col3:
    pass

df_sorted = df.sort_values(sort_by, ascending=False).head(top_n)

for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
    with st.expander(f"#{i} {str(row['title'])[:60]}...", expanded=(i <= 3)):
        c1, c2, c3 = st.columns(3)
        c1.metric("播放", f"{int(row['play_count']):,}")
        c2.metric("点赞", f"{int(row['like_count']):,}")
        c3.metric("互动率", f"{row['engagement_rate']:.2%}")
        st.caption(f"时长 {int(row['duration'])}s | 标签: {row.get('tags', '')}")
        vid = str(row.get("video_id", ""))
        url = str(row.get("video_url", "") or "").strip()
        if is_real_data and url and not vid.startswith("sample_"):
            st.link_button("查看视频", url)
        elif not is_real_data:
            st.caption("演示数据。配置 TIKHUB_API_TOKEN 并运行 python run_all.py 可获取真实可播放的今日热门视频。")

# 趋势概览（模块 1：爆款结构）
st.subheader("趋势概览")
df_agg = df.agg({
    "play_count": "sum",
    "like_count": "sum",
    "comment_count": "sum",
    "duration": "mean",
}).round(1)
m1, m2, m3, m4 = st.columns(4)
m1.metric("总播放", f"{int(df_agg['play_count']):,}")
m2.metric("总点赞", f"{int(df_agg['like_count']):,}")
m3.metric("总评论", f"{int(df_agg['comment_count']):,}")
m4.metric("平均时长", f"{df_agg['duration']:.0f}s")

# 时长分布
st.subheader("视频时长分布")
dur_bins = [0, 15, 30, 60, 120, 999]
dur_labels = ["0-15s", "15-30s", "30-60s", "60-120s", "120s+"]
df["dur_bin"] = pd.cut(df["duration"], bins=dur_bins, labels=dur_labels)
st.bar_chart(df["dur_bin"].value_counts().sort_index())

# 加载 AI 分析结果（如有）
ai_files = sorted(PROCESSED_DATA_DIR.glob("ai_analysis_*.json"), reverse=True)
if ai_files:
    st.divider()
    st.subheader("AI 分析摘要")
    import json
    with open(ai_files[0], "r", encoding="utf-8") as f:
        ai = json.load(f)
    viral = ai.get("viral_model", {})
    if viral:
        st.write("**爆款结构**")
        st.json(viral)
    ideas = ai.get("ai_ideas", [])
    if ideas:
        st.write("**AI 推荐创意**")
        for j, idea in enumerate(ideas[:3], 1):
            st.write(f"{j}. {idea.get('title', '')} | 标签: {idea.get('tags', [])}")
