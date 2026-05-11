from __future__ import annotations

import json
from typing import Any


IMAGE_RESULT_TOOLS = frozenset({"capture_screen", "capture_camera"})


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
