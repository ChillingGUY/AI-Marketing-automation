# -*- coding: utf-8 -*-
"""
视频数据模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VideoRaw(BaseModel):
    """原始视频数据（抓取/导入）"""

    video_id: str = Field(..., description="视频ID")
    item_id: str = Field(..., description="作品ID")
    title: str = Field(default="", description="标题/描述")
    cover_url: str = Field(default="", description="封面图URL")
    video_url: str = Field(default="", description="视频链接")
    duration: int = Field(default=0, description="时长（秒）")
    # 统计数据
    play_count: int = Field(default=0, description="播放量")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    share_count: int = Field(default=0, description="转发数")
    # 元信息
    tags: list[str] = Field(default_factory=list, description="标签/话题")
    region: str = Field(default="", description="地区")
    country_code: str = Field(default="", description="国家代码")
    publish_time: Optional[datetime] = None
    fetch_time: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="tikhub", description="数据来源: tikhub | csv | api")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class VideoProcessed(BaseModel):
    """处理后视频数据（用于分析/看板）"""

    video_id: str
    title: str
    cover_url: str
    video_url: str
    duration: int
    play_count: int
    like_count: int
    comment_count: int
    share_count: int
    tags: list[str]
    region: str
    country_code: str
    publish_time: Optional[datetime] = None
    fetch_date: str = Field(..., description="抓取日期 YYYY-MM-DD")
    # 衍生指标
    engagement_rate: float = Field(default=0.0, description="互动率 (点赞+评论+转发)/播放")
    rank: int = Field(default=0, description="今日排名")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
