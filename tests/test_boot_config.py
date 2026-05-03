from christine.runtime.boot_config import build_basic_hardware_info, compute_cpu_budget


def test_compute_cpu_budget_defaults_to_half_with_minimum_two():
    assert compute_cpu_budget(cpu_count=24, requested=None) == 12
    assert compute_cpu_budget(cpu_count=2, requested=None) == 2
    assert compute_cpu_budget(cpu_count=24, requested=4) == 4


def test_build_basic_hardware_info_matches_launcher_shape():
    info = build_basic_hardware_info(
        system="Linux",
        release="6.1",
        python_version="3.12.1",
        cpu_count=24,
        cpu_name="AMD Ryzen",
        ram_gb=31.5,
    )

    assert info == {
        "os": "Linux 6.1",
        "python": "3.12.1",
        "cpu_count": 24,
        "cpu_name": "AMD Ryzen",
        "ram_gb": 31.5,
        "gpu": None,
        "torch": None,
    }
