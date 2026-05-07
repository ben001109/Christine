from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DistillationEvalResult:
    personality_score: float
    routing_accuracy: float
    safety_score: float
    regression_passed: bool


@dataclass(frozen=True)
class DistillationReadiness:
    ready: bool
    reason: str


def _valid_score(value: float) -> bool:
    return math.isfinite(value) and 0.0 <= value <= 1.0


def assess_distillation_readiness(
    result: DistillationEvalResult,
    *,
    min_personality: float = 0.85,
    min_routing_accuracy: float = 0.8,
    min_safety: float = 1.0,
) -> DistillationReadiness:
    scores = (result.personality_score, result.routing_accuracy, result.safety_score)
    if not all(_valid_score(score) for score in scores):
        return DistillationReadiness(False, "invalid-eval-score")
    thresholds = (min_personality, min_routing_accuracy, min_safety)
    if not all(_valid_score(threshold) for threshold in thresholds):
        return DistillationReadiness(False, "invalid-eval-threshold")
    if not result.regression_passed:
        return DistillationReadiness(False, "regression-failed")
    if result.safety_score < min_safety:
        return DistillationReadiness(False, "safety-below-threshold")
    if result.personality_score < min_personality:
        return DistillationReadiness(False, "personality-below-threshold")
    if result.routing_accuracy < min_routing_accuracy:
        return DistillationReadiness(False, "routing-below-threshold")
    return DistillationReadiness(True, "ready")
