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
