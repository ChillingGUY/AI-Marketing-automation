# -*- coding: utf-8 -*-
"""
营销 Agent
编排工具调用与 LLM，完成复杂任务
"""

from typing import Optional

from .tools import AgentTools
from src.ai_analysis.llm_client import LLMClient


class MarketingAgent:
    """营销自动化 Agent"""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()
        self.tools = AgentTools

    def _get_tools_desc(self) -> str:
        lines = ["可用工具:"]
        for name, info in AgentTools.TOOLS.items():
            lines.append(f"  - {name}: {info['desc']}")
        return "\n".join(lines)

    def run(self, task: str, max_steps: int = 5) -> str:
        """
        执行任务
        支持：分析今日趋势、生成创意、检索知识等
        """
        tools_desc = self._get_tools_desc()
        sys_prompt = f"""你是营销自动化助手。根据用户任务，选择并调用合适工具，最后给出回答。
{tools_desc}

调用工具格式（仅当需要时）: TOOL: 工具名 | 参数1=值1 | 参数2=值2
例如: TOOL: rag_retrieve | query=搞笑创意 | top_k=3
例如: TOOL: fetch_hot_rank
若无须调用工具，直接回答。"""

        messages = [{"role": "system", "content": sys_prompt}]
        user_msg = f"用户任务: {task}"
        messages.append({"role": "user", "content": user_msg})

        if not self.llm.is_available():
            if "热门" in task or "趋势" in task:
                return AgentTools.run("fetch_hot_rank")
            if "爆款" in task or "模型" in task:
                return AgentTools.run("get_viral_model")
            return "请配置 OPENAI_API_KEY 以使用 Agent。"

        user_content = user_msg
        for step in range(max_steps):
            resp = self.llm.chat(sys_prompt, user_content)
            if "TOOL:" not in resp:
                return resp
            try:
                line = resp.split("TOOL:")[1].strip().split("\n")[0]
                parts = [p.strip() for p in line.split("|")]
                tool_name = parts[0]
                kwargs = {}
                for p in parts[1:]:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        v = v.strip().strip('"\'')
                        if k.strip() == "top_k":
                            v = int(v)
                        kwargs[k.strip()] = v
                result = AgentTools.run(tool_name, **kwargs)
                user_content = f"{user_content}\n\n[上轮助手响应]\n{resp}\n\n[工具{tool_name}返回]\n{result}\n\n请基于工具结果完成任务并给出最终回答。"
            except Exception as e:
                user_content = f"{user_content}\n\n工具调用出错: {e}\n请直接基于已有信息回答。"

        return "达到最大步数，任务未完成。"

    def analyze_trends(self) -> str:
        """数据分析：今日趋势摘要"""
        rank = AgentTools.run("fetch_hot_rank")
        viral = AgentTools.run("get_viral_model")
        if self.llm.is_available():
            return self.llm.chat(
                "你是数据分析师，根据以下数据写一段简短的今日趋势分析（3-5句话）。",
                f"热门榜:\n{rank}\n\n爆款模型:\n{viral}",
            )
        return f"热门榜:\n{rank}\n\n爆款模型:\n{viral}"

    def generate_with_rag(self, topic: str, employee_id: Optional[str] = None) -> str:
        """RAG 增强的创意生成"""
        rag = AgentTools.run("rag_retrieve", query=topic, top_k=3)
        viral = AgentTools.run("get_viral_model")
        context = f"知识库参考:\n{rag}\n\n爆款模型:\n{viral}"
        if self.llm.is_available():
            return self.llm.chat(
                "根据知识库和爆款模型，为以下主题生成 3 个短视频创意，JSON 数组格式。",
                f"主题: {topic}\n\n{context}",
            )
        return context
