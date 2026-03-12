# -*- coding: utf-8 -*-
"""
员工画像存储
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.employee import EmployeeProfile, CreativeRecord
from config import DATA_DIR


class EmployeeStore:
    """员工画像存储"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or DATA_DIR / "employees")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.base_dir / "profiles.json"
        self.history_dir = self.base_dir / "creative_history"
        self.history_dir.mkdir(exist_ok=True)

    def _load_profiles(self) -> list[dict]:
        if not self.profiles_file.exists():
            self._seed_defaults()
        with open(self.profiles_file, "r", encoding="utf-8") as f:
            return json.load(f)
        with open(self.profiles_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _seed_defaults(self) -> None:
        """首次运行时添加示例员工"""
        defaults = [
            {
                "id": "emp_001",
                "name": "小王",
                "position": "创意策划",
                "industry_experience": "2年短视频营销",
                "content_style": "幽默搞笑，擅长玩梗",
                "ai_assistant_type": "搞笑型创意策划",
                "expertise": ["搞笑", "日常", "热点"],
            },
            {
                "id": "emp_002",
                "name": "小李",
                "position": "创意策划",
                "industry_experience": "3年剧情类内容",
                "content_style": "故事感强，反转惊喜",
                "ai_assistant_type": "剧情反转型创意策划",
                "expertise": ["剧情", "反转", "情感"],
            },
            {
                "id": "emp_003",
                "name": "小陈",
                "position": "创意策划",
                "industry_experience": "4年知识类博主",
                "content_style": "干货实用，逻辑清晰",
                "ai_assistant_type": "干货型创意策划",
                "expertise": ["干货", "教程", "职场"],
            },
        ]
        self._save_profiles(defaults)

    def _save_profiles(self, data: list[dict]) -> None:
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self) -> list[EmployeeProfile]:
        """列出所有员工"""
        data = self._load_profiles()
        return [EmployeeProfile(**d) for d in data]

    def get(self, employee_id: str) -> Optional[EmployeeProfile]:
        """根据ID获取员工"""
        for p in self.list_all():
            if p.id == employee_id:
                return p
        return None

    def save(self, profile: EmployeeProfile) -> EmployeeProfile:
        """保存或更新员工"""
        data = self._load_profiles()
        now = datetime.now()
        profile.updated_at = now

        for i, d in enumerate(data):
            if d.get("id") == profile.id:
                data[i] = profile.model_dump(mode="json")
                self._save_profiles(data)
                return profile

        if not profile.created_at:
            profile.created_at = now
        if not profile.id:
            profile.id = str(uuid.uuid4())[:8]
        data.append(profile.model_dump(mode="json"))
        self._save_profiles(data)
        return profile

    def delete(self, employee_id: str) -> bool:
        """删除员工"""
        data = self._load_profiles()
        new_data = [d for d in data if d.get("id") != employee_id]
        if len(new_data) == len(data):
            return False
        self._save_profiles(new_data)
        return True

    def add_creative_record(self, record: CreativeRecord) -> None:
        """添加创意历史"""
        import uuid
        record.created_at = record.created_at or datetime.now()
        if not record.id:
            record.id = str(uuid.uuid4())[:12]
        path = self.history_dir / f"{record.employee_id}_{record.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    def get_creative_history(self, employee_id: str, limit: int = 20) -> list[CreativeRecord]:
        """获取员工创意历史"""
        records = []
        for f in sorted(self.history_dir.glob(f"{employee_id}_*.json"), reverse=True)[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    records.append(CreativeRecord.parse_file(data))
            except Exception:
                pass
        return records
