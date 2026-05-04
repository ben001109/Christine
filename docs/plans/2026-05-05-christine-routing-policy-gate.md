# Christine Routing Policy Gate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic policy gate for future routing model recommendations before any runtime routing integration.

**Architecture:** Introduce a pure stdlib modelization module that accepts a `RoutePrediction` and returns an accepted or rejected `RoutePolicyDecision`. By default, side-effect-capable targets fall back to `direct`; callers must opt in before `tools`, `gui`, or `worker` recommendations are accepted.

**Tech Stack:** Python 3.10+, stdlib dataclasses, uv, pytest.

---

## Requirements Captured

- Modelization design says model output can recommend routes, but deterministic policy makes final decisions.
- Add the policy gate before adding any model inference or live routing integration.
- Keep this local, pure, deterministic, dependency-free, and side-effect free.
- Do not change `ask()`, `christine_final.py`, tool execution, GUI behavior, memory, persisted state, or launcher behavior.
- Do not add Sentry, New Relic, Clerk, telemetry, cloud calls, embeddings, vector databases, or model inference.
- Default behavior must reject side-effect-capable route recommendations: `tools`, `gui`, and `worker`.

## Non-Goals

- No runtime router integration.
- No model classifier.
- No prompt construction.
- No tool execution or authorization system.
- No persisted policy config.

---

### Task 1: Add Routing Policy Gate Contract Tests

**Files:**
- Create: `tests/test_modelization_routing_policy.py`

**Step 1: Write the failing tests**

```python
import pytest

from christine.modelization.routing_eval import RoutePrediction
from christine.modelization.routing_policy import (
    SIDE_EFFECT_TARGETS,
    RoutePolicy,
    apply_route_policy,
)


def test_route_policy_accepts_safe_recommendations_by_default():
    decision = apply_route_policy(RoutePrediction("repository", "repo question"))

    assert decision.accepted is True
    assert decision.target == "repository"
    assert decision.reason == "accepted"


def test_route_policy_rejects_side_effect_targets_by_default():
    assert SIDE_EFFECT_TARGETS == ("tools", "gui", "worker")

    decision = apply_route_policy(RoutePrediction("tools", "open app"))

    assert decision.accepted is False
    assert decision.target == "direct"
    assert decision.reason == "rejected-side-effect-target:tools"


def test_route_policy_can_opt_into_side_effect_targets():
    policy = RoutePolicy(allow_side_effect_targets=True)

    decision = apply_route_policy(RoutePrediction("gui", "screen command"), policy)

    assert decision.accepted is True
    assert decision.target == "gui"
    assert decision.reason == "accepted"


def test_route_policy_rejects_unknown_targets():
    with pytest.raises(ValueError, match="unknown route target"):
        apply_route_policy(RoutePrediction("unknown", "bad target"))
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_modelization_routing_policy.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.modelization.routing_policy'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping the session.

---

### Task 2: Implement Deterministic Policy Gate

**Files:**
- Create: `christine/modelization/routing_policy.py`
- Test: `tests/test_modelization_routing_policy.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass

from .routing_eval import ROUTE_TARGETS, RoutePrediction


SIDE_EFFECT_TARGETS = ("tools", "gui", "worker")


@dataclass(frozen=True)
class RoutePolicy:
    allow_side_effect_targets: bool = False
    fallback_target: str = "direct"


@dataclass(frozen=True)
class RoutePolicyDecision:
    target: str
    accepted: bool
    reason: str


def _validate_target(target: str) -> None:
    if target not in ROUTE_TARGETS:
        raise ValueError(f"unknown route target: {target}")


def apply_route_policy(
    prediction: RoutePrediction,
    policy: RoutePolicy = RoutePolicy(),
) -> RoutePolicyDecision:
    _validate_target(policy.fallback_target)
    _validate_target(prediction.target)
    if prediction.target in SIDE_EFFECT_TARGETS and not policy.allow_side_effect_targets:
        return RoutePolicyDecision(
            target=policy.fallback_target,
            accepted=False,
            reason=f"rejected-side-effect-target:{prediction.target}",
        )
    return RoutePolicyDecision(target=prediction.target, accepted=True, reason="accepted")
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/modelization/routing_policy.py tests/test_modelization_routing_policy.py
git commit -m "refactor: add routing policy gate"
```

---

### Task 3: Export Routing Policy Gate

**Files:**
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_routing_policy.py`

**Step 1: Add export test**

Append to `tests/test_modelization_routing_policy.py`:

```python
def test_modelization_exports_routing_policy_gate():
    from christine.modelization import RoutePolicy, RoutePolicyDecision, apply_route_policy

    assert RoutePolicy.__name__ == "RoutePolicy"
    assert RoutePolicyDecision.__name__ == "RoutePolicyDecision"
    assert callable(apply_route_policy)
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_modelization_routing_policy.py::test_modelization_exports_routing_policy_gate -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/modelization/__init__.py`:

```python
from .routing_policy import SIDE_EFFECT_TARGETS, RoutePolicy, RoutePolicyDecision, apply_route_policy

__all__ = [
    ...,
    "SIDE_EFFECT_TARGETS",
    "RoutePolicy",
    "RoutePolicyDecision",
    "apply_route_policy",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/modelization/__init__.py tests/test_modelization_routing_policy.py
git commit -m "refactor: export routing policy gate"
```

---

### Task 4: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused modelization tests**

Run: `uv run pytest tests/test_modelization_routing_policy.py tests/test_modelization_routing_eval.py tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

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

Request blocker-focused code review for the routing policy gate.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.
