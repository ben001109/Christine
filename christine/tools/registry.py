from __future__ import annotations

from collections.abc import Callable, Iterable, MutableMapping
from dataclasses import dataclass
from typing import Any


ToolHandler = Callable[[dict[str, Any]], Any]


def tool_schema(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
        },
    }


@dataclass(frozen=True)
class ToolRegistration:
    schema: dict[str, Any]
    handler: ToolHandler | None = None
    keywords: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return str(self.schema.get("name", ""))


def apply_tool_registrations(
    core: Iterable[dict[str, Any]],
    extra: list[dict[str, Any]],
    handlers: MutableMapping[str, ToolHandler],
    keywords: list[str],
    registrations: Iterable[ToolRegistration],
) -> list[dict[str, Any]]:
    for registration in registrations:
        extra.append(registration.schema)
        if registration.handler is not None and registration.name:
            handlers[registration.name] = registration.handler
        for keyword in registration.keywords:
            if keyword not in keywords:
                keywords.append(keyword)
    return list(core) + extra
