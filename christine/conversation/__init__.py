"""Conversation routing helpers for Christine's legacy ask chain."""

from .context import build_recent_messages, build_v10_system_prompt
from .policy_router import PolicyRouteResult, route_with_policy
from .router import (
    augment_input_with_hint,
    dedupe_tool_specs,
    route_observed_voice_then_fallback,
    route_voice_then_fallback,
)
from .runtime_routing_hook import (
    RuntimeRouteObservation,
    RuntimeRoutingHook,
    observe_direct_runtime_route,
    observe_runtime_route,
)

__all__ = [
    "augment_input_with_hint",
    "build_recent_messages",
    "build_v10_system_prompt",
    "dedupe_tool_specs",
    "PolicyRouteResult",
    "RuntimeRouteObservation",
    "RuntimeRoutingHook",
    "observe_direct_runtime_route",
    "observe_runtime_route",
    "route_observed_voice_then_fallback",
    "route_voice_then_fallback",
    "route_with_policy",
]
