# -*- coding: utf-8 -*-
"""
飞书机器人
自动日报、创意推送
"""

import json
import os
from typing import Optional

import requests


class FeishuBot:
    """飞书机器人"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.app_id = app_id or os.getenv("FEISHU_APP_ID", "")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET", "")
        self.chat_id = chat_id or os.getenv("FEISHU_CHAT_ID", "")
        self._token: Optional[str] = None

    def _get_token(self) -> Optional[str]:
        """获取 tenant_access_token"""
        if not self.app_id or not self.app_secret:
            return None
        if self._token:
            return self._token
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            self._token = data.get("tenant_access_token")
        return self._token

    def is_available(self) -> bool:
        return bool(self.app_id and self.app_secret and self.chat_id)

    def send_text(self, text: str) -> bool:
        """发送文本消息"""
        token = self._get_token()
        if not token or not self.chat_id:
            return False
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "chat_id"}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "receive_id": self.chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }
        resp = requests.post(url, params=params, headers=headers, json=payload, timeout=10)
        return resp.status_code == 200 and resp.json().get("code") == 0

    def send_daily_report(self, hot_rank: list, viral_summary: str = "") -> bool:
        """发送自动日报"""
        def _v(x, default=0):
            if x is None or (isinstance(x, float) and x != x):
                return default
            return x

        lines = ["【营销数据分析 - 自动日报】\n", "今日热门视频榜 Top 5：\n"]
        for i, r in enumerate(hot_rank[:5], 1):
            t = _v(r.get("title"), "")
            title = (str(t)[:30] + ("..." if len(str(t)) > 30 else ""))
            play = int(_v(r.get("play_count"), 0) or 0)
            like = int(_v(r.get("like_count"), 0) or 0)
            lines.append(f"{i}. {title}")
            lines.append(f"   播放:{play} 点赞:{like}\n")
        if viral_summary:
            lines.append(f"\n爆款结构摘要：\n{viral_summary[:200]}...")
        return self.send_text("\n".join(lines))

    def send_creative_push(self, ideas: list) -> bool:
        """创意推送"""
        lines = ["【AI 推荐创意】\n"]
        for i, idea in enumerate(ideas[:3], 1):
            title = idea.get("title", "")
            tags = idea.get("tags", [])
            tags_s = ", ".join(tags) if isinstance(tags, list) else str(tags)
            lines.append(f"{i}. {title}")
            lines.append(f"   标签: {tags_s}\n")
        return self.send_text("\n".join(lines))
