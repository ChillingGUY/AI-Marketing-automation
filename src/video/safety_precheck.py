# -*- coding: utf-8 -*-
"""
视频脚本本地预检：
- 检测高风险表达
- 自动替换为合规中性表达
"""

from __future__ import annotations

import re


# (pattern, replacement, risk_label)
_RULES: list[tuple[str, str, str]] = [
    (r"(砍|杀|捅|爆头|枪击|血腥|尸体|自残|自杀)", "激烈冲突", "violence"),
    (r"(吸毒|贩毒|毒品)", "违法内容", "drug"),
    (r"(赌博|博彩|赌局)", "高风险行为", "gambling"),
    (r"(仇恨|种族歧视|侮辱性词汇)", "不当表达", "hate"),
    (r"(成人内容|情色|性暗示|露骨)", "不当内容", "sexual"),
    (r"(政治敏感|颠覆|违法集会)", "敏感议题", "politics"),
    (r"(诈骗|洗钱|违法教程|黑产)", "违规行为", "illegal"),
]


def precheck_and_sanitize_script(text: str) -> dict:
    """
    返回：
    {
      "clean_text": str,
      "changed": bool,
      "hits": [{"label": str, "matched": str}, ...]
    }
    """
    source = text or ""
    clean = source
    hits: list[dict] = []

    for pattern, replacement, label in _RULES:
        for m in re.finditer(pattern, clean, flags=re.IGNORECASE):
            hits.append({"label": label, "matched": m.group(0)})
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)

    # 兜底：去除明显异常字符，避免乱码触发
    clean = re.sub(r"[\uFFF9-\uFFFB]", "", clean)
    clean = re.sub(r"\s{3,}", "  ", clean).strip()

    return {
        "clean_text": clean,
        "changed": clean != source,
        "hits": hits,
    }

