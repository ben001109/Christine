# Observed Ask Routing Helper Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the V1484 ask wrapper's "observe runtime route, then voice/hint/fallback" orchestration into a small pure conversation router helper without changing Christine's responses.

**Architecture:** Keep `christine_final.py` as the runtime entry point and keep disabled runtime route observation disabled. Add `route_observed_voice_then_fallback()` beside `route_voice_then_fallback()` so the monolith only supplies callbacks and configuration; the helper observes first, ignores observer failures, then delegates to the existing voice/hint/fallback path.

**Tech Stack:** Python 3.10+, existing `christine.conversation.router`, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve current `ask()` output and wrapper chaining.
- Preserve V1484 voice command priority and existing hybrid hint injection behavior.
- Keep runtime routing observation disabled by default.
- Do not wire `route_with_policy()` or live policy dispatch into `christine_final.py`.
- Do not enable `allow_side_effect_targets=True` in the monolith.
- Do not persist logs, write runtime state, add dependencies, or change launcher behavior.
- Do not import `christine_final.py` from tests.

## Non-Goals

- No live route switching.
- No route prediction model call.
- No tool, GUI, or worker dispatch from the routing policy.
- No broad rewrite of V1484 brain logic.
- No changes to Chinese user-facing command text.

---

### Task 1: Add Observed Voice/Fallback Helper Tests

**Files:**
- Modify: `tests/test_conversation_router.py`

**Step 1: Write failing tests**

Extend imports:

```python
from christine.conversation.router import (
    augment_input_with_hint,
    dedupe_tool_specs,
    route_observed_voice_then_fallback,
    route_voice_then_fallback,
)
```

Add:

```python
def test_route_observed_voice_then_fallback_observes_before_voice():
    calls = []

    def observer(inp):
        calls.append(("observe", inp))

    def voice(inp):
        calls.append(("voice", inp))
        return "voice-result"

    def fallback(inp):
        calls.append(("fallback", inp))
        return "fallback-result"

    result = route_observed_voice_then_fallback("hi", observer, voice, fallback, lambda: "hint")

    assert result == "voice-result"
    assert calls == [("observe", "hi"), ("voice", "hi")]


def test_route_observed_voice_then_fallback_ignores_observer_errors():
    calls = []

    def observer(inp):
        calls.append(("observe", inp))
        raise RuntimeError("routing observation failed")

    def fallback(inp, *args, **kwargs):
        calls.append(("fallback", inp, args, kwargs))
        return "fallback-result"

    result = route_observed_voice_then_fallback(
        "hi",
        observer,
        lambda inp: None,
        fallback,
        lambda: "hint",
        hybrid_enabled=True,
        args=("extra",),
        kwargs={"flag": True},
    )

    assert result == "fallback-result"
    assert calls == [("observe", "hi"), ("fallback", "hint\nhi", ("extra",), {"flag": True})]
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_router.py -q`

Expected: FAIL because `route_observed_voice_then_fallback` does not exist.

---

### Task 2: Implement Observed Voice/Fallback Helper

**Files:**
- Modify: `christine/conversation/router.py`
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_router.py`

**Step 1: Add minimal helper**

Add to `christine/conversation/router.py` after `route_voice_then_fallback()`:

```python
def route_observed_voice_then_fallback(
    inp: Any,
    route_observer: Callable[[Any], Any],
    voice_handler: Callable[[Any], Any],
    fallback: Callable[..., Any],
    hint_provider: Callable[[], str | None] | None = None,
    hybrid_enabled: bool = True,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> Any:
    try:
        route_observer(inp)
    except Exception:
        pass
    return route_voice_then_fallback(
        inp,
        voice_handler,
        fallback,
        hint_provider,
        hybrid_enabled=hybrid_enabled,
        args=args,
        kwargs=kwargs,
    )
```

Export it from `christine/conversation/__init__.py`.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_conversation_router.py -q`

Expected: PASS.

**Step 3: Commit**

Run: `git add christine/conversation/router.py christine/conversation/__init__.py tests/test_conversation_router.py && git commit -m "refactor: add observed ask routing helper"`

---

### Task 3: Delegate V1484 Ask Wrapper To Helper

**Files:**
- Modify: `christine_final.py`
- Modify: `tests/test_ask_routing_monolith.py`
- Test: `tests/test_ask_routing_monolith.py`

**Step 1: Update static guard**

In `tests/test_ask_routing_monolith.py`, replace the V1484 helper assertion to require `route_observed_voice_then_fallback` and to reject the old direct observation call inside `ask()`:

```python
def test_v1484_ask_wrapper_uses_observed_router_voice_hint_helper():
    block = _v1484_ask_wrapper_block()

    assert "route_observed_voice_then_fallback" in block
    assert "_v180_try_voice" in block
    assert "_v180_prev_ask" in block
    assert "brain_hint(as_prompt=True)" in block
    assert "_v180_observe_runtime_route(inp)" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_ask_routing_monolith.py -q`

Expected: FAIL because the monolith still uses `route_voice_then_fallback()` and directly observes before it.

**Step 3: Update V1484 import and call**

In `christine_final.py`, change:

```python
from christine.conversation.router import route_voice_then_fallback
```

to:

```python
from christine.conversation.router import route_observed_voice_then_fallback
```

Then replace the direct observation call plus router call with:

```python
return route_observed_voice_then_fallback(
    inp,
    _v180_observe_runtime_route,
    _voice_handler,
    _v180_prev_ask,
    lambda: brain_hint(as_prompt=True),
    hybrid_enabled=_V1480_CFG.get("hybrid", True),
    args=args,
    kwargs=kwargs,
)
```

Keep `_v180_observe_runtime_route()` itself so the disabled hook and debug logging remain local to the monolith.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_ask_routing_monolith.py tests/test_runtime_routing_integration_guard.py tests/test_conversation_router.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine_final.py tests/test_ask_routing_monolith.py && git commit -m "refactor: delegate observed ask routing"`

---

### Task 4: Final Verification And Review

**Files:**
- No planned edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_conversation_router.py tests/test_ask_routing_monolith.py tests/test_runtime_routing_integration_guard.py tests/test_conversation_runtime_routing_hook.py tests/test_boot_contract.py -q`

Expected: PASS.

**Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: PASS.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 3: Request review**

Request blocker-focused review for:
- `christine/conversation/router.py`
- `christine/conversation/__init__.py`
- `christine_final.py`
- `tests/test_conversation_router.py`
- `tests/test_ask_routing_monolith.py`

**Step 4: Finish branch**

If review has no blocking findings, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
