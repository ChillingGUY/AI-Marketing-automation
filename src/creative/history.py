# -*- coding: utf-8 -*-
"""
创意中心历史记录
统一存储每次生成的创意，不依赖员工
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import DATA_DIR


class CreativeHistoryStore:
    """创意历史存储"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or DATA_DIR / "creative_history")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _list_files(self) -> list[Path]:
        return sorted(self.base_dir.glob("*.json"), reverse=True, key=lambda p: p.stat().st_mtime)

    def add(
        self,
        topic: str,
        ideas: list[dict],
        script: str = "",
        product: str = "",
        industry: str = "",
        employee_id: str = "",
    ) -> str:
        """添加创意历史，返回 id"""
        rid = str(uuid.uuid4())[:12]
        record = {
            "id": rid,
            "topic": topic,
            "product": product,
            "industry": industry,
            "ideas": ideas,
            "script": script,
            "employee_id": employee_id,
            "created_at": datetime.now().isoformat(),
        }
        path = self.base_dir / f"{rid}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return rid

    def list_all(self, limit: int = 50) -> list[dict]:
        """列出历史记录"""
        records = []
        for p in self._list_files()[:limit]:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    records.append(json.load(f))
            except Exception:
                pass
        return records

    def get(self, record_id: str) -> Optional[dict]:
        """获取单条记录"""
        path = self.base_dir / f"{record_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
