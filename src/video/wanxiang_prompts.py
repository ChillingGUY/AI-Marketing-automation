# -*- coding: utf-8 -*-
"""
万象 2.6 视频生成专用 Prompt 定义
- 脚本是唯一依据，视频严格按脚本实现
- 输出严格按脚本内容
- 文字须正确、简体中文、清晰易读
- 视频风格、配音为单独选项（市面常见四类）
"""

import re

# 视频风格（四类）
VIDEO_STYLES = [
    ("现代商务", "modern_business", "Modern business style, professional and clean, suitable for corporate/product marketing."),
    ("时尚潮流", "fashion_trendy", "Fashionable and trendy aesthetic, vibrant colors, dynamic, suitable for lifestyle and youth brands."),
    ("温馨生活", "warm_lifestyle", "Warm and cozy lifestyle aesthetic, soft lighting, relatable daily scenes, suitable for FMCG and family products."),
    ("科技简约", "tech_minimal", "Tech-inspired minimal style, sleek, futuristic, clean lines, suitable for tech and innovation products."),
]

# 负面提示（严禁乱码、模糊、艺术化字体等）
WANXIANG_NEGATIVE_PROMPT = (
    "garbled text, wrong characters, traditional Chinese, unreadable font, "
    "strange symbols, corrupted text, blurry text, pixelated text, wrong spelling, "
    "messy subtitles, stylized font, decorative font, artistic font, calligraphic font, "
    "tiny text, small unreadable text, distorted characters, illegible, "
    "non-Chinese characters in Chinese text, mojibake, encoding errors"
)

# 标准字体：宋体 SimSun - 清晰易读、用户看得明白不模糊
FONT_STANDARD = (
    "If any text must appear in frames: use SimSun (Songti/宋体) font ONLY. "
    "White text with thin black outline. Clear, readable, no blur, no garbled characters. "
    "Subtitles will be added in post-production with controlled Songti font."
)

# 字体风格（宋体为标准，四类微调）
FONT_STYLES = [
    ("宋体（推荐）", "songti", "SimSun (Songti) font, standard for Chinese readability, white with black outline, clear and unambiguous."),
    ("圆润易读", "round_friendly", "SimSun-based rounded style, highly legible, white with black outline."),
    ("现代简约", "modern_minimal", "SimSun minimal style, clear strokes, white with black outline."),
    ("稳重大气", "solid_serif", "SimSun serif for headings, clear and legible, white with black outline."),
]

# 配音性别（用户选择后必须严格对应）
VOICE_GENDERS = [
    ("男声", "male", "MUST use male Chinese voice (中文男声) only. No female voice."),
    ("女声", "female", "MUST use female Chinese voice (中文女声) only. No male voice."),
]

# 配音/旁白风格（四类）
VOICE_STYLES = [
    ("专业解说", "professional", "Professional narrator tone, clear and authoritative, like a commercial spokesperson."),
    ("活泼亲和", "lively", "Lively and friendly tone, energetic and approachable, suitable for youth and casual brands."),
    ("沉稳大气", "calm", "Calm and dignified tone, trustworthy and premium, suitable for luxury and formal products."),
    ("轻松幽默", "humorous", "Light and humorous tone, witty and engaging, suitable for entertainment and casual content."),
]


def _extract_script_by_time_range(script: str, start_sec: float, end_sec: float) -> str:
    """提取脚本中属于 [start_sec, end_sec) 时段的内容（按 **0-3秒** 等块匹配）"""
    blocks = []
    # 匹配 **X-Y秒** 或 **X:XX–Y:YY** 格式
    pattern = re.compile(r"\*\*(\d+)[-–:](\d+)(?:[-–:](\d+))?(?:[-–:](\d+))?\s*[秒s]?\*\*\s*(.*?)(?=\*\*\d|$)", re.DOTALL)
    for m in pattern.finditer(script):
        g = m.groups()
        if g[2] is None:
            seg_start, seg_end = float(g[0]), float(g[1])
        else:
            seg_start = float(g[0]) * 60 + float(g[1])
            seg_end = float(g[2]) * 60 + float(g[3])
        if seg_end > start_sec and seg_start < end_sec:
            blocks.append(m.group(0).strip())
    return "\n\n".join(blocks) if blocks else ""


def wanxiang_script_to_prompt(
    title: str,
    hook: str,
    script: str,
    industry: str,
    *,
    video_style: str = "modern_business",
    font_style: str = "songti",
    voice_style: str = "professional",
    voice_gender: str = "female",
    max_chars: int = 1400,
    segment: int | None = None,
    segment_seconds: tuple[int, int] | None = None,
) -> str:
    """
    万象 2.6 专用：脚本转视频 prompt。脚本是唯一依据，视频严格按脚本实现。
    """
    parts = []

    # 0. 任务定义（脚本是唯一依据）
    parts.append(
        "TASK: Script-to-Video. The script below is the ONLY source of truth. "
        "You MUST implement the video strictly according to the script. "
        "Do NOT add, remove, or alter any content. Do NOT output content not in the script."
    )

    # 1. 核心约束
    parts.append(
        "MUST: (1) Match script timing exactly. (2) Voice: user-selected gender (女声=female Chinese, 男声=male Chinese). "
        "(3) Font: SimSun, legible Simplified Chinese. (4) FORBIDDEN: garbled text, illegible characters, mojibake."
    )
    parts.append(
        "CONTENT SAFETY: FORBIDDEN content includes violence, blood, hate, discrimination, sexual/erotic, drugs, gambling, "
        "political sensitive, illegal activity, self-harm, medical misinformation, insults or threats. "
        "If script has risky wording, rewrite it into compliant neutral marketing expression and keep business intent."
    )

    # 2. 行业与定位
    if industry:
        parts.append(f"Industry: {industry}.")
    parts.append("Vertical 9:16, Douyin/TikTok style.")
    # 3. 视频风格
    style_map = {row[1]: row[2] for row in VIDEO_STYLES}
    style_desc = style_map.get(video_style, VIDEO_STYLES[0][2])
    parts.append(f"Visual style: {style_desc}")
    # 4. 字体
    font_map = {row[1]: row[2] for row in FONT_STYLES}
    font_desc = font_map.get(font_style, FONT_STYLES[0][2])
    parts.append(f"USER FONT REQUIREMENT: {font_desc} {FONT_STANDARD}")
    parts.append("Any on-screen text MUST use this font. FORBIDDEN: garbled characters, mojibake, unreadable symbols, wrong encoding.")
    # 5. 配音
    voice_map = {row[1]: row[2] for row in VOICE_STYLES}
    voice_desc = voice_map.get(voice_style, VOICE_STYLES[0][2])
    gender_map = {row[1]: row[2] for row in VOICE_GENDERS}
    gender_desc = gender_map.get(voice_gender, VOICE_GENDERS[0][2])
    parts.append(f"USER VOICE REQUIREMENT: {gender_desc} Voice style: {voice_desc}. The output MUST match the selected gender.")
    
    # 5. 标题、钩子
    if title:
        parts.append(f"Title/theme: {title}.")
    if hook:
        parts.append(f"Opening hook: {hook}.")
    
    # 6. 时段约束（多段时）
    if segment and segment_seconds:
        parts.append(f"[Part {segment}: STRICTLY follow script content from {segment_seconds[0]}-{segment_seconds[1]} seconds. No deviation, no extra content.]")

    # 7. 画面文字（后制加字幕，本阶段避免烧录文字；若必须则用宋体）
    parts.append(
        "Subtitles added in POST-PRODUCTION. Avoid burning text into frames. "
        "If text MUST appear: SimSun (Songti) font, white with black outline, Simplified Chinese only, no garbled text."
    )

    # 8. 脚本内容（必须严格按此执行，大模型仅针对脚本）
    raw_script = script or ""
    if segment and segment_seconds:
        extracted = _extract_script_by_time_range(raw_script, segment_seconds[0], segment_seconds[1])
        if extracted:
            raw_script = extracted
    script_clean = raw_script.replace("\n", " ").strip()[:max_chars]
    parts.append("SCRIPT CONTENT - follow EXACTLY, second by second, no addition or omission:")
    parts.append(script_clean)
    
    return " ".join(parts)
