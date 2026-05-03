from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    logs: Path
    growth_log: Path
    heartbeat: Path
    nexus_state: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "RuntimePaths":
        base = Path(root).resolve()
        return cls(
            root=base,
            data=base / "data",
            logs=base / "level5_logs",
            growth_log=base / "growth.log",
            heartbeat=base / "heartbeat.txt",
            nexus_state=base / "nexus_v2_state.json",
        )
