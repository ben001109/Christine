from __future__ import annotations

from pathlib import PurePosixPath


EXCLUDED_PARTS = {".git", ".venv", "data", "level5_logs", "__pycache__"}
EXCLUDED_PREFIXES = {"brain/generated", "ARC-AGI"}
EXCLUDED_SUFFIXES = {".env", ".pyc", ".pkl", ".npy", ".safetensors", ".pt"}


def should_include_in_model_corpus(path: str) -> bool:
    normalized = path.replace("\\", "/")
    posix = PurePosixPath(normalized)
    if any(part in EXCLUDED_PARTS for part in posix.parts):
        return False
    if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in EXCLUDED_PREFIXES):
        return False
    return not any(normalized.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)
