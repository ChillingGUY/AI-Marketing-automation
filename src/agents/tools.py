# -*- coding: utf-8 -*-
"""
Agent 工具定义
"""

import json
from pathlib import Path
from typing import Optional

from config import PROCESSED_DATA_DIR, DATA_DIR

ROOT = Path(__file__).resolve().parent.parent.parent


def _load_json(path: Path, default=None):
    if not path.exists():
        return default or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tool_fetch_hot_rank() -> str:
    """获取今日热门视频榜"""
    files = sorted(PROCESSED_DATA_DIR.glob("hot_rank_*.csv"), reverse=True)
    if not files:
        return "暂无热门榜数据，请先运行数据采集。"
    import pandas as pd
    df = pd.read_csv(files[0], encoding="utf-8-sig")
    top = df.head(10)[["title", "play_count", "like_count", "engagement_rate"]]
    return top.to_string()


def tool_get_viral_model() -> str:
    """获取爆款内容模型"""
    files = sorted(PROCESSED_DATA_DIR.glob("ai_analysis_*.json"), reverse=True)
    if not files:
        return "暂无爆款模型，请先运行数据分析。"
    data = _load_json(files[0])
    viral = data.get("viral_model", {})
    return json.dumps(viral, ensure_ascii=False, indent=2)


def tool_rag_retrieve(query: str, top_k: int = 3) -> str:
    """从知识库检索相关内容"""
    try:
        from src.rag.knowledge_base import RAGKnowledgeBase
        rag = RAGKnowledgeBase()
        if not rag.is_available():
            return "RAG 知识库未初始化，请先同步爆款内容库。"
        return rag.retrieve_for_prompt(query, top_k=top_k)
    except Exception as e:
        return f"检索失败: {e}"


def tool_list_employees() -> str:
    """列出员工画像"""
    try:
        from src.employees.store import EmployeeStore
        store = EmployeeStore()
        emps = store.list_all()
        if not emps:
            return "暂无员工画像。"
        lines = [f"- {e.name} | {e.position} | {e.ai_assistant_type}" for e in emps]
        return "\n".join(lines)
    except Exception as e:
        return f"获取失败: {e}"


class AgentTools:
    """Agent 工具集"""

    TOOLS = {
        "fetch_hot_rank": {
            "func": tool_fetch_hot_rank,
            "desc": "获取今日热门视频榜 Top 10",
        },
        "get_viral_model": {
            "func": tool_get_viral_model,
            "desc": "获取最新爆款内容模型",
        },
        "rag_retrieve": {
            "func": tool_rag_retrieve,
            "desc": "从知识库检索相关内容，参数: query(str), top_k(int)=3",
        },
        "list_employees": {
            "func": tool_list_employees,
            "desc": "列出所有员工画像",
        },
    }

    @classmethod
    def run(cls, tool_name: str, **kwargs) -> str:
        t = cls.TOOLS.get(tool_name)
        if not t:
            return f"未知工具: {tool_name}"
        try:
            return str(t["func"](**kwargs))
        except Exception as e:
            return f"执行失败: {e}"
