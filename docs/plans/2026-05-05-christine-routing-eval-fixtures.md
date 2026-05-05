# Christine Routing Eval Fixtures Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add curated routing evaluation fixtures and a deterministic readiness threshold before any routing model is trusted by runtime code.

**Architecture:** Keep routing evaluation in `christine.modelization` as local stdlib-only data and scoring utilities. Add stable fixture examples covering safe and side-effect-capable route targets, then add a small threshold assessment helper that wraps the existing `score_route_predictions()` result.

**Tech Stack:** Python 3.10+, stdlib dataclasses, uv, pytest.

---

## Requirements Captured

- Routing model output remains advisory.
- Deterministic policy and evaluation must exist before runtime trust.
- Keep this local, side-effect free, dependency-free, and test-only.
- Do not change `christine_final.py`, live `ask()`, tool execution, GUI behavior, memory, persisted state, launchers, or the policy router adapter.
- Do not add Sentry, New Relic, Clerk, telemetry, cloud calls, embeddings, vector databases, or model inference.
- Fixtures should include Chinese Christine-style requests and cover at least `repository`, `tools`, `gui`, `brain`, and `direct`.

## Non-Goals

- No classifier.
- No prompt construction.
- No live runtime hook.
- No persisted eval registry.
- No ingestion of private memory or transcripts.

---

### Task 1: Add Routing Eval Fixture Contract Tests

**Files:**
- Create: `tests/test_modelization_routing_fixtures.py`

**Step 1: Write the failing tests**

```python
from christine.modelization.routing_eval import RouteEvalExample
from christine.modelization.routing_fixtures import ROUTING_EVAL_FIXTURES


def test_routing_eval_fixtures_are_stable_and_cover_core_targets():
    assert ROUTING_EVAL_FIXTURES == (
        RouteEvalExample("整理這個 repo 的架構", "repository"),
        RouteEvalExample("幫我看目前螢幕", "gui"),
        RouteEvalExample("開啟 runtime health check", "tools"),
        RouteEvalExample("你現在感覺如何", "brain"),
        RouteEvalExample("直接回答這句話", "direct"),
    )


def test_routing_eval_fixtures_have_unique_inputs():
    inputs = [example.input_text for example in ROUTING_EVAL_FIXTURES]

    assert len(inputs) == len(set(inputs))
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_modelization_routing_fixtures.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.modelization.routing_fixtures'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping the session.

---

### Task 2: Add Stable Routing Eval Fixtures

**Files:**
- Create: `christine/modelization/routing_fixtures.py`
- Test: `tests/test_modelization_routing_fixtures.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

from .routing_eval import RouteEvalExample


ROUTING_EVAL_FIXTURES = (
    RouteEvalExample("整理這個 repo 的架構", "repository"),
    RouteEvalExample("幫我看目前螢幕", "gui"),
    RouteEvalExample("開啟 runtime health check", "tools"),
    RouteEvalExample("你現在感覺如何", "brain"),
    RouteEvalExample("直接回答這句話", "direct"),
)
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_fixtures.py tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/modelization/routing_fixtures.py tests/test_modelization_routing_fixtures.py
git commit -m "test: add routing eval fixtures"
```

---

### Task 3: Add Routing Readiness Threshold Tests

**Files:**
- Modify: `tests/test_modelization_routing_eval.py`

**Step 1: Add threshold tests**

Append to `tests/test_modelization_routing_eval.py`:

```python
from christine.modelization.routing_eval import assess_route_readiness


def test_assess_route_readiness_passes_when_accuracy_meets_threshold():
    examples = (
        RouteEvalExample("a", "direct"),
        RouteEvalExample("b", "repository"),
    )
    predictions = (
        RoutePrediction("direct"),
        RoutePrediction("repository"),
    )

    readiness = assess_route_readiness(examples, predictions, min_accuracy=1.0)

    assert readiness.ready is True
    assert readiness.min_accuracy == 1.0
    assert readiness.result.correct == 2


def test_assess_route_readiness_fails_when_accuracy_is_below_threshold():
    examples = (
        RouteEvalExample("a", "direct"),
        RouteEvalExample("b", "repository"),
    )
    predictions = (
        RoutePrediction("direct"),
        RoutePrediction("direct", "missed repo"),
    )

    readiness = assess_route_readiness(examples, predictions, min_accuracy=0.75)

    assert readiness.ready is False
    assert readiness.result.accuracy == 0.5


def test_assess_route_readiness_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="min_accuracy must be between 0 and 1"):
        assess_route_readiness((), (), min_accuracy=1.1)
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_modelization_routing_eval.py::test_assess_route_readiness_passes_when_accuracy_meets_threshold -q`

Expected: fail with import error for `assess_route_readiness`.

**Step 3: Continue to Task 4**

Do not commit RED tests alone unless stopping the session.

---

### Task 4: Implement Routing Readiness Threshold

**Files:**
- Modify: `christine/modelization/routing_eval.py`
- Test: `tests/test_modelization_routing_eval.py`

**Step 1: Add the minimal implementation**

Add after `RouteEvalResult`:

```python
@dataclass(frozen=True)
class RouteReadiness:
    ready: bool
    min_accuracy: float
    result: RouteEvalResult
```

Add after `score_route_predictions()`:

```python
def assess_route_readiness(
    examples: tuple[RouteEvalExample, ...],
    predictions: tuple[RoutePrediction, ...],
    *,
    min_accuracy: float = 0.8,
) -> RouteReadiness:
    if not 0 <= min_accuracy <= 1:
        raise ValueError("min_accuracy must be between 0 and 1")
    result = score_route_predictions(examples, predictions)
    return RouteReadiness(
        ready=result.accuracy >= min_accuracy,
        min_accuracy=min_accuracy,
        result=result,
    )
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_eval.py tests/test_modelization_routing_fixtures.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/modelization/routing_eval.py tests/test_modelization_routing_eval.py
git commit -m "refactor: add routing readiness threshold"
```

---

### Task 5: Export Routing Fixtures And Readiness

**Files:**
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_routing_fixtures.py`

**Step 1: Add export test**

Append to `tests/test_modelization_routing_fixtures.py`:

```python
def test_modelization_exports_routing_eval_fixtures_and_readiness():
    from christine.modelization import ROUTING_EVAL_FIXTURES, RouteReadiness, assess_route_readiness

    assert ROUTING_EVAL_FIXTURES
    assert RouteReadiness.__name__ == "RouteReadiness"
    assert callable(assess_route_readiness)
```

**Step 2: Run export test to verify RED**

Run: `uv run pytest tests/test_modelization_routing_fixtures.py::test_modelization_exports_routing_eval_fixtures_and_readiness -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/modelization/__init__.py`:

```python
from .routing_eval import ..., RouteReadiness, assess_route_readiness
from .routing_fixtures import ROUTING_EVAL_FIXTURES
```

Add to `__all__`:

```python
"ROUTING_EVAL_FIXTURES",
"RouteReadiness",
"assess_route_readiness",
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_fixtures.py tests/test_modelization_routing_eval.py tests/test_modelization_routing_policy.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/modelization/__init__.py tests/test_modelization_routing_fixtures.py
git commit -m "refactor: export routing eval fixtures"
```

---

### Task 6: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused modelization tests**

Run: `uv run pytest tests/test_modelization_routing_fixtures.py tests/test_modelization_routing_eval.py tests/test_modelization_routing_policy.py tests/test_conversation_policy_router.py -q`

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

Request blocker-focused code review for the routing eval fixtures and readiness threshold.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.
