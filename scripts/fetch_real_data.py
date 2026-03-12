# -*- coding: utf-8 -*-
"""
获取真实今日热门视频（可播放 + 真实播放量/点赞）
需先配置 TIKHUB_API_TOKEN
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

if not os.getenv("TIKHUB_API_TOKEN"):
    print("=" * 60)
    print("请先配置 TIKHUB_API_TOKEN 以获取真实热门视频")
    print("=" * 60)
    print("1. 复制 .env.example 为 .env")
    print("2. 在 https://tikhub.io 注册并创建 API Token")
    print("3. 在 .env 中填入: TIKHUB_API_TOKEN=your_token")
    print()
    print("配置完成后运行: python run_all.py")
    sys.exit(1)

from run_all import run
run()
print("\n数据已更新，刷新 dashboard 即可看到真实可播放视频。")
