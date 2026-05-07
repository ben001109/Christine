from christine.platform import PlatformFeature, require_platform_feature
import christine.runtime.health_summary as health_summary
from christine.runtime.health_summary import build_runtime_health_summary, render_runtime_health_summary
from christine.runtime.optional_dependencies import OptionalDependencyStatus


def test_build_runtime_health_summary_marks_optional_dependency_degradation_non_fatal():
    summary = build_runtime_health_summary(
        (
            OptionalDependencyStatus("torch", False, "GPU acceleration", "missing"),
            OptionalDependencyStatus("ollama", True, "local LLM", "reachable"),
        )
    )

    assert summary.ready is True
    assert summary.degraded_count == 1
    assert len(summary.items) == 2
    assert summary.items[0].name == "torch"
    assert summary.items[0].category == "optional_dependency"
    assert summary.items[0].ok is False
    assert summary.items[0].fatal is False
    assert summary.items[0].message == "missing"


def test_build_runtime_health_summary_is_ready_when_all_optional_dependencies_available():
    summary = build_runtime_health_summary(
        (
            OptionalDependencyStatus("torch", True, "GPU acceleration", "available"),
            OptionalDependencyStatus("ollama", True, "local LLM", "reachable"),
        )
    )

    assert summary.ready is True
    assert summary.degraded_count == 0


def test_render_runtime_health_summary_is_boot_readable_without_colors():
    summary = build_runtime_health_summary(
        (
            OptionalDependencyStatus("torch", False, "GPU acceleration", "missing"),
            OptionalDependencyStatus("ollama", True, "local LLM", "reachable"),
        )
    )

    lines = render_runtime_health_summary(summary, colors=False)
    text = "\n".join(lines)

    assert "[Runtime Health]" in text
    assert "ready" in text
    assert "1 degraded optional capability" in text
    assert "torch" in text
    assert "degraded" in text
    assert "missing" in text
    assert "GPU acceleration" in text
    assert "ollama" in text
    assert "ok" in text
    assert "reachable" in text


def test_build_runtime_health_summary_includes_platform_feature_degradation():
    summary = build_runtime_health_summary(
        (),
        platform_requirements=(require_platform_feature("linux", PlatformFeature.SYSTEM_AUDIO),),
    )

    assert summary.ready is True
    assert summary.degraded_count == 1
    assert len(summary.items) == 1
    assert summary.items[0].name == "linux:system_audio"
    assert summary.items[0].category == "platform_feature"
    assert summary.items[0].ok is False
    assert summary.items[0].fatal is False
    assert "尚未支援" in summary.items[0].message
    assert "loopback audio" in summary.items[0].purpose


def test_build_runtime_health_summary_keeps_supported_platform_features_ok():
    summary = build_runtime_health_summary(
        (),
        platform_requirements=(require_platform_feature("windows", "autostart"),),
    )

    assert summary.ready is True
    assert summary.degraded_count == 0
    assert summary.items[0].name == "windows:autostart"
    assert summary.items[0].category == "platform_feature"
    assert summary.items[0].ok is True


def test_render_runtime_health_summary_includes_platform_feature_items():
    summary = build_runtime_health_summary(
        (),
        platform_requirements=(require_platform_feature("linux", "system_audio"),),
    )

    text = "\n".join(render_runtime_health_summary(summary, colors=False))

    assert "linux:system_audio" in text
    assert "degraded" in text
    assert "尚未支援" in text
    assert "loopback audio" in text


def test_runtime_health_summary_renders_version_info_inside_health_section():
    assert hasattr(health_summary, "RuntimeVersionInfo")
    runtime_version_info = health_summary.RuntimeVersionInfo
    summary = build_runtime_health_summary(
        (
            OptionalDependencyStatus("torch", False, "GPU acceleration", "missing"),
        ),
        version_info=runtime_version_info("0.2.0-alpha.1", "0.2.0a1"),
    )

    lines = render_runtime_health_summary(summary, colors=False)
    text = "\n".join(lines)

    assert summary.ready is True
    assert summary.degraded_count == 1
    assert "[Runtime Health]" in text
    assert "version" in text
    assert "0.2.0-alpha.1" in text
    assert "0.2.0a1" in text


def test_runtime_exports_health_summary_api():
    from christine.runtime import (
        RuntimeHealthItem,
        RuntimeHealthSummary,
        RuntimeVersionInfo,
        build_runtime_health_summary,
        render_runtime_health_summary,
    )

    assert RuntimeHealthItem.__name__ == "RuntimeHealthItem"
    assert RuntimeHealthSummary.__name__ == "RuntimeHealthSummary"
    assert RuntimeVersionInfo.__name__ == "RuntimeVersionInfo"
    assert callable(build_runtime_health_summary)
    assert callable(render_runtime_health_summary)
