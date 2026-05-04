from pathlib import Path

from christine.gui.presentation import format_chat_prefix
from christine.gui.theme import GuiTheme, fallback_chat_theme, modern_dark_theme


def test_fallback_chat_theme_preserves_legacy_pink_tokens():
    theme = fallback_chat_theme()

    assert isinstance(theme, GuiTheme)
    assert theme.name == "legacy-pink"
    assert theme.colors["window_bg"] == "#fff0f5"
    assert theme.colors["title_bg"] == "#ffb6c1"
    assert theme.colors["title_fg"] == "#d63384"
    assert theme.fonts["body"] == ("Segoe UI", 10)


def test_modern_dark_theme_contains_v600_tokens():
    theme = modern_dark_theme()

    assert theme.name == "v600-dark"
    for key in ("bg_main", "bg_sidebar", "bg_chat", "bg_input", "text_primary", "accent_pink"):
        assert key in theme.colors


def test_format_chat_prefix_preserves_legacy_labels():
    assert format_chat_prefix("user") == "\n🧑 You: "
    assert format_chat_prefix("assistant") == "\n♡ Christine: "
    assert format_chat_prefix("system") == ""


def _fallback_gui_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("def launch_chat_window():")
    end = text.index("def close_chat_window():", start)
    return text[start:end]


def test_fallback_gui_uses_theme_and_prefix_helpers():
    block = _fallback_gui_block()

    assert "fallback_chat_theme()" in block
    assert "format_chat_prefix(" in block
    assert "_fallback_theme.colors" in block
