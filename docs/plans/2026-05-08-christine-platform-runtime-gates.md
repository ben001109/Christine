# Platform Runtime Gates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect Christine's platform capability matrix to runtime wrapper helpers so unsupported platform features return structured unavailable results before any live OS call.

**Architecture:** Keep `christine_final.py`, boot behavior, and Windows launcher behavior unchanged. Add a small pure `PlatformAvailability` result in `christine.platform.base`, then add Linux/macOS autostart wrappers that use `require_platform_feature()` and return unavailable instead of attempting OS integration. Preserve existing Windows helpers and use the new gate only where it does not change current Windows behavior.

**Tech Stack:** Python 3.10+, dataclasses, pathlib, existing `christine.platform` modules, uv, pytest.

---

## Requirements Captured

- Preserve `boot_christine.py`, `christine_final.py`, and Windows launcher behavior.
- Do not implement Linux/macOS autostart yet.
- Do not add dependencies or call live OS APIs in tests.
- Keep unsupported feature responses structured and user-facing.
- Use TDD and focused platform tests before implementation.

## Non-Goals

- No Linux desktop autostart implementation.
- No macOS LaunchAgent implementation.
- No GUI modernization.
- No monolith routing or tool-call rewiring in this slice.
- No changes to persisted state formats.

---

### Task 1: Add Platform Availability Result

**Files:**
- Modify: `christine/platform/base.py`
- Modify: `christine/platform/__init__.py`
- Modify: `tests/test_platform_capabilities.py`

**Step 1: Write failing tests**

Append to `tests/test_platform_capabilities.py`:

```python
from christine.platform.base import platform_availability


def test_platform_availability_wraps_supported_feature():
    result = platform_availability("windows", "autostart")

    assert result.available is True
    assert result.platform_name == "windows"
    assert result.feature == PlatformFeature.AUTOSTART
    assert result.message == "windows:autostart 已支援"
    assert result.as_text() == "windows:autostart 已支援"


def test_platform_availability_wraps_unsupported_feature():
    result = platform_availability("linux", "autostart")

    assert result.available is False
    assert result.platform_name == "linux"
    assert result.feature == PlatformFeature.AUTOSTART
    assert "尚未支援" in result.message
    assert result.as_text().startswith("unavailable:")
```

Add export coverage to `test_platform_exports_capability_matrix_api()`:

```python
PlatformAvailability,
platform_availability,
```

and assert `PlatformAvailability.__name__ == "PlatformAvailability"` and `callable(platform_availability)`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: FAIL because `platform_availability` and `PlatformAvailability` do not exist.

**Step 3: Implement minimal result**

Add to `christine/platform/base.py`:

```python
@dataclass(frozen=True)
class PlatformAvailability:
    platform_name: str
    feature: PlatformFeature
    available: bool
    message: str
    detail: str

    def as_text(self) -> str:
        if self.available:
            return self.message
        return f"unavailable:{self.message}"


def platform_availability(platform_name: str, feature: PlatformFeature | str) -> PlatformAvailability:
    requirement = require_platform_feature(platform_name, feature)
    return PlatformAvailability(
        platform_name=requirement.platform_name,
        feature=requirement.feature,
        available=requirement.supported,
        message=requirement.message,
        detail=requirement.detail,
    )
```

Export both symbols from `christine/platform/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/platform/base.py christine/platform/__init__.py tests/test_platform_capabilities.py && git commit -m "refactor: add platform availability result"`

---

### Task 2: Add Linux And macOS Autostart Runtime Gates

**Files:**
- Modify: `christine/platform/linux.py`
- Modify: `christine/platform/macos.py`
- Test: `tests/test_platform_runtime_gates.py`

**Step 1: Write failing tests**

Create `tests/test_platform_runtime_gates.py`:

```python
from christine.platform.linux import autostart_status as linux_autostart_status
from christine.platform.linux import setup_autostart as linux_setup_autostart
from christine.platform.macos import autostart_status as macos_autostart_status
from christine.platform.macos import setup_autostart as macos_setup_autostart


def test_linux_autostart_wrappers_return_structured_unavailable():
    assert linux_setup_autostart().startswith("unavailable:linux:autostart")
    assert linux_autostart_status().startswith("unavailable:linux:autostart")


def test_macos_autostart_wrappers_return_structured_unavailable():
    assert macos_setup_autostart().startswith("unavailable:macos:autostart")
    assert macos_autostart_status().startswith("unavailable:macos:autostart")
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_platform_runtime_gates.py -q`

Expected: FAIL because autostart wrapper functions do not exist in Linux/macOS modules.

**Step 3: Implement minimal wrappers**

In `christine/platform/linux.py`:

```python
from .base import PlatformCapabilities, platform_availability


def _unavailable(feature: str) -> str:
    return platform_availability("linux", feature).as_text()


def setup_autostart(*args, **kwargs) -> str:
    return _unavailable("autostart")


def autostart_status(*args, **kwargs) -> str:
    return _unavailable("autostart")
```

In `christine/platform/macos.py`, use the same shape with platform name `"macos"`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_platform_runtime_gates.py tests/test_platform_capabilities.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/platform/linux.py christine/platform/macos.py tests/test_platform_runtime_gates.py && git commit -m "refactor: gate unavailable platform autostart wrappers"`

---

### Task 3: Guard Windows Behavior And Verify

**Files:**
- Modify: `tests/test_platform_runtime_gates.py`

**Step 1: Add Windows preservation tests**

Append to `tests/test_platform_runtime_gates.py`:

```python
from christine.platform.windows import autostart_status, setup_autostart, startup_folder


def test_windows_autostart_helpers_still_use_startup_folder(tmp_path):
    result = setup_autostart(
        appdata=tmp_path,
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="",
    )

    bat_path = startup_folder(tmp_path) / "Christine.bat"

    assert result.startswith("ok:")
    assert bat_path.is_file()
    assert "已啟用" in autostart_status(appdata=tmp_path)
```

**Step 2: Run test**

Run: `uv run pytest tests/test_platform_runtime_gates.py tests/test_windows_autostart.py -q`

Expected: PASS. If `tests/test_windows_autostart.py` does not exist, run only `tests/test_platform_runtime_gates.py`.

**Step 3: Run final focused checks**

Run: `uv run pytest tests/test_platform*.py tests/test_startup_platform_imports.py tests/test_runtime_health_summary.py tests/test_boot_contract.py -q`

Expected: PASS.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 4: Request review and finish branch**

Request blocker-focused review for platform runtime gates. If no blocking findings remain, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
