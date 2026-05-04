# Christine Modelization Repository Index Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first local repository knowledge/RAG groundwork by building a deterministic, safe corpus manifest over Christine's filtered repository files.

**Architecture:** Keep this wave metadata-only: no embeddings, no vector store, no model calls, no remote services, and no persisted index writes. Add `christine.modelization.repository_index` to turn safe corpus paths from `iter_model_corpus_paths()` into immutable document metadata and a deterministic manifest with SHA-256 digests and byte sizes.

**Tech Stack:** Python 3.10+, pathlib, hashlib, dataclasses, stdlib JSON-friendly dicts, uv, pytest. No new dependencies.

---

## Requirements Captured

- Build on the Wave 9 corpus filter and iterator; do not bypass `iter_model_corpus_paths()`.
- Do not build embeddings, train models, call remote services, upload files, or read excluded/private runtime state.
- Do not persist generated indexes in this wave.
- Keep output deterministic for tests and future cache invalidation.
- Preserve existing `christine.modelization` public exports.
- Use TDD for every production-code change.

## Current Facts

- `christine/modelization/corpus.py` owns safe path decisions and `iter_model_corpus_paths(root)`.
- `tests/test_modelization_corpus.py` verifies private/generated/worktree/binary/secret/traversal exclusions.
- `docs/plans/2026-05-03-christine-modelization-design.md` says repository knowledge should be read-only and local-first.
- `docs/plans/2026-05-03-christine-full-refactor.md` says repository embeddings/RAG must happen before any fine-tuning, but after corpus filter/design.

## Out Of Scope

- Embedding generation, vector databases, nearest-neighbor search, or chunk ranking.
- Reading or summarizing `data/`, logs, generated cortex files, backups, mirrors, worktrees, secrets, or model weights.
- Writing a manifest file to disk.
- Integrating with `christine_final.py`, launcher startup, GUI, deployment health, or ask routing.
- Adding dependencies.

---

### Task 1: Add Repository Document Metadata Tests

**Files:**
- Create: `tests/test_modelization_repository_index.py`
- Later create: `christine/modelization/repository_index.py`

**Step 1: Write failing document metadata test**

Create `tests/test_modelization_repository_index.py`:

```python
from hashlib import sha256

from christine.modelization.repository_index import CorpusDocument, build_corpus_document


def test_build_corpus_document_records_stable_metadata(tmp_path):
    root = tmp_path
    document = root / "docs" / "plan.md"
    document.parent.mkdir(parents=True)
    document.write_text("Christine\n", encoding="utf-8")

    assert build_corpus_document(root, "docs/plan.md") == CorpusDocument(
        path="docs/plan.md",
        suffix=".md",
        size_bytes=10,
        sha256=sha256(b"Christine\n").hexdigest(),
    )
```

**Step 2: Write failing path validation tests**

Append:

```python
import pytest


@pytest.mark.parametrize(
    "relative_path",
    ["../outside.md", "/tmp/outside.md", "C:\\outside.md", "C:outside.md"],
)
def test_build_corpus_document_rejects_non_relative_repository_paths(tmp_path, relative_path):
    with pytest.raises(ValueError, match="repository-relative"):
        build_corpus_document(tmp_path, relative_path)
```

**Step 3: Run RED**

Run: `uv run pytest tests/test_modelization_repository_index.py -q`

Expected: fail because `christine.modelization.repository_index` does not exist.

---

### Task 2: Implement Corpus Document Metadata

**Files:**
- Create: `christine/modelization/repository_index.py`
- Modify: `christine/modelization/__init__.py`

**Step 1: Implement dataclass and private path validator**

Create `christine/modelization/repository_index.py`:

```python
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
```

**Step 2: Implement `build_corpus_document`**

```python
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
```

Do not catch exceptions from missing files; callers should see normal filesystem errors.

**Step 3: Export new symbols**

Modify `christine/modelization/__init__.py`:

```python
from .repository_index import CorpusDocument, build_corpus_document
```

Add `CorpusDocument` and `build_corpus_document` to `__all__`.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_repository_index.py tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 5: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 6: Commit**

Commit message: `refactor: add repository corpus document metadata`

---

### Task 3: Add Deterministic Repository Manifest

**Files:**
- Modify: `tests/test_modelization_repository_index.py`
- Modify: `christine/modelization/repository_index.py`
- Modify: `christine/modelization/__init__.py`

**Step 1: Add failing manifest test**

Append to `tests/test_modelization_repository_index.py`:

```python
from christine.modelization.repository_index import CorpusManifest, build_corpus_manifest


def test_build_corpus_manifest_uses_safe_iterator_and_deterministic_order(tmp_path):
    files = {
        "docs/b.md": "B",
        "docs/a.md": "A",
        "data/private.md": "private",
        "brain/generated/area.py": "generated",
        "secrets/config.py": "secret",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    manifest = build_corpus_manifest(tmp_path)

    assert isinstance(manifest, CorpusManifest)
    assert manifest.schema_version == 1
    assert [document.path for document in manifest.documents] == ["docs/a.md", "docs/b.md"]
    assert manifest.document_count == 2
    assert manifest.total_size_bytes == 2
```

**Step 2: Add failing serialization test**

```python
def test_corpus_manifest_serializes_without_file_contents(tmp_path):
    document = tmp_path / "docs" / "plan.md"
    document.parent.mkdir(parents=True)
    document.write_text("secret-free text", encoding="utf-8")

    payload = build_corpus_manifest(tmp_path).to_dict()

    assert payload["schema_version"] == 1
    assert payload["document_count"] == 1
    assert payload["documents"][0]["path"] == "docs/plan.md"
    assert "secret-free text" not in repr(payload)
```

**Step 3: Run RED**

Run: `uv run pytest tests/test_modelization_repository_index.py -q`

Expected: fail because `CorpusManifest` and `build_corpus_manifest` do not exist.

**Step 4: Implement manifest dataclass**

Add to `repository_index.py`:

```python
from .corpus import iter_model_corpus_paths


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
```

**Step 5: Implement manifest builder**

```python
def build_corpus_manifest(root: str | Path) -> CorpusManifest:
    documents = tuple(build_corpus_document(root, relative) for relative in iter_model_corpus_paths(root))
    return CorpusManifest(schema_version=1, documents=documents)
```

**Step 6: Export manifest symbols**

Modify `christine/modelization/__init__.py` to import and export `CorpusManifest` and `build_corpus_manifest`.

**Step 7: Run focused tests**

Run: `uv run pytest tests/test_modelization_repository_index.py tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 8: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 9: Commit**

Commit message: `refactor: add repository corpus manifest`

---

### Task 4: Add Manifest Root Safety Tests

**Files:**
- Modify: `tests/test_modelization_repository_index.py`
- Modify: `christine/modelization/repository_index.py`

**Step 1: Add failing root safety tests**

Append:

```python
def test_build_corpus_manifest_rejects_non_directory_root(tmp_path):
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="directory root"):
        build_corpus_manifest(not_a_dir)


def test_build_corpus_manifest_rejects_symlink_root(tmp_path):
    target = tmp_path / "repo"
    target.mkdir()
    link = tmp_path / "repo-link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported in this environment")

    with pytest.raises(ValueError, match="symlink root"):
        build_corpus_manifest(link)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_repository_index.py -q`

Expected: fail because root validation is not implemented.

**Step 3: Implement root validator**

Add to `repository_index.py`:

```python
def _validate_manifest_root(root: str | Path) -> Path:
    root_path = Path(root)
    if root_path.is_symlink():
        raise ValueError("manifest root must not be a symlink root")
    if not root_path.is_dir():
        raise ValueError("manifest root must be a directory root")
    return root_path
```

Update `build_corpus_manifest` to call `_validate_manifest_root(root)` once and use the returned `root_path`.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_repository_index.py tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 5: Run full tests and compile**

Run: `uv run pytest -q`

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: both pass.

**Step 6: Commit**

Commit message: `fix: validate repository manifest root`

---

### Task 5: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_modelization_repository_index.py tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 2: Run full test suite**

Run: `uv run pytest -q`

Expected: pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: pass.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass and print `自檢完成`.

**Step 5: Run whitespace diff check**

Run: `git diff --check`

Expected: no output.

**Step 6: Request code review**

Review requirements:

- Manifest builder uses `iter_model_corpus_paths()` and does not bypass corpus filtering.
- Manifest does not store document text.
- No embeddings, vector database, model calls, uploads, remote calls, or persistence added.
- Root validation rejects file roots and symlink roots.
- Existing modelization APIs remain exported.
- No new dependencies.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_modelization_repository_index.py tests/test_modelization_corpus.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if manifest generation causes risk.
- Do not delete or rewrite runtime state.
- Do not persist generated manifests until a later explicit plan defines storage, retention, and privacy handling.
- Future embeddings should consume this manifest or the safe iterator, not direct filesystem walks.
