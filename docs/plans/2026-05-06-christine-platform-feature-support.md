# Christine Platform Feature Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a small, safe lookup API on top of Christine's platform capability matrix.

**Architecture:** Keep the implementation inside `christine.platform.base` as pure functions over the existing immutable capability matrix. Callers can ask whether a feature is supported without importing OS-only modules or wiring behavior into `christine_final.py`. Invalid feature input should fail with a clear `ValueError`, not a raw `KeyError`.

**Tech Stack:** Python 3.10+, dataclasses, enum, stdlib only, uv, pytest.

---

## Requirements Captured

- Continue the multi-platform reliability boundary work.
- Do not touch `christine_final.py`, `boot_christine.py`, launchers, runtime state, or generated files.
- Do not add dependencies.
- Keep API pure and import-safe on Windows/Linux/macOS.
- Preserve the existing capability matrix and Chinese unavailable messages.

## Non-Goals

- No live runtime wiring.
- No platform feature implementation or parity work.
- No installing `pynput`, `torch`, TTS, Ollama, or model packages.

---

### Task 1: Add Feature Support Lookup Tests

**Files:**
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Write failing tests**

Append these tests:

```python
import pytest

from christine.platform.base import feature_support, is_feature_supported


def test_feature_support_returns_known_platform_feature_detail():
    support = feature_support("linux", PlatformFeature.SYSTEM_AUDIO)

    assert support.supported is False
    assert "loopback audio" in support.detail


def test_feature_support_accepts_feature_strings_for_call_sites():
    assert is_feature_supported("windows", "autostart") is True
    assert is_feature_supported("linux", "system_audio") is False


def test_feature_support_falls_back_for_unknown_platform_names():
    support = feature_support("plan9", PlatformFeature.GUI)

    assert support.supported is False
    assert support.detail == "unknown platform"


def test_feature_support_rejects_unknown_feature_names():
    with pytest.raises(ValueError, match="unknown platform feature"):
        feature_support("linux", "screen_reader")
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: fail with import error for missing `feature_support` or `is_feature_supported`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping.

---

### Task 2: Implement Feature Support Lookup

**Files:**
- Modify: `christine/platform/base.py`
- Test: `tests/test_platform_capabilities.py`

**Step 1: Add minimal implementation**

Add to `christine/platform/base.py`:

```python
def _coerce_feature(feature: PlatformFeature | str) -> PlatformFeature:
    try:
        return feature if isinstance(feature, PlatformFeature) else PlatformFeature(feature)
    except ValueError as exc:
        raise ValueError(f"unknown platform feature: {feature}") from exc


def feature_support(platform_name: str, feature: PlatformFeature | str) -> FeatureSupport:
    normalized_feature = _coerce_feature(feature)
    platform_features = _CAPABILITY_MATRIX.get(platform_name, _CAPABILITY_MATRIX["unknown"])
    return platform_features[normalized_feature]


def is_feature_supported(platform_name: str, feature: PlatformFeature | str) -> bool:
    return feature_support(platform_name, feature).supported
```

Update `unsupported_message()` to call `feature_support()` instead of indexing the matrix directly.

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/platform/base.py tests/test_platform_capabilities.py
git commit -m "refactor: add platform feature support lookup"
```

---

### Task 3: Export Feature Support Lookup API

**Files:**
- Modify: `christine/platform/__init__.py`
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Add export test**

Extend `test_platform_exports_capability_matrix_api()`:

```python
from christine.platform import feature_support, is_feature_supported

assert callable(feature_support)
assert callable(is_feature_supported)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py::test_platform_exports_capability_matrix_api -q`

Expected: fail with import error for missing exports.

**Step 3: Export symbols**

Modify `christine/platform/__init__.py` to import and list:

```python
feature_support,
is_feature_supported,
```

**Step 4: Run platform tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/platform/__init__.py tests/test_platform_capabilities.py
git commit -m "refactor: export platform feature support lookup"
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

Ask for blocker-focused review on the feature support lookup branch.

**Step 7: Finish branch**

Use the finishing branch workflow after review and verification.

## Future Work After This Plan

- Use `is_feature_supported()` inside platform wrappers before adding any live platform behavior.
- Add monolith integration only after a separate plan defines the exact behavior to preserve.
