from __future__ import annotations

from typing import TypeVar

ToolList = TypeVar("ToolList")


def pick_all_tools(inp: str, all_tools: ToolList) -> ToolList:
    return all_tools
