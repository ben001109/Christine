# Christine Modelization Retrieval Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a safe, local, read-only repository retrieval boundary for Christine's modelization layer.

**Architecture:** Build a small lexical retrieval module on top of the existing corpus filter. The module reads only paths allowed by `iter_model_corpus_paths()`, returns ranked snippets, and avoids embeddings, cloud calls, persistence, or runtime behavior changes.

**Tech Stack:** Python 3.10+, stdlib only, uv, pytest.

---

## Requirements Captured

- Continue the modelization track after the corpus filter and repository manifest.
- Keep retrieval local-first and read-only.
- Do not add Sentry, New Relic, Clerk, embedding services, vector databases, or cloud telemetry.
- Do not read paths excluded by `christine.modelization.corpus`.
- Do not persist indexes or modify runtime state.
- Preserve launcher and monolith behavior.

## Non-Goals

- No semantic embeddings.
- No model inference.
- No fine-tuning or LoRA/SFT.
- No upload or sync.
- No chat/memory ingestion.
- No changes to `christine_final.py` behavior.

## Task 1: Add Retrieval Contract Tests

**Files:**
- Create: `tests/test_modelization_retrieval.py`

**Step 1: Write the failing tests**

```python
from christine.modelization.retrieval import search_repository_corpus


def _write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_search_repository_corpus_ranks_safe_matches(tmp_path):
    _write(tmp_path, "docs/runtime.md", "runtime health health check")
    _write(tmp_path, "christine/runtime/health.py", "def runtime_self_test(): return 'health'")
    _write(tmp_path, "data/private.md", "runtime health private memory")

    results = search_repository_corpus(tmp_path, "runtime health")

    assert [result.path for result in results] == [
        "docs/runtime.md",
        "christine/runtime/health.py",
    ]
    assert all("data/private.md" != result.path for result in results)


def test_search_repository_corpus_returns_bounded_snippets(tmp_path):
    _write(tmp_path, "docs/long.md", "alpha " * 100 + "runtime health " + "omega " * 100)

    (result,) = search_repository_corpus(tmp_path, "runtime health", snippet_chars=80)

    assert result.path == "docs/long.md"
    assert "runtime health" in result.snippet
    assert len(result.snippet) <= 80


def test_search_repository_corpus_returns_empty_for_blank_query(tmp_path):
    _write(tmp_path, "docs/runtime.md", "runtime health")

    assert search_repository_corpus(tmp_path, "   ") == ()
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_modelization_retrieval.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.modelization.retrieval'`.

**Step 3: Commit**

Do not commit RED tests alone unless stopping the session. Continue to Task 2 in the same batch.

---

## Task 2: Implement Local Lexical Retrieval

**Files:**
- Create: `christine/modelization/retrieval.py`
- Test: `tests/test_modelization_retrieval.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .corpus import iter_model_corpus_paths


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class RepositorySearchResult:
    path: str
    score: int
    snippet: str


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in TOKEN_RE.findall(text))


def _snippet(text: str, query_tokens: tuple[str, ...], snippet_chars: int) -> str:
    lower_text = text.lower()
    first_match = min(
        (lower_text.find(token) for token in query_tokens if token in lower_text),
        default=0,
    )
    start = max(0, first_match - snippet_chars // 3)
    return text[start : start + snippet_chars].replace("\n", " ")


def search_repository_corpus(
    root: str | Path,
    query: str,
    *,
    limit: int = 10,
    snippet_chars: int = 240,
    max_document_bytes: int = 200_000,
) -> tuple[RepositorySearchResult, ...]:
    query_tokens = _tokens(query)
    if not query_tokens or limit <= 0:
        return ()

    root_path = Path(root)
    results: list[RepositorySearchResult] = []
    for relative in iter_model_corpus_paths(root_path):
        path = root_path / relative
        data = path.read_bytes()[:max_document_bytes]
        text = data.decode("utf-8", errors="replace")
        counts = Counter(_tokens(text))
        score = sum(counts[token] for token in query_tokens)
        if score:
            results.append(
                RepositorySearchResult(
                    path=relative,
                    score=score,
                    snippet=_snippet(text, query_tokens, snippet_chars),
                )
            )

    return tuple(sorted(results, key=lambda result: (-result.score, result.path))[:limit])
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/modelization/retrieval.py tests/test_modelization_retrieval.py
git commit -m "refactor: add local repository retrieval"
```

---

## Task 3: Export Retrieval Boundary

**Files:**
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_retrieval.py`

**Step 1: Add export test**

Append to `tests/test_modelization_retrieval.py`:

```python
def test_modelization_exports_repository_retrieval_boundary():
    from christine.modelization import RepositorySearchResult, search_repository_corpus

    assert RepositorySearchResult.__name__ == "RepositorySearchResult"
    assert callable(search_repository_corpus)
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_modelization_retrieval.py::test_modelization_exports_repository_retrieval_boundary -q`

Expected: fail with import error.

**Step 3: Export symbols**

```python
from .retrieval import RepositorySearchResult, search_repository_corpus

__all__ = [
    ...,
    "RepositorySearchResult",
    "search_repository_corpus",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/modelization/__init__.py tests/test_modelization_retrieval.py
git commit -m "refactor: export repository retrieval boundary"
```

---

## Task 4: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused modelization tests**

Run: `uv run pytest tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

Expected: all pass.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: all pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0 with no compile errors.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `自檢完成`.

**Step 5: Run whitespace check**

Run: `git diff --check`

Expected: exit 0.

**Step 6: Request review**

Request blocker-focused code review for the retrieval boundary.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.
