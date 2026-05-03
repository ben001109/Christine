from pathlib import Path

import pytest

from christine.platform.windows import (
    auto_register_once,
    autostart_remove,
    autostart_status,
    build_autostart_batch,
    get_startup_programs,
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
    assert 'set "ANTHROPIC_API_KEY=secret"' in content
    assert 'cd /d "C:\\Christine"' in content
    assert 'start "" "C:\\Python\\pythonw.exe" "C:\\Christine\\christine_final.py"' in content
    assert "\r\n" in content


def test_build_autostart_batch_quotes_api_key_for_cmd():
    content = build_autostart_batch(
        work_dir=Path("C:/Christine"),
        script_path=Path("C:/Christine/christine_final.py"),
        python_exe=Path("C:/Python/pythonw.exe"),
        api_key="secret&still_key",
    )

    assert 'set "ANTHROPIC_API_KEY=secret&still_key"' in content
    assert "set ANTHROPIC_API_KEY=" not in content


def test_build_autostart_batch_rejects_newline_api_key():
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_autostart_batch(
            work_dir=Path("C:/Christine"),
            script_path=Path("C:/Christine/christine_final.py"),
            python_exe=Path("C:/Python/pythonw.exe"),
            api_key="secret\r\ncalc",
        )


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


def test_autostart_operations_reject_empty_appdata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = setup_autostart(
        appdata="",
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="",
    )

    assert result == "err:APPDATA is not set"
    assert autostart_status(appdata="") == "err:APPDATA is not set"
    assert autostart_remove(appdata="") == "err:APPDATA is not set"
    assert not (tmp_path / "Microsoft").exists()


def test_autostart_status_redacts_api_key(tmp_path):
    setup_autostart(
        appdata=tmp_path,
        script_path=tmp_path / "christine_final.py",
        python_exe=tmp_path / "python.exe",
        api_key="secret",
    )

    status = autostart_status(appdata=tmp_path)

    assert "已啟用" in status
    assert "secret" not in status
    assert 'set "ANTHROPIC_API_KEY=<redacted>"' in status


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


def test_auto_register_once_returns_error_when_flag_cannot_be_written(tmp_path):
    data_file = tmp_path / "data"
    data_file.write_text("not a directory", encoding="utf-8")

    try:
        result = auto_register_once(
            data_dir=data_file,
            appdata=tmp_path / "appdata",
            script_path=tmp_path / "christine_final.py",
            python_exe=tmp_path / "python.exe",
            api_key="",
            is_windows=True,
        )
    except Exception as exc:  # pragma: no cover - failure path assertion
        pytest.fail(f"auto_register_once raised {type(exc).__name__}: {exc}")

    assert result and result.startswith("err:")


def test_get_startup_programs_uses_runner_output():
    class Result:
        stdout = "Name Command\nChristine pythonw christine_final.py\n"

    def runner(*args, **kwargs):
        return Result()

    output = get_startup_programs(runner=runner)

    assert "Christine" in output


def test_monolith_autostart_functions_delegate_to_platform_module():
    text = Path("christine_final.py").read_text(encoding="utf-8")

    assert "from christine.platform import windows as _christine_windows" in text
    assert "_christine_windows.setup_autostart" in text
    assert "_christine_windows.autostart_status" in text
    assert "_christine_windows.autostart_remove" in text
    assert "_christine_windows.auto_register_once" in text
