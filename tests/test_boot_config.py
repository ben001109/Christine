from christine.runtime.boot_config import compute_cpu_budget


def test_compute_cpu_budget_defaults_to_half_with_minimum_two():
    assert compute_cpu_budget(cpu_count=24, requested=None) == 12
    assert compute_cpu_budget(cpu_count=2, requested=None) == 2
    assert compute_cpu_budget(cpu_count=24, requested=4) == 4
