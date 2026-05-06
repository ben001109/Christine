from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.util import find_spec
from urllib.request import urlopen


PLAIN_COLORS = {"GR": "", "YE": "", "D": "", "R": ""}


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


def check_ollama_service(
    *,
    url: str = "http://127.0.0.1:11434/api/tags",
    timeout: float = 0.2,
    opener: Callable[..., object] = urlopen,
) -> OptionalDependencyStatus:
    try:
        with opener(url, timeout=timeout):
            return OptionalDependencyStatus("ollama", True, "local LLM", "reachable")
    except Exception as exc:
        return OptionalDependencyStatus("ollama", False, "local LLM", str(exc)[:120])


def _colors(enabled: bool) -> dict[str, str]:
    if not enabled:
        return PLAIN_COLORS
    return {"GR": "\033[32m", "YE": "\033[33m", "D": "\033[2m", "R": "\033[0m"}


def render_optional_dependency_diagnostics(
    statuses: tuple[OptionalDependencyStatus, ...],
    *,
    colors: bool = True,
) -> list[str]:
    c = _colors(colors)
    lines = [f"  {c['YE']}[Optional Dependencies]{c['R']}"]
    for status in statuses:
        mark = f"{c['GR']}✓{c['R']}" if status.available else f"{c['YE']}~{c['R']}"
        lines.append(f"    {status.name:<22}: {mark} {status.message} ({status.purpose})")
    return lines


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
