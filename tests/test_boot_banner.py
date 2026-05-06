from pathlib import Path

from christine.runtime.boot_banner import render_boot_banner


def test_render_boot_banner_includes_cpu_only_hardware_lines():
    hw = {
        "os": "Linux 6.1",
        "python": "3.12.1",
        "cpu_count": 24,
        "cpu_name": "AMD Ryzen 7950X",
        "ram_gb": 31.5,
        "gpu": None,
        "torch": None,
    }

    lines = render_boot_banner(hw, cpu_cores=12, gpu_ready=False, elapsed=0.25, colors=False)
    text = "\n".join(lines)

    assert "CHRISTINE V1485 — Boot Sequence" in text
    assert "OS        : Linux 6.1     Python 3.12.1" in text
    assert "CPU       : AMD Ryzen 7950X" in text
    assert "Cores     : 12 / 24   (給 Christine: 50%)" in text
    assert "RAM       : 31.5 GB" in text
    assert "GPU       : — (CPU-only)" in text
    assert "Boot budget applied in 250ms" in text


def test_render_boot_banner_includes_gpu_budget_when_ready():
    hw = {
        "os": "Windows 11",
        "python": "3.12.1",
        "cpu_count": 16,
        "cpu_name": "Intel",
        "ram_gb": 64,
        "gpu": {"name": "RTX", "vram_gb": 16, "capability": "8.9"},
        "torch": "2.5.0",
    }

    lines = render_boot_banner(
        hw,
        cpu_cores=8,
        gpu_ready=True,
        elapsed=0.1,
        gpu_frac="0.75",
        gpu_warm_ms="123",
        colors=False,
    )
    text = "\n".join(lines)

    assert "GPU       : ✓ RTX  (16 GB, sm_8.9)" in text
    assert "GPU 預算  : 75% VRAM  warm=123ms" in text
    assert "PyTorch   : 2.5.0" in text


def test_launcher_delegates_banner_rendering_to_runtime_module():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "from christine.runtime.boot_banner import render_boot_banner" in text
    assert "render_boot_banner(" in text


def test_launcher_prints_runtime_health_summary():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "optional_dependency_report" in text
    assert "check_ollama_service" in text
    assert "build_runtime_health_summary" in text
    assert "render_runtime_health_summary" in text
    assert "print_runtime_health_summary" in text
