# Boot Version Health Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show Christine's canonical current version inside the boot/check Runtime Health output.

**Architecture:** Extend the pure runtime health summary model with optional version metadata that renders inside the existing `[Runtime Health]` block without affecting readiness or degraded capability counts. Wire `boot_christine.py` to pass `christine.versioning.current_version()` into the health summary, preserving `CURRENT_VERSION` as release governance and keeping package metadata as display-only Python tooling metadata.

**Tech Stack:** Python 3.10+ dataclasses, pytest, existing `christine.runtime.health_summary`, existing `christine.versioning`, existing launcher smoke checks.

---

### Task 1: Baseline And Plan

**Target Version:** `0.2.0-alpha.1`

**Package Metadata Version:** `0.2.0a1`

**Stage:** `alpha`

**Files:**
- Create: `docs/plans/2026-05-07-christine-boot-version-health.md`

**Step 1: Verify baseline**

Run: `uv sync && uv run pytest tests/test_versioning.py -q`

Expected: all focused versioning tests pass.

**Step 2: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-boot-version-health.md && git commit -m "docs: plan boot version health output"`

Expected: plan commit succeeds.

---

### Task 2: Add Runtime Health Version Model And Renderer

**Files:**
- Modify: `christine/runtime/health_summary.py`
- Modify: `christine/runtime/__init__.py`
- Modify: `tests/test_runtime_health_summary.py`

**Step 1: Write failing tests**

Add tests that assert:
- `RuntimeVersionInfo("0.2.0-alpha.1", "0.2.0a1")` can be attached through `build_runtime_health_summary(..., version_info=...)`.
- `render_runtime_health_summary(..., colors=False)` includes `[Runtime Health]`, `version`, `0.2.0-alpha.1`, and `0.2.0a1`.
- Version info does not change `ready` or `degraded_count`.
- `christine.runtime` exports `RuntimeVersionInfo`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: FAIL because `RuntimeVersionInfo` and `version_info` support do not exist yet.

**Step 3: Implement minimal runtime health support**

In `christine/runtime/health_summary.py`, add:

```python
@dataclass(frozen=True)
class RuntimeVersionInfo:
    public: str
    package_metadata: str
```

Then add `version_info: RuntimeVersionInfo | None` to `RuntimeHealthSummary`, accept `version_info: RuntimeVersionInfo | None = None` in `build_runtime_health_summary()`, and insert a rendered line after the header:

```python
if summary.version_info is not None:
    lines.append(
        f"    version               : {summary.version_info.public} "
        f"(package {summary.version_info.package_metadata})"
    )
```

Export `RuntimeVersionInfo` from `christine/runtime/__init__.py`.

Rules:
- Do not count version metadata as a health item.
- Do not affect readiness or degraded count.
- Do not import `christine_final.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_runtime_health_summary.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add christine/runtime/health_summary.py christine/runtime/__init__.py tests/test_runtime_health_summary.py && git commit -m "refactor: add version info to runtime health"`

Expected: commit succeeds.

---

### Task 3: Wire Boot Runtime Health To Current Version

**Files:**
- Modify: `boot_christine.py`
- Modify: `tests/test_boot_banner.py`

**Step 1: Write failing tests**

Add a static launcher guard that asserts `boot_christine.py`:
- Imports `current_version` from `christine.versioning`.
- Imports or references `RuntimeVersionInfo`.
- Passes `version_info=` into `build_runtime_health_summary()`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_boot_banner.py -q`

Expected: FAIL because the launcher is not wired to current version yet.

**Step 3: Implement minimal boot wiring**

In `boot_christine.py`:

```python
from christine.versioning import current_version
from christine.runtime.health_summary import RuntimeVersionInfo, build_runtime_health_summary, render_runtime_health_summary
```

Then in `print_runtime_health_summary()`:

```python
version = current_version()
summary = build_runtime_health_summary(
    statuses,
    version_info=RuntimeVersionInfo(version.public, version.package_metadata),
)
```

Rules:
- Do not add a separate version section outside Runtime Health.
- Do not change boot step numbering.
- Do not change `CURRENT_VERSION`, `pyproject.toml`, `uv.lock`, or legacy labels.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_boot_banner.py tests/test_runtime_health_summary.py -q`

Expected: tests pass.

**Step 5: Commit**

Run: `git add boot_christine.py tests/test_boot_banner.py && git commit -m "refactor: show current version in runtime health"`

Expected: commit succeeds.

---

### Task 4: Final Verification And Merge

**Files:**
- No additional planned edits.

**Step 1: Run final checks**

Run: `uv run pytest tests/test_runtime_health_summary.py tests/test_boot_banner.py tests/test_versioning.py -q`

Expected: all pass.

Run: `uv run pytest -q`

Expected: all pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成` and Runtime Health output includes `0.2.0-alpha.1` and `0.2.0a1`.

Run: `git diff --check`

Expected: no output.

**Step 2: Review**

Request blocker-focused review for:
- `boot_christine.py`
- `christine/runtime/health_summary.py`
- `christine/runtime/__init__.py`
- `tests/test_runtime_health_summary.py`
- `tests/test_boot_banner.py`
- plan doc

**Step 3: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove `.worktrees/boot-version-health`.
- Delete branch `boot-version-health`.
- Push `main` under the current “push後繼續” workflow.
