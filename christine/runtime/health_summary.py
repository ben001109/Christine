from __future__ import annotations

from dataclasses import dataclass

from christine.platform.base import PlatformFeatureRequirement

from .optional_dependencies import OptionalDependencyStatus


PLAIN_COLORS = {"GR": "", "YE": "", "D": "", "R": ""}


@dataclass(frozen=True)
class RuntimeHealthItem:
    name: str
    category: str
    ok: bool
    fatal: bool
    message: str
    purpose: str


@dataclass(frozen=True)
class RuntimeHealthSummary:
    ready: bool
    degraded_count: int
    items: tuple[RuntimeHealthItem, ...]


def build_runtime_health_summary(
    optional_statuses: tuple[OptionalDependencyStatus, ...],
    *,
    platform_requirements: tuple[PlatformFeatureRequirement, ...] = (),
) -> RuntimeHealthSummary:
    optional_items = tuple(
        RuntimeHealthItem(
            name=status.name,
            category="optional_dependency",
            ok=status.available,
            fatal=False,
            message=status.message,
            purpose=status.purpose,
        )
        for status in optional_statuses
    )
    platform_items = tuple(
        RuntimeHealthItem(
            name=f"{requirement.platform_name}:{requirement.feature.value}",
            category="platform_feature",
            ok=requirement.supported,
            fatal=False,
            message=requirement.message,
            purpose=requirement.detail,
        )
        for requirement in platform_requirements
    )
    items = optional_items + platform_items
    degraded_count = sum(1 for item in items if not item.ok)
    ready = all(item.ok or not item.fatal for item in items)
    return RuntimeHealthSummary(ready=ready, degraded_count=degraded_count, items=items)


def _colors(enabled: bool) -> dict[str, str]:
    if not enabled:
        return PLAIN_COLORS
    return {"GR": "\033[32m", "YE": "\033[33m", "D": "\033[2m", "R": "\033[0m"}


def _degraded_detail(count: int) -> str:
    if count == 0:
        return "all optional capabilities available"
    noun = "capability" if count == 1 else "capabilities"
    return f"{count} degraded optional {noun}"


def render_runtime_health_summary(
    summary: RuntimeHealthSummary,
    *,
    colors: bool = True,
) -> list[str]:
    c = _colors(colors)
    state = "ready" if summary.ready else "blocked"
    lines = [f"  {c['YE']}[Runtime Health]{c['R']} {state} ({_degraded_detail(summary.degraded_count)})"]
    for item in summary.items:
        mark = f"{c['GR']}✓{c['R']}" if item.ok else f"{c['YE']}~{c['R']}"
        status = "ok" if item.ok else "degraded"
        lines.append(f"    {item.name:<22}: {mark} {status} - {item.message} ({item.purpose})")
    return lines
