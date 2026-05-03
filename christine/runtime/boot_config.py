from __future__ import annotations


def compute_cpu_budget(cpu_count: int, requested: int | None = None) -> int:
    if requested is None:
        return max(2, int(cpu_count) // 2)
    return max(1, min(int(requested), int(cpu_count)))
