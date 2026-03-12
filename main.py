# -*- coding: utf-8 -*-
"""
AI营销自动化平台 - 营销数据分析模块
主入口：数据采集 → ETL → 输出
"""

import sys
import io
from pathlib import Path

# 确保项目根目录在 path 中
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import TIKHUB_API_TOKEN, FETCH_CONFIG, DEMO_MODE, DEMO_DATA_PATH
from src.data_source.tiktok_fetcher import TikTokHotVideoFetcher
from src.data_processing.etl import ETLProcessor
from src.ai_analysis.analysis_runner import AnalysisRunner


def run_fetch_and_etl(use_demo: bool = False):
    """执行抓取 + ETL"""
    print("=" * 50)
    print("营销数据分析模块 - 数据采集")
    print("=" * 50)

    videos = []
    demo_path = Path(DEMO_DATA_PATH) if DEMO_DATA_PATH else ROOT / "data" / "raw" / "demo_tiktok_hot.csv"
    sample_path = ROOT / "data" / "raw" / "sample_tiktok_hot.csv"

    # 演示模式：始终使用预置 demo 数据（适合公司演示）
    if DEMO_MODE and demo_path.exists():
        from src.data_source.csv_import import import_from_csv
        videos = import_from_csv(demo_path)
        print("\n[演示模式] 使用预置演示数据，流程稳定、无需 API")
        print(f"数据文件: {demo_path} ({len(videos)} 条)\n")
    elif use_demo or not TIKHUB_API_TOKEN:
        if not TIKHUB_API_TOKEN:
            print("\n[提示] 未配置 TIKHUB_API_TOKEN")
            print("使用示例数据演示流程。配置 Token 后可从 TikHub 实时抓取。")
            print("公司演示建议设置 DEMO_MODE=true 使用 data/raw/demo_tiktok_hot.csv")
            print("注册地址: https://tikhub.io\n")
        fallback = demo_path if demo_path.exists() else sample_path
        if fallback.exists():
            from src.data_source.csv_import import import_from_csv
            videos = import_from_csv(fallback)
            print(f"已加载示例数据: {fallback} ({len(videos)} 条)")
        else:
            print("示例数据不存在，请配置 TIKHUB_API_TOKEN 或创建 data/raw/demo_tiktok_hot.csv")
            return
    else:
        fetcher = TikTokHotVideoFetcher()
        print("正在抓取 TikTok 热门视频...")
        videos = fetcher.fetch_hot_videos(
            max_pages=FETCH_CONFIG["max_pages"],
            enrich_metrics=FETCH_CONFIG["enrich_metrics"],
            batch_delay=1.0,
        )

    if not videos:
        print("未获取到视频数据，请检查 API 配置或网络。")
        return

    print(f"抓取完成，共 {len(videos)} 条视频")

    etl = ETLProcessor()
    print("执行 ETL 处理...")
    processed_df, raw_path, processed_path = etl.process(videos)

    print(f"原始数据已保存: {raw_path}")
    print(f"处理后数据已保存: {processed_path}")

    # AI 分析
    print("\n执行 AI 分析...")
    runner = AnalysisRunner()
    analysis = runner.run(processed_df, top_n=5, topic="营销", save=True)
    if analysis.get("_saved_path"):
        print(f"AI 分析结果已保存: {analysis['_saved_path']}")
        from src.knowledge.viral_library import ViralContentLibrary
        n = ViralContentLibrary().sync_from_analysis(Path(analysis["_saved_path"]))
        if n:
            print(f"已同步 {n} 条到爆款内容库")
        try:
            from src.rag.knowledge_base import RAGKnowledgeBase
            r = RAGKnowledgeBase()
            if r.sync_from_viral_library():
                print("已同步 RAG 知识库")
        except Exception:
            pass
    viral = analysis.get("viral_model", {})
    ideas = analysis.get("ai_ideas", [])
    if viral:
        print("\n爆款内容模型要点:", viral.get("script_formula", viral.get("common_patterns", [])))
    if ideas:
        print("\nAI 推荐创意示例:", ideas[0].get("title", ideas[0]) if ideas else "-")

    # 简单输出今日热门榜
    print("\n" + "=" * 50)
    print("今日热门视频榜（Top 10）")
    print("=" * 50)
    top = processed_df.head(10)
    for _, row in top.iterrows():
        rank = row["rank"]
        title = (row["title"] or "")[:40] + ("..." if len(str(row["title"] or "")) > 40 else "")
        play = row["play_count"]
        like = row["like_count"]
        dur = row["duration"]
        print(f"  {rank:2}. {title}")
        print(f"      播放:{play} 点赞:{like} 时长:{dur}s")
        print()

    print("完成。")
    return processed_df, raw_path, processed_path


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    run_fetch_and_etl()
