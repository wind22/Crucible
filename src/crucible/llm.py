"""LLM 后端。

内核通过一个极小的协议与模型解耦：complete(system_shared, system_role, user, schema) -> dict。
默认实现使用 Anthropic API（claude-opus-4-8 + adaptive thinking + structured outputs）。
测试用 FakeLLM 注入脚本化回复，不需要网络。
"""

from __future__ import annotations

import json
from typing import Any, Protocol

DEFAULT_MODEL = "claude-opus-4-8"


class LLM(Protocol):
    def complete(
        self,
        system_shared: str,
        system_role: str,
        user: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """执行一次角色调用，返回符合 schema 的 dict。"""
        ...


class LLMOutputError(RuntimeError):
    """模型没有产出可用的结构化结果（截断、拒答等）。"""


class AnthropicLLM:
    """Anthropic Messages API 后端。

    - 系统提示词分两块：共享段（内核信条 + 实例描述符，带 cache_control，
      同一次运行内三个角色反复复用）+ 角色段。
    - structured outputs（output_config.format=json_schema）保证输出可直接
      json.loads，无需容错解析。
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 16000,
        effort: str = "high",
    ):
        import anthropic  # 延迟导入：测试路径不需要 SDK

        self._anthropic = anthropic
        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort

    def complete(
        self,
        system_shared: str,
        system_role: str,
        user: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
            system=[
                {
                    "type": "text",
                    "text": system_shared,
                    "cache_control": {"type": "ephemeral"},
                },
                {"type": "text", "text": system_role},
            ],
            messages=[{"role": "user", "content": user}],
        )
        if response.stop_reason == "refusal":
            raise LLMOutputError("模型拒绝了本次请求（stop_reason=refusal）。")
        if response.stop_reason == "max_tokens":
            raise LLMOutputError(
                f"输出在 {self.max_tokens} tokens 处被截断（stop_reason=max_tokens），请提高 max_tokens。"
            )
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise LLMOutputError("模型响应中没有文本块。")
        return json.loads(text)


class FakeLLM:
    """脚本化后端：按调用顺序依次弹出预置回复。用于测试与离线演示。"""

    def __init__(self, script: list[dict[str, Any]]):
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        system_shared: str,
        system_role: str,
        user: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "system_shared": system_shared,
                "system_role": system_role,
                "user": user,
                "schema": schema,
            }
        )
        if not self.script:
            raise AssertionError("FakeLLM 脚本已耗尽，但引擎仍在发起调用。")
        return self.script.pop(0)
