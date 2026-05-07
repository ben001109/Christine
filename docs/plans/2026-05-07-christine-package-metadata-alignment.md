# Package Metadata Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align Christine's Python package metadata with the canonical current development version by changing package metadata from `0.1.0` to the PEP 440 form `0.2.0a1`.

**Architecture:** Keep `christine.versioning.CURRENT_VERSION` as the release-governance source and use `CURRENT_VERSION.package_metadata` as the expected package metadata value. Update `pyproject.toml` and the generated `uv.lock` package entry, then keep `LEGACY_VERSION_RECORDS` and `docs/versions/LEGACY_VERSIONS.md` as audit records showing the active package metadata and the previous `0.1.0` value.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, uv lock management, existing `christine.versioning` module, existing versioning policy docs.

---

### Task 1: Baseline And Plan

**Target Version:** `0.2.0-alpha.1`

**Package Metadata Version:** `0.2.0a1`

**Stage:** `alpha`

**Files:**
- Create: `docs/plans/2026-05-07-christine-package-metadata-alignment.md`

**Step 1: Verify baseline**

Run: `uv sync && uv run pytest tests/test_versioning.py -q`

Expected: all focused versioning tests pass.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-package-metadata-alignment.md && git commit -m "docs: plan package metadata alignment"`

Expected: plan commit succeeds.

---

### Task 2: Add Package Metadata Alignment Guards

**Files:**
- Modify: `tests/test_versioning.py`

**Step 1: Write failing tests**

Add tests for:
- `pyproject.toml` containing `version = "0.2.0a1"`.
- `uv.lock` containing the local package entry `name = "christine"` with `version = "0.2.0a1"`.
- `legacy_version_by_name("pyproject.version").value == current_version().package_metadata`.
- The previous `0.1.0` package metadata is retained as an inactive audit record, not lost.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because `pyproject.toml`, `uv.lock`, and the registry still use `0.1.0`.

---

### Task 3: Align Package Metadata And Audit Records

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `christine/versioning.py`
- Modify: `docs/versions/LEGACY_VERSIONS.md`
- Modify: `tests/test_versioning.py`

**Step 1: Update package metadata**

In `pyproject.toml`, change:

```toml
version = "0.1.0"
```

to:

```toml
version = "0.2.0a1"
```

Run: `uv lock`

Expected: `uv.lock` updates the local `christine` package entry to `version = "0.2.0a1"` without dependency churn.

**Step 2: Update registry**

In `christine/versioning.py`:
- Set active `pyproject.version` record to `0.2.0a1`.
- Update its note to say package metadata is aligned with `CURRENT_VERSION.package_metadata`, but release governance still comes from `CURRENT_VERSION`.
- Add inactive `pyproject.version.previous` record for `0.1.0` as a package metadata audit record.

**Step 3: Update legacy inventory docs**

In `docs/versions/LEGACY_VERSIONS.md`:
- Change the active `pyproject.version` row to `0.2.0a1`.
- Add inactive `pyproject.version.previous` with `0.1.0`.
- State that package metadata is aligned but is not the release-governance source.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add pyproject.toml uv.lock christine/versioning.py docs/versions/LEGACY_VERSIONS.md tests/test_versioning.py && git commit -m "chore: align package metadata version"`

Expected: commit succeeds.

---

### Task 4: Update Versioning Policy Docs

**Files:**
- Modify: `docs/VERSIONING.md`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing docs guard**

Add a docs guard that asserts `docs/VERSIONING.md` contains:
- `pyproject.toml`.
- `0.2.0a1`.
- `CURRENT_VERSION.package_metadata`.
- `not the release-governance source`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because the policy still says package metadata remains unchanged until a later migration.

**Step 3: Update docs**

Update `docs/VERSIONING.md` so it says:
- The active package metadata is aligned to `CURRENT_VERSION.package_metadata`.
- `pyproject.toml` uses `0.2.0a1` for the active `0.2.0-alpha.1` line.
- Package metadata supports Python tooling but is not the release-governance source.
- `CURRENT_VERSION` remains the canonical release-governance source.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add docs/VERSIONING.md tests/test_versioning.py && git commit -m "docs: document package metadata alignment"`

Expected: commit succeeds.

---

### Task 5: Final Verification And Merge

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
- `pyproject.toml`
- `uv.lock`
- `christine/versioning.py`
- `tests/test_versioning.py`
- `docs/VERSIONING.md`
- `docs/versions/LEGACY_VERSIONS.md`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/package-metadata-alignment`.
- Delete branch `package-metadata-alignment`.
- Push `main` under the current “push後繼續” workflow.
