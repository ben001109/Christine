from christine.platform.base import detect_platform
from christine.platform.base import PlatformFeature, capability_matrix, unsupported_message


def test_detect_platform_returns_capability_object():
    platform = detect_platform()

    assert platform.name in {"windows", "linux", "macos", "unknown"}
    assert isinstance(platform.supports_autostart, bool)
    assert isinstance(platform.supports_global_hotkeys, bool)
    assert isinstance(platform.supports_system_audio, bool)
    assert isinstance(platform.supports_gui, bool)


def test_platform_capability_matrix_lists_core_features_for_each_platform():
    matrix = capability_matrix()

    assert set(matrix) == {"windows", "linux", "macos", "unknown"}
    for features in matrix.values():
        assert set(features) == {
            PlatformFeature.AUTOSTART,
            PlatformFeature.GLOBAL_HOTKEYS,
            PlatformFeature.SYSTEM_AUDIO,
            PlatformFeature.GUI,
            PlatformFeature.TTS,
            PlatformFeature.LOCAL_LLM,
        }


def test_platform_capability_matrix_preserves_windows_first_support():
    matrix = capability_matrix()

    assert matrix["windows"][PlatformFeature.AUTOSTART].supported is True
    assert matrix["windows"][PlatformFeature.GLOBAL_HOTKEYS].supported is True
    assert matrix["windows"][PlatformFeature.SYSTEM_AUDIO].supported is True
    assert matrix["windows"][PlatformFeature.GUI].supported is True


def test_platform_capability_matrix_marks_linux_system_integrations_unavailable():
    matrix = capability_matrix()

    assert matrix["linux"][PlatformFeature.AUTOSTART].supported is False
    assert matrix["linux"][PlatformFeature.GLOBAL_HOTKEYS].supported is False
    assert matrix["linux"][PlatformFeature.SYSTEM_AUDIO].supported is False
    assert matrix["linux"][PlatformFeature.GUI].supported is True


def test_unsupported_message_is_user_facing_and_specific():
    message = unsupported_message("linux", PlatformFeature.SYSTEM_AUDIO)

    assert "linux" in message
    assert "system_audio" in message
    assert "尚未支援" in message


def test_platform_exports_capability_matrix_api():
    from christine.platform import FeatureSupport, PlatformFeature, capability_matrix, unsupported_message

    assert FeatureSupport.__name__ == "FeatureSupport"
    assert PlatformFeature.SYSTEM_AUDIO.value == "system_audio"
    assert callable(capability_matrix)
    assert callable(unsupported_message)


def test_platform_capability_matrix_avoids_python_311_only_strenum():
    from pathlib import Path

    source = Path("christine/platform/base.py").read_text(encoding="utf-8")
    plan = Path("docs/plans/2026-05-06-christine-platform-capability-matrix.md").read_text(encoding="utf-8")

    assert "StrEnum" not in source
    assert "StrEnum" not in plan
