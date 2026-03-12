# -*- coding: utf-8 -*-
"""
Agent 基类
BaseAgent.run(state: dict) -> dict  返回 state 增量
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Agent 基类"""

    name: str = "base"

    @abstractmethod
    def run(self, state: dict) -> dict:
        """
        执行任务，接收共享 state，返回要合并的增量
        返回 dict，如 {"trend_data": ..., "errors": [...]}
        """
        pass
