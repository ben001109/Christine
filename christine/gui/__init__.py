"""GUI contracts for Christine."""

from .app import GuiMessage, GuiQueues
from .host import GuiHost, GuiHostResult, GuiQueueBridge
from .presentation import format_chat_prefix
from .theme import GuiTheme, fallback_chat_theme, modern_dark_theme

__all__ = [
    "GuiMessage",
    "GuiQueues",
    "GuiHost",
    "GuiHostResult",
    "GuiQueueBridge",
    "GuiTheme",
    "fallback_chat_theme",
    "format_chat_prefix",
    "modern_dark_theme",
]
