# -*- coding: utf-8 -*-
"""
按顺序执行完整流程
1. 数据采集 → 2. ETL → 3. AI 分析 → 4. 工作流编排(可选) → 5. 热门趋势看板(需单独启动) → 6. 自动化推送
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import run_fetch_and_etl
from config import TIKHUB_API_TOKEN, PROCESSED_DATA_DIR, USE_WORKFLOW, DEMO_MODE
from src.automation.feishu import FeishuBot
import json


def run():
    print("=" * 60)
    print("AI 营销自动化平台 - 按顺序执行")
    print("=" * 60)

    # 1. 数据采集 + ETL + AI 分析（DEMO_MODE 或 无 Token 时使用预置数据）
    run_fetch_and_etl(use_demo=DEMO_MODE or not TIKHUB_API_TOKEN)

    # 加载最新 AI 分析结果（用于工作流、飞书推送）
    ai_files = sorted(PROCESSED_DATA_DIR.glob("ai_analysis_*.json"), reverse=True)
    result = {}
    if ai_files:
        with open(ai_files[0], "r", encoding="utf-8") as f:
            result = json.load(f)

    # 2. 工作流编排（Phase 2：趋势→策略→脚本→评分 入库）
    if USE_WORKFLOW and result:
        print("\n" + "=" * 60)
        print("工作流编排 (Trend → Strategy → Script → Score)")
        print("=" * 60)
        try:
            from src.db.models import init_tables
            from src.workflow.state import initial_state
            from src.workflow.graph import get_app

            init_tables()
            initial = initial_state(analysis_result=result)
            app = get_app()
            final = app.invoke(initial)
            n_trends = len(final.get("trend_ids", []))
            n_scripts = len(final.get("script_ids", []))
            print(f"趋势入库: {n_trends} 条 | 脚本入库: {n_scripts} 条")
            if final.get("scores"):
                print("内容分析完成")
        except Exception as e:
            print(f"工作流执行失败: {e}")

    # 3. 热门趋势看板（需单独启动）
    print("\n" + "=" * 60)
    print("4. 热门趋势看板")
    print("=" * 60)
    print("请执行: streamlit run dashboard.py")
    print("侧边栏：趋势分析、创意中心、爆款库、员工画像、Agent与RAG、内容分析、视频生成(规划中)")

    # 5. 自动化推送（飞书）
    print("\n" + "=" * 60)
    print("5. 自动化推送（飞书）")
    print("=" * 60)
    bot = FeishuBot()
    if bot.is_available():
        ok1 = bot.send_daily_report(
            result.get("hot_rank", []),
            viral_summary=json.dumps(result.get("viral_model", {}), ensure_ascii=False)[:300],
        )
        ok2 = bot.send_creative_push(result.get("ai_ideas", []))
        print(f"日报推送: {'成功' if ok1 else '失败'}")
        print(f"创意推送: {'成功' if ok2 else '失败'}")
    else:
        print("未配置飞书 (FEISHU_APP_ID/SECRET/CHAT_ID)，跳过推送。")
        print("配置 .env 后即可启用自动日报和创意推送。")

    print("\n" + "=" * 60)
    print("全部流程执行完毕。")
    print("=" * 60)


if __name__ == "__main__":
    run()
