# -*- coding: utf-8 -*-
"""视频生成模块 - Kling / 万象2.6 对接"""

from .kling_client import KlingClient, script_to_prompt
from .wanxiang_client import WanxiangClient

__all__ = ["KlingClient", "WanxiangClient", "script_to_prompt"]
