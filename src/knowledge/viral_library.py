# -*- coding: utf-8 -*-
"""
爆款内容库
存储、检索热门创意拆解与爆款模型
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import PROCESSED_DATA_DIR, DATA_DIR


class ViralContentLibrary:
    """爆款内容库"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or DATA_DIR / "knowledge")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.viral_dir = self.base_dir / "viral_models"
        self.decon_dir = self.base_dir / "deconstructions"
        self.viral_dir.mkdir(exist_ok=True)
        self.decon_dir.mkdir(exist_ok=True)

    def save_viral_model(self, model: dict, date: Optional[str] = None) -> Path:
        """保存爆款模型"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        path = self.viral_dir / f"viral_{date}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=2)
        return path

    def save_deconstruction(self, video_id: str, data: dict, date: Optional[str] = None) -> Path:
        """保存单条热门拆解"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        name = f"{video_id}_{date}.json"
        path = self.decon_dir / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def list_viral_models(self, limit: int = 30) -> list[dict]:
        """列出爆款模型，按日期倒序"""
        files = sorted(self.viral_dir.glob("viral_*.json"), reverse=True)[:limit]
        out = []
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                data["_date"] = f.stem.replace("viral_", "")
                data["_path"] = str(f)
                out.append(data)
            except Exception:
                pass
        return out

    def search_by_tags(self, tags: list[str], limit: int = 10) -> list[dict]:
        """按标签检索拆解"""
        results = []
        for f in sorted(self.decon_dir.glob("*.json"), reverse=True)[:100]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                vid_tags = data.get("tags") or []
                if isinstance(vid_tags, str):
                    vid_tags = [t.strip() for t in str(vid_tags).replace("|", ",").split(",") if t.strip()]
                if any(t in vid_tags for t in tags):
                    data["_path"] = str(f)
                    results.append(data)
                    if len(results) >= limit:
                        break
            except Exception:
                pass
        return results

    def get_latest_model(self) -> Optional[dict]:
        """获取最新爆款模型"""
        models = self.list_viral_models(limit=1)
        return models[0] if models else None

    def sync_from_analysis(self, ai_analysis_path: Path) -> int:
        """从 AI 分析结果同步到知识库"""
        count = 0
        try:
            with open(ai_analysis_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return 0
        date = data.get("fetch_time", "")[:8]
        if len(date) >= 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        viral = data.get("viral_model", {})
        if viral:
            self.save_viral_model(viral, date=date)
            count += 1
        for d in data.get("deconstructions", []):
            vid = d.get("video_id", "unknown")
            self.save_deconstruction(vid, d, date=date)
            count += 1
        return count
