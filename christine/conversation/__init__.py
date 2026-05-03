"""Conversation routing helpers for Christine's legacy ask chain."""

from .router import augment_input_with_hint, dedupe_tool_specs, route_voice_then_fallback

__all__ = ["augment_input_with_hint", "dedupe_tool_specs", "route_voice_then_fallback"]
