import pytest

from christine.platform.base import detect_platform
from christine.platform.base import (
    PlatformAvailability,
    PlatformFeature,
    capability_matrix,
    feature_support,
    is_feature_supported,
    platform_availability,
    require_platform_feature,
    unsupported_message,
)


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
    from christine.platform import (
        FeatureSupport,
        PlatformAvailability,
        PlatformFeatureRequirement,
        PlatformFeature,
        capability_matrix,
        feature_support,
        is_feature_supported,
        platform_availability,
        require_platform_feature,
        unsupported_message,
    )

    assert FeatureSupport.__name__ == "FeatureSupport"
    assert PlatformAvailability.__name__ == "PlatformAvailability"
    assert PlatformFeatureRequirement.__name__ == "PlatformFeatureRequirement"
    assert PlatformFeature.SYSTEM_AUDIO.value == "system_audio"
    assert callable(capability_matrix)
    assert callable(feature_support)
    assert callable(is_feature_supported)
    assert callable(platform_availability)
    assert callable(require_platform_feature)
    assert callable(unsupported_message)


def test_platform_capability_matrix_avoids_python_311_only_strenum():
    from pathlib import Path

    source = Path("christine/platform/base.py").read_text(encoding="utf-8")
    plan = Path("docs/plans/2026-05-06-christine-platform-capability-matrix.md").read_text(encoding="utf-8")

    assert "StrEnum" not in source
    assert "StrEnum" not in plan


def test_feature_support_returns_known_platform_feature_detail():
    support = feature_support("linux", PlatformFeature.SYSTEM_AUDIO)

    assert support.supported is False
    assert "loopback audio" in support.detail


def test_feature_support_accepts_feature_strings_for_call_sites():
    assert is_feature_supported("windows", "autostart") is True
    assert is_feature_supported("linux", "system_audio") is False


def test_feature_support_falls_back_for_unknown_platform_names():
    support = feature_support("plan9", PlatformFeature.GUI)

    assert support.supported is False
    assert support.detail == "unknown platform"


def test_feature_support_rejects_unknown_feature_names():
    with pytest.raises(ValueError, match="unknown platform feature"):
        feature_support("linux", "screen_reader")


def test_require_platform_feature_returns_structured_unavailable_result():
    result = require_platform_feature("linux", PlatformFeature.SYSTEM_AUDIO)

    assert result.platform_name == "linux"
    assert result.feature == PlatformFeature.SYSTEM_AUDIO
    assert result.supported is False
    assert "system_audio" in result.message
    assert "尚未支援" in result.message
    assert "loopback audio" in result.detail


def test_require_platform_feature_returns_structured_supported_result():
    result = require_platform_feature("windows", "autostart")

    assert result.platform_name == "windows"
    assert result.feature == PlatformFeature.AUTOSTART
    assert result.supported is True
    assert result.message == "windows:autostart 已支援"


def test_require_platform_feature_keeps_unknown_platform_safe():
    result = require_platform_feature("plan9", "gui")

    assert result.platform_name == "plan9"
    assert result.feature == PlatformFeature.GUI
    assert result.supported is False
    assert result.detail == "unknown platform"


def test_platform_availability_wraps_supported_feature():
    result = platform_availability("windows", "autostart")

    assert result.available is True
    assert result.platform_name == "windows"
    assert result.feature == PlatformFeature.AUTOSTART
    assert result.message == "windows:autostart 已支援"
    assert result.as_text() == "windows:autostart 已支援"


def test_platform_availability_wraps_unsupported_feature():
    result = platform_availability("linux", "autostart")

    assert result.available is False
    assert result.platform_name == "linux"
    assert result.feature == PlatformFeature.AUTOSTART
    assert "尚未支援" in result.message
    assert result.as_text().startswith("unavailable:")
