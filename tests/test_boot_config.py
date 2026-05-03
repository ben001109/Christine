from pathlib import Path
import builtins

import boot_christine

from christine.runtime.boot_config import build_basic_hardware_info, build_cpu_thread_env, compute_cpu_budget


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


def test_build_cpu_thread_env_sets_thread_limits():
    env = build_cpu_thread_env(6)

    assert env == {
        "OMP_NUM_THREADS": "6",
        "MKL_NUM_THREADS": "6",
        "OPENBLAS_NUM_THREADS": "6",
        "NUMEXPR_NUM_THREADS": "6",
        "CHRISTINE_CPU_CORES": "6",
    }


def test_launcher_uses_basic_hardware_builder_for_notorch_path():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "build_basic_hardware_info(" in text


def test_launcher_disables_torch_side_effects_for_notorch_path():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "allow_torch=not args.notorch" in text


def test_apply_compute_budget_allow_torch_false_skips_all_torch_imports(monkeypatch):
    imported_torch = False
    real_import = builtins.__import__

    def track_torch_import(name, *args, **kwargs):
        nonlocal imported_torch
        if name == "torch" or name.startswith("torch."):
            imported_torch = True
            raise RuntimeError("torch import attempted")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", track_torch_import)

    env, cpu_cores, gpu_ready = boot_christine.apply_compute_budget(
        {"cpu_count": 8, "gpu": {"name": "Fake GPU"}},
        cpu_cores=4,
        use_gpu=True,
        allow_torch=False,
    )

    assert imported_torch is False
    assert env["CHRISTINE_GPU"] == "0"
    assert cpu_cores == 4
    assert gpu_ready is False
