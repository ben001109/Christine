# Runtime Health Summary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a pure runtime health summary boundary that turns optional dependency diagnostics into a reusable ready/degraded summary and uses it in launcher diagnostics.

**Architecture:** Add `christine.runtime.health_summary` as a small pure formatter module. Optional dependencies remain responsible for detection; the new module only summarizes already-collected statuses, so it performs no imports, no network checks, and no startup side effects.

**Tech Stack:** Python 3.10+ dataclasses, pytest, `uv run` commands, existing `boot_christine.py` launcher.

---

### Task 1: Plan And Baseline

**Files:**
- Create: `docs/plans/2026-05-07-christine-runtime-health-summary.md`

**Step 1: Verify isolated baseline**

Run: `uv run pytest -q`

Expected: `196 passed`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: optional dependency diagnostics are printed and the launcher reaches `自檢完成`.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-runtime-health-summary.md && git commit -m "docs: plan runtime health summary"`

Expected: plan commit succeeds.

---

### Task 2: Add Pure Health Summary API

**Files:**
- Create: `christine/runtime/health_summary.py`
- Test: `tests/test_runtime_health_summary.py`

**Step 1: Write failing tests**

Create `tests/test_runtime_health_summary.py` with tests for:
- `build_runtime_health_summary(...)` converts optional statuses into non-fatal health items.
- Missing optional dependencies mark the summary as `ready=True` and `degraded_count > 0`.
- `render_runtime_health_summary(..., colors=False)` returns clear boot-readable lines with `[Runtime Health]`, `ready`, dependency names, messages, and purposes.

**Step 2: Run RED**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: FAIL during collection because `christine.runtime.health_summary` does not exist.

**Step 3: Implement minimal module**

Add frozen dataclasses:
- `RuntimeHealthItem`
- `RuntimeHealthSummary`

Add functions:
- `build_runtime_health_summary(optional_statuses)`
- `render_runtime_health_summary(summary, colors=True)`

Rules:
- Optional dependency degradation is non-fatal.
- `summary.ready` is false only when a future fatal item is unavailable.
- No dependency checks, network calls, or heavy imports in this module.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/runtime/health_summary.py tests/test_runtime_health_summary.py && git commit -m "refactor: add runtime health summary boundary"`

Expected: commit succeeds.

---

### Task 3: Export Health Summary API

**Files:**
- Modify: `christine/runtime/__init__.py`
- Test: `tests/test_runtime_health_summary.py`

**Step 1: Write failing export test**

Add a test importing from `christine.runtime`:
- `RuntimeHealthItem`
- `RuntimeHealthSummary`
- `build_runtime_health_summary`
- `render_runtime_health_summary`

**Step 2: Run RED**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: FAIL because the names are not exported.

**Step 3: Add exports**

Modify `christine/runtime/__init__.py` to import and include the new names in `__all__`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_runtime_health_summary.py tests/test_optional_dependencies.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/runtime/__init__.py tests/test_runtime_health_summary.py && git commit -m "refactor: export runtime health summary"`

Expected: commit succeeds.

---

### Task 4: Wire Launcher Diagnostics To Health Summary

**Files:**
- Modify: `boot_christine.py`
- Modify: `tests/test_boot_banner.py`

**Step 1: Write failing launcher test**

Update the static launcher test to assert:
- `build_runtime_health_summary` is imported or referenced.
- `render_runtime_health_summary` is imported or referenced.
- `print_runtime_health_summary` is the launcher helper name.

**Step 2: Run RED**

Run: `uv run pytest tests/test_boot_banner.py::test_launcher_prints_optional_dependency_diagnostics -q`

Expected: FAIL because the launcher still uses only optional dependency diagnostics.

**Step 3: Update launcher wiring**

Change `boot_christine.py` so it:
- Still calls `optional_dependency_report(service_checkers={"ollama": _check_ollama_for_report})`.
- Builds a `RuntimeHealthSummary` from those statuses.
- Prints `render_runtime_health_summary(summary, colors=True)`.
- Preserves `--check`, `--no-banner`, handoff, and exit semantics.

**Step 4: Run GREEN and smoke check**

Run: `uv run pytest tests/test_boot_banner.py tests/test_runtime_health_summary.py tests/test_optional_dependencies.py -q`

Expected: tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `[Runtime Health]` and reaches `自檢完成`.

**Step 5: Commit**

Run: `git add boot_christine.py tests/test_boot_banner.py && git commit -m "refactor: show runtime health summary during boot"`

Expected: commit succeeds.

---

### Task 5: Final Verification And Merge

**Files:**
- No planned production edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_runtime_health_summary.py tests/test_optional_dependencies.py tests/test_boot_banner.py tests/test_boot_config.py -q`

Expected: all pass.

**Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: `[Runtime Health]` output and `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 3: Review**

Request blocker-focused review for the branch diff against `main`, covering:
- `christine/runtime/health_summary.py`
- `christine/runtime/__init__.py`
- `boot_christine.py`
- `tests/test_runtime_health_summary.py`
- `tests/test_boot_banner.py`

**Step 4: Merge and clean up**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Re-run merged-main verification.
- Remove `.worktrees/runtime-health-summary`.
- Delete branch `runtime-health-summary`.
- Ask before pushing if not already authorized.
