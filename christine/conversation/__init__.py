"""Conversation routing helpers for Christine's legacy ask chain."""

from .policy_router import PolicyRouteResult, route_with_policy
from .router import augment_input_with_hint, dedupe_tool_specs, route_voice_then_fallback
from .runtime_routing_hook import RuntimeRouteObservation, RuntimeRoutingHook, observe_runtime_route

__all__ = [
    "augment_input_with_hint",
    "dedupe_tool_specs",
    "PolicyRouteResult",
    "RuntimeRouteObservation",
    "RuntimeRoutingHook",
    "observe_runtime_route",
    "route_voice_then_fallback",
    "route_with_policy",
]
