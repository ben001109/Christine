from pathlib import Path

from christine.platform.windows import (
    autostart_remove,
    autostart_status,
    build_autostart_batch,
    setup_autostart,
    startup_folder,
)


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
