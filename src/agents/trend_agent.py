# -*- coding: utf-8 -*-
"""
趋势分析 Agent
输入：analysis_result (hot_rank)
输出：trend_ids，写入 trends 表
"""

from typing import Any

from src.db.models import insert_trend, insert_agent_log
from src.agents.base import BaseAgent


class TrendAgent(BaseAgent):
    name = "trend"

    def run(self, state: dict) -> dict:
        analysis = state.get("analysis_result") or {}
        hot_rank = analysis.get("hot_rank") or []

        trend_ids = []
        for item in hot_rank[:20]:  # 最多 20 条
            tid = insert_trend(
                platform="TikTok",
                video_url=str(item.get("video_url", ""))[:500],
                likes=int(item.get("like_count", 0) or 0),
                comments=int(item.get("comment_count", 0) or 0),
                views=int(item.get("play_count", 0) or 0),
                topic=str(item.get("tags", "") or item.get("title", ""))[:200],
            )
            trend_ids.append(tid)

        task_desc = f"写入 {len(trend_ids)} 条趋势"
        insert_agent_log(self.name, task_desc, f"trend_ids={trend_ids}")

        return {
            "trend_data": hot_rank,
            "trend_ids": trend_ids,
        }
