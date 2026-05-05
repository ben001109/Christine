from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


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
    mismatches: tuple[Mapping[str, object], ...]

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.correct / self.total


@dataclass(frozen=True)
class RouteReadiness:
    ready: bool
    min_accuracy: float
    result: RouteEvalResult


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
    mismatches: list[Mapping[str, object]] = []
    for index, (example, prediction) in enumerate(zip(examples, predictions, strict=True)):
        _validate_target(example.expected_target)
        _validate_target(prediction.target)
        if prediction.target == example.expected_target:
            correct += 1
            continue
        mismatches.append(
            MappingProxyType(
                {
                    "index": index,
                    "input_text": example.input_text,
                    "expected": example.expected_target,
                    "predicted": prediction.target,
                    "reason": prediction.reason,
                }
            )
        )
    return RouteEvalResult(total=len(examples), correct=correct, mismatches=tuple(mismatches))


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
