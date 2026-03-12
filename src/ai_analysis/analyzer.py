# -*- coding: utf-8 -*-
"""
LLM 分析模块
1. 热门视频拆解 2. 爆款结构提取 3. 创意生成 4. 内容脚本生成
营销设计专业领域，输出自然语言、商业价值、文案字数适中
"""

import json
from typing import Optional

import pandas as pd
from .llm_client import LLMClient

try:
    from src.prompts.marketing_prompts import MarketingPrompts
except ImportError:
    MarketingPrompts = None
try:
    from src.models.employee import EmployeeProfile
    from src.employees.prompt_builder import PromptBuilder
except ImportError:
    EmployeeProfile = None
    PromptBuilder = None


class LLMAnalyzer:
    """LLM 分析器"""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    def _ensure_result(self, text: str, default: dict | list) -> dict | list:
        """尝试解析 JSON，失败则返回默认"""
        text = (text or "").strip()
        if not text:
            return default
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text} if isinstance(default, dict) else [{"raw": text}]

    def deconstruct_hot_video(self, row: pd.Series) -> dict:
        """
        1. 热门视频拆解
        分析单条热门视频的构成要素
        """
        title = str(row.get("title", ""))
        tags = row.get("tags", "")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.replace("|", ",").split(",") if t.strip()]
        duration = int(row.get("duration", 0))
        play = int(row.get("play_count", 0))
        like = int(row.get("like_count", 0))
        comment = int(row.get("comment_count", 0))
        engage = float(row.get("engagement_rate", 0))

        sys_p = MarketingPrompts.DECONSTRUCT_SYSTEM if MarketingPrompts else """你是短视频营销分析专家。根据提供的视频元数据，拆解其热门要素。
请用 JSON 格式返回，包含：content_type(内容类型)、hook(吸引点)、structure(结构特点)、duration_tips(时长建议)、tag_strategy(标签策略)、success_factors(成功因素列表)。"""

        user_p = f"""视频信息：
标题: {title}
标签: {tags}
时长: {duration}秒
播放: {play} 点赞: {like} 评论: {comment} 互动率: {engage:.2%}

请拆解该视频的热门要素，返回 JSON。"""

        if not self.llm.is_available():
            return {
                "content_type": "短视频",
                "hook": title[:50] if title else "标题吸引",
                "structure": f"约{duration}秒",
                "duration_tips": f"时长{duration}s，适合短视频平台",
                "tag_strategy": tags[:5] if tags else [],
                "success_factors": ["高播放", "高互动", "标签精准"],
                "raw_analysis": "（未配置 LLM，返回规则分析）",
            }

        out = self.llm.chat(sys_p, user_p)
        return self._ensure_result(out, {"raw": out})

    def extract_viral_structure(self, df: pd.DataFrame, top_n: int = 5) -> dict:
        """
        2. 爆款结构提取
        从多条热门视频中提取可复制的爆款内容结构
        """
        rows = df.head(top_n)
        items = []
        for _, r in rows.iterrows():
            items.append({
                "title": str(r.get("title", "")),
                "tags": r.get("tags", ""),
                "duration": int(r.get("duration", 0)),
                "play_count": int(r.get("play_count", 0)),
                "engagement_rate": float(r.get("engagement_rate", 0)),
            })

        sys_p = MarketingPrompts.VIRAL_SYSTEM if MarketingPrompts else """你是爆款内容分析专家。根据多条热门视频数据，提取共性爆款结构。
用 JSON 返回：common_patterns(共同模式)、optimal_duration(最佳时长范围)、top_tags(高频标签)、script_formula(脚本公式/套路)、recommendations(可复制建议列表)。"""

        user_p = f"""热门视频数据：\n{json.dumps(items, ensure_ascii=False, indent=2)}\n\n请提取爆款结构，返回 JSON。"""

        if not self.llm.is_available():
            return {
                "common_patterns": ["短平快", "强钩子", "标签密集"],
                "optimal_duration": "15-60秒",
                "top_tags": ["热点", "教程", "干货"],
                "script_formula": "开场钩子+核心内容+行动号召",
                "recommendations": ["控制时长", "用好标签", "提升互动"],
                "raw_analysis": "（未配置 LLM，返回规则分析）",
            }

        out = self.llm.chat(sys_p, user_p)
        return self._ensure_result(out, {"raw": out})

    def generate_ideas(
        self,
        viral_model: dict,
        topic: str = "营销",
        employee: Optional["EmployeeProfile"] = None,
        rag_context: Optional[str] = None,
    ) -> list[dict]:
        """
        3. 创意生成
        基于爆款模型生成新创意，可选员工风格匹配
        """
        viral_str = json.dumps(viral_model, ensure_ascii=False)
        if PromptBuilder and employee:
            sys_p = PromptBuilder.build_idea_system_prompt(employee)
            user_p = PromptBuilder.build_idea_user_prompt(viral_model, topic, employee)
        else:
            sys_p = MarketingPrompts.IDEA_SYSTEM if MarketingPrompts else """你是创意策划专家。根据爆款内容模型，生成可落地的短视频创意。
用 JSON 数组返回，每项包含：title(标题)、hook(钩子)、tags(标签列表)、duration(建议时长秒)、angle(切入角度)。"""
            user_p = MarketingPrompts.idea_user(viral_str, topic, rag_context or "") if MarketingPrompts else f"""爆款模型：\n{viral_str}\n\n主题方向：{topic}\n\n请生成 3 个创意，返回 JSON 数组。"""
        if rag_context and PromptBuilder and employee:
            user_p = f"{rag_context}\n\n{user_p}"

        if not self.llm.is_available():
            return [
                {"title": f"{topic}干货分享", "hook": "3个技巧", "tags": [topic, "干货"], "duration": 26, "angle": "实用向"},
                {"title": f"{topic}避坑指南", "hook": "千万别这样", "tags": [topic, "避坑"], "duration": 26, "angle": "警示向"},
                {"title": f"{topic}案例拆解", "hook": "真实案例", "tags": [topic, "案例"], "duration": 26, "angle": "案例向"},
            ]

        out = self.llm.chat(sys_p, user_p)
        parsed = self._ensure_result(out, [])
        return parsed if isinstance(parsed, list) else [parsed]

    def generate_script(
        self,
        idea: dict,
        employee: Optional["EmployeeProfile"] = None,
    ) -> str:
        """
        4. 内容脚本生成
        将创意转化为可拍摄的脚本，可选员工风格匹配
        """
        idea_str = json.dumps(idea, ensure_ascii=False)
        if PromptBuilder and employee:
            sys_p = PromptBuilder.build_script_system_prompt(employee)
            user_p = PromptBuilder.build_script_user_prompt(idea, employee)
        else:
            sys_p = MarketingPrompts.SCRIPT_SYSTEM if MarketingPrompts else """你是短视频脚本创作专家。根据创意要点，写出可直接拍摄的分镜脚本。
格式：按秒数分段，每段写明画面、文案、备注。简明扼要。"""
            user_p = MarketingPrompts.script_user(idea_str) if MarketingPrompts else f"""创意：\n{idea_str}\n\n请生成拍摄脚本。"""

        if not self.llm.is_available():
            return f"""【0-3秒】开场：{idea.get('hook', '')}\n【4-12秒】痛点/爽点展开\n【13-20秒】卖点呈现\n【21-26秒】CTA 行动号召"""

        return self.llm.chat(sys_p, user_p)
