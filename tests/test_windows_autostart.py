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
