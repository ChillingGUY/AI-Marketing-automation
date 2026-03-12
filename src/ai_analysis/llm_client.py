# -*- coding: utf-8 -*-
"""
LLM 客户端封装
支持：OpenAI / 兼容接口 / 通义千问(DashScope)
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _detect_provider() -> str:
    """自动检测可用 Provider"""
    if os.getenv("DASHSCOPE_API_KEY"):
        return "dashscope"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return ""


class LLMClient:
    """LLM 调用客户端"""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER") or _detect_provider()).lower()
        self._openai_client: Optional[object] = None

        if self.provider == "dashscope":
            self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
            self.model = model or os.getenv("DASHSCOPE_MODEL", "qwen-plus")
            self.base_url = None
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
            self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        from openai import OpenAI
        if not self._openai_client:
            kw = {"api_key": self.api_key}
            if self.base_url:
                kw["base_url"] = self.base_url
            self._openai_client = OpenAI(**kw)
        resp = self._openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return (resp.choices[0].message.content or "").strip()

    def _call_dashscope(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from dashscope import Generation
        except ImportError:
            return "[请安装 dashscope: pip install dashscope]"
        resp = Generation.call(
            api_key=self.api_key,
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            result_format="message",
            temperature=0.7,
        )
        if resp.status_code == 200 and resp.output and resp.output.choices:
            return (resp.output.choices[0].message.content or "").strip()
        return f"[通义调用失败: {getattr(resp, 'message', resp)}]"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 对话"""
        if not self.is_available():
            return ""
        try:
            if self.provider == "dashscope":
                return self._call_dashscope(system_prompt, user_prompt)
            return self._call_openai(system_prompt, user_prompt)
        except Exception as e:
            return f"[LLM 调用失败: {e}]"

    def is_available(self) -> bool:
        return bool(self.api_key)
