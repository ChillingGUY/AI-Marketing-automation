# -*- coding: utf-8 -*-
"""
工作流编排 - 轻量级 StateGraph
支持 add_node、add_edge、compile、invoke
流程：Trend -> Strategy -> Script -> Score
"""

from typing import Callable

from .state import initial_state, merge_state


class StateGraph:
    """轻量级状态图，按边顺序执行节点"""

    def __init__(self):
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._entry: str | None = None

    def add_node(self, name: str, fn: Callable[[dict], dict]) -> "StateGraph":
        self._nodes[name] = fn
        if self._entry is None:
            self._entry = name
        return self

    def add_edge(self, from_node: str, to_node: str) -> "StateGraph":
        self._edges.append((from_node, to_node))
        return self

    def compile(self) -> "CompiledGraph":
        return CompiledGraph(
            nodes=self._nodes,
            edges=self._edges,
            entry=self._entry,
        )


class CompiledGraph:
    """编译后的图，支持 invoke"""

    def __init__(
        self,
        nodes: dict[str, Callable],
        edges: list[tuple[str, str]],
        entry: str | None,
    ):
        self._nodes = nodes
        self._edges = edges
        self._entry = entry
        self._order = self._topo_order()

    def _topo_order(self) -> list[str]:
        """根据边得到执行顺序"""
        order: list[str] = []
        seen: set[str] = set()
        out_edges: dict[str, list[str]] = {n: [] for n in self._nodes}
        for a, b in self._edges:
            out_edges.setdefault(a, []).append(b)

        def visit(n: str):
            if n in seen:
                return
            seen.add(n)
            for ch in out_edges.get(n, []):
                visit(ch)
            order.append(n)

        start = self._entry or list(self._nodes)[0]
        visit(start)
        order.reverse()
        return order

    def invoke(self, state: dict) -> dict:
        """执行工作流，返回最终 state"""
        current = dict(state)
        for name in self._order:
            if name not in self._nodes:
                continue
            fn = self._nodes[name]
            try:
                updates = fn(current)
                if updates:
                    current = merge_state(current, updates)
            except Exception as e:
                errs = list(current.get("errors", []))
                errs.append(f"{name}: {e}")
                current = merge_state(current, {"errors": errs})
        return current


def _create_default_graph():
    """创建默认工作流：需要注入具体 Agent，此处仅建骨架"""
    from src.agents.trend_agent import TrendAgent
    from src.agents.strategy_agent import StrategyAgent
    from src.agents.script_agent import ScriptAgent
    from src.agents.score_agent import ScoreAgent

    trend_agent = TrendAgent()
    strategy_agent = StrategyAgent()
    script_agent = ScriptAgent()
    score_agent = ScoreAgent()

    g = StateGraph()
    g.add_node("trend", trend_agent.run)
    g.add_node("strategy", strategy_agent.run)
    g.add_node("script", script_agent.run)
    g.add_node("score", score_agent.run)
    g.add_edge("trend", "strategy")
    g.add_edge("strategy", "script")
    g.add_edge("script", "score")
    return g.compile()


# 延迟创建，避免循环导入
_app: CompiledGraph | None = None


def get_app() -> CompiledGraph:
    global _app
    if _app is None:
        _app = _create_default_graph()
    return _app


# 兼容：from src.workflow.graph import app
app = property(lambda self: get_app())


def _app_getter():
    return get_app()


# 模块级别 app 为可调用对象，invoke 时使用 get_app().invoke
class _AppProxy:
    def invoke(self, state: dict):
        return get_app().invoke(state)

    def __repr__(self):
        return f"<CompiledGraph trend->strategy->script->score>"


app = _AppProxy()
