# Christine Modelization Corpus Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden Christine's modelization corpus safety boundary before any embeddings, training, sync, upload, or inference work.

**Architecture:** Keep modelization local and read-only. Extend `christine.modelization.corpus` from a boolean predicate into a reasoned, testable corpus policy plus a safe repository path iterator that prunes excluded directories before reading files.

**Tech Stack:** Python 3.10+, pathlib/os.walk, dataclasses, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Preserve the existing public `should_include_in_model_corpus(path: str) -> bool` API.
- Do not build embeddings, train models, call remote services, upload files, or read private runtime state.
- Exclude runtime state, generated code, mirrors, backups, self replicas, caches, worktrees, model weights, binary artifacts, secrets, and credential-like names.
- Include conservative source/docs/test paths needed for future local repository knowledge work.
- Keep behavior deterministic and import-side-effect free.
- Use TDD for every production-code change.

## Current Facts

- `christine/modelization/corpus.py` currently has `should_include_in_model_corpus(path)` with small exclusion sets.
- `tests/test_modelization_corpus.py` has a basic include/exclude smoke test.
- `docs/plans/2026-05-03-christine-modelization-design.md` defines the modelization boundary and first corpus filter goal.
- Top-level repository contains large or unsafe folders such as `backups/`, `mirrors/`, `v42_export/`, `.venv/`, and generated/runtime artifacts.

## Out Of Scope

- Embedding indexes or vector stores.
- Fine-tuning, LoRA, SFT, or behavior distillation.
- Reading `data/`, memory databases, logs, `nexus_v2_state.json`, or other runtime state.
- Changing launcher, brain, GUI, deployment, or ask-routing behavior.
- Adding dependencies.

---

### Task 1: Add Reasoned Corpus Policy Tests

**Files:**
- Modify: `tests/test_modelization_corpus.py`
- Later modify: `christine/modelization/corpus.py`

**Step 1: Replace the basic test with explicit include cases**

Use `pytest.mark.parametrize` for allowed paths:

```python
import pytest

from christine.modelization.corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    should_include_in_model_corpus,
)


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "boot_christine.py",
        "christine/modelization/corpus.py",
        "brain/runtime.py",
        "docs/plans/x.md",
        "tests/test_modelization_corpus.py",
        "Start_Christine.bat",
        "啟動Christine.ps1",
        "pyproject.toml",
    ],
)
def test_model_corpus_includes_conservative_source_docs_and_tests(path):
    assert should_include_in_model_corpus(path)
```

**Step 2: Add explicit exclusion cases**

```python
@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "config/credentials.json",
        "config/api_token.txt",
        "browser/Cookies",
        "data/private_memory.json",
        "level5_logs/run.log",
        "growth.log",
        "heartbeat.txt",
        "nexus_v2_state.json",
        "brain/generated/area_000001.py",
        "ARC-AGI/data.json",
        "backups/christine_final.py",
        "mirrors/a/christine_final.py",
        "self_replicas/christine_final.py",
        ".worktrees/feature/christine_final.py",
        ".venv/lib/site-packages/pkg.py",
        ".pytest_cache/v/cache/nodeids",
        "v42_export/model.safetensors",
        "models/local.pt",
        "notes/archive.zip",
        "image.png",
        "uv.lock",
    ],
)
def test_model_corpus_excludes_private_generated_bulk_and_binary_paths(path):
    assert not should_include_in_model_corpus(path)
```

**Step 3: Add reasoned decision test**

```python
def test_model_corpus_returns_reasoned_decisions():
    assert decide_model_corpus_path("christine/modelization/corpus.py") == CorpusDecision(
        include=True,
        reason="included",
    )

    assert decide_model_corpus_path("data/private_memory.json") == CorpusDecision(
        include=False,
        reason="excluded-path-part:data",
    )

    assert decide_model_corpus_path("config/credentials.json") == CorpusDecision(
        include=False,
        reason="excluded-secret-name",
    )
```

**Step 4: Run RED**

Run: `uv run pytest tests/test_modelization_corpus.py -q`

Expected: fail because `CorpusDecision` and `decide_model_corpus_path` do not exist, and current exclusions are incomplete.

---

### Task 2: Implement Reasoned Corpus Decisions

**Files:**
- Modify: `christine/modelization/corpus.py`
- Modify: `christine/modelization/__init__.py`

**Step 1: Add dataclass and conservative policy constants**

Implement in `christine/modelization/corpus.py`:

```python
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
```

**Step 2: Normalize paths consistently**

```python
def _normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/")
```

**Step 3: Implement decision function**

```python
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
```

**Step 4: Preserve boolean wrapper**

```python
def should_include_in_model_corpus(path: str) -> bool:
    return decide_model_corpus_path(path).include
```

**Step 5: Export new symbols**

Modify `christine/modelization/__init__.py`:

```python
from .corpus import CorpusDecision, decide_model_corpus_path, should_include_in_model_corpus

__all__ = ["CorpusDecision", "decide_model_corpus_path", "should_include_in_model_corpus"]
```

**Step 6: Run focused tests**

Run: `uv run pytest tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 7: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 8: Commit**

Commit message: `refactor: harden model corpus path policy`

---

### Task 3: Add Safe Corpus Path Iterator

**Files:**
- Modify: `tests/test_modelization_corpus.py`
- Modify: `christine/modelization/corpus.py`
- Modify: `christine/modelization/__init__.py`

**Step 1: Add failing iterator test**

Append to `tests/test_modelization_corpus.py`:

```python
def test_iter_model_corpus_paths_prunes_excluded_directories(tmp_path):
    files = {
        "AGENTS.md": "guide",
        "christine/modelization/corpus.py": "source",
        "docs/plans/modelization.md": "plan",
        "tests/test_modelization_corpus.py": "tests",
        "data/private_memory.json": "private",
        "brain/generated/area_000001.py": "generated",
        "mirrors/a/christine_final.py": "mirror",
        ".worktrees/feature/christine_final.py": "worktree",
        "v42_export/model.safetensors": "weights",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    assert list(iter_model_corpus_paths(tmp_path)) == [
        "AGENTS.md",
        "christine/modelization/corpus.py",
        "docs/plans/modelization.md",
        "tests/test_modelization_corpus.py",
    ]
```

Import `iter_model_corpus_paths` at the top.

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_corpus.py -q`

Expected: fail because `iter_model_corpus_paths` does not exist.

**Step 3: Implement directory pruning helper**

Add to `corpus.py`:

```python
from pathlib import Path
from collections.abc import Iterator
import os


def _is_excluded_container(path: str) -> bool:
    decision = decide_model_corpus_path(path + "/placeholder.py")
    return not decision.include and (
        decision.reason.startswith("excluded-path-part:") or decision.reason.startswith("excluded-prefix:")
    )
```

Keep imports sorted and avoid introducing any side effects.

**Step 4: Implement iterator**

```python
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
            relative = path.relative_to(root_path).as_posix()
            if should_include_in_model_corpus(relative):
                yield relative
```

**Step 5: Export iterator**

Modify `christine/modelization/__init__.py` to include `iter_model_corpus_paths` in import and `__all__`.

**Step 6: Run focused tests**

Run: `uv run pytest tests/test_modelization_corpus.py -q`

Expected: pass.

**Step 7: Run related tests**

Run: `uv run pytest tests/test_modelization_corpus.py tests/test_deployment_protocol.py -q`

Expected: pass.

**Step 8: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 9: Commit**

Commit message: `refactor: add safe model corpus iterator`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_modelization_corpus.py -q`

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

- Existing `should_include_in_model_corpus()` API preserved.
- No embeddings/training/upload/remote calls added.
- Excluded directories are pruned before file-level inclusion checks.
- Runtime/private state, generated code, backups, mirrors, worktrees, model weights, binary artifacts, and credential-like names are excluded.
- No new dependencies.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_modelization_corpus.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if corpus filtering blocks a needed source.
- Do not alter runtime state artifacts.
- Do not read excluded directories as part of tests or implementation.
- Keep `should_include_in_model_corpus()` as the compatibility wrapper even if later waves add richer policy objects.
