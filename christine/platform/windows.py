from __future__ import annotations

from pathlib import Path

from .base import PlatformCapabilities


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


CAPABILITIES = PlatformCapabilities("windows", True, True, True, True)
