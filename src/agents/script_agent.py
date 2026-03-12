# -*- coding: utf-8 -*-
"""
脚本生成 Agent
输入：strategy_output (ideas), script_ids
输出：script_output，更新 scripts 表的 script/scene
"""

from typing import Any

from src.db.models import insert_agent_log
from src.db.session import get_connection
from src.ai_analysis.analyzer import LLMAnalyzer
from src.ai_analysis.llm_client import LLMClient
from src.agents.base import BaseAgent


class ScriptAgent(BaseAgent):
    name = "script"

    def __init__(self, llm=None):
        self.analyzer = LLMAnalyzer(llm or LLMClient())

    def run(self, state: dict) -> dict:
        ideas = state.get("strategy_output") or []
        script_ids = state.get("script_ids") or []

        script_output = []
        conn = get_connection()
        cur = conn.cursor()

        for i, idea in enumerate(ideas[: len(script_ids)]):
            sid = script_ids[i] if i < len(script_ids) else None
            script_text = self.analyzer.generate_script(idea)

            # 简单解析：前 100 字作 scene，其余作 script
            scene = script_text[:150].replace("\n", " ") if script_text else ""
            script_full = script_text or ""

            if sid:
                cur.execute(
                    "UPDATE scripts SET script = ?, scene = ? WHERE id = ?",
                    (script_full, scene, sid),
                )
                script_output.append({"script_id": sid, "script": script_full[:200], "scene": scene})

        conn.commit()
        conn.close()

        task_desc = f"补全 {len(script_output)} 个脚本"
        insert_agent_log(self.name, task_desc, f"updated {len(script_output)} scripts")

        return {
            "script_output": script_output,
        }
