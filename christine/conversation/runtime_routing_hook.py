from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from christine.modelization.routing_eval import ROUTE_TARGETS, RoutePrediction
from christine.modelization.routing_policy import RoutePolicy, apply_route_policy


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


def _validate_target(target: str) -> None:
    if target not in ROUTE_TARGETS:
        raise ValueError(f"unknown route target: {target}")


def observe_runtime_route(
    input_text: str,
    prediction: RoutePrediction,
    *,
    hook: RuntimeRoutingHook = RuntimeRoutingHook(),
    recorder: Callable[[RuntimeRouteObservation], None] | None = None,
) -> RuntimeRouteObservation:
    if not hook.enabled:
        _validate_target(hook.policy.fallback_target)
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


def observe_direct_runtime_route(
    input_text: str,
    *,
    hook: RuntimeRoutingHook = RuntimeRoutingHook(),
    recorder: Callable[[RuntimeRouteObservation], None] | None = None,
) -> RuntimeRouteObservation:
    return observe_runtime_route(
        input_text,
        RoutePrediction("direct", "legacy ask wrapper"),
        hook=hook,
        recorder=recorder,
    )
