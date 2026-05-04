from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuiTheme:
    name: str
    colors: dict[str, str]
    fonts: dict[str, tuple]
    spacing: dict[str, int]


def fallback_chat_theme() -> GuiTheme:
    return GuiTheme(
        name="legacy-pink",
        colors={
            "window_bg": "#fff0f5",
            "title_bg": "#ffb6c1",
            "title_fg": "#d63384",
            "close_bg": "#ff69b4",
            "close_active_bg": "#ff1493",
            "chat_bg": "#fff5f8",
            "chat_fg": "#4a4a4a",
            "input_shell_bg": "#ffe4e1",
            "select_bg": "#ffc0cb",
            "user_fg": "#6a5acd",
            "assistant_fg": "#d63384",
            "system_fg": "#c0c0c0",
            "button_bg": "#fce4ec",
            "send_bg": "#ffb6c1",
        },
        fonts={
            "title": ("Segoe UI", 12, "bold"),
            "body": ("Segoe UI", 10),
            "input": ("Segoe UI", 11),
            "button": ("Segoe UI", 9),
            "button_bold": ("Segoe UI", 10, "bold"),
            "system": ("Segoe UI", 9),
        },
        spacing={"outer_pad": 10, "inner_pad": 6, "button_padx": 10, "button_pady": 4},
    )


def modern_dark_theme() -> GuiTheme:
    return GuiTheme(
        name="v600-dark",
        colors={
            "bg_main": "#1a1a2e",
            "bg_sidebar": "#16213e",
            "bg_chat": "#1e1e3a",
            "bg_input": "#262650",
            "bg_user_bubble": "#4a3f6b",
            "bg_bot_bubble": "#2d2d5e",
            "accent_pink": "#ff6b9d",
            "accent_purple": "#c084fc",
            "accent_blue": "#60a5fa",
            "accent_green": "#4ade80",
            "accent_red": "#f87171",
            "text_primary": "#e2e8f0",
            "text_secondary": "#94a3b8",
            "text_muted": "#64748b",
            "border": "#334155",
        },
        fonts={
            "body": ("Segoe UI", 11),
            "small": ("Segoe UI", 9),
            "mono_small": ("Consolas", 8),
            "title": ("Segoe UI", 12, "bold"),
        },
        spacing={"outer_pad": 10, "inner_pad": 5, "sidebar_width": 210},
    )
