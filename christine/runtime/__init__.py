"""Runtime helpers for Christine."""

from .boot_config import compute_cpu_budget
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
    "RuntimePaths",
    "check_ollama_service",
    "check_optional_module",
    "check_optional_service",
    "compute_cpu_budget",
    "optional_dependency_report",
    "render_optional_dependency_diagnostics",
]
