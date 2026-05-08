from christine.platform.linux import autostart_status as linux_autostart_status
from christine.platform.linux import setup_autostart as linux_setup_autostart
from christine.platform.macos import autostart_status as macos_autostart_status
from christine.platform.macos import setup_autostart as macos_setup_autostart
from christine.platform.windows import autostart_status, setup_autostart, startup_folder


def test_linux_autostart_wrappers_return_structured_unavailable():
    assert linux_setup_autostart().startswith("unavailable:linux:autostart")
    assert linux_autostart_status().startswith("unavailable:linux:autostart")


def test_macos_autostart_wrappers_return_structured_unavailable():
    assert macos_setup_autostart().startswith("unavailable:macos:autostart")
    assert macos_autostart_status().startswith("unavailable:macos:autostart")


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
