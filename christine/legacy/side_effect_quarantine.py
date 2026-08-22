"""Fail-closed denials for legacy side-effecting tool entry points."""

from __future__ import annotations


def deny_legacy_code_execution() -> dict[str, object]:
    """Return a fresh, content-free denial for legacy code execution tools."""
    return {
        "ok": False,
        "e": "tool_denied",
        "code": "legacy-code-execution-quarantined",
    }


__all__ = ["deny_legacy_code_execution"]
