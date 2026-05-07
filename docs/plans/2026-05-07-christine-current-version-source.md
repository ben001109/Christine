# Current Version Source Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish `0.2.0-alpha.1` as Christine's canonical current development-line version without changing package metadata or monolith runtime labels.

**Architecture:** Extend the pure `christine.versioning` module with `CURRENT_VERSION` and `current_version()`. Documentation will explain that this is the release-governance source for the active refactor line, while `pyproject.toml` package metadata and legacy monolith labels remain separate until explicit migration.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, existing `docs/VERSIONING.md`, existing `christine.versioning` module.

---

### Task 1: Baseline And Plan

**Target Version:** `0.2.0-alpha.1`

**Stage:** `alpha`


**Files:**
- Create: `docs/plans/2026-05-07-christine-current-version-source.md`

**Step 1: Verify baseline**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成`.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-current-version-source.md && git commit -m "docs: plan current version source"`

Expected: plan commit succeeds.

---

### Task 2: Add Current Version API

**Files:**
- Modify: `christine/versioning.py`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing tests**

Add tests for:
- `CURRENT_VERSION.public == "0.2.0-alpha.1"`.
- `CURRENT_VERSION.stage == VersionStage.ALPHA`.
- `current_version() == CURRENT_VERSION`.
- `current_version().public` parses with `parse_version()`.
- `current_version()` does not depend on legacy labels.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because `CURRENT_VERSION` and `current_version()` do not exist.

**Step 3: Implement minimal pure API**

In `christine/versioning.py`, add:

```python
CURRENT_VERSION = ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1)

def current_version() -> ChristineVersion:
    return CURRENT_VERSION
```

Rules:
- Do not mutate `pyproject.toml` in this slice.
- Do not change `christine_final.py` labels.
- Do not add boot output wiring.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/versioning.py tests/test_versioning.py && git commit -m "refactor: add current version source"`

Expected: commit succeeds.

---

### Task 3: Document Current Version Source

**Files:**
- Modify: `docs/VERSIONING.md`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing docs guard**

Add tests that assert `docs/VERSIONING.md` contains:
- `Current Development Version`
- `0.2.0-alpha.1`
- `CURRENT_VERSION`
- `pyproject.toml` remains package metadata until migration.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because docs do not describe current version source yet.

**Step 3: Update docs**

Add `## Current Development Version` to `docs/VERSIONING.md`:
- Current canonical development-line version is `0.2.0-alpha.1`.
- `CURRENT_VERSION` and `current_version()` in `christine.versioning` are the current release-governance source.
- `pyproject.toml` remains package metadata and will be aligned only in a separate package/version migration slice.
- Legacy labels remain in `LEGACY_VERSION_RECORDS`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add docs/VERSIONING.md tests/test_versioning.py && git commit -m "docs: document current development version"`

Expected: commit succeeds.

---

### Task 4: Final Verification And Merge

**Files:**
- No planned production edits.

**Step 1: Run final checks**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: all pass.

Run: `uv run pytest -q`

Expected: all pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 2: Review**

Request blocker-focused review for:
- `christine/versioning.py`
- `tests/test_versioning.py`
- `docs/VERSIONING.md`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/current-version-source`.
- Delete branch `current-version-source`.
- Push `main` under the current “push後繼續” workflow.
