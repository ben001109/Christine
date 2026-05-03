from __future__ import annotations


def build_basic_hardware_info(
    *,
    system: str,
    release: str,
    python_version: str,
    cpu_count: int,
    cpu_name: str,
    ram_gb: float | None = None,
) -> dict:
    return {
        "os": f"{system} {release}",
        "python": python_version,
        "cpu_count": int(cpu_count),
        "cpu_name": cpu_name or "unknown",
        "ram_gb": ram_gb,
        "gpu": None,
        "torch": None,
    }


def compute_cpu_budget(cpu_count: int, requested: int | None = None) -> int:
    if requested is None:
        return max(2, int(cpu_count) // 2)
    return max(1, min(int(requested), int(cpu_count)))


def build_cpu_thread_env(cpu_cores: int) -> dict[str, str]:
    cores = str(int(cpu_cores))
    return {
        "OMP_NUM_THREADS": cores,
        "MKL_NUM_THREADS": cores,
        "OPENBLAS_NUM_THREADS": cores,
        "NUMEXPR_NUM_THREADS": cores,
        "CHRISTINE_CPU_CORES": cores,
    }
