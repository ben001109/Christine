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


CAPABILITIES = PlatformCapabilities("windows", True, True, True, True)
