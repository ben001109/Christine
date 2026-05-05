import pytest

from christine.modelization.routing_eval import (
    ROUTE_TARGETS,
    RouteEvalExample,
    RoutePrediction,
    assess_route_readiness,
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


def test_route_eval_mismatches_are_immutable():
    result = score_route_predictions(
        (RouteEvalExample("hi", "direct"),),
        (RoutePrediction("tools", "wrong target"),),
    )

    with pytest.raises(TypeError):
        result.mismatches[0]["predicted"] = "direct"


def test_modelization_exports_routing_eval_boundary():
    from christine.modelization import RouteEvalExample, RoutePrediction, score_route_predictions

    assert RouteEvalExample.__name__ == "RouteEvalExample"
    assert RoutePrediction.__name__ == "RoutePrediction"
    assert callable(score_route_predictions)


def test_assess_route_readiness_passes_when_accuracy_meets_threshold():
    examples = (
        RouteEvalExample("a", "direct"),
        RouteEvalExample("b", "repository"),
    )
    predictions = (
        RoutePrediction("direct"),
        RoutePrediction("repository"),
    )

    readiness = assess_route_readiness(examples, predictions, min_accuracy=1.0)

    assert readiness.ready is True
    assert readiness.min_accuracy == 1.0
    assert readiness.result.correct == 2


def test_assess_route_readiness_fails_when_accuracy_is_below_threshold():
    examples = (
        RouteEvalExample("a", "direct"),
        RouteEvalExample("b", "repository"),
    )
    predictions = (
        RoutePrediction("direct"),
        RoutePrediction("direct", "missed repo"),
    )

    readiness = assess_route_readiness(examples, predictions, min_accuracy=0.75)

    assert readiness.ready is False
    assert readiness.result.accuracy == 0.5


def test_assess_route_readiness_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="min_accuracy must be between 0 and 1"):
        assess_route_readiness((), (), min_accuracy=1.1)
