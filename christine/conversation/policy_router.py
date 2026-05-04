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
