# Christine Platform Capability Matrix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a small cross-platform capability matrix so Christine can reason about supported platform features before wiring platform-specific runtime behavior.

**Architecture:** Extend the existing `christine.platform` boundary with pure, import-safe capability data. The matrix describes whether each OS supports key capability areas and provides user-facing unavailable messages; it does not change `christine_final.py`, launchers, runtime state, or actual platform behavior in this batch.

**Tech Stack:** Python 3.10+, dataclasses, stdlib only, uv, pytest.

---

## Requirements Captured

- Prioritize multi-platform reliability boundaries, not full feature parity.
- Preserve Windows-first behavior and existing launchers.
- Keep Linux/macOS startup safe by describing unavailable capabilities instead of importing platform-only modules.
- Do not touch `christine_final.py` in this batch.
- Do not add optional dependencies such as `pynput`, `torch`, `sentence_transformers`, or TTS packages.
- Do not modify runtime artifacts under `data/`, `level5_logs/`, `growth.log`, `heartbeat.txt`, or generated brain files.

## Capability Scope For This Batch

- `autostart`
- `global_hotkeys`
- `system_audio`
- `gui`
- `tts`
- `local_llm`

The matrix is descriptive only. It does not install or enable features.

---

### Task 1: Add Capability Matrix Contract Tests

**Files:**
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Write failing tests**

Append these tests:

```python
from christine.platform.base import PlatformFeature, capability_matrix, unsupported_message


def test_platform_capability_matrix_lists_core_features_for_each_platform():
    matrix = capability_matrix()

    assert set(matrix) == {"windows", "linux", "macos", "unknown"}
    for features in matrix.values():
        assert set(features) == {
            PlatformFeature.AUTOSTART,
            PlatformFeature.GLOBAL_HOTKEYS,
            PlatformFeature.SYSTEM_AUDIO,
            PlatformFeature.GUI,
            PlatformFeature.TTS,
            PlatformFeature.LOCAL_LLM,
        }


def test_platform_capability_matrix_preserves_windows_first_support():
    matrix = capability_matrix()

    assert matrix["windows"][PlatformFeature.AUTOSTART].supported is True
    assert matrix["windows"][PlatformFeature.GLOBAL_HOTKEYS].supported is True
    assert matrix["windows"][PlatformFeature.SYSTEM_AUDIO].supported is True
    assert matrix["windows"][PlatformFeature.GUI].supported is True


def test_platform_capability_matrix_marks_linux_system_integrations_unavailable():
    matrix = capability_matrix()

    assert matrix["linux"][PlatformFeature.AUTOSTART].supported is False
    assert matrix["linux"][PlatformFeature.GLOBAL_HOTKEYS].supported is False
    assert matrix["linux"][PlatformFeature.SYSTEM_AUDIO].supported is False
    assert matrix["linux"][PlatformFeature.GUI].supported is True


def test_unsupported_message_is_user_facing_and_specific():
    message = unsupported_message("linux", PlatformFeature.SYSTEM_AUDIO)

    assert "linux" in message
    assert "system_audio" in message
    assert "尚未支援" in message
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: fail with import error for missing `PlatformFeature`, `capability_matrix`, or `unsupported_message`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping.

---

### Task 2: Implement Pure Capability Matrix

**Files:**
- Modify: `christine/platform/base.py`
- Test: `tests/test_platform_capabilities.py`

**Step 1: Add minimal implementation**

Add to `christine/platform/base.py`:

```python
from enum import StrEnum
from types import MappingProxyType


class PlatformFeature(StrEnum):
    AUTOSTART = "autostart"
    GLOBAL_HOTKEYS = "global_hotkeys"
    SYSTEM_AUDIO = "system_audio"
    GUI = "gui"
    TTS = "tts"
    LOCAL_LLM = "local_llm"


@dataclass(frozen=True)
class FeatureSupport:
    supported: bool
    detail: str


def _features(**values: FeatureSupport):
    return MappingProxyType(values)


_CAPABILITY_MATRIX = MappingProxyType(
    {
        "windows": _features(
            autostart=FeatureSupport(True, "Windows Startup folder integration"),
            global_hotkeys=FeatureSupport(True, "Windows keyboard hooks"),
            system_audio=FeatureSupport(True, "pyaudiowpatch loopback audio"),
            gui=FeatureSupport(True, "Tk desktop GUI"),
            tts=FeatureSupport(False, "optional local TTS dependency not guaranteed"),
            local_llm=FeatureSupport(False, "requires external local model service"),
        ),
        "linux": _features(
            autostart=FeatureSupport(False, "Linux autostart integration is not wired yet"),
            global_hotkeys=FeatureSupport(False, "pynput/X11/Wayland support is not wired yet"),
            system_audio=FeatureSupport(False, "Windows loopback audio dependency is unavailable"),
            gui=FeatureSupport(True, "Tk desktop GUI when display is available"),
            tts=FeatureSupport(False, "local TTS dependency is optional and not guaranteed"),
            local_llm=FeatureSupport(False, "requires Ollama or another local model service"),
        ),
        "macos": _features(
            autostart=FeatureSupport(False, "macOS launch agent integration is not wired yet"),
            global_hotkeys=FeatureSupport(False, "macOS accessibility hotkeys are not wired yet"),
            system_audio=FeatureSupport(False, "macOS system audio capture is not wired yet"),
            gui=FeatureSupport(True, "Tk desktop GUI when display is available"),
            tts=FeatureSupport(False, "local TTS dependency is optional and not guaranteed"),
            local_llm=FeatureSupport(False, "requires Ollama or another local model service"),
        ),
        "unknown": _features(
            autostart=FeatureSupport(False, "unknown platform"),
            global_hotkeys=FeatureSupport(False, "unknown platform"),
            system_audio=FeatureSupport(False, "unknown platform"),
            gui=FeatureSupport(False, "unknown platform"),
            tts=FeatureSupport(False, "unknown platform"),
            local_llm=FeatureSupport(False, "unknown platform"),
        ),
    }
)


def capability_matrix():
    return _CAPABILITY_MATRIX


def unsupported_message(platform_name: str, feature: PlatformFeature) -> str:
    platform_features = _CAPABILITY_MATRIX.get(platform_name, _CAPABILITY_MATRIX["unknown"])
    support = platform_features[feature]
    if support.supported:
        return f"{platform_name}:{feature.value} 已支援"
    return f"{platform_name}:{feature.value} 尚未支援 — {support.detail}"
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/platform/base.py tests/test_platform_capabilities.py
git commit -m "refactor: add platform capability matrix"
```

---

### Task 3: Export Capability Matrix API

**Files:**
- Modify: `christine/platform/__init__.py`
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Add export test**

Append:

```python
def test_platform_exports_capability_matrix_api():
    from christine.platform import FeatureSupport, PlatformFeature, capability_matrix, unsupported_message

    assert FeatureSupport.__name__ == "FeatureSupport"
    assert PlatformFeature.SYSTEM_AUDIO.value == "system_audio"
    assert callable(capability_matrix)
    assert callable(unsupported_message)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py::test_platform_exports_capability_matrix_api -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/platform/__init__.py`:

```python
from .base import (
    FeatureSupport,
    PlatformCapabilities,
    PlatformFeature,
    capability_matrix,
    detect_platform,
    unsupported_message,
)

__all__ = [
    "FeatureSupport",
    "PlatformCapabilities",
    "PlatformFeature",
    "capability_matrix",
    "detect_platform",
    "unsupported_message",
]
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/platform/__init__.py tests/test_platform_capabilities.py
git commit -m "refactor: export platform capability matrix"
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

Ask for blocker-focused review on the capability matrix branch.

**Step 7: Finish branch**

Use the finishing branch workflow after review and verification.

## Future Work After This Plan

- Add runtime wrappers that ask the matrix before calling platform-specific features.
- Add disabled-by-default Linux/macOS autostart experiments only after tests define behavior.
- Keep full functional parity as a later decision, not part of this batch.
