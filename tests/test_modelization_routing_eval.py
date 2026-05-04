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
