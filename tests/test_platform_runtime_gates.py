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
