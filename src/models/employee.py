# -*- coding: utf-8 -*-
"""
员工数字人 - 画像模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# 预设员工AI助手类型（创意策划风格）
EMPLOYEE_STYLE_TYPES = [
    "搞笑型创意策划",
    "剧情型创意策划",
    "干货型创意策划",
    "情感型创意策划",
    "科普型创意策划",
    "探店型创意策划",
    "开箱测评型创意策划",
    "剧情反转型创意策划",
]


class EmployeeProfile(BaseModel):
    """员工数字人画像"""

    id: str = Field(..., description="员工ID")
    name: str = Field(..., description="姓名")
    position: str = Field(..., description="岗位")
    industry_experience: str = Field(default="", description="行业经验")
    content_style: str = Field(..., description="内容风格")
    ai_assistant_type: str = Field(..., description="员工AI助手类型")
    expertise: list[str] = Field(default_factory=list, description="擅长领域")
    # 员工自定义 prompt 模板（按岗位规范）
    idea_prompt_template: str = Field(
        default="",
        description="创意生成 prompt 模板，可用 {{topic}} {{viral_model}}",
    )
    script_prompt_template: str = Field(
        default="",
        description="脚本生成 prompt 模板，可用 {{idea}}",
    )
    system_prompt_override: str = Field(
        default="",
        description="覆盖默认系统 prompt，为空则用内置",
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_ai_context(self) -> str:
        """生成 AI 生成时的角色上下文"""
        parts = [
            f"员工：{self.name}",
            f"岗位：{self.position}",
            f"AI助手类型：{self.ai_assistant_type}",
            f"内容风格：{self.content_style}",
        ]
        if self.industry_experience:
            parts.append(f"行业经验：{self.industry_experience}")
        if self.expertise:
            parts.append(f"擅长领域：{', '.join(self.expertise)}")
        return "\n".join(parts)


class CreativeRecord(BaseModel):
    """员工创意历史记录"""

    id: str = ""
    employee_id: str = ""
    topic: str = ""
    ideas: list = Field(default_factory=list, description="创意列表")
    script: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    @classmethod
    def parse_file(cls, data: dict) -> "CreativeRecord":
        """从 JSON 解析，兼容 datetime 字符串"""
        d = dict(data)
        if isinstance(d.get("created_at"), str):
            try:
                d["created_at"] = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
            except Exception:
                d["created_at"] = None
        return cls(**d)
