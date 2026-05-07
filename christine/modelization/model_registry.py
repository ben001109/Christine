from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ModelArtifactRecord:
    name: str
    base_model: str
    adapter_path: str
    eval_report: str


def validate_model_artifact_path(path: str) -> Path:
    posix = PurePosixPath(path.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError("path must be repository-relative")
    if len(posix.parts) < 3 or posix.parts[0] != "artifacts" or posix.parts[1] != "models":
        raise ValueError("model artifacts must live under artifacts/models")
    return Path(posix.as_posix())
