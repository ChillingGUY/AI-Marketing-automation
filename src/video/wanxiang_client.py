# -*- coding: utf-8 -*-
"""
万象 2.6 视频生成客户端
优先使用官方 Wan26Media MCP（streamable HTTP），失败时回退 DashScope SDK。
"""

import json
import os
from typing import Any

import requests


class WanxiangClient:
    """阿里万象 2.6 文生视频客户端（MCP + SDK fallback）"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        self.mcp_url = os.getenv(
            "WANXIANG_MCP_URL",
            "https://dashscope.aliyuncs.com/api/v1/mcps/Wan26Media/mcp",
        ).strip()
        self.mcp_token = (
            os.getenv("WANXIANG_MCP_API_KEY", "").strip()
            or self.api_key
        )
        self._mcp_session_id = ""
        self._req_id = 0

    def is_available(self) -> bool:
        return bool(self.mcp_token and self.mcp_token not in ("", "your_dashscope_key"))

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _extract_json_from_sse(self, text: str) -> dict[str, Any]:
        """从 SSE 响应里抽取最后一个 JSON-RPC 包"""
        last_obj: dict[str, Any] = {}
        for line in (text or "").splitlines():
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload:
                continue
            try:
                obj = json.loads(payload)
                if isinstance(obj, dict):
                    last_obj = obj
            except Exception:
                continue
        return last_obj

    def _mcp_post(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self.mcp_url:
            return {"error": "未配置 WANXIANG_MCP_URL"}
        headers = {
            "Authorization": f"Bearer {self.mcp_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._mcp_session_id:
            headers["Mcp-Session-Id"] = self._mcp_session_id
        try:
            resp = requests.post(self.mcp_url, headers=headers, json=body, timeout=40)
            sid = resp.headers.get("Mcp-Session-Id", "")
            if sid:
                self._mcp_session_id = sid
            ctype = (resp.headers.get("Content-Type", "") or "").lower()
            if "text/event-stream" in ctype:
                data = self._extract_json_from_sse(resp.text or "")
            else:
                data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                msg = ""
                if isinstance(data, dict):
                    msg = (
                        str(data.get("error") or "")
                        or str((data.get("result") or {}).get("message", ""))
                        or str(data.get("message") or "")
                    )
                return {"error": msg or f"HTTP {resp.status_code}", "raw": data}
            return data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            return {"error": str(e)}

    def _mcp_initialize(self) -> dict[str, Any]:
        if self._mcp_session_id:
            return {"ok": True}
        init_body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "yingxiao-app", "version": "1.0.0"},
                "capabilities": {},
            },
        }
        init_rsp = self._mcp_post(init_body)
        if init_rsp.get("error"):
            return {"error": init_rsp["error"]}
        # 可选通知：initialized
        notify_body = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        _ = self._mcp_post(notify_body)
        return {"ok": True}

    def _mcp_call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        init = self._mcp_initialize()
        if init.get("error"):
            return {"error": init["error"]}
        body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        rsp = self._mcp_post(body)
        if rsp.get("error"):
            return rsp
        if rsp.get("result") is not None:
            result = rsp["result"] if isinstance(rsp["result"], dict) else {"raw": rsp["result"]}
            # 兼容 result.content[].text 里嵌套 JSON 文本
            content = result.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text")
                    if not isinstance(text, str):
                        continue
                    t = text.strip()
                    if (t.startswith("{") and t.endswith("}")) or (t.startswith("[") and t.endswith("]")):
                        try:
                            parsed = json.loads(t)
                            if isinstance(parsed, dict):
                                result.update(parsed)
                        except Exception:
                            pass
            return result
        return rsp

    def _deep_get_first(self, obj: Any, keys: tuple[str, ...]) -> str:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in keys and isinstance(v, (str, int, float)):
                    return str(v)
                found = self._deep_get_first(v, keys)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = self._deep_get_first(item, keys)
                if found:
                    return found
        return ""

    def text2video(
        self,
        prompt: str,
        *,
        model: str = "wan2.6-t2v",
        size: str = "720*1280",
        duration: int = 5,
        shot_type: str = "single",
        prompt_extend: bool = True,
        negative_prompt: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """提交文生视频任务，返回 task_id 或 error"""
        if not self.is_available():
            return {"error": "未配置 DASHSCOPE_API_KEY / WANXIANG_MCP_API_KEY"}

        # 1) 优先 MCP
        mcp_args: dict[str, Any] = {
            "prompt": (prompt or "")[:2000],
            "size": size,
            "duration": duration,
            "shot_type": shot_type,
            "prompt_extend": prompt_extend,
        }
        if negative_prompt:
            mcp_args["negative_prompt"] = negative_prompt[:500]
        # MCP 工具 schema 未声明 model，但保留兼容
        if model:
            mcp_args["model"] = model
        mcp_args.update(kwargs or {})

        mcp_rsp = self._mcp_call_tool("modelstudio_text_to_video_wan26_submit_task", mcp_args)
        task_id = self._deep_get_first(mcp_rsp, ("task_id", "taskId"))
        if task_id:
            return {"task_id": task_id}
        if not mcp_rsp.get("error"):
            # 部分服务把结果放在 content.text 里
            content_text = self._deep_get_first(mcp_rsp, ("text", "message", "msg"))
            if content_text:
                # 尝试从文本里提取 task_id
                for token in str(content_text).replace('"', " ").replace("'", " ").split():
                    if "-" in token and len(token) >= 16:
                        task_id = token.strip(" ,;")
                        break
            if task_id:
                return {"task_id": task_id}

        # 2) MCP 失败回退 SDK
        try:
            from dashscope import VideoSynthesis

            call_kw = {
                "api_key": self.api_key,
                "model": model,
                "prompt": (prompt or "")[:2000],
                "size": size,
                "duration": duration,
                "shot_type": shot_type,
                "prompt_extend": prompt_extend,
                **kwargs,
            }
            if negative_prompt:
                call_kw["negative_prompt"] = negative_prompt[:500]
            rsp = VideoSynthesis.async_call(**call_kw)
            out = getattr(rsp, "output", None)
            sdk_task = getattr(out, "task_id", None) if out else None
            if sdk_task:
                return {"task_id": sdk_task}
            msg = getattr(rsp, "message", "") or ""
            if mcp_rsp.get("error"):
                msg = f"MCP失败: {mcp_rsp['error']} | SDK失败: {msg or '未返回 task_id'}"
            return {"error": msg or "未返回 task_id"}
        except ImportError:
            return {"error": mcp_rsp.get("error", "MCP失败，且未安装 dashscope")}
        except Exception as e:
            mcp_err = mcp_rsp.get("error", "")
            return {"error": f"{mcp_err} | SDK回退失败: {e}" if mcp_err else str(e)}

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """查询任务状态"""
        if not self.is_available():
            return {"status": "failed", "error": "未配置 DASHSCOPE_API_KEY / WANXIANG_MCP_API_KEY"}

        # 1) 优先 MCP 查询
        mcp_rsp = self._mcp_call_tool("modelstudio_wan_video_fetch_result", {"task_id": task_id})
        status = (self._deep_get_first(mcp_rsp, ("task_status", "status")) or "").lower()
        video_url = self._deep_get_first(mcp_rsp, ("video_url", "url"))
        if status or video_url:
            status_map = {"succeeded": "completed", "success": "completed", "failed": "failed"}
            norm = status_map.get(status, status) or ("completed" if video_url else "processing")
            out = {"status": norm, "video_url": video_url or ""}
            if norm == "failed":
                out["error"] = self._deep_get_first(mcp_rsp, ("message", "msg", "error")) or "生成失败"
            return out

        # 2) MCP 无结果回退 SDK
        try:
            from dashscope import VideoSynthesis

            rsp = VideoSynthesis.fetch(task=task_id, api_key=self.api_key)
            out = getattr(rsp, "output", None)
            sdk_status = ""
            sdk_url = ""
            if out:
                sdk_status = (getattr(out, "task_status", "") or "").lower()
                sdk_url = getattr(out, "video_url", "") or ""
            status_map = {"succeeded": "completed", "success": "completed", "failed": "failed"}
            norm = status_map.get(sdk_status, sdk_status) or ("completed" if sdk_url else "processing")
            result = {"status": norm, "video_url": sdk_url or ""}
            if norm == "failed":
                msg = getattr(rsp, "message", "") or mcp_rsp.get("error", "生成失败")
                result["error"] = msg
            return result
        except Exception as e:
            return {"status": "failed", "error": mcp_rsp.get("error") or str(e)}
