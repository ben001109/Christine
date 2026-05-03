# Christine Full Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor Christine into a uv-managed, fully modular, cross-platform, reliable, distributed-ready desktop assistant while preserving current identity, state, memory, and launch behavior.

**Architecture:** Use a strangler-style refactor: keep `boot_christine.py` and `christine_final.py` working while new modules are introduced around stable seams. New code goes into a package-oriented structure, with compatibility wrappers back to the current monolith until each capability is safely extracted and tested.

**Tech Stack:** Python 3.10+, uv, pytest, ruff, tkinter first for GUI compatibility, optional GPU/LLM extras, future optional FastAPI/Uvicorn for distributed deployment.

---

## Requirements Captured

- Full refactor of the entire program.
- Full modularization.
- Project management through uv.
- Cross-platform support: Windows first, Linux/macOS safe fallbacks.
- High reliability: tests, health checks, defensive platform boundaries, no state loss.
- Distributed deployment readiness.
- GUI and UI/UX modernization.
- Preserve Christine's user-facing personality, Chinese wording, memory behavior, emotional semantics, and existing launch entry points.

## Current Facts

- `boot_christine.py` is a clean launcher with self-check, CPU/GPU budgeting, and handoff to `christine_final.py`.
- `christine_final.py` is a 121k-line legacy monolith with repeated `ask()` and `main()` definitions, GUI, audio, tools, memory, autostart, brain integration, and platform code.
- `brain/` is already a partial package and is the safest first modular extraction target.
- `brain/generated/` contains many generated MegaCortex area files and must be excluded from routine compile/lint tasks.
- `data/`, `level5_logs/`, `growth.log`, `heartbeat.txt`, and `nexus_v2_state.json` are runtime state and must not be rewritten during refactor without an explicit migration.
- Windows launchers exist as `.bat` and `.ps1` files and must remain compatible.

## Approach Options

### Option A: Strangler Refactor (Recommended)

Keep current launch behavior intact and add tested modules around it. Extract one seam at a time, then route old code through the new module. This is slower than a rewrite but protects state, personality, launch behavior, and Windows-specific integrations.

### Option B: Big-Bang Rewrite

Create a new application from scratch and port features over. This is faster on paper but too risky for this project because much behavior exists only inside the monolith and persisted state formats are unclear.

### Option C: Brain-First Rewrite

Focus only on `brain/` first, then return to the monolith. This is safe but does not address platform, GUI, deployment, and reliability soon enough.

Decision: use Option A, with `brain/` and launcher contracts as the first protected surfaces.

---

## Target Package Shape

```text
christine/
  __init__.py
  runtime/
    paths.py
    config.py
    logging.py
    health.py
  platform/
    base.py
    windows.py
    linux.py
    macos.py
    audio.py
    desktop.py
  brain_bridge/
    service.py
    contracts.py
  conversation/
    router.py
    memory.py
    tools.py
  gui/
    app.py
    tk_app.py
    theme.py
  deployment/
    server.py
    worker.py
    protocol.py
  legacy/
    monolith.py
```

Do not move existing modules into this structure until tests prove the behavior to preserve. Early modules should wrap or call existing code instead of replacing it.

---

### Task 1: Establish Safety Baseline Tests

**Files:**
- Create: `tests/test_boot_contract.py`
- Create: `tests/test_brain_contract.py`
- Modify: `pyproject.toml`

**Step 1: Write the failing boot contract test**

```python
import subprocess
import sys


def test_fast_boot_check_exits_zero():
    result = subprocess.run(
        [sys.executable, "boot_christine.py", "--check", "--notorch", "--fast", "--no-banner"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "自檢完成" in result.stdout
```

**Step 2: Run test to verify it fails or exposes missing pytest setup**

Run: `uv run pytest tests/test_boot_contract.py -q`

Expected: fail only if pytest/env setup is missing or the launcher contract is broken.

**Step 3: Write the brain contract test**

```python
from brain import build_default_brain


def test_brain_can_understand_and_respond():
    brain = build_default_brain(size="tiny", warmup=False)
    perception = brain.perceive_text("你好 Christine")
    assert "understanding" in perception
    assert isinstance(brain.respond("你好 Christine"), str)
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_boot_contract.py tests/test_brain_contract.py -q`

Expected: both pass before any extraction starts.

**Step 5: Commit**

If git has been initialized, commit with: `git commit -m "test: add Christine baseline contracts"`

---

### Task 2: Create Runtime Foundation Package

**Files:**
- Create: `christine/__init__.py`
- Create: `christine/runtime/__init__.py`
- Create: `christine/runtime/paths.py`
- Create: `tests/test_runtime_paths.py`

**Step 1: Write the failing path test**

```python
from christine.runtime.paths import RuntimePaths


def test_runtime_paths_keep_state_in_repo_root(tmp_path):
    paths = RuntimePaths.from_root(tmp_path)
    assert paths.data == tmp_path / "data"
    assert paths.logs == tmp_path / "level5_logs"
    assert paths.nexus_state == tmp_path / "nexus_v2_state.json"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_runtime_paths.py -q`

Expected: fail with missing module.

**Step 3: Implement minimal paths module**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    logs: Path
    growth_log: Path
    heartbeat: Path
    nexus_state: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "RuntimePaths":
        base = Path(root).resolve()
        return cls(
            root=base,
            data=base / "data",
            logs=base / "level5_logs",
            growth_log=base / "growth.log",
            heartbeat=base / "heartbeat.txt",
            nexus_state=base / "nexus_v2_state.json",
        )
```

**Step 4: Run test and focused compile**

Run: `uv run pytest tests/test_runtime_paths.py -q`

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 5: Commit**

If git has been initialized, commit with: `git commit -m "refactor: add runtime path foundation"`

---

### Task 3: Add Platform Capability Boundaries

**Files:**
- Create: `christine/platform/__init__.py`
- Create: `christine/platform/base.py`
- Create: `christine/platform/windows.py`
- Create: `christine/platform/linux.py`
- Create: `christine/platform/macos.py`
- Create: `tests/test_platform_capabilities.py`

**Step 1: Write tests for platform detection**

```python
from christine.platform.base import detect_platform


def test_detect_platform_returns_capability_object():
    platform = detect_platform()
    assert platform.name in {"windows", "linux", "macos", "unknown"}
    assert isinstance(platform.supports_autostart, bool)
    assert isinstance(platform.supports_global_hotkeys, bool)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: fail with missing module.

**Step 3: Implement minimal capability dataclass**

```python
from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class PlatformCapabilities:
    name: str
    supports_autostart: bool
    supports_global_hotkeys: bool
    supports_system_audio: bool
    supports_gui: bool


def detect_platform() -> PlatformCapabilities:
    if sys.platform.startswith("win"):
        return PlatformCapabilities("windows", True, True, True, True)
    if sys.platform == "darwin":
        return PlatformCapabilities("macos", False, False, False, True)
    if sys.platform.startswith("linux"):
        return PlatformCapabilities("linux", False, False, False, True)
    return PlatformCapabilities("unknown", False, False, False, False)
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_platform_capabilities.py -q`

Expected: pass.

**Step 5: Commit**

If git has been initialized, commit with: `git commit -m "refactor: add platform capability boundary"`

---

### Task 4: Wrap Launcher Configuration Without Changing Boot Behavior

**Files:**
- Create: `christine/runtime/boot_config.py`
- Create: `tests/test_boot_config.py`
- Modify: `boot_christine.py`

**Step 1: Write a boot config test**

```python
from christine.runtime.boot_config import compute_cpu_budget


def test_compute_cpu_budget_defaults_to_half_with_minimum_two():
    assert compute_cpu_budget(cpu_count=24, requested=None) == 12
    assert compute_cpu_budget(cpu_count=2, requested=None) == 2
    assert compute_cpu_budget(cpu_count=24, requested=4) == 4
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_boot_config.py -q`

Expected: fail with missing module.

**Step 3: Implement minimal pure function**

```python
def compute_cpu_budget(cpu_count: int, requested: int | None = None) -> int:
    if requested is None:
        return max(2, cpu_count // 2)
    return max(1, min(int(requested), int(cpu_count)))
```

**Step 4: Wire `boot_christine.py` to call the pure function**

Keep the old behavior and output unchanged. Replace only the local CPU default calculation in `apply_compute_budget()`.

**Step 5: Verify launcher behavior**

Run: `uv run pytest tests/test_boot_config.py tests/test_boot_contract.py -q`
Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`
Expected: pass and exit 0.

**Step 6: Commit**

If git has been initialized, commit with: `git commit -m "refactor: isolate boot CPU budget logic"`

---

### Task 5: Create GUI Boundary Before Replacing UI

**Files:**
- Create: `christine/gui/__init__.py`
- Create: `christine/gui/app.py`
- Create: `christine/gui/tk_app.py`
- Create: `tests/test_gui_contract.py`

**Step 1: Write GUI contract test without opening a window**

```python
from christine.gui.app import GuiMessage, GuiQueues


def test_gui_queues_store_user_and_assistant_messages():
    queues = GuiQueues()
    queues.submit_user("hello")
    queues.submit_assistant("hi")
    assert queues.next_user() == GuiMessage(role="user", text="hello")
    assert queues.next_assistant() == GuiMessage(role="assistant", text="hi")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail with missing module.

**Step 3: Implement queue contract only**

```python
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class GuiMessage:
    role: str
    text: str


class GuiQueues:
    def __init__(self):
        self._user = deque()
        self._assistant = deque()

    def submit_user(self, text: str) -> None:
        self._user.append(GuiMessage("user", text))

    def submit_assistant(self, text: str) -> None:
        self._assistant.append(GuiMessage("assistant", text))

    def next_user(self):
        return self._user.popleft() if self._user else None

    def next_assistant(self):
        return self._assistant.popleft() if self._assistant else None
```

**Step 4: Integrate later, not in this task**

Do not replace `launch_chat_window()` yet. First prove the queue contract and then create a separate extraction task for the Tkinter implementation.

**Step 5: Commit**

If git has been initialized, commit with: `git commit -m "refactor: add GUI message contract"`

---

### Task 6: Add Distributed Deployment Skeleton

**Files:**
- Create: `christine/deployment/__init__.py`
- Create: `christine/deployment/protocol.py`
- Create: `tests/test_deployment_protocol.py`
- Modify: `pyproject.toml`

**Step 1: Add optional dependency group only after a test exists**

Add a `distributed` optional extra with `fastapi`, `uvicorn`, and `httpx` only when the first protocol module is ready.

**Step 2: Write protocol tests**

```python
from christine.deployment.protocol import HealthStatus


def test_health_status_serializes_core_fields():
    status = HealthStatus(ok=True, service="christine", detail="ready")
    assert status.to_dict() == {"ok": True, "service": "christine", "detail": "ready"}
```

**Step 3: Implement protocol without starting a server**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    service: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {"ok": self.ok, "service": self.service, "detail": self.detail}
```

**Step 4: Verify**

Run: `uv run pytest tests/test_deployment_protocol.py -q`
Expected: pass.

**Step 5: Commit**

If git has been initialized, commit with: `git commit -m "refactor: add deployment protocol skeleton"`

---

## Later Extraction Waves

Each wave needs its own detailed child plan before edits.

1. Extract autostart and startup registration from `christine_final.py:2310-2396` into `christine/platform/windows.py`.
2. Extract legacy GUI queue behavior from `christine_final.py:1857-1961` and `christine_final.py:10016-10036` into `christine/gui/`.
3. Extract boot banner and hardware budget functions from `boot_christine.py` into pure runtime modules.
4. Wrap `brain/` behind `christine/brain_bridge/service.py` before moving files.
5. Extract `ask()` routing in layers, starting with stable wrappers around `christine_final.py:6093` and `christine_final.py:120940-120958`.
6. Split tool registration into declarative modules only after a tool contract test exists.
7. Add distributed server process only after local contracts are green.
8. Modernize GUI UI/UX after the message queue contract is independent from Tkinter.

## Verification Gate For Every Wave

Run the narrowest relevant commands first:

```bash
uv run pytest tests/<focused_test>.py -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine
uv run python boot_christine.py --check --notorch --fast --no-banner
```

For Windows-only changes, also run the relevant `.bat` or `.ps1` launcher on Windows before declaring that behavior preserved.
