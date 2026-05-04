from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .registry import ToolRegistration, tool_schema


RUNTIME_CAPABILITY_KEYWORDS = (
    "功能",
    "能力",
    "capability",
    "capabilities",
    "你會什麼",
    "會什麼",
    "自檢",
    "檢測",
    "健康檢查",
    "診斷",
    "runtime",
    "self test",
)


def build_runtime_capability_registrations(
    capabilities_summary: Callable[[str], Any],
    runtime_self_test: Callable[[], Any],
) -> tuple[ToolRegistration, ...]:
    return (
        ToolRegistration(
            schema=tool_schema(
                "capabilities_summary",
                "summarize current capabilities",
                properties={"topic": {"type": "string"}},
                required=[],
            ),
            handler=lambda args: capabilities_summary(args.get("topic", "")),
            keywords=RUNTIME_CAPABILITY_KEYWORDS,
        ),
        ToolRegistration(
            schema=tool_schema(
                "runtime_self_test",
                "run local runtime diagnostics",
                required=[],
            ),
            handler=lambda args: runtime_self_test(),
        ),
    )
