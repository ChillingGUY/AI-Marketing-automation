# -*- coding: utf-8 -*-
"""
工作流状态定义
State 字段：trend_data, strategy_output, script_output, scores, errors, trend_ids, script_ids
"""

from typing import Any


def initial_state(
    trend_data: Any = None,
    strategy_output: Any = None,
    script_output: Any = None,
    scores: Any = None,
    errors: list | None = None,
    trend_ids: list | None = None,
    script_ids: list | None = None,
    processed_df: Any = None,
    analysis_result: dict | None = None,
) -> dict:
    """构建初始工作流状态"""
    return {
        "trend_data": trend_data,
        "strategy_output": strategy_output,
        "script_output": script_output,
        "scores": scores,
        "errors": errors or [],
        "trend_ids": trend_ids or [],
        "script_ids": script_ids or [],
        "processed_df": processed_df,
        "analysis_result": analysis_result or {},
    }


def merge_state(state: dict, updates: dict) -> dict:
    """合并 updates 到 state，返回新 state"""
    out = dict(state)
    for k, v in updates.items():
        if v is not None:
            out[k] = v
    return out
