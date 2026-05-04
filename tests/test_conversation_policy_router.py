import pytest

from christine.conversation.policy_router import route_with_policy
from christine.modelization import RoutePolicy, RoutePrediction


def test_route_with_policy_dispatches_accepted_safe_prediction():
    calls = []

    def repository_handler(inp):
        calls.append(("repository", inp))
        return "repo-result"

    result = route_with_policy(
        "整理 repo 架構",
        RoutePrediction("repository", "repo question"),
        handlers={"repository": repository_handler},
        fallback=lambda inp: "fallback",
    )

    assert result.target == "repository"
    assert result.accepted is True
    assert result.reason == "accepted"
    assert result.value == "repo-result"
    assert calls == [("repository", "整理 repo 架構")]


def test_route_with_policy_rejects_side_effect_prediction_to_fallback():
    calls = []

    def tool_handler(inp):
        calls.append(("tools", inp))
        return "tool-result"

    result = route_with_policy(
        "開啟工具",
        RoutePrediction("tools", "tool intent"),
        handlers={"tools": tool_handler},
        fallback=lambda inp: "fallback-result",
    )

    assert result.target == "direct"
    assert result.accepted is False
    assert result.reason == "rejected-side-effect-target:tools"
    assert result.value == "fallback-result"
    assert calls == []


def test_route_with_policy_can_opt_into_side_effect_dispatch():
    result = route_with_policy(
        "看螢幕",
        RoutePrediction("gui", "screen command"),
        handlers={"gui": lambda inp: "gui-result"},
        fallback=lambda inp: "fallback",
        policy=RoutePolicy(allow_side_effect_targets=True),
    )

    assert result.target == "gui"
    assert result.accepted is True
    assert result.value == "gui-result"


def test_route_with_policy_uses_fallback_when_target_handler_missing():
    result = route_with_policy(
        "hello",
        RoutePrediction("repository", "repo question"),
        handlers={},
        fallback=lambda inp: "fallback-result",
    )

    assert result.target == "direct"
    assert result.accepted is False
    assert result.reason == "missing-handler:repository"
    assert result.value == "fallback-result"


def test_route_with_policy_rejects_unknown_prediction_targets():
    with pytest.raises(ValueError, match="unknown route target"):
        route_with_policy(
            "hello",
            RoutePrediction("unknown", "bad target"),
            handlers={},
            fallback=lambda inp: "fallback",
        )


def test_conversation_exports_policy_router():
    from christine.conversation import PolicyRouteResult, route_with_policy

    assert PolicyRouteResult.__name__ == "PolicyRouteResult"
    assert callable(route_with_policy)
