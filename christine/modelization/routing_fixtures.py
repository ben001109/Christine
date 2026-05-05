from __future__ import annotations

from .routing_eval import RouteEvalExample


ROUTING_EVAL_FIXTURES = (
    RouteEvalExample("整理這個 repo 的架構", "repository"),
    RouteEvalExample("幫我看目前螢幕", "gui"),
    RouteEvalExample("開啟 runtime health check", "tools"),
    RouteEvalExample("你現在感覺如何", "brain"),
    RouteEvalExample("直接回答這句話", "direct"),
)
