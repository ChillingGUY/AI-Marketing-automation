# -*- coding: utf-8 -*-
"""
定时任务 - 每日自动执行
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import schedule
import time
from run_all import run


def job():
    print(f"[{__import__('datetime').datetime.now()}] 执行定时任务...")
    run()
    print("定时任务完成。")


if __name__ == "__main__":
    # 每天 9:00 执行
    schedule.every().day.at("09:00").do(job)
    # 立即执行一次（可选）
    # job()

    print("定时任务已启动，每天 09:00 执行。Ctrl+C 退出。")
    while True:
        schedule.run_pending()
        time.sleep(60)
