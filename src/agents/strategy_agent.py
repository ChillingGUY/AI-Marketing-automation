# -*- coding: utf-8 -*-
"""
内容策略 Agent
输入：trend_data / analysis_result (viral_model, ai_ideas)
输出：strategy_output, script_ids（写入 scripts 表 title/hook/industry）
"""

from typing import Any

from src.db.models import insert_script, insert_agent_log
from src.agents.base import BaseAgent


class StrategyAgent(BaseAgent):
    name = "strategy"

    def run(self, state: dict) -> dict:
        analysis = state.get("analysis_result") or {}
        ideas = analysis.get("ai_ideas") or []

        if not ideas:
            ideas = [
                {"title": "营销干货分享", "hook": "3个技巧", "industry": "营销", "tags": ["干货"]},
            ]

        script_ids = []
        for idea in ideas[:5]:
            title = str(idea.get("title", ""))
            hook = str(idea.get("hook", ""))
            industry = str(idea.get("industry", "营销"))
            sid = insert_script(
                title=title,
                hook=hook,
                script="",
                scene="",
                industry=industry,
                trend_id=state.get("trend_ids", [None])[0] if state.get("trend_ids") else None,
            )
            script_ids.append(sid)

        task_desc = f"生成 {len(script_ids)} 个策略并写入脚本"
        insert_agent_log(self.name, task_desc, f"script_ids={script_ids}")

        return {
            "strategy_output": ideas,
            "script_ids": script_ids,
        }
