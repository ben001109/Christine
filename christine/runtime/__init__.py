"""Runtime helpers for Christine."""

from .boot_config import compute_cpu_budget
from .health_summary import (
    RuntimeHealthItem,
    RuntimeHealthSummary,
    RuntimeVersionInfo,
    build_runtime_health_summary,
    render_runtime_health_summary,
)
from .optional_dependencies import (
    OptionalDependencyStatus,
    check_ollama_service,
    check_optional_module,
    check_optional_service,
    optional_dependency_report,
    render_optional_dependency_diagnostics,
)
from .paths import RuntimePaths

__all__ = [
    "OptionalDependencyStatus",
    "RuntimeHealthItem",
    "RuntimeHealthSummary",
    "RuntimeVersionInfo",
    "RuntimePaths",
    "build_runtime_health_summary",
    "check_ollama_service",
    "check_optional_module",
    "check_optional_service",
    "compute_cpu_budget",
    "optional_dependency_report",
    "render_runtime_health_summary",
    "render_optional_dependency_diagnostics",
]
