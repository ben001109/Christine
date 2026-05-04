from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class CorpusDocument:
    path: str
    suffix: str
    size_bytes: int
    sha256: str


def _validate_repository_relative_path(relative_path: str) -> PurePosixPath:
    raw = relative_path.replace("\\", "/")
    windows_path = PureWindowsPath(relative_path)
    posix = PurePosixPath(raw)
    if posix.is_absolute() or windows_path.is_absolute() or windows_path.drive or ".." in posix.parts:
        raise ValueError("path must be repository-relative")
    return PurePosixPath(posix.as_posix())


def build_corpus_document(root: str | Path, relative_path: str) -> CorpusDocument:
    posix = _validate_repository_relative_path(relative_path)
    path = Path(root) / posix.as_posix()
    data = path.read_bytes()
    return CorpusDocument(
        path=posix.as_posix(),
        suffix=posix.suffix.lower(),
        size_bytes=len(data),
        sha256=sha256(data).hexdigest(),
    )
