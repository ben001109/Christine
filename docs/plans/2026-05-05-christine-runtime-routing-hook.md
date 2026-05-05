# Christine Runtime Routing Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a disabled-by-default runtime routing hook that can observe advisory routing decisions without changing live `ask()` behavior or executing side effects.

**Architecture:** Keep the hook as a pure conversation-layer module. The hook receives an input and advisory `RoutePrediction`, applies the deterministic `RoutePolicy` only when enabled, and returns a structured observation; it never dispatches handlers or writes runtime state by itself. The legacy monolith remains unwired in this batch.

**Tech Stack:** Python 3.10+, dataclasses, stdlib callables, uv, pytest.

---

## Requirements Captured

- Preserve `boot_christine.py`, `christine_final.py`, and Windows launchers.
- Do not change live `ask()` behavior in this batch.
- Do not execute tools, GUI actions, workers, model inference, cloud calls, telemetry, embeddings, vector databases, or persistent policy writes.
- Keep side-effect routes rejected by default through `RoutePolicy`.
- Provide a small future seam for local runtime logging by accepting an optional recorder callback only when the hook is enabled.

## Non-Goals

- No `christine_final.py` integration.
- No handler dispatch; `route_with_policy()` remains the explicit dispatch adapter.
- No persisted logs, config files, memory migration, or state changes.
- No side-effect authorization beyond existing `RoutePolicy(allow_side_effect_targets=True)` test coverage.

---

### Task 1: Add Runtime Routing Hook Contract Tests

**Files:**
- Create: `tests/test_conversation_runtime_routing_hook.py`

**Step 1: Write failing tests**

```python
from christine.conversation.runtime_routing_hook import RuntimeRoutingHook, observe_runtime_route
from christine.modelization import RoutePolicy, RoutePrediction


def test_disabled_runtime_routing_hook_returns_fallback_without_recording():
    records = []

    observation = observe_runtime_route(
        "整理 repo 架構",
        RoutePrediction("repository", "repo intent"),
        recorder=records.append,
    )

    assert observation.enabled is False
    assert observation.predicted_target == "repository"
    assert observation.target == "direct"
    assert observation.accepted is False
    assert observation.reason == "runtime-routing-disabled"
    assert records == []


def test_enabled_runtime_routing_hook_records_safe_policy_decision():
    records = []

    observation = observe_runtime_route(
        "整理 repo 架構",
        RoutePrediction("repository", "repo intent"),
        hook=RuntimeRoutingHook(enabled=True),
        recorder=records.append,
    )

    assert observation.enabled is True
    assert observation.target == "repository"
    assert observation.accepted is True
    assert observation.reason == "accepted"
    assert records == [observation]


def test_enabled_runtime_routing_hook_keeps_side_effect_targets_rejected_by_default():
    observation = observe_runtime_route(
        "開啟工具",
        RoutePrediction("tools", "tool intent"),
        hook=RuntimeRoutingHook(enabled=True),
    )

    assert observation.target == "direct"
    assert observation.accepted is False
    assert observation.reason == "rejected-side-effect-target:tools"


def test_enabled_runtime_routing_hook_can_use_explicit_policy_override():
    observation = observe_runtime_route(
        "看螢幕",
        RoutePrediction("gui", "screen intent"),
        hook=RuntimeRoutingHook(enabled=True, policy=RoutePolicy(allow_side_effect_targets=True)),
    )

    assert observation.target == "gui"
    assert observation.accepted is True
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.conversation.runtime_routing_hook'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping the session.

---

### Task 2: Implement Pure Runtime Routing Hook

**Files:**
- Create: `christine/conversation/runtime_routing_hook.py`
- Test: `tests/test_conversation_runtime_routing_hook.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from christine.modelization import RoutePolicy, RoutePrediction, apply_route_policy


@dataclass(frozen=True)
class RuntimeRoutingHook:
    enabled: bool = False
    policy: RoutePolicy = RoutePolicy()


@dataclass(frozen=True)
class RuntimeRouteObservation:
    input_text: str
    predicted_target: str
    target: str
    accepted: bool
    reason: str
    enabled: bool


def observe_runtime_route(
    input_text: str,
    prediction: RoutePrediction,
    *,
    hook: RuntimeRoutingHook = RuntimeRoutingHook(),
    recorder: Callable[[RuntimeRouteObservation], None] | None = None,
) -> RuntimeRouteObservation:
    if not hook.enabled:
        return RuntimeRouteObservation(
            input_text=input_text,
            predicted_target=prediction.target,
            target=hook.policy.fallback_target,
            accepted=False,
            reason="runtime-routing-disabled",
            enabled=False,
        )

    decision = apply_route_policy(prediction, hook.policy)
    observation = RuntimeRouteObservation(
        input_text=input_text,
        predicted_target=prediction.target,
        target=decision.target,
        accepted=decision.accepted,
        reason=decision.reason,
        enabled=True,
    )
    if recorder is not None:
        recorder(observation)
    return observation
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py tests/test_modelization_routing_policy.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/conversation/runtime_routing_hook.py tests/test_conversation_runtime_routing_hook.py
git commit -m "refactor: add disabled runtime routing hook"
```

---

### Task 3: Export Runtime Routing Hook

**Files:**
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_runtime_routing_hook.py`

**Step 1: Add export test**

Append to `tests/test_conversation_runtime_routing_hook.py`:

```python
def test_conversation_exports_runtime_routing_hook():
    from christine.conversation import RuntimeRouteObservation, RuntimeRoutingHook, observe_runtime_route

    assert RuntimeRouteObservation.__name__ == "RuntimeRouteObservation"
    assert RuntimeRoutingHook.__name__ == "RuntimeRoutingHook"
    assert callable(observe_runtime_route)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py::test_conversation_exports_runtime_routing_hook -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/conversation/__init__.py`:

```python
from .runtime_routing_hook import RuntimeRouteObservation, RuntimeRoutingHook, observe_runtime_route

__all__ = [
    "augment_input_with_hint",
    "dedupe_tool_specs",
    "PolicyRouteResult",
    "route_voice_then_fallback",
    "route_with_policy",
    "RuntimeRouteObservation",
    "RuntimeRoutingHook",
    "observe_runtime_route",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py tests/test_conversation_policy_router.py tests/test_conversation_router.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/conversation/__init__.py tests/test_conversation_runtime_routing_hook.py
git commit -m "refactor: export runtime routing hook"
```

---

### Task 4: Guard Against Accidental Monolith Wiring

**Files:**
- Modify: `tests/test_runtime_routing_integration_guard.py`

**Step 1: Extend static guard**

```python
def test_runtime_routing_hook_is_not_wired_into_monolith_yet():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "observe_runtime_route" not in text
    assert "RuntimeRoutingHook" not in text
```

**Step 2: Run guard**

Run: `uv run pytest tests/test_runtime_routing_integration_guard.py -q`

Expected: pass.

**Step 3: Commit**

```bash
git add tests/test_runtime_routing_integration_guard.py
git commit -m "test: guard runtime routing hook boundary"
```

---

### Task 5: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py tests/test_conversation_policy_router.py tests/test_conversation_router.py tests/test_runtime_routing_integration_guard.py tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: all pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0 with no output.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `自檢完成`.

**Step 5: Run whitespace check**

Run: `git diff --check`

Expected: exit 0.

**Step 6: Request review**

Request blocker-focused code review for the disabled runtime routing hook.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.

## Future Integration After This Plan

- Add a local-only runtime log sink if a later plan needs persistent policy diagnostics.
- Add an explicit disabled-by-default monolith wrapper only after hook behavior and static guard remain green.
- Keep `tools`, `gui`, and `worker` behind side-effect authorization tests before live wiring.
