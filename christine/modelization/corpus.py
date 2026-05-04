from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


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
    normalized = _normalize(path)
    posix = PurePosixPath(normalized)
    lower_name = posix.name.lower()

    for part in posix.parts:
        if part in EXCLUDED_PARTS:
            return CorpusDecision(False, f"excluded-path-part:{part}")
    for prefix in EXCLUDED_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return CorpusDecision(False, f"excluded-prefix:{prefix}")
    if lower_name in EXCLUDED_FILE_NAMES:
        return CorpusDecision(False, f"excluded-file:{lower_name}")
    if any(marker in lower_name for marker in SECRET_NAME_MARKERS):
        return CorpusDecision(False, "excluded-secret-name")
    if any(lower_name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return CorpusDecision(False, "excluded-binary-or-artifact")
    if posix.suffix.lower() not in ALLOWED_SUFFIXES:
        return CorpusDecision(False, "excluded-unsupported-suffix")
    return CorpusDecision(True, "included")


def should_include_in_model_corpus(path: str) -> bool:
    return decide_model_corpus_path(path).include
