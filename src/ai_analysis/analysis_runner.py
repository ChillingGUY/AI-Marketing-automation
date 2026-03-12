# -*- coding: utf-8 -*-
"""
AI 分析执行器
串联：热门视频拆解 → 爆款结构提取 → 创意生成 → 脚本生成
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from config import PROCESSED_DATA_DIR
from .analyzer import LLMAnalyzer
from .llm_client import LLMClient


class AnalysisRunner:
    """分析流程执行器"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir or PROCESSED_DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = LLMAnalyzer(LLMClient())

    def run(
        self,
        processed_df: pd.DataFrame,
        top_n: int = 5,
        topic: str = "营销",
        save: bool = True,
    ) -> dict:
        """
        执行完整分析流程
        返回：今日热门榜、热门创意拆解、爆款内容模型、AI推荐创意
        """
        top = processed_df.head(top_n)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 今日热门视频榜
        hot_rank = top.to_dict(orient="records")
        for i, r in enumerate(hot_rank, 1):
            r["rank"] = i

        # 热门创意拆解（对每条热门做拆解）
        deconstructions = []
        for _, row in top.iterrows():
            d = self.analyzer.deconstruct_hot_video(row)
            d["video_id"] = str(row.get("video_id", ""))
            d["title"] = str(row.get("title", ""))
            deconstructions.append(d)

        # 爆款结构提取
        viral_model = self.analyzer.extract_viral_structure(processed_df, top_n=top_n)

        # 创意生成
        ideas = self.analyzer.generate_ideas(viral_model, topic=topic)

        # 为第一个创意生成脚本
        script = ""
        if ideas:
            script = self.analyzer.generate_script(ideas[0])

        result = {
            "fetch_time": ts,
            "hot_rank": hot_rank,
            "deconstructions": deconstructions,
            "viral_model": viral_model,
            "ai_ideas": ideas,
            "sample_script": script,
        }

        if save:
            # 清理 NaN 以符合 JSON 规范
            def _sanitize(obj):
                if isinstance(obj, dict):
                    return {k: _sanitize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_sanitize(x) for x in obj]
                if isinstance(obj, float) and (obj != obj):  # NaN
                    return None
                return obj
            result_clean = _sanitize(result)
            out_path = self.output_dir / f"ai_analysis_{ts}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result_clean, f, ensure_ascii=False, indent=2)
            result["_saved_path"] = str(out_path)

        return result
