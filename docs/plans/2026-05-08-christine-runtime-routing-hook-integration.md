# Runtime Routing Hook Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a disabled-by-default runtime routing observation seam inside the legacy ask wrapper without changing Christine's conversation output or executing side effects.

**Architecture:** Keep `christine_final.py` as the runtime entry point and keep the existing `route_voice_then_fallback()` behavior intact. Add a pure direct-route observation helper under `christine.conversation.runtime_routing_hook`, then call it from the V1484 ask wrapper through a disabled `RuntimeRoutingHook`; the call must be best-effort and must not affect responses, tool execution, GUI, worker, memory, or files.

**Tech Stack:** Python 3.10+, dataclasses, existing `christine.conversation` and `christine.modelization` modules, uv, pytest.

---

## Requirements Captured

- Preserve `boot_christine.py`, `christine_final.py`, and Windows launcher behavior.
- Preserve current `ask()` output and wrapper chaining.
- Do not enable live policy dispatch or `route_with_policy()` in the monolith.
- Keep `tools`, `gui`, and `worker` side-effect routes rejected by default.
- Do not persist logs, write state, add model inference, add cloud calls, or add dependencies.
- Keep the runtime hook disabled by default and best-effort only.

## Non-Goals

- No live route switching.
- No model route prediction.
- No persistent routing logs.
- No tool/GUI/worker dispatch through policy router.
- No broad rewrite of `ask()`.

---

### Task 1: Add Direct Runtime Observation Helper

**Files:**
- Modify: `christine/conversation/runtime_routing_hook.py`
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_runtime_routing_hook.py`

**Step 1: Write failing tests**

Add to `tests/test_conversation_runtime_routing_hook.py`:

```python
def test_direct_runtime_route_observation_defaults_to_disabled_direct_fallback():
    records = []

    observation = observe_direct_runtime_route("hello", recorder=records.append)

    assert observation.enabled is False
    assert observation.predicted_target == "direct"
    assert observation.target == "direct"
    assert observation.accepted is False
    assert observation.reason == "runtime-routing-disabled"
    assert records == []


def test_enabled_direct_runtime_route_observation_records_accepted_direct_route():
    records = []

    observation = observe_direct_runtime_route(
        "hello",
        hook=RuntimeRoutingHook(enabled=True),
        recorder=records.append,
    )

    assert observation.enabled is True
    assert observation.predicted_target == "direct"
    assert observation.target == "direct"
    assert observation.accepted is True
    assert observation.reason == "accepted"
    assert records == [observation]
```

Extend export test:

```python
from christine.conversation import observe_direct_runtime_route
assert callable(observe_direct_runtime_route)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py -q`

Expected: FAIL because `observe_direct_runtime_route` is missing.

**Step 3: Implement helper**

Add to `christine/conversation/runtime_routing_hook.py`:

```python
def observe_direct_runtime_route(
    input_text: str,
    *,
    hook: RuntimeRoutingHook = RuntimeRoutingHook(),
    recorder: Callable[[RuntimeRouteObservation], None] | None = None,
) -> RuntimeRouteObservation:
    return observe_runtime_route(
        input_text,
        RoutePrediction("direct", "legacy ask wrapper"),
        hook=hook,
        recorder=recorder,
    )
```

Export it from `christine/conversation/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/conversation/runtime_routing_hook.py christine/conversation/__init__.py tests/test_conversation_runtime_routing_hook.py && git commit -m "refactor: add direct runtime routing observation"`

---

### Task 2: Update Monolith Routing Guard For Disabled Observation

**Files:**
- Modify: `tests/test_runtime_routing_integration_guard.py`

**Step 1: Replace old no-wiring guard**

Keep the policy dispatch guard unchanged. Replace `test_runtime_routing_hook_is_not_wired_into_monolith_yet()` with:

```python
def test_runtime_routing_hook_is_wired_as_disabled_observation_only():
    text = Path("christine_final.py").read_text(encoding="utf-8", errors="ignore")

    assert "observe_direct_runtime_route" in text
    assert "RuntimeRoutingHook(enabled=False)" in text
    assert "_v180_observe_runtime_route(" in text
    assert "observe_runtime_route(" not in text
    assert "allow_side_effect_targets=True" not in text
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_runtime_routing_integration_guard.py -q`

Expected: FAIL because monolith is not wired yet.

**Step 3: Commit only after Task 3**

Do not commit failing tests alone.

---

### Task 3: Wire Disabled Observation Into V1484 Ask Wrapper

**Files:**
- Modify: `christine_final.py`
- Test: `tests/test_runtime_routing_integration_guard.py`

**Step 1: Add imports in V1480/V1484 block**

Near the existing `route_voice_then_fallback` import in the V1480/V1484 block, add:

```python
from christine.conversation.runtime_routing_hook import RuntimeRoutingHook, observe_direct_runtime_route
```

**Step 2: Add disabled hook constant and best-effort observer**

Before the V1484 wrapper installs `def ask(inp, *args, **kwargs):`, add:

```python
_V1484_RUNTIME_ROUTING_HOOK = RuntimeRoutingHook(enabled=False)


def _v180_observe_runtime_route(candidate):
    try:
        observe_direct_runtime_route(str(candidate), hook=_V1484_RUNTIME_ROUTING_HOOK)
    except Exception:
        try: log.debug("[V1484] runtime routing observation skipped", exc_info=True)
        except Exception: pass
```

**Step 3: Call observer inside ask wrapper**

At the start of `def ask(inp, *args, **kwargs):`, before `_voice_handler`, add:

```python
_v180_observe_runtime_route(inp)
```

This must not branch on observation output and must not alter `inp`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_runtime_routing_integration_guard.py tests/test_conversation_runtime_routing_hook.py tests/test_ask_routing_monolith.py -q`

Expected: PASS.

**Step 5: Compile and smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: reaches `自檢完成`.

**Step 6: Commit**

Run: `git add christine_final.py tests/test_runtime_routing_integration_guard.py && git commit -m "refactor: observe disabled runtime routing in ask wrapper"`

---

### Task 4: Final Verification And Review

**Files:**
- No planned edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_conversation_runtime_routing_hook.py tests/test_runtime_routing_integration_guard.py tests/test_ask_routing_monolith.py tests/test_boot_contract.py -q`

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
- `christine/conversation/runtime_routing_hook.py`
- `christine/conversation/__init__.py`
- `christine_final.py`
- `tests/test_conversation_runtime_routing_hook.py`
- `tests/test_runtime_routing_integration_guard.py`

**Step 4: Finish branch**

If review has no blocking findings, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
