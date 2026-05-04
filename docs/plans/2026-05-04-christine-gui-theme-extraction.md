# Christine GUI Theme Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Start GUI modernization safely by extracting theme tokens and message presentation helpers without changing Christine's Tkinter launch behavior.

**Architecture:** Add pure GUI presentation modules under `christine.gui`: `theme.py` for named color/font/spacing tokens and `presentation.py` for message label formatting. Keep Tkinter construction inside `christine_final.py` for this wave, but delegate selected hard-coded theme dictionaries and message labels through the new pure helpers.

**Tech Stack:** Python 3.10+, stdlib dataclasses/typing, Tkinter remains legacy runtime dependency, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Preserve existing GUI entry points: `launch_chat_window()` and `close_chat_window()`.
- Do not import `christine_final.py` from tests.
- Do not open Tkinter windows in tests.
- Do not remove Chinese user-facing wording, personality, or emotional semantics.
- Do not rewrite V600 UI layout in this wave.
- Keep fallback GUI and V600 Modern UI behavior compatible with existing queue adapters.
- Prefer pure, testable modules before broader UI/UX changes.

## Current Facts

- `christine/gui/app.py` owns `GuiQueues` and legacy queue adapters.
- `christine/gui/commands.py` owns raw GUI command processing.
- `christine/gui/tk_app.py` is currently a placeholder exporting queue contracts.
- `christine_final.py:1864-1963` contains fallback Tkinter chat window creation with hard-coded pink theme values.
- `christine_final.py:104520-104699` contains V600 Modern UI widgets using a `self._theme` dictionary.
- Existing tests in `tests/test_gui_contract.py` avoid opening windows and use static monolith checks.

## Out Of Scope

- Moving `launch_chat_window()` out of `christine_final.py`.
- Replacing the V600 layout.
- Adding screenshots, visual regression testing, or image comparison.
- Changing queue semantics, ask routing, or GUI command handling.
- Introducing a new GUI framework.

---

### Task 1: Add GUI Theme And Presentation Tests

**Files:**
- Create: `tests/test_gui_theme.py`
- Create later: `christine/gui/theme.py`
- Create later: `christine/gui/presentation.py`

**Step 1: Write failing theme tests**

Create `tests/test_gui_theme.py`:

```python
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
```

**Step 2: Write failing message formatting test**

```python
def test_format_chat_prefix_preserves_legacy_labels():
    assert format_chat_prefix("user") == "\n🧑 You: "
    assert format_chat_prefix("assistant") == "\n♡ Christine: "
    assert format_chat_prefix("system") == ""
```

**Step 3: Run RED**

Run: `uv run pytest tests/test_gui_theme.py -q`

Expected: fail with missing `christine.gui.theme` or `christine.gui.presentation`.

---

### Task 2: Implement Pure GUI Theme And Presentation Modules

**Files:**
- Create: `christine/gui/theme.py`
- Create: `christine/gui/presentation.py`
- Modify: `christine/gui/__init__.py`
- Modify: `christine/gui/tk_app.py`
- Modify: `tests/test_gui_theme.py` only if needed for import/style.

**Step 1: Implement theme dataclass and fallback tokens**

Create `christine/gui/theme.py`:

```python
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
```

**Step 2: Implement V600 token function**

Add to `theme.py`:

```python
def modern_dark_theme() -> GuiTheme:
    return GuiTheme(
        name="v600-dark",
        colors={
            "bg_main": "#0f0f1e",
            "bg_sidebar": "#151528",
            "bg_chat": "#0b0b17",
            "bg_input": "#1a1a2e",
            "text_primary": "#f5f5ff",
            "text_secondary": "#c9c7ff",
            "text_muted": "#7f7aa8",
            "accent_pink": "#ff69b4",
            "accent_purple": "#9b5cff",
            "accent_blue": "#6ab7ff",
            "accent_green": "#7ee787",
            "border": "#2b2b45",
        },
        fonts={
            "body": ("Segoe UI", 11),
            "small": ("Segoe UI", 9),
            "mono_small": ("Consolas", 8),
            "title": ("Segoe UI", 12, "bold"),
        },
        spacing={"outer_pad": 10, "inner_pad": 5, "sidebar_width": 210},
    )
```

If the exact existing V600 `_theme` values differ after inspection, use existing values instead of invented ones.

**Step 3: Implement presentation helper**

Create `christine/gui/presentation.py`:

```python
def format_chat_prefix(role: str) -> str:
    if role == "user":
        return "\n🧑 You: "
    if role == "assistant":
        return "\n♡ Christine: "
    return ""
```

**Step 4: Export modules**

Modify `christine/gui/__init__.py`:

```python
"""GUI contracts for Christine."""

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
```

Modify `christine/gui/tk_app.py` similarly if useful to expose these seam helpers for future Tkinter extraction.

**Step 5: Run focused tests**

Run: `uv run pytest tests/test_gui_theme.py tests/test_gui_contract.py -q`

Expected: pass.

**Step 6: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 7: Commit**

Commit message: `refactor: add GUI theme contracts`

---

### Task 3: Delegate Fallback GUI Theme Tokens

**Files:**
- Modify: `christine_final.py:1864-1963`
- Modify: `tests/test_gui_theme.py`

**Step 1: Add static monolith smoke test**

Append to `tests/test_gui_theme.py`:

```python
from pathlib import Path


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
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_gui_theme.py -q`

Expected: fail because fallback GUI still uses inline colors and message prefixes.

**Step 3: Import helpers near GUI seam**

Near existing GUI imports in `christine_final.py`, add:

```python
from christine.gui.presentation import format_chat_prefix
from christine.gui.theme import fallback_chat_theme
```

If imports are already grouped near `create_legacy_queue_adapters`, place them there.

**Step 4: Instantiate theme inside fallback `_run`**

Inside `_run()`, before creating `win`, add:

```python
        _fallback_theme = fallback_chat_theme()
        _colors = _fallback_theme.colors
        _fonts = _fallback_theme.fonts
```

**Step 5: Replace selected hard-coded fallback values**

Replace only selected obvious values:

- `win.configure(bg="#fff0f5")` -> `win.configure(bg=_colors["window_bg"])`
- title bar frame/label `bg`/`fg` -> `_colors["title_bg"]`, `_colors["title_fg"]`
- close button `bg`/active bg -> `_colors["close_bg"]`, `_colors["close_active_bg"]`
- chat display bg/fg/select -> `_colors["chat_bg"]`, `_colors["chat_fg"]`, `_colors["select_bg"]`
- input shell bg -> `_colors["input_shell_bg"]`
- chat tags -> `_colors["user_fg"]`, `_colors["assistant_fg"]`, `_colors["system_fg"]`

Do not change layout, queue behavior, window title, or Chinese strings.

**Step 6: Replace fallback message prefixes only**

In `ac(who, text)`, replace hard-coded prefixes with:

```python
            if who=="u": cd.insert("end", format_chat_prefix("user"), "u"); cd.insert("end",text+"\n")
            elif who=="c": cd.insert("end", format_chat_prefix("assistant"), "c"); cd.insert("end",text+"\n")
```

Keep the system branch unchanged.

**Step 7: Run focused tests**

Run: `uv run pytest tests/test_gui_theme.py tests/test_gui_contract.py -q`

Expected: pass.

**Step 8: Run compile and boot smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: both pass.

**Step 9: Commit**

Commit message: `refactor: delegate fallback GUI theme tokens`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_gui_theme.py tests/test_gui_contract.py -q`

Expected: pass.

**Step 2: Run full test suite**

Run: `uv run pytest -q`

Expected: pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: pass.

**Step 4: Run boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass and print `自檢完成`.

**Step 5: Run whitespace diff check**

Run: `git diff --check`

Expected: no output.

**Step 6: Request code review**

Review requirements:

- No Tkinter windows opened in tests.
- GUI queue behavior unchanged.
- Fallback GUI user-facing Chinese wording preserved.
- `launch_chat_window()` and `close_chat_window()` entry points preserved.
- No broad V600 rewrite.
- No new dependencies.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_gui_theme.py tests/test_gui_contract.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if GUI behavior regresses.
- Do not alter runtime state artifacts.
- Do not change GUI command queues or ask routing in this wave.
- If theme delegation causes risk, keep `christine.gui.theme` and revert only the `christine_final.py` delegation commit.
