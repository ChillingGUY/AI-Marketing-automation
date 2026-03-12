# -*- coding: utf-8 -*-
"""数据库连接与会话"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from config import DATA_DIR

# 支持环境变量覆盖
DB_PATH_ENV = os.getenv("DB_PATH", "")


def get_db_path() -> Path:
    """获取 SQLite 数据库路径"""
    if DB_PATH_ENV:
        p = Path(DB_PATH_ENV)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / "yingxiao.db"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    path = get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
