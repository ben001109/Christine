from christine.platform.base import detect_platform


def test_detect_platform_returns_capability_object():
    platform = detect_platform()

    assert platform.name in {"windows", "linux", "macos", "unknown"}
    assert isinstance(platform.supports_autostart, bool)
    assert isinstance(platform.supports_global_hotkeys, bool)
    assert isinstance(platform.supports_system_audio, bool)
    assert isinstance(platform.supports_gui, bool)
