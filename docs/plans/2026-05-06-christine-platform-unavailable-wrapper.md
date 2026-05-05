# Christine Platform Unavailable Wrapper Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a pure wrapper that turns platform feature support checks into structured, user-facing availability results.

**Architecture:** Keep the wrapper in `christine.platform.base` on top of the existing capability matrix and lookup helpers. The wrapper returns a frozen dataclass containing the normalized feature, support flag, detail, and Chinese message; it does not import platform-specific modules, execute behavior, or wire into `christine_final.py` in this batch.

**Tech Stack:** Python 3.10+, dataclasses, enum, stdlib only, uv, pytest.

---

## Requirements Captured

- Continue the multi-platform reliability boundary work.
- Provide a pure result object future platform wrappers can use before calling OS-specific code.
- Unsupported features must return structured data, not crash.
- Invalid feature names should still fail clearly through existing `ValueError` behavior.
- Do not touch `christine_final.py`, `boot_christine.py`, launchers, runtime state, or generated files.
- Do not add dependencies.

## Non-Goals

- No live runtime wiring.
- No platform feature implementation or parity work.
- No new fallback behavior in the monolith.
- No dependency installation.

---

### Task 1: Add Unavailable Wrapper Contract Tests

**Files:**
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Write failing tests**

Append these tests:

```python
from christine.platform.base import require_platform_feature


def test_require_platform_feature_returns_structured_unavailable_result():
    result = require_platform_feature("linux", PlatformFeature.SYSTEM_AUDIO)

    assert result.platform_name == "linux"
    assert result.feature == PlatformFeature.SYSTEM_AUDIO
    assert result.supported is False
    assert "system_audio" in result.message
    assert "尚未支援" in result.message
    assert "loopback audio" in result.detail


def test_require_platform_feature_returns_structured_supported_result():
    result = require_platform_feature("windows", "autostart")

    assert result.platform_name == "windows"
    assert result.feature == PlatformFeature.AUTOSTART
    assert result.supported is True
    assert result.message == "windows:autostart 已支援"


def test_require_platform_feature_keeps_unknown_platform_safe():
    result = require_platform_feature("plan9", "gui")

    assert result.platform_name == "plan9"
    assert result.feature == PlatformFeature.GUI
    assert result.supported is False
    assert result.detail == "unknown platform"
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: fail with import error for missing `require_platform_feature`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping.

---

### Task 2: Implement Pure Requirement Result

**Files:**
- Modify: `christine/platform/base.py`
- Test: `tests/test_platform_capabilities.py`

**Step 1: Add minimal implementation**

Add to `christine/platform/base.py`:

```python
@dataclass(frozen=True)
class PlatformFeatureRequirement:
    platform_name: str
    feature: PlatformFeature
    supported: bool
    detail: str
    message: str


def require_platform_feature(platform_name: str, feature: PlatformFeature | str) -> PlatformFeatureRequirement:
    normalized_feature = _coerce_feature(feature)
    support = feature_support(platform_name, normalized_feature)
    return PlatformFeatureRequirement(
        platform_name=platform_name,
        feature=normalized_feature,
        supported=support.supported,
        detail=support.detail,
        message=unsupported_message(platform_name, normalized_feature),
    )
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/platform/base.py tests/test_platform_capabilities.py
git commit -m "refactor: add platform feature availability wrapper"
```

---

### Task 3: Export Wrapper API

**Files:**
- Modify: `christine/platform/__init__.py`
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Add export test**

Extend `test_platform_exports_capability_matrix_api()`:

```python
from christine.platform import PlatformFeatureRequirement, require_platform_feature

assert PlatformFeatureRequirement.__name__ == "PlatformFeatureRequirement"
assert callable(require_platform_feature)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py::test_platform_exports_capability_matrix_api -q`

Expected: fail with import error for missing exports.

**Step 3: Export symbols**

Modify `christine/platform/__init__.py` to import and list:

```python
PlatformFeatureRequirement,
require_platform_feature,
```

**Step 4: Run platform tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/platform/__init__.py tests/test_platform_capabilities.py
git commit -m "refactor: export platform availability wrapper"
```

---

### Task 4: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused platform tests**

Run: `uv run pytest tests/test_platform_capabilities.py tests/test_startup_platform_imports.py -q`

Expected: all pass.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: all pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0 with no output.

**Step 4: Run fast boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `自檢完成`.

**Step 5: Run whitespace check**

Run: `git diff --check`

Expected: exit 0.

**Step 6: Request code review**

Ask for blocker-focused review on the unavailable wrapper branch.

**Step 7: Finish branch**

Use the finishing branch workflow after review and verification.

## Future Work After This Plan

- Use `require_platform_feature()` inside platform wrappers before live OS calls.
- Add monolith integration only after a separate plan defines the exact behavior and fallback text to preserve.
