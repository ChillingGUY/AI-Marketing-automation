# -*- coding: utf-8 -*-
"""
视频生成任务持久化 - F5 刷新不丢失
"""

import json
from pathlib import Path
from typing import Any

from config import DATA_DIR

VIDEO_TASKS_FILE = DATA_DIR / "video_tasks.json"


def load_video_tasks() -> list[dict[str, Any]]:
    """从磁盘加载任务列表"""
    if not VIDEO_TASKS_FILE.exists():
        return []
    try:
        with open(VIDEO_TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_video_tasks(tasks: list[dict[str, Any]]) -> None:
    """保存任务列表到磁盘"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # 仅保留可序列化字段
    out = []
    for t in tasks:
        clean = {
            k: v for k, v in t.items()
            if k in ("task_id", "task_ids", "video_provider", "title", "hook", "script", "industry",
                     "status", "video_url", "local_path", "prompt_used", "error", "segment_count", "segment_urls",
                     "use_post_production", "voice_gender")
            and isinstance(v, (str, int, float, bool, type(None), list))
        }
        out.append(clean)
    with open(VIDEO_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
