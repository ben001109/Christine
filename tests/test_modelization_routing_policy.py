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


def test_modelization_exports_routing_policy_gate():
    from christine.modelization import RoutePolicy, RoutePolicyDecision, apply_route_policy

    assert RoutePolicy.__name__ == "RoutePolicy"
    assert RoutePolicyDecision.__name__ == "RoutePolicyDecision"
    assert callable(apply_route_policy)
