# -*- coding: utf-8 -*-
"""
员工 prompt 模板构建
员工可根据岗位自定义 prompt，AI 生成内容匹配员工风格
统一营销设计专业领域：自然语言、专业术语、商业价值、文案字数适中
"""

from typing import Optional

from src.models.employee import EmployeeProfile

try:
    from src.prompts.marketing_prompts import MarketingPrompts
except ImportError:
    MarketingPrompts = None


# 默认按风格类型的系统 prompt 片段
STYLE_SYSTEM_SNIPPETS = {
    "搞笑型创意策划": "你擅长搞笑、幽默、梗文化，创意要有趣、接地气、容易引发笑点。",
    "剧情型创意策划": "你擅长故事叙事，创意要有情节、冲突、反转，引人入胜。",
    "干货型创意策划": "你擅长知识输出，创意要实用、清晰、有方法论，用户能学到东西。",
    "情感型创意策划": "你擅长情感共鸣，创意要真诚、有温度、触动人心。",
    "科普型创意策划": "你擅长科普讲解，创意要准确、通俗、有趣味。",
    "探店型创意策划": "你擅长探店体验，创意要真实、有代入感、突出亮点。",
    "开箱测评型创意策划": "你擅长开箱测评，创意要客观、细节丰富、有购买参考价值。",
    "剧情反转型创意策划": "你擅长剧情反转，创意要铺垫、埋伏笔、结尾出其不意。",
}


class PromptBuilder:
    """Prompt 构建器"""

    @staticmethod
    def build_idea_system_prompt(employee: Optional[EmployeeProfile]) -> str:
        """创意生成 - 系统 prompt（营销设计专业领域）"""
        base = (MarketingPrompts.IDEA_SYSTEM if MarketingPrompts else
                "你是创意策划专家。根据爆款内容模型，生成可落地的短视频创意。")
        if employee:
            style_snippet = STYLE_SYSTEM_SNIPPETS.get(
                employee.ai_assistant_type,
                f"你的内容风格：{employee.content_style}。",
            )
            base = f"{base}\n\n{employee.to_ai_context()}\n{style_snippet}"
            if employee.system_prompt_override:
                base = employee.system_prompt_override
        if not MarketingPrompts:
            base = base + "\n用 JSON 数组返回，每项包含：title(标题)、hook(钩子)、tags(标签列表)、duration(建议时长秒)、angle(切入角度)。"
        return base

    @staticmethod
    def build_idea_user_prompt(
        viral_model: dict,
        topic: str,
        employee: Optional[EmployeeProfile] = None,
    ) -> str:
        """创意生成 - 用户 prompt"""
        import json
        if employee and employee.idea_prompt_template:
            return employee.idea_prompt_template.replace("{{topic}}", topic).replace(
                "{{viral_model}}", json.dumps(viral_model, ensure_ascii=False)
            )
        return f"""爆款模型：
{json.dumps(viral_model, ensure_ascii=False)}

主题方向：{topic}

请生成 3 个创意，返回 JSON 数组。"""

    @staticmethod
    def build_script_system_prompt(employee: Optional[EmployeeProfile]) -> str:
        """脚本生成 - 系统 prompt（营销设计专业、商业价值、文案适中）"""
        base = (MarketingPrompts.SCRIPT_SYSTEM if MarketingPrompts else
                "你是短视频脚本创作专家。根据创意要点，写出可直接拍摄的分镜脚本。")
        if employee:
            base = f"{base}\n\n{employee.to_ai_context()}\n内容需符合你的风格。"
            if employee.system_prompt_override:
                base = employee.system_prompt_override
        if not MarketingPrompts:
            base = base + "\n格式：按秒数分段，每段写明画面、文案、备注。简明扼要。"
        return base

    @staticmethod
    def build_script_user_prompt(
        idea: dict,
        employee: Optional[EmployeeProfile] = None,
    ) -> str:
        """脚本生成 - 用户 prompt"""
        import json
        idea_str = json.dumps(idea, ensure_ascii=False)
        if employee and employee.script_prompt_template:
            return employee.script_prompt_template.replace("{{idea}}", idea_str)
        return f"""创意：
{idea_str}

请生成 **26 秒** 拍摄脚本，必须按 **0-3秒**、**4-8秒**、**9-14秒**、**15-20秒**、**21-26秒** 输出。
每段必须包含【画面】【口播文案】【备注】三项，供视频生成逐段严格实现。
若创意中包含敏感、不合规或高风险表达，必须自动改写为合规中性营销表达，禁止输出敏感脚本内容。"""
