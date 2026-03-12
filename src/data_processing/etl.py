# -*- coding: utf-8 -*-
"""
ETL 数据处理
Python + Pandas：清洗、转换、加载
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from src.models.video import VideoRaw, VideoProcessed
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR


class ETLProcessor:
    """
    ETL 处理器
    将原始视频数据转换为可用于分析的结构化数据
    """

    def __init__(
        self,
        raw_dir: Path = RAW_DATA_DIR,
        processed_dir: Path = PROCESSED_DATA_DIR,
    ):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _raw_to_df(self, videos: list[VideoRaw]) -> pd.DataFrame:
        """VideoRaw 列表转 DataFrame"""
        rows = []
        for v in videos:
            rows.append({
                "video_id": v.video_id,
                "item_id": v.item_id,
                "title": v.title,
                "cover_url": v.cover_url,
                "video_url": v.video_url,
                "duration": v.duration,
                "play_count": v.play_count,
                "like_count": v.like_count,
                "comment_count": v.comment_count,
                "share_count": v.share_count,
                "tags": "|".join(v.tags) if v.tags else "",
                "region": v.region,
                "country_code": v.country_code,
                "publish_time": v.publish_time.isoformat() if v.publish_time else None,
                "fetch_time": v.fetch_time.isoformat(),
                "source": v.source,
            })
        return pd.DataFrame(rows)

    def _compute_engagement_rate(self, row: pd.Series) -> float:
        """计算互动率"""
        play = row.get("play_count") or 0
        if play <= 0:
            return 0.0
        engage = (
            (row.get("like_count") or 0)
            + (row.get("comment_count") or 0)
            + (row.get("share_count") or 0)
        )
        return round(engage / play, 6)

    def transform(self, df: pd.DataFrame, fetch_date: str) -> pd.DataFrame:
        """
        转换：清洗、衍生指标、排序
        """
        df = df.copy()
        df["fetch_date"] = fetch_date

        # 清洗
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0).astype(int)
        df["play_count"] = pd.to_numeric(df["play_count"], errors="coerce").fillna(0).astype(int)
        df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
        df["comment_count"] = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0).astype(int)
        df["share_count"] = pd.to_numeric(df["share_count"], errors="coerce").fillna(0).astype(int)

        # 衍生：互动率
        df["engagement_rate"] = df.apply(self._compute_engagement_rate, axis=1)

        # 排序：播放量降序，作为今日排行
        df = df.sort_values("play_count", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1

        return df

    def load_raw(self, videos: list[VideoRaw], prefix: str = "tiktok") -> Path:
        """保存原始数据到 raw 目录"""
        df = self._raw_to_df(videos)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.raw_dir / f"{prefix}_hot_{ts}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def load_processed(self, df: pd.DataFrame, prefix: str = "hot_rank") -> Path:
        """保存处理后数据到 processed 目录"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.processed_dir / f"{prefix}_{ts}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def process(self, videos: list[VideoRaw]) -> tuple[pd.DataFrame, Path, Path]:
        """
        完整 ETL 流程
        返回：(处理后 DataFrame, 原始文件路径, 处理后文件路径)
        """
        fetch_date = datetime.now().strftime("%Y-%m-%d")
        raw_df = self._raw_to_df(videos)
        processed_df = self.transform(raw_df, fetch_date)

        raw_path = self.load_raw(videos)
        processed_path = self.load_processed(processed_df)

        return processed_df, raw_path, processed_path
