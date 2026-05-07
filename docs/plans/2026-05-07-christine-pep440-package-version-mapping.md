# PEP 440 Package Version Mapping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a pure, tested mapping from Christine public versions such as `0.2.0-alpha.1` to Python package metadata versions such as `0.2.0a1` without changing current package metadata.

**Architecture:** Extend `christine.versioning.ChristineVersion` with a read-only `package_metadata` property that returns the PEP 440-compatible package version string for the same validated version object. Documentation will make clear that this mapping prepares a later `pyproject.toml` alignment slice, but this slice does not edit package metadata or legacy monolith labels.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, existing `christine.versioning` module, existing `docs/VERSIONING.md` policy.

---

### Task 1: Baseline And Plan

**Target Version:** `0.2.0-alpha.1`

**Stage:** `alpha`

**Files:**
- Create: `docs/plans/2026-05-07-christine-pep440-package-version-mapping.md`

**Step 1: Verify baseline**

Run: `uv sync && uv run pytest tests/test_versioning.py -q`

Expected: all focused versioning tests pass.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-pep440-package-version-mapping.md && git commit -m "docs: plan pep 440 package version mapping"`

Expected: plan commit succeeds.

---

### Task 2: Add PEP 440 Mapping API

**Files:**
- Modify: `christine/versioning.py`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing tests**

Add tests for:
- `ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1).package_metadata == "0.2.0a1"`.
- `ChristineVersion(0, 2, 0, VersionStage.BETA, 2).package_metadata == "0.2.0b2"`.
- `ChristineVersion(0, 2, 0, VersionStage.RC, 3).package_metadata == "0.2.0rc3"`.
- `ChristineVersion(0, 2, 0, VersionStage.RELEASE).package_metadata == "0.2.0"`.
- `current_version().package_metadata == "0.2.0a1"`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because `ChristineVersion.package_metadata` does not exist yet.

**Step 3: Implement minimal pure mapping**

In `christine/versioning.py`, add a read-only property to `ChristineVersion`:

```python
@property
def package_metadata(self) -> str:
    base = f"{self.major}.{self.minor}.{self.patch}"
    if self.stage == VersionStage.RELEASE:
        return base
    pep440_stage = {
        VersionStage.ALPHA: "a",
        VersionStage.BETA: "b",
        VersionStage.RC: "rc",
    }[self.stage]
    return f"{base}{pep440_stage}{self.prerelease}"
```

Rules:
- Do not edit `pyproject.toml` in this slice.
- Do not change `CURRENT_VERSION.public`.
- Do not change `christine_final.py` legacy labels.
- Do not add boot output wiring.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/versioning.py tests/test_versioning.py && git commit -m "refactor: map versions to pep 440 metadata"`

Expected: commit succeeds.

---

### Task 3: Document Package Metadata Mapping

**Files:**
- Modify: `docs/VERSIONING.md`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing docs guard**

Add a docs guard that asserts `docs/VERSIONING.md` contains:
- `PEP 440 Package Metadata`.
- `package_metadata`.
- `0.2.0-alpha.1`.
- `0.2.0a1`.
- `pyproject.toml` remains unchanged until a separate migration.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because the policy does not describe PEP 440 package metadata mapping yet.

**Step 3: Update docs**

Add `## PEP 440 Package Metadata` to `docs/VERSIONING.md`:
- Christine public versions keep `-alpha.N`, `-beta.N`, and `-rc.N` formatting.
- Python package metadata must use PEP 440-compatible forms from `package_metadata`.
- Current `0.2.0-alpha.1` maps to `0.2.0a1`.
- This slice does not update `pyproject.toml`; package metadata alignment remains a separate migration slice.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add docs/VERSIONING.md tests/test_versioning.py && git commit -m "docs: document pep 440 package metadata mapping"`

Expected: commit succeeds.

---

### Task 4: Final Verification And Merge

**Files:**
- No planned production edits beyond `christine/versioning.py`.

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
- Remove `.worktrees/pep440-package-version`.
- Delete branch `pep440-package-version`.
- Push `main` under the current “push後繼續” workflow.
