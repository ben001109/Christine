from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def _tool_name(tool: Any) -> str:
    if not isinstance(tool, dict):
        return ""
    return str(tool.get("name") or tool.get("function", {}).get("name", ""))


def dedupe_tool_specs(tools: Iterable[Any]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = _tool_name(tool)
        if name:
            seen[name] = tool
    return list(seen.values())


def augment_input_with_hint(inp: Any, hint: str | None, enabled: bool = True) -> Any:
    if not enabled or not hint:
        return inp
    return f"{hint}\n{inp}"


def route_voice_then_fallback(
    inp: Any,
    voice_handler: Callable[[Any], Any],
    fallback: Callable[..., Any],
    hint_provider: Callable[[], str | None] | None = None,
    hybrid_enabled: bool = True,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> Any:
    routed = voice_handler(inp)
    if routed is not None:
        return routed
    hint = None
    if hybrid_enabled and hint_provider is not None:
        try:
            hint = hint_provider()
        except Exception:
            hint = None
    augmented = augment_input_with_hint(inp, hint, enabled=hybrid_enabled)
    return fallback(augmented, *args, **(kwargs or {}))
