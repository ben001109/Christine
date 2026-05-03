# Christine Boot Runtime Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract boot hardware summary, CPU/GPU budget environment calculation, and boot banner rendering from `boot_christine.py` into tested `christine.runtime` modules while preserving launcher output and handoff behavior.

**Architecture:** Keep `boot_christine.py` as the executable entry point and hardware side-effect owner. Move pure data shaping and display rendering into `christine.runtime.boot_config` and a new `christine.runtime.boot_banner` module. The launcher should become a thin adapter that gathers live OS/torch data, calls pure helpers, applies env vars, prints rendered lines, then hands off to `christine_final.py` unchanged.

**Tech Stack:** Python stdlib (`dataclasses`, `platform`, `multiprocessing`, `os`, `time`), pytest, uv.

---

## Current Legacy Behavior

Production seams in `boot_christine.py`:

- `boot_christine.py:40-93` defines `detect_hardware()` and mixes live OS probing, RAM probing, torch import timeout, CUDA probing, and progress printing.
- `boot_christine.py:99-147` defines `apply_compute_budget()`, computes CPU env vars, mutates torch thread settings, optionally warms CUDA, and returns `(env, cpu_cores, gpu_ready)`.
- `boot_christine.py:153-182` defines `print_boot_banner()` and directly prints colorized banner lines, reading GPU budget details from `os.environ`.
- `boot_christine.py:205-218` duplicates a no-torch hardware dictionary path inside `main()`.

Preserve current launcher behavior:

- `uv run python boot_christine.py --check --notorch --fast --no-banner` exits 0 and prints `自檢完成`.
- `--notorch` must not import torch.
- `boot_christine.py` remains executable and remains the handoff entry point to `christine_final.py`.
- Chinese boot output wording must remain unchanged unless a test explicitly updates it.

---

### Task 1: Add Pure Hardware Summary Builder

**Files:**

- Modify: `christine/runtime/boot_config.py`
- Modify: `tests/test_boot_config.py`

**Step 1: Write the failing test**

Add:

```python
from christine.runtime.boot_config import build_basic_hardware_info


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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_boot_config.py -q`

Expected: fail with missing `build_basic_hardware_info`.

**Step 3: Implement minimal helper**

Add to `christine/runtime/boot_config.py`:

```python
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
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_boot_config.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/runtime/boot_config.py tests/test_boot_config.py
git commit -m "refactor: add boot hardware summary helper"
```

---

### Task 2: Extract CPU Thread Environment Calculation

**Files:**

- Modify: `christine/runtime/boot_config.py`
- Modify: `tests/test_boot_config.py`

**Step 1: Write the failing test**

Add:

```python
from christine.runtime.boot_config import build_cpu_thread_env


def test_build_cpu_thread_env_sets_thread_limits():
    env = build_cpu_thread_env(6)

    assert env == {
        "OMP_NUM_THREADS": "6",
        "MKL_NUM_THREADS": "6",
        "OPENBLAS_NUM_THREADS": "6",
        "NUMEXPR_NUM_THREADS": "6",
        "CHRISTINE_CPU_CORES": "6",
    }
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_boot_config.py -q`

Expected: fail with missing `build_cpu_thread_env`.

**Step 3: Implement minimal helper**

Add:

```python
def build_cpu_thread_env(cpu_cores: int) -> dict[str, str]:
    cores = str(int(cpu_cores))
    return {
        "OMP_NUM_THREADS": cores,
        "MKL_NUM_THREADS": cores,
        "OPENBLAS_NUM_THREADS": cores,
        "NUMEXPR_NUM_THREADS": cores,
        "CHRISTINE_CPU_CORES": cores,
    }
```

**Step 4: Wire `boot_christine.py` CPU env calculation**

Import `build_cpu_thread_env` from `christine.runtime.boot_config` and replace the inline CPU env assignment in `apply_compute_budget()` with:

```python
env = build_cpu_thread_env(cpu_cores)
```

Do not change torch thread side effects in this task.

**Step 5: Run focused tests and launcher smoke**

Run:

```bash
uv run pytest tests/test_boot_config.py tests/test_boot_contract.py -q
uv run python boot_christine.py --check --notorch --fast --no-banner
```

Expected: pass.

**Step 6: Commit**

Run:

```bash
git add christine/runtime/boot_config.py tests/test_boot_config.py boot_christine.py
git commit -m "refactor: extract boot CPU env calculation"
```

---

### Task 3: Extract Pure Boot Banner Rendering

**Files:**

- Create: `christine/runtime/boot_banner.py`
- Create: `tests/test_boot_banner.py`

**Step 1: Write failing banner tests**

Create `tests/test_boot_banner.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_boot_banner.py -q`

Expected: fail with missing `christine.runtime.boot_banner`.

**Step 3: Implement renderer**

Create `christine/runtime/boot_banner.py`:

```python
from __future__ import annotations


PLAIN_COLORS = {"CY": "", "GR": "", "YE": "", "RD": "", "B": "", "D": "", "R": "", "M": ""}


def _colors(enabled: bool) -> dict[str, str]:
    if not enabled:
        return PLAIN_COLORS
    return {
        "CY": "\033[36m",
        "GR": "\033[32m",
        "YE": "\033[33m",
        "RD": "\033[31m",
        "B": "\033[1m",
        "D": "\033[2m",
        "R": "\033[0m",
        "M": "\033[35m",
    }


def render_boot_banner(
    hw,
    cpu_cores,
    gpu_ready,
    elapsed,
    *,
    gpu_frac="0.8",
    gpu_warm_ms="?",
    colors=True,
) -> list[str]:
    c = _colors(colors)
    bar = "═" * 70
    lines = [
        "",
        f"  {c['CY']}{bar}{c['R']}",
        f"  {c['M']}◆{c['R']}  {c['B']}CHRISTINE V1485 — Boot Sequence{c['R']}",
        f"  {c['CY']}{bar}{c['R']}",
        "",
        f"  {c['YE']}[Hardware]{c['R']}",
        f"    OS        : {hw['os']}     Python {hw['python']}",
        f"    CPU       : {hw['cpu_name'][:60]}",
        f"    Cores     : {c['B']}{cpu_cores}{c['R']} / {hw['cpu_count']}   (給 Christine: {int(cpu_cores / hw['cpu_count'] * 100)}%)",
        f"    RAM       : {hw['ram_gb']} GB",
    ]
    if hw["gpu"]:
        g = hw["gpu"]
        mark = f"{c['GR']}✓{c['R']}" if gpu_ready else f"{c['YE']}~{c['R']}"
        lines.append(f"    GPU       : {mark} {g['name']}  ({g['vram_gb']} GB, sm_{g['capability']})")
        if gpu_ready:
            lines.append(f"    GPU 預算  : {int(float(gpu_frac) * 100)}% VRAM  warm={gpu_warm_ms}ms")
    else:
        lines.append(f"    GPU       : {c['D']}— (CPU-only){c['R']}")
    if hw["torch"]:
        lines.append(f"    PyTorch   : {hw['torch']}")
    lines.extend([
        "",
        f"  {c['GR']}◆{c['R']}  Boot budget applied in {c['B']}{elapsed * 1000:.0f}ms{c['R']}  →  {c['B']}handing off to christine_final.py …{c['R']}",
        f"  {c['CY']}{bar}{c['R']}",
        "",
    ])
    return lines
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_boot_banner.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/runtime/boot_banner.py tests/test_boot_banner.py
git commit -m "refactor: add boot banner renderer"
```

---

### Task 4: Delegate Launcher Banner Printing To Renderer

**Files:**

- Modify: `boot_christine.py:153-182`
- Modify: `tests/test_boot_banner.py`

**Step 1: Add static delegation smoke test**

Add to `tests/test_boot_banner.py`:

```python
from pathlib import Path


def test_launcher_delegates_banner_rendering_to_runtime_module():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "from christine.runtime.boot_banner import render_boot_banner" in text
    assert "render_boot_banner(" in text
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_boot_banner.py -q`

Expected: fail because launcher still prints inline banner.

**Step 3: Wire launcher wrapper**

Import renderer:

```python
from christine.runtime.boot_banner import render_boot_banner
```

Replace `print_boot_banner()` body with:

```python
def print_boot_banner(hw, cpu_cores, gpu_ready, elapsed):
    lines = render_boot_banner(
        hw,
        cpu_cores,
        gpu_ready,
        elapsed,
        gpu_frac=os.environ.get("CHRISTINE_GPU_FRAC", "0.8"),
        gpu_warm_ms=os.environ.get("CHRISTINE_GPU_WARM_MS", "?"),
        colors=True,
    )
    for line in lines:
        print(line)
```

**Step 4: Run focused verification**

Run:

```bash
uv run pytest tests/test_boot_banner.py tests/test_boot_contract.py -q
uv run python boot_christine.py --check --notorch --fast --no-banner
```

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add boot_christine.py tests/test_boot_banner.py
git commit -m "refactor: delegate boot banner rendering"
```

---

### Task 5: Wire Basic Hardware Builder Into No-Torch Path

**Files:**

- Modify: `boot_christine.py:205-216`
- Modify: `tests/test_boot_config.py`

**Step 1: Add static delegation test**

Add to `tests/test_boot_config.py`:

```python
from pathlib import Path


def test_launcher_uses_basic_hardware_builder_for_notorch_path():
    text = Path("boot_christine.py").read_text(encoding="utf-8")

    assert "build_basic_hardware_info(" in text
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_boot_config.py -q`

Expected: fail because `main()` still builds the no-torch dict inline.

**Step 3: Wire no-torch path**

Import `build_basic_hardware_info` and replace the inline dict in `main()` with:

```python
hw = build_basic_hardware_info(
    system=platform.system(),
    release=platform.release(),
    python_version=platform.python_version(),
    cpu_count=multiprocessing.cpu_count(),
    cpu_name=platform.processor() or "unknown",
    ram_gb=None,
)
```

Keep the existing psutil RAM fill immediately after this call.

**Step 4: Run focused verification**

Run:

```bash
uv run pytest tests/test_boot_config.py tests/test_boot_contract.py -q
uv run python boot_christine.py --check --notorch --fast --no-banner
```

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add boot_christine.py tests/test_boot_config.py
git commit -m "refactor: delegate no-torch hardware summary"
```

---

## Final Verification

Run before reporting this wave complete:

```bash
uv run pytest tests/test_boot_config.py tests/test_boot_banner.py tests/test_boot_contract.py tests/test_platform_capabilities.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

Expected: all pass.

## Not In This Wave

- Do not change `christine_final.py` handoff behavior.
- Do not move torch import, CUDA warmup, or thread-setting side effects out of `boot_christine.py` yet.
- Do not change banner wording or Chinese boot output.
- Do not add distributed server behavior.
- Do not alter persisted runtime state.
