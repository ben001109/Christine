from christine.conversation.runtime_routing_hook import RuntimeRoutingHook, observe_runtime_route
from christine.modelization import RoutePolicy, RoutePrediction


def test_disabled_runtime_routing_hook_returns_fallback_without_recording():
    records = []

    observation = observe_runtime_route(
        "整理 repo 架構",
        RoutePrediction("repository", "repo intent"),
        recorder=records.append,
    )

    assert observation.enabled is False
    assert observation.predicted_target == "repository"
    assert observation.target == "direct"
    assert observation.accepted is False
    assert observation.reason == "runtime-routing-disabled"
    assert records == []


def test_enabled_runtime_routing_hook_records_safe_policy_decision():
    records = []

    observation = observe_runtime_route(
        "整理 repo 架構",
        RoutePrediction("repository", "repo intent"),
        hook=RuntimeRoutingHook(enabled=True),
        recorder=records.append,
    )

    assert observation.enabled is True
    assert observation.target == "repository"
    assert observation.accepted is True
    assert observation.reason == "accepted"
    assert records == [observation]


def test_enabled_runtime_routing_hook_keeps_side_effect_targets_rejected_by_default():
    observation = observe_runtime_route(
        "開啟工具",
        RoutePrediction("tools", "tool intent"),
        hook=RuntimeRoutingHook(enabled=True),
    )

    assert observation.target == "direct"
    assert observation.accepted is False
    assert observation.reason == "rejected-side-effect-target:tools"


def test_enabled_runtime_routing_hook_can_use_explicit_policy_override():
    observation = observe_runtime_route(
        "看螢幕",
        RoutePrediction("gui", "screen intent"),
        hook=RuntimeRoutingHook(enabled=True, policy=RoutePolicy(allow_side_effect_targets=True)),
    )

    assert observation.target == "gui"
    assert observation.accepted is True


def test_conversation_exports_runtime_routing_hook():
    from christine.conversation import RuntimeRouteObservation, RuntimeRoutingHook, observe_runtime_route

    assert RuntimeRouteObservation.__name__ == "RuntimeRouteObservation"
    assert RuntimeRoutingHook.__name__ == "RuntimeRoutingHook"
    assert callable(observe_runtime_route)
