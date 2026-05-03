# Christine AutoBoot Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract Windows startup/autostart behavior from `christine_final.py` into `christine.platform.windows` while preserving current user-facing commands and Chinese status text.

**Architecture:** Keep `christine_final.py` as the compatibility surface, but move path construction, batch-file rendering, registration, status, removal, and one-time registration helpers into tested platform code. The extracted module must support dependency injection so tests never write to the real Windows Startup folder.

**Tech Stack:** Python stdlib (`pathlib`, `os`, `sys`, `subprocess`, `datetime`), pytest, uv.

---

## Current Legacy Behavior

Relevant `christine_final.py` seams:

- `christine_final.py:2254-2256` defines `get_startup_programs()` using PowerShell `Win32_StartupCommand`.
- `christine_final.py:2310-2344` defines `setup_autostart()` and writes `Christine.bat` to `%APPDATA%/Microsoft/Windows/Start Menu/Programs/Startup`.
- `christine_final.py:2346-2374` defines `autostart_status()` and `autostart_remove()`.
- `christine_final.py:2376-2396` defines `_v1483_auto_register_once()` using `data/_autostart_registered.flag`.
- `christine_final.py:5262` and `christine_final.py:5272` expose tool schemas for `get_startup_programs` and `setup_autostart`.
- `christine_final.py:5454+` maps tool calls to these functions.
- `christine_final.py:119681-119699` handles voice commands: `自動開機`, `autostart on/off`, and flag updates.

Do not remove these user-facing commands in this wave. Replace their internals with compatibility wrappers only.

---

### Task 1: Add Pure AutoBoot Path And Batch Rendering

**Files:**

- Modify: `christine/platform/windows.py`
- Create: `tests/test_windows_autostart.py`

**Step 1: Write the failing tests**

```python
from pathlib import Path

from christine.platform.windows import build_autostart_batch, startup_folder


def test_startup_folder_uses_appdata_root(tmp_path):
    assert startup_folder(tmp_path) == (
        tmp_path / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    )


def test_build_autostart_batch_preserves_utf8_and_api_key():
    content = build_autostart_batch(
        work_dir=Path("C:/Christine"),
        script_path=Path("C:/Christine/christine_final.py"),
        python_exe=Path("C:/Python/pythonw.exe"),
        api_key="secret",
    )

    assert "chcp 65001 >nul" in content
    assert "set PYTHONUTF8=1" in content
    assert "set PYTHONIOENCODING=utf-8" in content
    assert "set ANTHROPIC_API_KEY=secret" in content
    assert 'cd /d "C:\\Christine"' in content
    assert 'start "" "C:\\Python\\pythonw.exe" "C:\\Christine\\christine_final.py"' in content
    assert "\r\n" in content
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: fail with missing `startup_folder` and `build_autostart_batch`.

**Step 3: Implement minimal pure helpers**

```python
from __future__ import annotations

from pathlib import Path


def _win_path(path: str | Path) -> str:
    return str(path).replace("/", "\\")


def startup_folder(appdata: str | Path) -> Path:
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def build_autostart_batch(
    work_dir: str | Path,
    script_path: str | Path,
    python_exe: str | Path,
    api_key: str = "",
) -> str:
    api_line = f"set ANTHROPIC_API_KEY={api_key}\r\n" if api_key else ""
    return (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "set PYTHONUTF8=1\r\n"
        "set PYTHONIOENCODING=utf-8\r\n"
        + api_line
        + f'cd /d "{_win_path(work_dir)}"\r\n'
        + f'start "" "{_win_path(python_exe)}" "{_win_path(script_path)}"\r\n'
    )
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/platform/windows.py tests/test_windows_autostart.py
git commit -m "refactor: add Windows autostart helpers"
```

---

### Task 2: Add Tested Register, Status, Remove Operations

**Files:**

- Modify: `christine/platform/windows.py`
- Modify: `tests/test_windows_autostart.py`

**Step 1: Extend tests without touching the real Startup folder**

```python
from christine.platform.windows import autostart_remove, autostart_status, setup_autostart


def test_setup_status_and_remove_autostart_use_temp_appdata(tmp_path):
    result = setup_autostart(
        appdata=tmp_path,
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="",
    )

    bat_path = startup_folder(tmp_path) / "Christine.bat"
    assert result.startswith("ok:")
    assert bat_path.is_file()
    assert "已註冊開機啟動" in result

    status = autostart_status(appdata=tmp_path)
    assert "已啟用" in status
    assert str(bat_path) in status

    removed = autostart_remove(appdata=tmp_path)
    assert "已移除開機啟動" in removed
    assert not bat_path.exists()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: fail with missing operation functions.

**Step 3: Implement file operations with injected paths**

Implement functions in `christine/platform/windows.py`:

```python
def _bat_path(appdata: str | Path) -> Path:
    return startup_folder(appdata) / "Christine.bat"


def setup_autostart(appdata, script_path, python_exe, api_key="") -> str:
    try:
        bat_path = _bat_path(appdata)
        bat_path.parent.mkdir(parents=True, exist_ok=True)
        py_exe = Path(python_exe)
        pyw = Path(str(py_exe).replace("python.exe", "pythonw.exe"))
        use_exe = pyw if pyw.is_file() else py_exe
        content = build_autostart_batch(Path(script_path).parent, script_path, use_exe, api_key)
        bat_path.write_text(content, encoding="utf-8")
        return f"ok: 已註冊開機啟動 → {bat_path}"
    except Exception as exc:
        return "err:" + str(exc)


def autostart_status(appdata) -> str:
    try:
        bat_path = _bat_path(appdata)
        if bat_path.is_file():
            try:
                content = bat_path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            return f"✓ 已啟用 → {bat_path}\n--- 內容 ---\n{content}"
        return f"✗ 未啟用（可用『自動開機 on』啟用）\n  預期位置：{bat_path}"
    except Exception as exc:
        return "err:" + str(exc)


def autostart_remove(appdata) -> str:
    try:
        bat_path = _bat_path(appdata)
        if bat_path.is_file():
            bat_path.unlink()
            return f"✓ 已移除開機啟動 ← {bat_path}"
        return "~ 原本就沒註冊，無需移除"
    except Exception as exc:
        return "err:" + str(exc)
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/platform/windows.py tests/test_windows_autostart.py
git commit -m "refactor: isolate Windows autostart operations"
```

---

### Task 3: Add One-Time Registration And Startup Program Listing Boundary

**Files:**

- Modify: `christine/platform/windows.py`
- Modify: `tests/test_windows_autostart.py`

**Step 1: Add tests for flag behavior and startup listing**

```python
from christine.platform.windows import auto_register_once, get_startup_programs


def test_auto_register_once_writes_flag_only_after_success(tmp_path):
    result = auto_register_once(
        data_dir=tmp_path / "data",
        appdata=tmp_path / "appdata",
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="",
        is_windows=True,
    )

    assert result and result.startswith("ok:")
    assert (tmp_path / "data" / "_autostart_registered.flag").is_file()

    second = auto_register_once(
        data_dir=tmp_path / "data",
        appdata=tmp_path / "appdata",
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="",
        is_windows=True,
    )
    assert second is None


def test_get_startup_programs_uses_runner_output():
    class Result:
        stdout = "Name Command\nChristine pythonw christine_final.py\n"

    def runner(*args, **kwargs):
        return Result()

    output = get_startup_programs(runner=runner)

    assert "Christine" in output
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: fail with missing functions.

**Step 3: Implement minimal helpers**

Add:

```python
import datetime
import subprocess


def auto_register_once(data_dir, appdata, script_path, python_exe, api_key="", is_windows=True):
    if not is_windows:
        return None
    flag = Path(data_dir) / "_autostart_registered.flag"
    if flag.is_file():
        return None
    result = setup_autostart(appdata, script_path, python_exe, api_key)
    if result.startswith("ok"):
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text(datetime.datetime.now().isoformat() + "\n" + result, encoding="utf-8")
    return result


def get_startup_programs(runner=subprocess.run) -> str:
    try:
        result = runner(
            'powershell -c "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command | Format-Table -AutoSize"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()[:400] if result.stdout.strip() else "none"
    except Exception:
        return "err"
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/platform/windows.py tests/test_windows_autostart.py
git commit -m "refactor: add Windows startup boundary helpers"
```

---

### Task 4: Replace Legacy Autostart Internals With Compatibility Wrappers

**Files:**

- Modify: `christine_final.py:2254-2396`
- Modify: `tests/test_windows_autostart.py`

**Step 1: Add static wrapper test**

```python
from pathlib import Path


def test_monolith_autostart_functions_delegate_to_platform_module():
    text = Path("christine_final.py").read_text(encoding="utf-8")

    assert "from christine.platform import windows as _christine_windows" in text
    assert "_christine_windows.setup_autostart" in text
    assert "_christine_windows.autostart_status" in text
    assert "_christine_windows.autostart_remove" in text
    assert "_christine_windows.auto_register_once" in text
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_windows_autostart.py -q`

Expected: fail because `christine_final.py` still has inline autostart implementation.

**Step 3: Add import near top-level imports**

Add near existing imports in `christine_final.py`:

```python
from christine.platform import windows as _christine_windows
```

**Step 4: Replace function bodies only**

Keep function names and user-facing commands unchanged. Replace:

```python
def get_startup_programs():
    return _christine_windows.get_startup_programs()


def setup_autostart():
    return _christine_windows.setup_autostart(
        appdata=os.environ.get("APPDATA", ""),
        script_path=os.path.abspath(__file__),
        python_exe=sys.executable,
        api_key=API_KEY,
    )


def autostart_status():
    return _christine_windows.autostart_status(appdata=os.environ.get("APPDATA", ""))


def autostart_remove():
    return _christine_windows.autostart_remove(appdata=os.environ.get("APPDATA", ""))


def _v1483_auto_register_once():
    result = _christine_windows.auto_register_once(
        data_dir=DD,
        appdata=os.environ.get("APPDATA", ""),
        script_path=os.path.abspath(__file__),
        python_exe=sys.executable,
        api_key=API_KEY,
        is_windows=sys.platform.startswith("win"),
    )
    if result is None:
        return
    if result.startswith("ok"):
        print(f"  {_GR}✓{_R} {_CY}V1483 AutoBoot{_R} — "
              f"已自動註冊開機啟動（大腦會隨系統啟動而醒來）")
    else:
        print(f"  {_YE}~{_R} AutoBoot 註冊失敗：{result}")
```

**Step 5: Run tests and compile**

Run:

```bash
uv run pytest tests/test_windows_autostart.py tests/test_boot_contract.py -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
```

Expected: pass.

**Step 6: Commit**

Run:

```bash
git add christine/platform/windows.py tests/test_windows_autostart.py christine_final.py
git commit -m "refactor: delegate AutoBoot to platform boundary"
```

---

## Final Verification

Run the focused suite before reporting this wave complete:

```bash
uv run pytest tests/test_windows_autostart.py tests/test_platform_capabilities.py tests/test_boot_contract.py tests/test_formula_runtime_isolation.py -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

Expected: all pass.
