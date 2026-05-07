from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ModelArtifactRecord:
    name: str
    base_model: str
    adapter_path: str
    eval_report: str

    def __post_init__(self) -> None:
        validate_model_artifact_path(self.adapter_path)
        validate_model_eval_report_path(self.eval_report)


def _validate_artifact_path(path: str, directory: str, message: str) -> Path:
    posix = PurePosixPath(str(path).replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError("path must be repository-relative")
    if len(posix.parts) < 3 or posix.parts[0] != "artifacts" or posix.parts[1] != directory:
        raise ValueError(message)
    return Path(posix.as_posix())


def validate_model_artifact_path(path: str) -> Path:
    return _validate_artifact_path(path, "models", "model artifacts must live under artifacts/models")


def validate_model_eval_report_path(path: str) -> Path:
    return _validate_artifact_path(path, "evals", "model eval reports must live under artifacts/evals")
