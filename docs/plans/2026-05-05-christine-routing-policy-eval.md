# Christine Routing Policy Eval Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic evaluation boundary for future routing/policy model recommendations.

**Architecture:** Introduce a stdlib-only modelization module that scores predicted route targets against curated examples. This does not route live requests, call models, or change `christine_final.py`; it only provides typed local metrics that future model recommendations must beat before being trusted.

**Tech Stack:** Python 3.10+, stdlib dataclasses, uv, pytest.

---

## Requirements Captured

- Build on the modelization design rule: routing/policy models may recommend, but deterministic policy decides.
- Add eval scaffolding before adding any model inference.
- Keep this local, read-only, deterministic, and dependency-free.
- Do not change `ask()`, `christine_final.py`, tool execution, GUI behavior, memory, persisted state, or launcher behavior.
- Do not add Sentry, New Relic, Clerk, telemetry, cloud calls, embeddings, or vector databases.
- Keep route labels explicit enough for later evals: `brain`, `local_llm`, `cloud_llm`, `tools`, `gui`, `worker`, `repository`, and `direct`.

## Non-Goals

- No runtime routing integration.
- No model classifier.
- No prompt construction.
- No tool selection behavior changes.
- No memory or transcript ingestion.

---

### Task 1: Add Routing Eval Contract Tests

**Files:**
- Create: `tests/test_modelization_routing_eval.py`

**Step 1: Write the failing tests**

```python
import pytest

from christine.modelization.routing_eval import (
    ROUTE_TARGETS,
    RouteEvalExample,
    RoutePrediction,
    score_route_predictions,
)


def test_route_targets_are_explicit_and_stable():
    assert ROUTE_TARGETS == (
        "brain",
        "local_llm",
        "cloud_llm",
        "tools",
        "gui",
        "worker",
        "repository",
        "direct",
    )


def test_score_route_predictions_counts_accuracy_and_mismatches():
    examples = (
        RouteEvalExample("幫我看目前畫面", "gui"),
        RouteEvalExample("整理這個 repo 的架構", "repository"),
        RouteEvalExample("開啟 runtime health check", "tools"),
    )
    predictions = (
        RoutePrediction("gui", "screen command"),
        RoutePrediction("repository", "repo question"),
        RoutePrediction("direct", "missed tool intent"),
    )

    result = score_route_predictions(examples, predictions)

    assert result.total == 3
    assert result.correct == 2
    assert result.accuracy == pytest.approx(2 / 3)
    assert result.mismatches == (
        {
            "index": 2,
            "input_text": "開啟 runtime health check",
            "expected": "tools",
            "predicted": "direct",
            "reason": "missed tool intent",
        },
    )


def test_score_route_predictions_rejects_unknown_targets():
    examples = (RouteEvalExample("hi", "direct"),)
    predictions = (RoutePrediction("unknown", "bad target"),)

    with pytest.raises(ValueError, match="unknown route target"):
        score_route_predictions(examples, predictions)
```

**Step 2: Run tests to verify RED**

Run: `uv run pytest tests/test_modelization_routing_eval.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.modelization.routing_eval'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping the session.

---

### Task 2: Implement Routing Eval Scoring

**Files:**
- Create: `christine/modelization/routing_eval.py`
- Test: `tests/test_modelization_routing_eval.py`

**Step 1: Add the minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass


ROUTE_TARGETS = (
    "brain",
    "local_llm",
    "cloud_llm",
    "tools",
    "gui",
    "worker",
    "repository",
    "direct",
)


@dataclass(frozen=True)
class RouteEvalExample:
    input_text: str
    expected_target: str


@dataclass(frozen=True)
class RoutePrediction:
    target: str
    reason: str = ""


@dataclass(frozen=True)
class RouteEvalResult:
    total: int
    correct: int
    mismatches: tuple[dict[str, object], ...]

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.correct / self.total


def _validate_target(target: str) -> None:
    if target not in ROUTE_TARGETS:
        raise ValueError(f"unknown route target: {target}")


def score_route_predictions(
    examples: tuple[RouteEvalExample, ...],
    predictions: tuple[RoutePrediction, ...],
) -> RouteEvalResult:
    if len(examples) != len(predictions):
        raise ValueError("examples and predictions must have the same length")

    correct = 0
    mismatches: list[dict[str, object]] = []
    for index, (example, prediction) in enumerate(zip(examples, predictions, strict=True)):
        _validate_target(example.expected_target)
        _validate_target(prediction.target)
        if prediction.target == example.expected_target:
            correct += 1
            continue
        mismatches.append(
            {
                "index": index,
                "input_text": example.input_text,
                "expected": example.expected_target,
                "predicted": prediction.target,
                "reason": prediction.reason,
            }
        )
    return RouteEvalResult(total=len(examples), correct=correct, mismatches=tuple(mismatches))
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_eval.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/modelization/routing_eval.py tests/test_modelization_routing_eval.py
git commit -m "refactor: add routing policy eval scoring"
```

---

### Task 3: Export Routing Eval Boundary

**Files:**
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_routing_eval.py`

**Step 1: Add export test**

Append to `tests/test_modelization_routing_eval.py`:

```python
def test_modelization_exports_routing_eval_boundary():
    from christine.modelization import RouteEvalExample, RoutePrediction, score_route_predictions

    assert RouteEvalExample.__name__ == "RouteEvalExample"
    assert RoutePrediction.__name__ == "RoutePrediction"
    assert callable(score_route_predictions)
```

**Step 2: Run test to verify RED**

Run: `uv run pytest tests/test_modelization_routing_eval.py::test_modelization_exports_routing_eval_boundary -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/modelization/__init__.py`:

```python
from .routing_eval import ROUTE_TARGETS, RouteEvalExample, RouteEvalResult, RoutePrediction, score_route_predictions

__all__ = [
    ...,
    "ROUTE_TARGETS",
    "RouteEvalExample",
    "RouteEvalResult",
    "RoutePrediction",
    "score_route_predictions",
]
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_modelization_routing_eval.py tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/modelization/__init__.py tests/test_modelization_routing_eval.py
git commit -m "refactor: export routing policy eval boundary"
```

---

### Task 4: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused modelization tests**

Run: `uv run pytest tests/test_modelization_routing_eval.py tests/test_modelization_retrieval.py tests/test_modelization_corpus.py tests/test_modelization_repository_index.py -q`

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

Request blocker-focused code review for the routing eval boundary.

**Step 7: Finish branch**

Use the finishing branch process after review and verification.
