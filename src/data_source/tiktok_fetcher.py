# -*- coding: utf-8 -*-
"""
TikTok 热门视频抓取工具
基于 TikHub API，非爬虫方式获取数据
"""

import re
import time
from datetime import datetime
from typing import Optional

import requests
from src.models.video import VideoRaw
from config import (
    TIKHUB_API_BASE,
    TIKHUB_API_TOKEN,
    FETCH_CONFIG,
)


def _extract_hashtags(text: str) -> list[str]:
    """从文本中提取 # 标签"""
    if not text:
        return []
    return re.findall(r"#(\w+)", text)


class TikTokHotVideoFetcher:
    """
    TikTok 热门视频抓取器
    使用 TikHub 官方 API，支持：
    - 热门趋势视频列表
    - 视频详细统计（点赞、播放、评论）
    """

    def __init__(
        self,
        api_base: str = TIKHUB_API_BASE,
        api_token: str = TIKHUB_API_TOKEN,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_token = api_token
        self.session = requests.Session()
        if api_token:
            self.session.headers["Authorization"] = f"Bearer {api_token}"
        self.session.headers["Content-Type"] = "application/json"

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.api_base}{path}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_popular_trends(
        self,
        period: int = FETCH_CONFIG["period"],
        page: int = 1,
        limit: int = FETCH_CONFIG["limit"],
        order_by: str = FETCH_CONFIG["order_by"],
        country_code: str = FETCH_CONFIG["country_code"],
    ) -> tuple[list[dict], dict]:
        """
        获取流行趋势视频
        API: GET /api/v1/tiktok/ads/get_popular_trends
        """
        params = {
            "period": period,
            "page": page,
            "limit": limit,
            "order_by": order_by,
            "country_code": country_code,
        }
        data = self._get("/api/v1/tiktok/ads/get_popular_trends", params)

        # 解析嵌套结构
        if isinstance(data.get("data"), dict):
            inner = data["data"].get("data") or data["data"]
        else:
            inner = data

        videos = inner.get("videos", []) or []
        pagination = inner.get("pagination", {}) or {}

        return videos, pagination

    def get_video_metrics(self, item_id: str) -> dict:
        """
        获取单个视频的统计数据
        API: GET /api/v1/tiktok/analytics/fetch_video_metrics
        """
        data = self._get(
            "/api/v1/tiktok/analytics/fetch_video_metrics",
            params={"item_id": item_id},
        )
        if isinstance(data.get("data"), dict) and "item_id" in data.get("data", {}):
            return data["data"]
        return {}

    def fetch_hot_videos(
        self,
        max_pages: int = FETCH_CONFIG["max_pages"],
        enrich_metrics: bool = FETCH_CONFIG["enrich_metrics"],
        batch_delay: float = 1.0,
    ) -> list[VideoRaw]:
        """
        抓取热门视频，支持分页和统计 enrich
        """
        results: list[VideoRaw] = []
        seen_ids: set[str] = set()
        page = 1

        while page <= max_pages:
            videos, pagination = self.get_popular_trends(page=page)

            for v in videos:
                vid = v.get("id") or v.get("item_id") or ""
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)

                raw = VideoRaw(
                    video_id=vid,
                    item_id=vid,
                    title=v.get("title") or "",
                    cover_url=v.get("cover") or "",
                    video_url=v.get("item_url") or "",
                    duration=int(v.get("duration") or 0),
                    tags=_extract_hashtags(v.get("title") or ""),
                    region=v.get("region") or "",
                    country_code=v.get("country_code") or "",
                    source="tikhub",
                )

                if enrich_metrics and self.api_token:
                    metrics = self.get_video_metrics(vid)
                    if metrics:
                        raw.play_count = int(
                            metrics.get("video_views", {}).get("value") or 0
                        )
                        raw.like_count = int(
                            metrics.get("likes", {}).get("value") or 0
                        )
                        raw.comment_count = int(
                            metrics.get("comments", {}).get("value") or 0
                        )
                    time.sleep(batch_delay)

                results.append(raw)

            has_more = pagination.get("has_more", False)
            if not has_more or not videos:
                break
            page += 1
            time.sleep(0.5)

        return results
