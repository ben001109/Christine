from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any


IMAGE_RESULT_TOOLS = frozenset({"capture_screen", "capture_camera"})

ToolHandlerMap = Mapping[str, Callable[[Any], Any]]

LEGACY_TOOL_FALLBACK_ALIASES = {
    "codeforge_write_any_file": "write_file",
    "codeforge_patch_any_file": "write_file",
    "docstudio_create_pdf": "create_pdf",
    "docstudio_create_docx": "create_pdf",
}


def execute_tool_handler(
    tool_name: str,
    tool_input: Any,
    handlers: ToolHandlerMap,
    *,
    fallback_aliases: Mapping[str, str] = LEGACY_TOOL_FALLBACK_ALIASES,
) -> Any:
    if tool_name not in handlers:
        return "tool_not_mapped:" + tool_name
    try:
        return handlers[tool_name](tool_input)
    except Exception as tool_error:
        fallback_name = fallback_aliases.get(tool_name)
        if fallback_name and fallback_name in handlers:
            try:
                fallback_result = handlers[fallback_name](tool_input)
                return str(fallback_result) + " (fallback:" + fallback_name + ")"
            except Exception:
                pass
        return {"ok": False, "e": "tool error: " + str(tool_error)}


def format_tool_result_message(
    tool_use_id: str,
    tool_name: str,
    result: Any,
    *,
    text_limit: int = 3000,
) -> dict[str, Any]:
    if tool_name in IMAGE_RESULT_TOOLS and isinstance(result, dict) and result.get("ok"):
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result["img"],
                    },
                },
                {"type": "text", "text": "Describe and help."},
            ],
        }
    if isinstance(result, dict):
        text = result.get("e", "err") if not result.get("ok", True) else json.dumps(result, ensure_ascii=False)
    else:
        text = str(result)
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": text[:text_limit]}
