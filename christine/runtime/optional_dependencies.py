from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True)
class OptionalDependencyStatus:
    name: str
    available: bool
    purpose: str
    message: str


def check_optional_module(
    name: str,
    *,
    purpose: str,
    finder: Callable[[str], object | None] = find_spec,
) -> OptionalDependencyStatus:
    available = finder(name) is not None
    return OptionalDependencyStatus(name, available, purpose, "available" if available else "missing")


def check_optional_service(
    name: str,
    *,
    purpose: str,
    checker: Callable[[], tuple[bool, str]],
) -> OptionalDependencyStatus:
    available, message = checker()
    return OptionalDependencyStatus(name, available, purpose, message)


def optional_dependency_report(
    *,
    finder: Callable[[str], object | None] = find_spec,
    service_checkers: Mapping[str, Callable[[], tuple[bool, str]]] | None = None,
) -> tuple[OptionalDependencyStatus, ...]:
    service_checkers = service_checkers or {}
    statuses = [
        check_optional_module("torch", purpose="GPU acceleration", finder=finder),
        check_optional_module("pynput", purpose="global hotkeys", finder=finder),
        check_optional_module("sentence_transformers", purpose="semantic embeddings", finder=finder),
    ]
    ollama_checker = service_checkers.get("ollama", lambda: (False, "not checked"))
    statuses.append(check_optional_service("ollama", purpose="local LLM", checker=ollama_checker))
    return tuple(statuses)
