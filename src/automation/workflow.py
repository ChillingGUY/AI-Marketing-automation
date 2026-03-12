# -*- coding: utf-8 -*-
"""
自动化工作流编排
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent.parent


def run_full_pipeline() -> dict:
    """
    完整自动化流水线
    数据采集 → ETL → AI 分析 → 知识库同步 → RAG 同步 → 飞书推送
    """
    result = {"steps": [], "success": True}
    try:
        from run_all import run
        run()
        result["steps"].append(("full", "完成", str(datetime.now())))
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    return result


def run_data_only() -> dict:
    """仅数据采集 + ETL + 分析"""
    result = {"steps": [], "success": True}
    try:
        from main import run_fetch_and_etl
        run_fetch_and_etl(use_demo=not __import__("os").getenv("TIKHUB_API_TOKEN"))
        result["steps"].append(("data", "完成", str(datetime.now())))
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    return result


def run_rag_sync() -> dict:
    """仅 RAG 知识库同步"""
    result = {"steps": [], "success": True}
    try:
        from src.rag.knowledge_base import RAGKnowledgeBase
        rag = RAGKnowledgeBase()
        n = rag.sync_from_viral_library()
        result["steps"].append(("rag_sync", str(n), str(datetime.now())))
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    return result
