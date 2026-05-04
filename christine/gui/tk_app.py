"""Tkinter integration placeholder for the legacy GUI extraction seam."""

from .app import GuiMessage, GuiQueues
from .presentation import format_chat_prefix
from .theme import GuiTheme, fallback_chat_theme, modern_dark_theme

__all__ = [
    "GuiMessage",
    "GuiQueues",
    "GuiTheme",
    "fallback_chat_theme",
    "format_chat_prefix",
    "modern_dark_theme",
]
