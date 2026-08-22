"""Capability gate for the legacy Christine monolith."""

from __future__ import annotations

_DENIED_EXIT_CODE = 86


def _build_legacy_runtime_gate():
    authorization = object()

    def _issue_legacy_runtime_authorization() -> object:
        """Return the private capability used by the trusted boot handoff."""
        return authorization

    def require_legacy_runtime_authorization(token: object | None = None) -> None:
        """Terminate silently unless ``token`` is the boot-issued capability."""
        if token is not authorization:
            raise SystemExit(_DENIED_EXIT_CODE)

    return _issue_legacy_runtime_authorization, require_legacy_runtime_authorization


_issue_legacy_runtime_authorization, require_legacy_runtime_authorization = _build_legacy_runtime_gate()
del _build_legacy_runtime_gate


__all__ = ["require_legacy_runtime_authorization"]
