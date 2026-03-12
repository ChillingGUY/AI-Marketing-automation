# -*- coding: utf-8 -*-
"""
初始化数据库表
执行: python scripts/init_db.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db.models import init_tables
from src.db.session import get_db_path


def main():
    path = get_db_path()
    print(f"初始化数据库: {path}")
    init_tables()
    print("表创建完成: trends, scripts, videos, agents_log")


if __name__ == "__main__":
    main()
