from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath

from .corpus import iter_model_corpus_paths


@dataclass(frozen=True)
class CorpusDocument:
    path: str
    suffix: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class CorpusManifest:
    schema_version: int
    documents: tuple[CorpusDocument, ...]

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def total_size_bytes(self) -> int:
        return sum(document.size_bytes for document in self.documents)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "document_count": self.document_count,
            "total_size_bytes": self.total_size_bytes,
            "documents": [
                {
                    "path": document.path,
                    "suffix": document.suffix,
                    "size_bytes": document.size_bytes,
                    "sha256": document.sha256,
                }
                for document in self.documents
            ],
        }


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


def _validate_manifest_root(root: str | Path) -> Path:
    root_path = Path(root)
    if root_path.is_symlink():
        raise ValueError("manifest root must not be a symlink root")
    if not root_path.is_dir():
        raise ValueError("manifest root must be a directory root")
    return root_path


def build_corpus_manifest(root: str | Path) -> CorpusManifest:
    root_path = _validate_manifest_root(root)
    documents = tuple(build_corpus_document(root_path, relative) for relative in iter_model_corpus_paths(root_path))
    return CorpusManifest(schema_version=1, documents=documents)
