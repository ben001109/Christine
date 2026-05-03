# Christine Ask Routing Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the first safe `ask()` routing helpers from `christine_final.py` without changing Christine's conversation behavior.

**Architecture:** Keep the legacy `ask()` chain in `christine_final.py` intact, but move pure routing/data-shaping helpers into `christine.conversation.router`. Start with two stable seams: V10 tool-spec deduplication in the API-core `ask(inp)` and the final V1484 voice-first/brain-hint wrapper.

**Tech Stack:** Python 3.10+, stdlib callables/typing, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Preserve all existing `ask()` entry points and wrapper chaining behavior.
- Do not import `christine_final.py` from tests.
- Do not remove Chinese user-facing wording or personality behavior.
- Do not change Claude API request semantics, tool loop semantics, or model routing.
- Do not change persisted conversation/memory/state formats.
- Keep this wave limited to pure helpers and compatibility delegation.
- Avoid broad rewrites of `christine_final.py`.

## Current Facts

- The earliest V10 API-core `ask(inp)` starts at `christine_final.py:6037`.
- V10 chooses `_V142_TRIFLOW_TOOLS` or `pick(inp)`, then deduplicates tool specs at `christine_final.py:6042-6055` before choosing dialogue tier.
- The V1484 final ask wrapper starts around `christine_final.py:119722`.
- V1484 currently calls `_v180_try_voice(inp)` first, returns any non-`None` result, otherwise optionally prepends `brain_hint(as_prompt=True)` to the input before calling `_v180_prev_ask(augmented, *args, **kwargs)`.
- Many other `ask(inp)` definitions exist in the monolith; this wave should not try to normalize all of them.

## Out Of Scope

- Replacing the whole ask chain.
- Changing prompt construction, tool execution, or Claude API calls.
- Extracting tool registry modules.
- Extracting memory, brain, or GUI logic.
- Adding distributed routing or model policy routing.

---

### Task 1: Add Conversation Router Helper Tests

**Files:**
- Create: `christine/conversation/__init__.py`
- Create later: `christine/conversation/router.py`
- Create: `tests/test_conversation_router.py`

**Step 1: Write failing tests for tool deduplication**

Create `tests/test_conversation_router.py`:

```python
from christine.conversation.router import (
    augment_input_with_hint,
    dedupe_tool_specs,
    route_voice_then_fallback,
)


def test_dedupe_tool_specs_matches_legacy_name_priority():
    first = {"name": "capture_screen", "description": "old"}
    replacement = {"name": "capture_screen", "description": "new"}
    function_tool = {"function": {"name": "write_file"}, "description": "fn"}
    unnamed = {"description": "ignored legacy shape"}

    assert dedupe_tool_specs([first, function_tool, replacement, unnamed]) == [
        replacement,
        function_tool,
    ]
```

**Step 2: Write failing tests for brain hint augmentation**

```python
def test_augment_input_with_hint_preserves_legacy_newline_prefix():
    assert augment_input_with_hint("hello", "【Christine 大腦的即時感受】情緒=中性") == (
        "【Christine 大腦的即時感受】情緒=中性\nhello"
    )


def test_augment_input_with_hint_returns_original_when_disabled_or_empty():
    assert augment_input_with_hint("hello", "hint", enabled=False) == "hello"
    assert augment_input_with_hint("hello", "") == "hello"
    assert augment_input_with_hint("hello", None) == "hello"
```

**Step 3: Write failing tests for voice-first routing**

```python
def test_route_voice_then_fallback_returns_voice_result_without_fallback():
    calls = []

    def voice(inp):
        calls.append(("voice", inp))
        return "voice-result"

    def fallback(inp, *args, **kwargs):
        calls.append(("fallback", inp, args, kwargs))
        return "fallback-result"

    assert route_voice_then_fallback("hi", voice, fallback, lambda: "hint") == "voice-result"
    assert calls == [("voice", "hi")]


def test_route_voice_then_fallback_augments_before_fallback():
    seen = {}

    def fallback(inp, *args, **kwargs):
        seen["inp"] = inp
        seen["args"] = args
        seen["kwargs"] = kwargs
        return "fallback-result"

    result = route_voice_then_fallback(
        "hi",
        lambda inp: None,
        fallback,
        lambda: "hint",
        hybrid_enabled=True,
        args=("extra",),
        kwargs={"flag": True},
    )

    assert result == "fallback-result"
    assert seen == {"inp": "hint\nhi", "args": ("extra",), "kwargs": {"flag": True}}
```

**Step 4: Write failing test for hint-provider errors**

```python
def test_route_voice_then_fallback_ignores_hint_provider_errors():
    def broken_hint():
        raise RuntimeError("hint failed")

    seen = {}

    def fallback(inp):
        seen["inp"] = inp
        return "ok"

    assert route_voice_then_fallback("hi", lambda inp: None, fallback, broken_hint) == "ok"
    assert seen["inp"] == "hi"
```

**Step 5: Run RED**

Run: `uv run pytest tests/test_conversation_router.py -q`

Expected: fail with missing `christine.conversation` module.

---

### Task 2: Implement Pure Conversation Router Helpers

**Files:**
- Create: `christine/conversation/__init__.py`
- Create: `christine/conversation/router.py`
- Modify: `tests/test_conversation_router.py` only if needed for import/style.

**Step 1: Create package init**

Create `christine/conversation/__init__.py`:

```python
"""Conversation routing helpers for Christine's legacy ask chain."""

from .router import augment_input_with_hint, dedupe_tool_specs, route_voice_then_fallback

__all__ = ["augment_input_with_hint", "dedupe_tool_specs", "route_voice_then_fallback"]
```

**Step 2: Implement `dedupe_tool_specs`**

Create `christine/conversation/router.py`:

```python
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def _tool_name(tool: Any) -> str:
    if not isinstance(tool, dict):
        return ""
    return str(tool.get("name") or tool.get("function", {}).get("name", ""))


def dedupe_tool_specs(tools: Iterable[Any]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = _tool_name(tool)
        if name:
            seen[name] = tool
    return list(seen.values())
```

This intentionally preserves the legacy dict behavior: first insertion order, later duplicate value replacement.

**Step 3: Implement `augment_input_with_hint`**

Add:

```python
def augment_input_with_hint(inp: Any, hint: str | None, enabled: bool = True) -> Any:
    if not enabled or not hint:
        return inp
    return f"{hint}\n{inp}"
```

**Step 4: Implement `route_voice_then_fallback`**

Add:

```python
def route_voice_then_fallback(
    inp: Any,
    voice_handler: Callable[[Any], Any],
    fallback: Callable[..., Any],
    hint_provider: Callable[[], str | None] | None = None,
    hybrid_enabled: bool = True,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> Any:
    routed = voice_handler(inp)
    if routed is not None:
        return routed
    hint = None
    if hybrid_enabled and hint_provider is not None:
        try:
            hint = hint_provider()
        except Exception:
            hint = None
    augmented = augment_input_with_hint(inp, hint, enabled=hybrid_enabled)
    return fallback(augmented, *args, **(kwargs or {}))
```

**Step 5: Run focused tests**

Run: `uv run pytest tests/test_conversation_router.py -q`

Expected: pass.

**Step 6: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 7: Commit**

Commit message: `refactor: add conversation routing helpers`

---

### Task 3: Delegate V10 Tool Deduplication To Router Helper

**Files:**
- Modify: `christine_final.py:6037-6055`
- Create or modify: `tests/test_ask_routing_monolith.py`

**Step 1: Add static smoke test for V10 helper usage**

Create `tests/test_ask_routing_monolith.py`:

```python
from pathlib import Path


def _v10_ask_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V10 ask()")
    end = text.index("# ╔", start + 1)
    return text[start:end]


def test_v10_ask_uses_router_tool_dedupe_helper():
    block = _v10_ask_block()

    assert "from christine.conversation.router import" in block
    assert "dedupe_tool_specs" in block
    assert "tools = dedupe_tool_specs(tools)" in block
    assert "_seen_names" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_ask_routing_monolith.py -q`

Expected: fail because V10 still contains inline `_seen_names` dedupe.

**Step 3: Import helper near the V10 block**

Add near the V10 ask block, before `def ask(inp):`:

```python
from christine.conversation.router import dedupe_tool_specs
```

**Step 4: Replace inline dedupe only**

Replace:

```python
    _seen_names={}
    for _t in tools:
        if isinstance(_t,dict):
            _n=_t.get('name') or _t.get('function',{}).get('name','')
            if _n: _seen_names[_n]=_t
    tools=list(_seen_names.values())
```

With:

```python
    tools = dedupe_tool_specs(tools)
```

Do not change any prompt, route tier, model, or tool loop code.

**Step 5: Verify focused tests**

Run: `uv run pytest tests/test_conversation_router.py tests/test_ask_routing_monolith.py -q`

Expected: pass.

**Step 6: Verify boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: pass.

**Step 7: Commit**

Commit message: `refactor: delegate ask tool dedupe`

---

### Task 4: Delegate V1484 Voice/Hint Wrapper To Router Helper

**Files:**
- Modify: `christine_final.py:119722-119741`
- Modify: `tests/test_ask_routing_monolith.py`

**Step 1: Add static smoke test for V1484 wrapper helper usage**

Add to `tests/test_ask_routing_monolith.py`:

```python
def _v1484_ask_wrapper_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("_v180_prev_ask = globals().get(\"ask\")")
    end = text.index("ask.__v180_wrapped__ = True", start)
    return text[start:end]


def test_v1484_ask_wrapper_uses_router_voice_hint_helper():
    block = _v1484_ask_wrapper_block()

    assert "route_voice_then_fallback" in block
    assert "_v180_try_voice" in block
    assert "_v180_prev_ask" in block
    assert "brain_hint(as_prompt=True)" in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_ask_routing_monolith.py -q`

Expected: fail because V1484 still has inline voice/hint routing.

**Step 3: Extend router import near V1484 block**

Inside the V1480/V1484 try block, add:

```python
    from christine.conversation.router import route_voice_then_fallback
```

**Step 4: Replace only the inner V1484 `ask` body**

Replace the body of the V1484 wrapper with:

```python
        def ask(inp, *args, **kwargs):
            return route_voice_then_fallback(
                inp,
                _v180_try_voice,
                _v180_prev_ask,
                lambda: brain_hint(as_prompt=True),
                hybrid_enabled=_V1480_CFG.get("hybrid", True),
                args=args,
                kwargs=kwargs,
            )
```

Do not remove `ask.__v180_wrapped__ = True` or `globals()["ask"] = ask`.

**Step 5: Verify focused tests**

Run: `uv run pytest tests/test_conversation_router.py tests/test_ask_routing_monolith.py tests/test_brain_bridge_monolith.py -q`

Expected: pass.

**Step 6: Verify compile and boot smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: both pass.

**Step 7: Commit**

Commit message: `refactor: delegate V1484 ask wrapper`

---

### Task 5: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_conversation_router.py tests/test_ask_routing_monolith.py tests/test_brain_bridge_monolith.py -q`

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

- V10 tool dedupe behavior preserved.
- V1484 voice-first behavior preserved.
- V1484 brain hint prefix behavior preserved.
- No `christine_final.py` import in tests.
- No broad ask-chain rewrite.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_conversation_router.py tests/test_ask_routing_monolith.py tests/test_brain_bridge_monolith.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if ask routing changes regress.
- Do not modify persisted conversation, memory, or state files.
- Do not remove legacy `ask()` definitions in this wave.
- If V1484 delegation is risky, keep `christine.conversation.router` and V10 dedupe extraction, then revert only the V1484 delegation commit.
