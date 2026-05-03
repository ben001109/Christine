from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    service: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {"ok": self.ok, "service": self.service, "detail": self.detail}
