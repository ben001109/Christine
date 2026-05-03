# Christine Brain Bridge Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wrap the existing `brain/` package behind `christine.brain_bridge.service` before any brain file moves, while preserving V1480/V1484 monolith behavior.

**Architecture:** Add a narrow service boundary that owns lazy brain construction, basic state accounting, `say`/`dream`/`understand` calls, and optional MegaCortex auto-enable. Keep the current `brain/` package as the implementation source of truth and keep `christine_final.py` as the runtime entry point by delegating its V1480 helper functions through the service.

**Tech Stack:** Python 3.10+, stdlib dataclasses/pathlib/typing, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Preserve `boot_christine.py`, `christine_final.py`, and Windows launchers as entry points.
- Do not move or rename files inside `brain/` in this wave.
- Do not import `christine_final.py` from tests.
- Preserve Chinese V1480/V1484 user-facing output and command behavior.
- Preserve lazy/eager brain construction semantics used by the monolith block.
- Keep generated MegaCortex files untouched.
- Do not change persisted data formats or runtime state files.
- Keep legacy globals such as `_V1480_BRAIN`, `_V1480_CFG`, and `brain_say` available during strangler extraction.

## Current Facts

- `brain.brain.build_default_brain(size="small", seed=42, warmup=True)` is called directly inside `christine_final.py` around the V1480 block.
- `brain.Brain` exposes `perceive_text`, `respond`, `dream`, `understand`, `reward`, `status`, `enable_mega`, and `mega_status`.
- `tests/test_brain_contract.py` already proves `build_default_brain(size="tiny", warmup=False)` can understand and respond.
- `christine_final.py` contains many V1480 helpers that read `_V1480_CFG` directly, so this wave should sync service state back into that dict rather than replacing all legacy access.
- `brain/generated/` is excluded from routine compile and must not be hand-edited.

## Out Of Scope

- Moving `brain/` modules under `christine/brain_bridge/`.
- Replacing V1480 command parsing or ask routing.
- Rewriting memory, emotional semantics, or Chinese status strings.
- Adding new formula work.
- Starting a distributed brain server.

---

### Task 1: Add Brain Bridge Service Contract Tests

**Files:**
- Create: `tests/test_brain_bridge_service.py`
- Create later in Task 2: `christine/brain_bridge/__init__.py`
- Create later in Task 2: `christine/brain_bridge/service.py`

**Step 1: Write fake-brain test doubles**

Add this support code to `tests/test_brain_bridge_service.py`:

```python
class FakeBrain:
    def __init__(self):
        self.enable_mega_calls = []

    def perceive_text(self, text):
        return {"loss": 0.25, "understanding": {"intent": "greet"}, "valence": 0.2}

    def respond(self, seed=None, max_len=80):
        return f"reply:{seed}:{max_len}"

    def dream(self, cycles=3):
        return int(cycles)

    def understand(self, text):
        return {"intent": "statement", "text": text}

    def status(self):
        return {"size": "fake", "ticks": 1}

    def enable_mega(self, active_pool=64, sample_per_tick=8):
        self.enable_mega_calls.append((active_pool, sample_per_tick))
        return True
```

**Step 2: Write the failing lazy construction test**

```python
from christine.brain_bridge.service import BrainService, BrainServiceConfig


def test_brain_service_builds_brain_once():
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return FakeBrain()

    service = BrainService(
        BrainServiceConfig(size="tiny", seed=7, warmup=False, auto_mega=False),
        brain_factory=factory,
    )

    first = service.ensure_brain()
    second = service.ensure_brain()

    assert first is second
    assert calls == [{"size": "tiny", "seed": 7, "warmup": False}]
    assert service.state.ready is True
    assert service.state.err is None
    assert service.state.build_ms is not None
```

**Step 3: Write the failing say/accounting test**

```python
def test_brain_service_say_updates_call_accounting():
    service = BrainService(
        BrainServiceConfig(auto_mega=False),
        brain_factory=lambda **kwargs: FakeBrain(),
    )

    perception, response = service.say("你好", max_len=12)

    assert perception["loss"] == 0.25
    assert response == "reply:你好:12"
    assert service.state.total_calls == 1
    assert service.state.last_loss == 0.25
    assert service.state.last_response == response
    assert service.state.total_perceive_ms >= 0.0
```

**Step 4: Write the failing unavailable test**

```python
def test_brain_service_returns_unavailable_message_when_factory_fails():
    def broken_factory(**kwargs):
        raise RuntimeError("boom")

    service = BrainService(
        BrainServiceConfig(auto_mega=False),
        brain_factory=broken_factory,
    )

    perception, response = service.say("hello")

    assert perception is None
    assert response.startswith("[brain unavailable: RuntimeError: boom]")
    assert service.state.ready is False
    assert service.state.err == "RuntimeError: boom"
```

**Step 5: Write the failing MegaCortex auto-enable test**

```python
def test_brain_service_auto_enables_mega_when_generated_areas_exist(tmp_path):
    generated = tmp_path / "brain" / "generated"
    generated.mkdir(parents=True)
    (generated / "area_000001.py").write_text("# generated marker\n", encoding="utf-8")

    service = BrainService(
        BrainServiceConfig(auto_mega=True, generated_dir=generated),
        brain_factory=lambda **kwargs: FakeBrain(),
    )

    brain = service.ensure_brain()

    assert brain.enable_mega_calls == [(64, 8)]
    assert service.state.mega_auto is True
    assert service.state.mega_areas_disk == 1
```

**Step 6: Run test to verify RED**

Run: `uv run pytest tests/test_brain_bridge_service.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.brain_bridge'`.

**Step 7: Commit only if a plan-only commit has not already been made**

Do not commit failing tests by themselves unless the next task cannot be completed in the same slice.

---

### Task 2: Implement Minimal BrainService

**Files:**
- Create: `christine/brain_bridge/__init__.py`
- Create: `christine/brain_bridge/service.py`
- Modify: `tests/test_brain_bridge_service.py`

**Step 1: Create the package init**

Create `christine/brain_bridge/__init__.py`:

```python
"""Bridge from Christine runtime code to the legacy brain package."""

from .service import BrainService, BrainServiceConfig, BrainServiceState

__all__ = ["BrainService", "BrainServiceConfig", "BrainServiceState"]
```

**Step 2: Implement config and state dataclasses**

Create `christine/brain_bridge/service.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable


BrainFactory = Callable[..., Any]


@dataclass(frozen=True)
class BrainServiceConfig:
    size: str = "small"
    seed: int = 42
    warmup: bool = True
    auto_mega: bool = True
    active_pool: int = 64
    sample_per_tick: int = 8
    generated_dir: Path | None = None


@dataclass
class BrainServiceState:
    ready: bool = False
    err: str | None = None
    build_ms: float | None = None
    total_calls: int = 0
    total_perceive_ms: float = 0.0
    last_loss: Any = None
    last_response: str = ""
    mega_auto: bool = False
    mega_areas_disk: int = 0
```

**Step 3: Implement lazy construction**

Add to `service.py`:

```python
def _default_brain_factory(**kwargs: Any) -> Any:
    from brain.brain import build_default_brain

    return build_default_brain(**kwargs)


def _default_generated_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "brain" / "generated"


class BrainService:
    def __init__(
        self,
        config: BrainServiceConfig | None = None,
        brain_factory: BrainFactory | None = None,
    ):
        self.config = config or BrainServiceConfig()
        self.state = BrainServiceState()
        self._brain_factory = brain_factory or _default_brain_factory
        self._brain: Any | None = None

    @property
    def brain(self) -> Any | None:
        return self._brain

    def ensure_brain(self) -> Any | None:
        if self._brain is not None:
            return self._brain
        try:
            t0 = time.time()
            self._brain = self._brain_factory(
                size=self.config.size,
                seed=self.config.seed,
                warmup=self.config.warmup,
            )
            self.state.ready = True
            self.state.err = None
            self.state.build_ms = (time.time() - t0) * 1000.0
            self._auto_enable_mega()
            return self._brain
        except Exception as exc:
            self.state.ready = False
            self.state.err = f"{type(exc).__name__}: {exc}"
            self._brain = None
            return None
```

**Step 4: Implement MegaCortex auto-enable**

Add to `BrainService`:

```python
    def _auto_enable_mega(self) -> None:
        if not self.config.auto_mega or self._brain is None:
            return
        generated_dir = self.config.generated_dir or _default_generated_dir()
        try:
            areas = [
                path for path in generated_dir.iterdir()
                if path.name.startswith("area_") and path.suffix == ".py"
            ]
        except OSError:
            areas = []
        self.state.mega_areas_disk = len(areas)
        if not areas or not hasattr(self._brain, "enable_mega"):
            self.state.mega_auto = False
            return
        try:
            self.state.mega_auto = bool(
                self._brain.enable_mega(
                    active_pool=self.config.active_pool,
                    sample_per_tick=self.config.sample_per_tick,
                )
            )
        except Exception:
            self.state.mega_auto = False
```

**Step 5: Implement service methods**

Add to `BrainService`:

```python
    def unavailable_message(self) -> str:
        return f"[brain unavailable: {self.state.err}]"

    def say(self, text: str, max_len: int = 48) -> tuple[dict[str, Any] | None, str]:
        brain = self.ensure_brain()
        if brain is None:
            return None, self.unavailable_message()
        t0 = time.time()
        perception = brain.perceive_text(str(text))
        response = brain.respond(seed=str(text), max_len=max_len)
        dt_ms = (time.time() - t0) * 1000.0
        self.state.total_calls += 1
        self.state.total_perceive_ms += dt_ms
        self.state.last_loss = perception.get("loss") if isinstance(perception, dict) else None
        self.state.last_response = response
        return perception, response

    def dream(self, cycles: int = 3) -> int | str:
        brain = self.ensure_brain()
        if brain is None:
            return self.unavailable_message()
        return brain.dream(cycles=int(cycles))

    def understand(self, text: str) -> dict[str, Any] | str:
        brain = self.ensure_brain()
        if brain is None:
            return self.unavailable_message()
        return brain.understand(str(text))

    def status(self) -> dict[str, Any] | str:
        brain = self.brain
        if brain is None:
            return "大腦尚未啟動"
        return brain.status()
```

**Step 6: Run focused tests**

Run: `uv run pytest tests/test_brain_bridge_service.py tests/test_brain_contract.py -q`

Expected: pass.

**Step 7: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 8: Commit**

Commit message: `refactor: add brain bridge service`

---

### Task 3: Delegate V1480 Brain Construction Through BrainService

**Files:**
- Modify: `christine_final.py:119173-119248`
- Modify: `christine_final.py:119250-119359`
- Modify: `christine_final.py:119632-119639`
- Create or modify: `tests/test_brain_bridge_monolith.py`

**Step 1: Write static monolith smoke tests**

Create `tests/test_brain_bridge_monolith.py`:

```python
from pathlib import Path


def _v1480_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V1480  Christine 自己的大腦")
    end = text.index("V1483 AutoBoot", start)
    return text[start:end]


def test_v1480_uses_brain_bridge_service_for_construction():
    block = _v1480_block()

    assert "from christine.brain_bridge.service import BrainService, BrainServiceConfig" in block
    assert "_V1480_SERVICE" in block
    assert "from brain.brain import build_default_brain" not in block


def test_v1480_preserves_legacy_brain_globals():
    block = _v1480_block()

    assert 'globals()["brain_say"] = brain_say' in block
    assert 'globals()["brain_dream"] = brain_dream' in block
    assert 'globals()["brain_understand"] = brain_understand' in block
    assert "_V1480_CFG" in block
    assert "_V1480_BRAIN" in block
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_brain_bridge_monolith.py -q`

Expected: fail because the monolith still imports `build_default_brain` directly and has no `_V1480_SERVICE`.

**Step 3: Import the service in the V1480 block**

Inside the existing V1480 `try:` import line, add `pathlib.Path` and service import without changing outer control flow:

```python
    from pathlib import Path as _v180_Path
    from christine.brain_bridge.service import BrainService, BrainServiceConfig
```

**Step 4: Add service construction helpers after `_V1480_CFG`**

Add:

```python
    def _v180_build_service():
        return BrainService(BrainServiceConfig(
            size=_V1480_CFG["size"],
            seed=42,
            warmup=True,
            auto_mega=True,
            generated_dir=_v180_Path(_v180_here) / "brain" / "generated",
        ))

    _V1480_SERVICE = _v180_build_service()

    def _v180_sync_service_state():
        global _V1480_BRAIN
        st = _V1480_SERVICE.state
        _V1480_BRAIN = _V1480_SERVICE.brain
        _V1480_CFG["ready"] = st.ready
        _V1480_CFG["err"] = st.err
        if st.build_ms is not None:
            _V1480_CFG["build_ms"] = st.build_ms
        _V1480_CFG["total_calls"] = st.total_calls
        _V1480_CFG["total_perceive_ms"] = st.total_perceive_ms
        _V1480_CFG["last_loss"] = st.last_loss
        _V1480_CFG["last_response"] = st.last_response
        _V1480_CFG["mega_auto"] = st.mega_auto
        _V1480_CFG["mega_areas_disk"] = st.mega_areas_disk
```

**Step 5: Delegate `_v180_ensure_brain`**

Replace only the direct `build_default_brain` body of `_v180_ensure_brain()` with:

```python
    def _v180_ensure_brain():
        """eager 啟動大腦；透過 BrainService 做暖機 + 自動啟 MegaCortex。"""
        brain = _V1480_SERVICE.ensure_brain()
        _v180_sync_service_state()
        try:
            if brain is not None:
                log.info("[V1480] BrainService('%s') ready", _V1480_CFG["size"])
        except Exception: pass
        return brain
```

Keep the function name and return shape unchanged.

**Step 6: Delegate `brain_say`, `brain_dream`, and `brain_understand`**

Change only these helpers first:

```python
    def brain_say(text, max_len=48):
        """對外快捷：丟一句話給大腦，回一串 (perceive_summary, response)。"""
        perc, resp = _V1480_SERVICE.say(str(text), max_len=max_len)
        _v180_sync_service_state()
        return perc, resp

    def brain_dream(cycles=3):
        result = _V1480_SERVICE.dream(cycles=int(cycles))
        _v180_sync_service_state()
        return result

    def brain_understand(text):
        """只跑理解器（5W1H / 情感 / 意圖 / 實體 / 主題），不觸發 cognitive cycle。"""
        try:
            u = _V1480_SERVICE.understand(str(text))
            _v180_sync_service_state()
            if isinstance(u, str):
                return u
            parts = [
                f"intent={u.get('intent','?')}",
                f"conf={u.get('confidence',0):.2f}",
                f"pol={u.get('polarity',0):+.2f}",
                f"topic={u.get('topic','-')}",
                f"addressee={u.get('addressee','-')}",
            ]
            ents = u.get("entities") or {}
            if ents:
                parts.append("entities=" + ",".join(f"{k}:{v}" for k, v in list(ents.items())[:4]))
            return " | ".join(parts)
        except Exception as e:
            return f"× understand 失敗: {e}"
```

Do not change `brain_reward`, `brain_teach`, `brain_recall`, `brain_hint`, or `_v180_try_voice` in this task unless required by tests.

**Step 7: Keep size rebuild behavior working**

In the `大腦 size` / `brain size` branch, after updating `_V1480_CFG["size"]`, replace the old manual reset with:

```python
                globals()["_V1480_SERVICE"] = _v180_build_service()
                globals()["_V1480_BRAIN"] = None
                _V1480_CFG["ready"] = False
                _v180_ensure_brain()
```

**Step 8: Run focused tests**

Run: `uv run pytest tests/test_brain_bridge_service.py tests/test_brain_bridge_monolith.py tests/test_brain_contract.py -q`

Expected: pass.

**Step 9: Run launcher smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass and print `自檢完成` without starting `christine_final.py`.

**Step 10: Commit**

Commit message: `refactor: delegate monolith brain bridge`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused brain bridge tests**

Run: `uv run pytest tests/test_brain_bridge_service.py tests/test_brain_bridge_monolith.py tests/test_brain_contract.py -q`

Expected: pass.

**Step 2: Run full test suite**

Run: `uv run pytest -q`

Expected: pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: pass.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass and print `自檢完成`.

**Step 5: Run whitespace diff check**

Run: `git diff --check`

Expected: no output.

**Step 6: Request code review**

Use the code review workflow with:

- Base SHA: the parent commit before this branch.
- Head SHA: current branch HEAD.
- Requirements: preserve V1480/V1484 behavior, no `brain/` file moves, no generated file edits, no persisted state changes, `christine_final.py` remains executable.

**Step 7: Fix review findings if needed**

For Critical or Warning findings, use TDD where behavior changes are needed, verify focused tests, then commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after all tests and review are clean.

---

## Verification Gate For This Wave

Run these before claiming the wave complete:

```bash
uv run pytest tests/test_brain_bridge_service.py tests/test_brain_bridge_monolith.py tests/test_brain_contract.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if the bridge causes regressions.
- Do not delete runtime state artifacts.
- Do not edit `brain/generated/`.
- If monolith delegation fails, keep `christine.brain_bridge.service` and revert only the `christine_final.py` delegation commit, then revisit the seam with narrower wrappers.
