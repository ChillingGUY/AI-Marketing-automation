# -*- coding: utf-8 -*-
"""
Kling API 客户端 - 营销/电商短视频生成
按可灵官方文档：AccessKey+SecretKey 生成 JWT，Header: Authorization Bearer {token}
中国区默认: https://api-beijing.klingai.com
"""

import os
import time
from typing import Any, Optional

import requests


# 视频单段最大时长（API 限制）
WANXIANG_MAX_DURATION = 15
KLING_MAX_DURATION = 10


def script_to_prompt(
    title: str,
    hook: str,
    script: str,
    industry: str,
    max_chars: int = 1800,
    segment: int | None = None,
    segment_seconds: tuple[int, int] | None = None,
) -> str:
    """
    将脚本转为视频生成的视觉描述 prompt，支持按时间段截取。
    segment=1, segment_seconds=(0,15) 表示只取脚本 0-15 秒对应内容。
    """
    parts = []
    if industry:
        parts.append(f"Professional short-form marketing video for {industry}.")
    parts.append("Product showcase style, clean and modern, suitable for TikTok/Douyin.")
    if title:
        parts.append(f"Title/theme: {title}.")
    if hook:
        parts.append(f"Opening hook: {hook}.")
    if segment and segment_seconds:
        parts.append(f"[Part {segment}: strictly follow script from {segment_seconds[0]}-{segment_seconds[1]} seconds.]")
    parts.append("Scene description (follow script timing exactly):")
    script_clean = (script or "").replace("\n", " ").strip()[:max_chars]
    parts.append(script_clean)
    return " ".join(parts)


class KlingClient:
    """Kling AI 视频生成 API 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key
        self._access_key = access_key or os.getenv("KLING_ACCESS_KEY", "").strip()
        self._secret_key = secret_key or os.getenv("KLING_SECRET_KEY", "").strip()
        if api_key is None:
            self._api_key = os.getenv("KLING_API_KEY", "").strip()
        # 中国区默认 api-beijing.klingai.com，国际区可用 api.klingai.com
        self.base_url = (base_url or os.getenv("KLING_API_BASE", "https://api-beijing.klingai.com")).rstrip("/")

    def is_available(self) -> bool:
        """是否已配置：单密钥 或 访问密钥+密钥"""
        if self._access_key and self._secret_key:
            return True
        return bool(self._api_key and self._api_key not in ("", "your_kling_api_key"))

    def _bearer(self) -> tuple[str, str]:
        """
        按官方文档 Step-2 生成 JWT：iss=ak, exp=当前+1800s, nbf=当前-5s
        返回 (token, error)，成功时 error 为空
        """
        if self._access_key and self._secret_key:
            try:
                import jwt
                payload = {
                    "iss": self._access_key,  # 填写 access key
                    "exp": int(time.time()) + 1800,  # 有效时间 30min
                    "nbf": int(time.time()) - 5,  # 开始生效时间
                }
                headers = {"alg": "HS256", "typ": "JWT"}
                t = jwt.encode(payload, self._secret_key, headers=headers, algorithm="HS256")
                token = t if isinstance(t, str) else t.decode("utf-8")
                return (token, "")
            except ImportError:
                return ("", "未安装 PyJWT，请运行: pip install PyJWT")
            except Exception as e:
                return ("", str(e))
        return (self._api_key or "", "")

    def text2video(
        self,
        prompt: str,
        *,
        model: str = "kling-v2.5-turbo",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        mode: str = "std",  # 可灵官方：std(标准) / pro(专家)
        negative_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        提交文生视频任务
        Returns: {"task_id": "...", "error": "..."} 或含 error 的 dict
        """
        if not self.is_available():
            return {"error": "未配置 KLING_ACCESS_KEY+KLING_SECRET_KEY 或 KLING_API_KEY"}

        bearer, err = self._bearer()
        if not bearer:
            return {"error": err or "无法生成认证 token（检查 AccessKey/SecretKey 或 API Key）"}

        url = f"{self.base_url}/v1/videos/text2video"
        # Step-3: Bearer 与 token 之间有空格
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt[:2500],
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt[:500]

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            data = resp.json() or {}
            err = data.get("message") or data.get("error") or data.get("msg", "")
            if "balance" in str(err).lower() or "余额" in str(err) or "insufficient" in str(err).lower():
                return {"error": "账户余额不足，请前往可灵平台充值后再试"}
            if resp.status_code != 200:
                return {"error": err or f"HTTP {resp.status_code}"}
            task_id = data.get("task_id") or data.get("data", {}).get("task_id")
            if not task_id:
                return {"error": data.get("message", "未返回 task_id")}
            return {"task_id": task_id}
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        查询任务状态
        Returns: {"status": "pending"|"processing"|"succeed"|"failed", "video_url": "..."}
        """
        if not self.is_available():
            return {"status": "failed", "error": "未配置 KLING_ACCESS_KEY+KLING_SECRET_KEY 或 KLING_API_KEY"}

        bearer, err = self._bearer()
        if not bearer:
            return {"status": "failed", "error": err or "无法生成认证 token"}

        url = f"{self.base_url}/v1/videos/{task_id}"
        headers = {"Authorization": f"Bearer {bearer}"}

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json() or {}
            if resp.status_code != 200:
                return {"status": "failed", "error": data.get("message", f"HTTP {resp.status_code}")}

            # 兼容不同 API 返回格式（klingapi.com / kling26ai 等）
            task = data.get("data", data)
            status = (task.get("task_status") or task.get("status") or "").lower()
            video_url = ""
            tr = task.get("task_result")
            if isinstance(tr, dict) and tr.get("videos"):
                video_url = (tr["videos"][0] or {}).get("url", "") if isinstance(tr["videos"][0], dict) else (tr["videos"][0] or "")
            elif isinstance(tr, list) and tr:
                video_url = tr[0].get("url", "") if isinstance(tr[0], dict) else (tr[0] or "")
            if not video_url:
                resp_arr = task.get("response", [])
                if isinstance(resp_arr, list) and resp_arr:
                    video_url = resp_arr[0] if isinstance(resp_arr[0], str) else (resp_arr[0].get("url", "") if isinstance(resp_arr[0], dict) else "")
            if not video_url:
                video_url = task.get("video_url") or task.get("url") or ""

            status_map = {"succeed": "completed", "success": "completed", "failed": "failed"}
            status = status_map.get(status, status) or "processing"

            err_msg = ""
            if status == "failed":
                err_msg = (
                    task.get("task_status_msg")  # 可灵官方：任务状态说明
                    or task.get("message")
                    or task.get("error_message")
                    or (task.get("task_result") or {}).get("message")
                    or data.get("message")
                    or data.get("error_message")
                    or ""
                )
                if isinstance(err_msg, dict):
                    err_msg = err_msg.get("message", err_msg.get("msg", "")) or ""
                err_msg = str(err_msg or "").strip()
                code = task.get("task_status_code") or task.get("code") or data.get("code")
                if code == 1301:
                    err_msg = "内容审核未通过，请简化提示词或避免敏感营销用语后重试"
                elif code in (1302, 1303):
                    err_msg = "请求过快或并发超限，请稍后重试"
                elif err_msg.lower() in ("no message available", "no message") or not err_msg:
                    err_msg = "任务失败（常见原因：① 内容审核未通过 ② 请求过快 ③ 服务器异常）。请简化提示词后重试，或间隔数分钟再试"

            out = {"status": status, "video_url": video_url or "", "raw": task}
            if status == "failed":
                out["error"] = err_msg or "生成失败"
            return out
        except requests.RequestException as e:
            return {"status": "failed", "error": str(e)}
