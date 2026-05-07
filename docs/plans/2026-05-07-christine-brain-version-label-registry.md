# Brain Version Label Registry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Register the existing `brain/__init__.py` `__version__ = "0.1.0"` label as a legacy brain subsystem label without changing runtime behavior.

**Architecture:** Treat `brain.__version__` as an active subsystem/runtime compatibility label owned by the extracted `brain` package, not as Christine's release-governance version and not as Python package metadata. Add it to `LEGACY_VERSION_RECORDS` and `docs/versions/LEGACY_VERSIONS.md` with tests that verify the value still exists in source and remains non-governing.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, existing `christine.versioning` module, existing legacy version inventory docs.

---

### Task 1: Baseline And Plan

**Target Version:** `0.2.0-alpha.1`

**Package Metadata Version:** `0.2.0a1`

**Stage:** `alpha`

**Files:**
- Create: `docs/plans/2026-05-07-christine-brain-version-label-registry.md`

**Step 1: Verify baseline**

Run: `uv sync && uv run pytest tests/test_versioning.py -q`

Expected: all focused versioning tests pass.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-brain-version-label-registry.md && git commit -m "docs: plan brain version label registry"`

Expected: plan commit succeeds.

---

### Task 2: Add Brain Version Label Guards

**Files:**
- Modify: `tests/test_versioning.py`

**Step 1: Write failing tests**

Add tests that assert:
- `legacy_version_by_name("brain.__version__")` exists.
- Its value is `0.1.0`.
- Its source is `brain/__init__.py`.
- Its kind is `LegacyVersionKind.SUBSYSTEM_LABEL`.
- It is active but `governs_public_release is False`.
- The active record value exists in `brain/__init__.py`.
- `docs/versions/LEGACY_VERSIONS.md` contains `brain.__version__` and `brain/__init__.py`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because `brain.__version__` is not registered or documented yet.

---

### Task 3: Register And Document Brain Version Label

**Files:**
- Modify: `christine/versioning.py`
- Modify: `docs/versions/LEGACY_VERSIONS.md`
- Modify: `tests/test_versioning.py`

**Step 1: Update registry**

Add this record to `LEGACY_VERSION_RECORDS`:

```python
LegacyVersionRecord(
    "brain.__version__",
    "0.1.0",
    "brain/__init__.py",
    LegacyVersionKind.SUBSYSTEM_LABEL,
    "Extracted brain package subsystem label retained for compatibility.",
)
```

Rules:
- Do not edit `brain/__init__.py` in this slice.
- Do not change `pyproject.toml` or `uv.lock`.
- Do not change `CURRENT_VERSION`.
- Do not change `christine_final.py` legacy labels.

**Step 2: Update inventory docs**

Add an active row for `brain.__version__` in `docs/versions/LEGACY_VERSIONS.md`.

**Step 3: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 4: Commit**

Run: `git add christine/versioning.py docs/versions/LEGACY_VERSIONS.md tests/test_versioning.py && git commit -m "refactor: register brain version label"`

Expected: commit succeeds.

---

### Task 4: Final Verification And Merge

**Files:**
- No additional planned edits.

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
- `docs/versions/LEGACY_VERSIONS.md`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/brain-version-label-registry`.
- Delete branch `brain-version-label-registry`.
- Push `main` under the current “push後繼續” workflow.
