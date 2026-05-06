# Legacy Version Registry Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bring legacy Christine version labels under the new version-management rules without rewriting runtime constants yet.

**Architecture:** Extend `christine.versioning` with a pure legacy registry of known historical/runtime version labels. The registry classifies each label as package metadata, monolith label, subsystem label, cache schema, generated/runtime label, or commented history, then documents why these are not release-governance versions.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, existing `docs/VERSIONING.md`, existing `christine.versioning` module.

---

### Task 1: Baseline And Plan

**Files:**
- Create: `docs/plans/2026-05-07-christine-legacy-version-registry.md`

**Step 1: Verify baseline**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成`.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-legacy-version-registry.md && git commit -m "docs: plan legacy version registry"`

Expected: plan commit succeeds.

---

### Task 2: Add Legacy Registry API

**Files:**
- Modify: `christine/versioning.py`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing tests**

Add tests for:
- `LegacyVersionRecord` and `LegacyVersionKind` exports from `christine.versioning`.
- `legacy_version_records()` includes `CHRISTINE_VERSION = "600.0-final-agi-opus"` as a `monolith_public_label`.
- Registry includes package metadata `pyproject.toml = "0.1.0"` separately from legacy monolith labels.
- Registry includes subsystem labels such as `V42_VERSION`, `V42_HERMES_VERSION`, `V58_VERSION`, `V60_VERSION`, and `_V70_VERSION`.
- Registry includes cache/runtime labels `_OMEGA_CACHE_VERSION`, `_V42_NEURAL_VERSION`, `V2000_SKILL_COMPILER_VERSION`, and `V2499_SKILL_COMPILER_VERSION`.
- `legacy_version_by_name("CHRISTINE_VERSION")` returns the active record.
- Active registry records with `source="christine_final.py"` still appear in the current monolith source.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because legacy registry API does not exist.

**Step 3: Implement minimal pure registry**

In `christine/versioning.py`, add:
- `LegacyVersionKind(str, Enum)`
- `LegacyVersionRecord` frozen dataclass
- `LEGACY_VERSION_RECORDS` tuple
- `legacy_version_records(active_only: bool = False)`
- `legacy_version_by_name(name: str)`

Rules:
- Do not read files or inspect git at import time.
- Do not rewrite `christine_final.py` constants.
- Do not treat legacy records as `ChristineVersion` unless they are already SemVer-compatible package metadata.
- Mark monolith/subsystem/cache values as release-governance legacy artifacts.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/versioning.py tests/test_versioning.py && git commit -m "refactor: register legacy version labels"`

Expected: commit succeeds.

---

### Task 3: Document Legacy Conversion Rules

**Files:**
- Modify: `docs/VERSIONING.md`
- Modify: `AGENTS.md`
- Create: `docs/versions/LEGACY_VERSIONS.md`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing docs guard**

Add tests that assert:
- `docs/VERSIONING.md` has a `Legacy Version Labels` section.
- `AGENTS.md` says old monolith version constants must be registered before changing.
- `docs/versions/LEGACY_VERSIONS.md` lists key legacy values including `600.0-final-agi-opus`, `42.8-titan`, `70.0-sovereign-agi`, and `2499.0-beyond-singularity`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because docs are absent.

**Step 3: Add docs**

Update `docs/VERSIONING.md` with:
- Legacy labels are historical/runtime identifiers, not public release versions.
- New public versions must use `ChristineVersion`.
- Do not rewrite active legacy labels unless a migration plan covers display/cache/runtime behavior.
- Every newly discovered legacy label must be added to `LEGACY_VERSION_RECORDS` and `docs/versions/LEGACY_VERSIONS.md`.

Create `docs/versions/LEGACY_VERSIONS.md` with a table of known labels and their categories.

Update `AGENTS.md` Version Management section with the same guard.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add docs/VERSIONING.md docs/versions/LEGACY_VERSIONS.md AGENTS.md tests/test_versioning.py && git commit -m "docs: document legacy version labels"`

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
- `docs/versions/LEGACY_VERSIONS.md`
- `AGENTS.md`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/legacy-version-registry`.
- Delete branch `legacy-version-registry`.
- Push `main` under the current “push後繼續” workflow.
