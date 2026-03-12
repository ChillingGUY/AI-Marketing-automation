# -*- coding: utf-8 -*-
"""
CSV / 手动导入
支持从 CSV 导入视频数据
"""

from pathlib import Path

import pandas as pd
from src.models.video import VideoRaw


def _parse_tags(s: object) -> list[str]:
    if pd.isna(s) or s == "":
        return []
    if isinstance(s, str):
        return [t.strip() for t in s.replace("|", ",").split(",") if t.strip()]
    return []


def import_from_csv(
    path: str | Path,
    encoding: str = "utf-8-sig",
    id_col: str = "video_id",
    title_col: str = "title",
    duration_col: str = "duration",
    play_col: str = "play_count",
    like_col: str = "like_count",
    comment_col: str = "comment_count",
    tags_col: str = "tags",
    url_col: str = "video_url",
    cover_col: str = "cover_url",
) -> list[VideoRaw]:
    """
    从 CSV 导入视频数据
    列名可通过参数映射，兼容多种导出格式
    """
    path = Path(path)
    if not path.exists():
        return []

    df = pd.read_csv(path, encoding=encoding)

    # 使用传入的列名
    id_c = id_col if id_col in df.columns else (df.columns[0] if len(df.columns) > 0 else "video_id")

    results: list[VideoRaw] = []
    for _, row in df.iterrows():
        vid = str(row.get(id_c, ""))
        if not vid or str(vid) == "nan":
            continue

        title = str(row.get(title_col, "")) if title_col in df.columns else ""
        duration = int(row.get(duration_col, 0) or 0) if duration_col in df.columns else 0
        play = int(row.get(play_col, 0) or 0) if play_col in df.columns else 0
        like = int(row.get(like_col, 0) or 0) if like_col in df.columns else 0
        comment = int(row.get(comment_col, 0) or 0) if comment_col in df.columns else 0
        tags = _parse_tags(row.get(tags_col, "")) if tags_col in df.columns else []
        video_url = str(row.get(url_col, "")) if url_col in df.columns else ""
        cover_url = str(row.get(cover_col, "")) if cover_col in df.columns else ""

        results.append(
            VideoRaw(
                video_id=vid,
                item_id=vid,
                title=title,
                cover_url=cover_url,
                video_url=video_url,
                duration=duration,
                play_count=play,
                like_count=like,
                comment_count=comment,
                share_count=0,
                tags=tags,
                region="",
                country_code="",
                source="csv",
            )
        )

    return results
