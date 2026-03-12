# -*- coding: utf-8 -*-
"""数据库层"""

from .session import get_db_path, get_connection
from .models import (
    init_tables,
    insert_trend,
    insert_script,
    insert_video,
    insert_agent_log,
    list_trends,
    list_scripts,
    list_scripts_with_scores,
    update_script_score,
    update_script_content,
)

__all__ = [
    "get_db_path",
    "get_connection",
    "init_tables",
    "insert_trend",
    "insert_script",
    "insert_video",
    "insert_agent_log",
    "list_trends",
    "list_scripts",
    "list_scripts_with_scores",
    "update_script_score",
    "update_script_content",
]
