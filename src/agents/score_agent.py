# -*- coding: utf-8 -*-
"""
内容评分 Agent
输入：script_ids，从 DB 读取脚本
输出：scores (creative_score, marketing_value, spread_potential, score)
"""

import json
from typing import Any

from src.db.models import insert_agent_log, update_script_score
from src.db.session import get_connection
from src.ai_analysis.llm_client import LLMClient
from src.agents.base import BaseAgent


class ScoreAgent(BaseAgent):
    name = "score"

    def __init__(self, llm=None):
        self.llm = llm or LLMClient()

    def run(self, state: dict) -> dict:
        script_ids = state.get("script_ids") or []
        if not script_ids:
            return {"scores": []}

        conn = get_connection()
        cur = conn.cursor()
        scores_out = []

        for sid in script_ids:
            cur.execute("SELECT id, title, hook, script FROM scripts WHERE id = ?", (sid,))
            row = cur.fetchone()
            if not row:
                continue

            script_row = dict(row)
            title = script_row.get("title", "") or ""
            hook = script_row.get("hook", "") or ""
            script_text = script_row.get("script", "") or ""

            score_result = self._score_script(title, hook, script_text)
            total = score_result.get("score", 0)
            update_script_score(sid, total)
            score_result["script_id"] = sid
            scores_out.append(score_result)

        conn.close()

        task_desc = f"评分 {len(scores_out)} 个脚本"
        insert_agent_log(self.name, task_desc, str(scores_out))

        return {"scores": scores_out}

    def _score_script(self, title: str, hook: str, script: str) -> dict:
        """调用 LLM 对脚本评分"""
        default = {
            "creative_score": 60,
            "marketing_value": 60,
            "spread_potential": 60,
            "score": 60,
        }

        if not self.llm.is_available():
            return default

        sys_p = """你是短视频内容评审专家。对以下脚本从三个维度打分（0-100）：
1. creative_score：创意评分（新颖度、吸引力）
2. marketing_value：营销价值（商业转化潜力）
3. spread_potential：传播潜力（病毒传播可能）
最终 score 为三者平均，四舍五入取整。
只返回 JSON，如：{"creative_score": 75, "marketing_value": 80, "spread_potential": 70, "score": 75}"""

        content = f"标题：{title}\n钩子：{hook}\n脚本：{script[:800]}"
        out = self.llm.chat(sys_p, content)
        if not out:
            return default

        try:
            # 尝试提取 JSON
            text = out.strip()
            if "```" in text:
                for part in text.split("```"):
                    if "{" in part and "}" in part:
                        text = part
                        break
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                obj = json.loads(text[start:end])
                cs = int(obj.get("creative_score", 60))
                mv = int(obj.get("marketing_value", 60))
                sp = int(obj.get("spread_potential", 60))
                s = int(obj.get("score", (cs + mv + sp) // 3))
                return {
                    "creative_score": min(100, max(0, cs)),
                    "marketing_value": min(100, max(0, mv)),
                    "spread_potential": min(100, max(0, sp)),
                    "score": min(100, max(0, s)),
                }
        except (json.JSONDecodeError, ValueError):
            pass
        return default
