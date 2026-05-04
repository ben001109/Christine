from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class CorpusDecision:
    include: bool
    reason: str


EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".worktrees",
    "__pycache__",
    "backups",
    "data",
    "level5_logs",
    "mirrors",
    "self_replicas",
    "v42_export",
}
EXCLUDED_PREFIXES = {"ARC-AGI", "brain/generated"}
EXCLUDED_FILE_NAMES = {".env", "growth.log", "heartbeat.txt", "nexus_v2_state.json", "uv.lock"}
EXCLUDED_SUFFIXES = {
    ".7z",
    ".bin",
    ".db",
    ".dll",
    ".exe",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".npy",
    ".npz",
    ".pdf",
    ".pickle",
    ".pkl",
    ".png",
    ".pt",
    ".pyc",
    ".pyo",
    ".safetensors",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".webp",
    ".zip",
}
SECRET_NAME_MARKERS = {"credential", "credentials", "secret", "token", "cookie", "cookies", "apikey", "api_key"}
ALLOWED_SUFFIXES = {".bat", ".md", ".ps1", ".py", ".toml", ".txt", ".yaml", ".yml"}


def _normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def decide_model_corpus_path(path: str) -> CorpusDecision:
    raw = path.replace("\\", "/")
    if PurePosixPath(raw).is_absolute() or PureWindowsPath(path).is_absolute():
        return CorpusDecision(False, "excluded-absolute-path")

    normalized = _normalize(path)
    posix = PurePosixPath(normalized)
    lower_name = posix.name.lower()
    lower_parts = tuple(part.lower() for part in posix.parts)

    if ".." in posix.parts:
        return CorpusDecision(False, "excluded-path-traversal")

    for part in lower_parts:
        if part in EXCLUDED_PARTS:
            return CorpusDecision(False, f"excluded-path-part:{part}")
    for prefix in EXCLUDED_PREFIXES:
        lower_normalized = normalized.lower()
        lower_prefix = prefix.lower()
        if lower_normalized == lower_prefix or lower_normalized.startswith(lower_prefix + "/"):
            return CorpusDecision(False, f"excluded-prefix:{prefix}")
    if lower_name in EXCLUDED_FILE_NAMES:
        return CorpusDecision(False, f"excluded-file:{lower_name}")
    if any(marker in part for part in lower_parts for marker in SECRET_NAME_MARKERS):
        return CorpusDecision(False, "excluded-secret-name")
    if any(lower_name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return CorpusDecision(False, "excluded-binary-or-artifact")
    if posix.suffix.lower() not in ALLOWED_SUFFIXES:
        return CorpusDecision(False, "excluded-unsupported-suffix")
    return CorpusDecision(True, "included")


def should_include_in_model_corpus(path: str) -> bool:
    return decide_model_corpus_path(path).include


def _is_excluded_container(path: str) -> bool:
    decision = decide_model_corpus_path(path + "/placeholder.py")
    return not decision.include and (
        decision.reason.startswith("excluded-path-part:")
        or decision.reason.startswith("excluded-prefix:")
        or decision.reason == "excluded-secret-name"
    )


def iter_model_corpus_paths(root: str | Path) -> Iterator[str]:
    root_path = Path(root)
    for current, dirs, files in os.walk(root_path):
        current_path = Path(current)
        relative_current = current_path.relative_to(root_path).as_posix()

        kept_dirs = []
        for directory in sorted(dirs):
            relative_dir = directory if relative_current == "." else f"{relative_current}/{directory}"
            if not _is_excluded_container(relative_dir):
                kept_dirs.append(directory)
        dirs[:] = kept_dirs

        for file_name in sorted(files):
            path = current_path / file_name
            if path.is_symlink():
                continue
            relative = path.relative_to(root_path).as_posix()
            if should_include_in_model_corpus(relative):
                yield relative
