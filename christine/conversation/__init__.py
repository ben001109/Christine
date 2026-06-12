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
from .session import (
    append_assistant_message,
    append_user_message,
    commit_assistant_turn,
    commit_conversation_turn,
    update_turn_memory,
)

__all__ = [
    "append_assistant_message",
    "append_user_message",
    "augment_input_with_hint",
    "build_recent_messages",
    "build_v10_system_prompt",
    "commit_assistant_turn",
    "commit_conversation_turn",
    "dedupe_tool_specs",
    "PolicyRouteResult",
    "RuntimeRouteObservation",
    "RuntimeRoutingHook",
    "observe_direct_runtime_route",
    "observe_runtime_route",
    "route_observed_voice_then_fallback",
    "route_voice_then_fallback",
    "route_with_policy",
    "update_turn_memory",
]
