# -*- coding: utf-8 -*-
"""
AI营销自动化平台 - 配置模块
营销数据分析模块
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RAW_DATA_DIR = DATA_DIR / "raw"  # 原始数据
PROCESSED_DATA_DIR = DATA_DIR / "processed"  # 处理后数据
RAW_DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DATA_DIR.mkdir(exist_ok=True)

# TikHub API 配置
TIKHUB_API_BASE = os.getenv("TIKHUB_API_BASE", "https://api.tikhub.io")
TIKHUB_API_TOKEN = os.getenv("TIKHUB_API_TOKEN", "")

# 中国大陆用户可使用
# TIKHUB_API_BASE = "https://api.tikhub.dev"

# LLM 配置
# 优先使用 provider 指定：openai | dashscope(通义) | 空则自动检测
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower() or None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
# 通义千问 / 百炼
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen3-max")

# Phase 2：工作流与数据库
USE_WORKFLOW = os.getenv("USE_WORKFLOW", "true").lower() in ("1", "true", "yes")
DB_PATH = os.getenv("DB_PATH", "")  # 空则使用 data/yingxiao.db

# 演示模式：True 时始终使用预置 demo CSV，适合公司演示
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
DEMO_DATA_PATH = os.getenv("DEMO_DATA_PATH", "")  # 空则使用 data/raw/demo_tiktok_hot.csv

# Kling 视频生成（营销/电商）
KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_API_KEY = os.getenv("KLING_API_KEY", "")  # 单密钥模式（可选）
# 中国区默认 api-beijing.klingai.com
KLING_API_BASE = os.getenv("KLING_API_BASE", "https://api-beijing.klingai.com")
# 生成视频本地保存目录
VIDEO_SAVE_DIR = Path(os.getenv("VIDEO_SAVE_DIR", "D:/movie"))

# 抓取配置
FETCH_CONFIG = {
    "period": 7,  # 时间范围（天）
    "limit": 50,  # 每页数量
    "order_by": "vv",  # 排序: vv(观看量) | like(点赞) | comment(评论) | repost(转发)
    "country_code": "US",  # 国家代码
    "max_pages": 2,  # 最大抓取页数
    "enrich_metrics": False,  # 关闭可降成本；列表数据通常已含基础统计
    "enrich_batch_size": 5,  # 批量拉取统计时的并发/间隔控制
}
