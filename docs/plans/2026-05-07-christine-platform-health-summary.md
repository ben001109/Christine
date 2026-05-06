# Platform Health Summary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let runtime health summaries include structured platform feature support/degradation without touching live monolith behavior.

**Architecture:** Extend the existing pure `christine.runtime.health_summary` builder with an optional `platform_requirements` input. Platform requirements are produced by `christine.platform.require_platform_feature()` and converted into non-fatal `RuntimeHealthItem` entries with category `platform_feature`.

**Tech Stack:** Python 3.10+ dataclasses, pytest, existing `christine.platform` and `christine.runtime` modules.

---

### Task 1: Baseline And Plan

**Files:**
- Create: `docs/plans/2026-05-07-christine-platform-health-summary.md`

**Step 1: Verify baseline**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: runtime health output and `自檢完成`.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-platform-health-summary.md && git commit -m "docs: plan platform health summary"`

Expected: plan commit succeeds.

---

### Task 2: Add Platform Requirement Health Items

**Files:**
- Modify: `christine/runtime/health_summary.py`
- Modify: `tests/test_runtime_health_summary.py`

**Step 1: Write failing tests**

Add tests that call:

```python
summary = build_runtime_health_summary(
    (),
    platform_requirements=(require_platform_feature("linux", PlatformFeature.SYSTEM_AUDIO),),
)
```

Expected assertions:
- `summary.ready is True`
- `summary.degraded_count == 1`
- item name is `linux:system_audio`
- item category is `platform_feature`
- item `ok is False`
- item `fatal is False`
- item message includes `尚未支援`
- rendered text includes `linux:system_audio` and platform detail.

Add one supported platform feature test:
- `require_platform_feature("windows", "autostart")` becomes an ok item and does not increase `degraded_count`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: FAIL because `build_runtime_health_summary()` does not accept `platform_requirements`.

**Step 3: Implement minimal builder extension**

In `christine/runtime/health_summary.py`:
- Import `PlatformFeatureRequirement` from `christine.platform.base` only for typing/field conversion.
- Add keyword-only `platform_requirements: tuple[PlatformFeatureRequirement, ...] = ()`.
- Convert each requirement into `RuntimeHealthItem`:
  - `name=f"{requirement.platform_name}:{requirement.feature.value}"`
  - `category="platform_feature"`
  - `ok=requirement.supported`
  - `fatal=False`
  - `message=requirement.message`
  - `purpose=requirement.detail`

Rules:
- Platform feature degradation is non-fatal in this slice.
- Do not call `detect_platform()` inside the health summary builder.
- Do not wire this into `boot_christine.py` yet.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_runtime_health_summary.py tests/test_platform_capabilities.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/runtime/health_summary.py tests/test_runtime_health_summary.py && git commit -m "refactor: include platform features in health summary"`

Expected: commit succeeds.

---

### Task 3: Final Verification And Merge

**Files:**
- No planned production edits.

**Step 1: Run final checks**

Run: `uv run pytest tests/test_runtime_health_summary.py tests/test_platform_capabilities.py tests/test_optional_dependencies.py tests/test_boot_banner.py -q`

Expected: all tests pass.

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: current boot output remains unchanged and reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 2: Review**

Request blocker-focused review for:
- `christine/runtime/health_summary.py`
- `tests/test_runtime_health_summary.py`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/platform-health-summary`.
- Delete branch `platform-health-summary`.
- Push `main` if authorized by the user's current “push then continue” instruction.
