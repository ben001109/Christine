# Versioning Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit version-number management rules plus alpha/beta/release stage mechanics for Christine.

**Architecture:** Add a pure `christine.versioning` module that validates and formats SemVer-compatible versions with `alpha`, `beta`, `rc`, and `release` stages. Document the policy in `docs/VERSIONING.md` and update `AGENTS.md` so future work follows the version rules.

**Tech Stack:** Python 3.10+ dataclasses/enums, pytest, existing `uv run` verification flow.

---

### Task 1: Baseline And Plan

**Files:**
- Create: `docs/plans/2026-05-07-christine-versioning-rules.md`

**Step 1: Verify baseline**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成`.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-versioning-rules.md && git commit -m "docs: plan versioning rules"`

Expected: plan commit succeeds.

---

### Task 2: Add Versioning API

**Files:**
- Create: `christine/versioning.py`
- Modify: `christine/__init__.py` if package exports already exist; otherwise leave package root unchanged.
- Create: `tests/test_versioning.py`

**Step 1: Write failing tests**

Create tests for:
- `ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1).public == "0.2.0-alpha.1"`
- beta format: `0.2.0-beta.1`
- release candidate format: `0.2.0-rc.1`
- release format: `0.2.0`
- parser accepts `0.2.0-alpha.1`, `0.2.0-beta.1`, `0.2.0-rc.1`, and `0.2.0`.
- parser rejects invalid stage names and release versions with prerelease number.
- `next_prerelease()` increments same-stage prerelease numbers.
- `promote_stage()` follows `alpha -> beta -> rc -> release`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because `christine.versioning` does not exist.

**Step 3: Implement minimal pure module**

Add:
- `VersionStage(str, Enum)` with `ALPHA`, `BETA`, `RC`, `RELEASE`.
- `ChristineVersion` frozen dataclass with `major`, `minor`, `patch`, `stage`, `prerelease`.
- `.public` property returning formatted version.
- `parse_version(text)`.
- `next_prerelease(version)`.
- `promote_stage(version)`.

Rules:
- release versions have no suffix and must not have `prerelease`.
- prerelease stages require positive integer prerelease numbers.
- no Git tag creation in this slice.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: all tests pass.

**Step 5: Commit**

Run: `git add christine/versioning.py tests/test_versioning.py && git commit -m "refactor: add versioning stage model"`

Expected: commit succeeds.

---

### Task 3: Document And Guard Versioning Rules

**Files:**
- Create: `docs/VERSIONING.md`
- Modify: `AGENTS.md`
- Modify: `tests/test_versioning.py`

**Step 1: Write failing docs guard**

Add tests that assert:
- `docs/VERSIONING.md` contains `alpha`, `beta`, `release`, and `rc`.
- `AGENTS.md` contains a `Version Management` section and references `docs/VERSIONING.md`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: FAIL because docs and agent rules are absent.

**Step 3: Add docs and agent rules**

`docs/VERSIONING.md` must define:
- Format: `MAJOR.MINOR.PATCH[-alpha.N|-beta.N|-rc.N]`.
- Stage order: `alpha -> beta -> rc -> release`.
- `release` is a stable public build and has no suffix.
- Alpha: internal experiments, unstable, okay to change behavior.
- Beta: feature-complete candidate, bug fixes and compatibility only unless approved.
- RC: release candidate, only blocker fixes.
- Release: tagged/stable; no direct breaking changes without new cycle.
- Commit/PR rule: any release-stage/version bump must mention the target version.
- Current package source: `pyproject.toml` remains package metadata; `christine.versioning` owns stage validation.

`AGENTS.md` must add `Version Management` section that points to `docs/VERSIONING.md` and says every release/bump must follow alpha/beta/rc/release gating.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_versioning.py -q`

Expected: all tests pass.

**Step 5: Commit**

Run: `git add docs/VERSIONING.md AGENTS.md tests/test_versioning.py && git commit -m "docs: add version management rules"`

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
- `AGENTS.md`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/versioning-rules`.
- Delete branch `versioning-rules`.
- Push `main` under the user's current “push後繼續” instruction.
