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
