from christine.modelization.routing_eval import RouteEvalExample
from christine.modelization.routing_fixtures import ROUTING_EVAL_FIXTURES


def test_routing_eval_fixtures_are_stable_and_cover_core_targets():
    assert ROUTING_EVAL_FIXTURES == (
        RouteEvalExample("整理這個 repo 的架構", "repository"),
        RouteEvalExample("幫我看目前螢幕", "gui"),
        RouteEvalExample("開啟 runtime health check", "tools"),
        RouteEvalExample("你現在感覺如何", "brain"),
        RouteEvalExample("直接回答這句話", "direct"),
    )


def test_routing_eval_fixtures_have_unique_inputs():
    inputs = [example.input_text for example in ROUTING_EVAL_FIXTURES]

    assert len(inputs) == len(set(inputs))
