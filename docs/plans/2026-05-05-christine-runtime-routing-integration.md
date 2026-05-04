# Christine Runtime Routing Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate routing model recommendations into Christine's runtime through a deterministic policy gate without changing live `ask()` behavior in the first batch.

**Architecture:** Add a small conversation-layer adapter that takes an advisory `RoutePrediction`, applies `christine.modelization.routing_policy.apply_route_policy()`, and dispatches only to explicitly provided handlers. The first implementation is pure and test-only; live monolith integration comes later behind an explicit opt-in after policy-bypass tests and eval thresholds exist.

**Tech Stack:** Python 3.10+, stdlib dataclasses/callables, uv, pytest.

---

## Requirements Captured

- `RoutePrediction`, `score_route_predictions()`, and `apply_route_policy()` already exist under `christine.modelization`.
- The next step is runtime integration, but model output must remain advisory.
- Deterministic policy must decide the final target before any handler runs.
- Side-effect-capable routes (`tools`, `gui`, `worker`) must remain rejected by default.
- Preserve `boot_christine.py`, `christine_final.py`, and Windows launchers.
- Do not change `ask()` behavior in the first integration batch.
- Do not add Sentry, New Relic, Clerk, telemetry, cloud calls, embeddings, vector databases, model inference, or persisted policy config.

## Integration Approach

Use a three-stage integration path:

1. Pure conversation adapter first.
2. Disabled-by-default runtime hook later.
3. Live routing only after eval thresholds and explicit side-effect authorization tests exist.

This plan implements only stage 1. It creates a seam that future runtime code can call, but does not connect the seam to the monolith yet.

## Non-Goals

- No live `ask()` routing changes.
- No `christine_final.py` edits in this batch.
- No model inference.
- No tool execution changes.
- No GUI command routing changes.
- No memory/state migration.

---

### Task 1: Add Conversation Policy Router Contract Tests

**Files:**
- Create: `tests/test_conversation_policy_router.py`

**Step 1: Write the failing tests**

```python
import pytest

from christine.conversation.policy_router import route_with_policy
from christine.modelization import RoutePolicy, RoutePrediction


def test_route_with_policy_dispatches_accepted_safe_prediction():
    calls = []

    def repository_handler(inp):
        calls.append(("repository", inp))
        return "repo-result"

    result = route_with_policy(
        "整理 repo 架構",
        RoutePrediction("repository", "repo question"),
        handlers={"repository": repository_handler},
        fallback=lambda inp: "fallback",
    )

    assert result.target == "repository"
    assert result.accepted is True
    assert result.reason == "accepted"
    assert result.value == "repo-result"
    assert calls == [("repository", "整理 repo 架構")]


def test_route_with_policy_rejects_side_effect_prediction_to_fallback():
    calls = []

    def tool_handler(inp):
        calls.append(("tools", inp))
        return "tool-result"

    result = route_with_policy(
        "開啟工具",
        RoutePrediction("tools", "tool intent"),
        handlers={"tools": tool_handler},
        fallback=lambda inp: "fallback-result",
    )

    assert result.target == "direct"
    assert result.accepted is False
    assert result.reason == "rejected-side-effect-target:tools"
    assert result.value == "fallback-result"
    assert calls == []


def test_route_with_policy_can_opt_into_side_effect_dispatch():
    result = route_with_policy(
        "看螢幕",
        RoutePrediction("gui", "screen command"),
        handlers={"gui": lambda inp: "gui-result"},
        fallback=lambda inp: "fallback",
        policy=RoutePolicy(allow_side_effect_targets=True),
    )

    assert result.target == "gui"
    assert result.accepted is True
    assert result.value == "gui-result"


def test_route_with_policy_uses_fallback_when_target_handler_missing():
    result = route_with_policy(
        "hello",
        RoutePrediction("repository", "repo question"),
        handlers={},
        fallback=lambda inp: "fallback-result",
    )

    assert result.target == "direct"
    assert result.accepted is False
    assert result.reason == "missing-handler:repository"
    assert result.value == "fallback-result"


def test_route_with_policy_rejects_unknown_prediction_targets():
    with pytest.raises(ValueError, match="unknown route target"):
        route_with_policy(
            "hello",
            RoutePrediction("unknown", "bad target"),
            handlers={},
            fallback=lambda inp: "fallback",
        )
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_conversation_policy_router.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.conversation.policy_router'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping the session.

---

### Task 2: Implement Pure Policy Router Adapter

**Files:**
- Create: `christine/conversation/policy_router.py`
- Test: `tests/test_conversation_policy_router.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from christine.modelization import RoutePolicy, RoutePrediction, apply_route_policy


@dataclass(frozen=True)
class PolicyRouteResult:
    target: str
    accepted: bool
    reason: str
    value: Any


def route_with_policy(
    inp: Any,
    prediction: RoutePrediction,
    *,
    handlers: Mapping[str, Callable[[Any], Any]],
    fallback: Callable[[Any], Any],
    policy: RoutePolicy = RoutePolicy(),
) -> PolicyRouteResult:
    decision = apply_route_policy(prediction, policy)
    if not decision.accepted:
        return PolicyRouteResult(
            target=decision.target,
            accepted=False,
            reason=decision.reason,
            value=fallback(inp),
        )
    handler = handlers.get(decision.target)
    if handler is None:
        return PolicyRouteResult(
            target=policy.fallback_target,
            accepted=False,
            reason=f"missing-handler:{decision.target}",
            value=fallback(inp),
        )
    return PolicyRouteResult(
        target=decision.target,
        accepted=True,
        reason=decision.reason,
        value=handler(inp),
    )
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_conversation_policy_router.py tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/conversation/policy_router.py tests/test_conversation_policy_router.py
git commit -m "refactor: add policy-gated conversation router"
```

---

### Task 3: Export Conversation Policy Router

**Files:**
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_policy_router.py`

**Step 1: Add export test**

Append to `tests/test_conversation_policy_router.py`:

```python
def test_conversation_exports_policy_router():
    from christine.conversation import PolicyRouteResult, route_with_policy

    assert PolicyRouteResult.__name__ == "PolicyRouteResult"
    assert callable(route_with_policy)
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_conversation_policy_router.py::test_conversation_exports_policy_router -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/conversation/__init__.py`:

```python
from .policy_router import PolicyRouteResult, route_with_policy

__all__ = [
    "augment_input_with_hint",
    "dedupe_tool_specs",
    "PolicyRouteResult",
    "route_voice_then_fallback",
    "route_with_policy",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_conversation_policy_router.py tests/test_conversation_router.py tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/conversation/__init__.py tests/test_conversation_policy_router.py
git commit -m "refactor: export policy-gated conversation router"
```

---

### Task 4: Add Static Guard Against Accidental Monolith Integration

**Files:**
- Create or modify: `tests/test_runtime_routing_integration_guard.py`

**Step 1: Add guard test**

```python
from pathlib import Path


def test_policy_router_is_not_wired_into_monolith_yet():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "route_with_policy" not in text
    assert "allow_side_effect_targets=True" not in text
```

**Step 2: Run test**

Run: `uv run pytest tests/test_runtime_routing_integration_guard.py -q`

Expected: pass, documenting that this batch is pure-adapter only.

**Step 3: Commit**

```bash
git add tests/test_runtime_routing_integration_guard.py
git commit -m "test: guard runtime routing integration boundary"
```

---

### Task 5: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_conversation_policy_router.py tests/test_conversation_router.py tests/test_runtime_routing_integration_guard.py tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: all pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0 with no compile errors.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `自檢完成`.

**Step 5: Run whitespace check**

Run: `git diff --check`

Expected: exit 0.

**Step 6: Request review**

Request blocker-focused code review for the runtime routing adapter.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.

## Future Integration After This Plan

- Add eval fixtures for real Christine routing examples.
- Require an accuracy threshold before advisory predictions are accepted.
- Add a disabled-by-default runtime hook that logs policy decisions locally.
- Only after those pass, wire safe targets into the final `ask()` wrapper.
- Keep `tools`, `gui`, and `worker` behind explicit side-effect authorization tests.
