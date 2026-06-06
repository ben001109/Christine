# Tool Loop Runtime Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or equivalent inline task execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a runtime-testable V10 tool-use loop seam so one mocked tool-use path is covered without importing `christine_final.py`.

**Architecture:** Extend `christine.tools.dispatch` with `build_tool_loop_results()`, a pure helper that iterates Claude-style tool-use blocks, invokes the existing `execute_tool_handler()`, and formats responses with `format_tool_result_message()`. Keep monolith-only side effects, such as progress printing and self-tool logging, behind callbacks supplied by V10 `ask()`.

**Tech Stack:** Python 3.10+, existing `christine.tools.dispatch`, uv, pytest, static monolith guards.

---

## Requirements Captured

- Add a runtime/mock test for a V10-style tool-use loop path without importing `christine_final.py`.
- Preserve current mapped-tool execution behavior through `execute_tool_handler()`.
- Preserve current tool result message formatting through `format_tool_result_message()`.
- Preserve V10 progress/status behavior by calling a callback before tool execution.
- Preserve V10 self-tool logging behavior by calling a callback after self-tool execution.
- Ignore non-`tool_use` content blocks as the current V10 loop does.
- Do not add permission gates, routing policy, retries, persistence, GUI dispatch, worker dispatch, or side-effect classification in this slice.
- Update `docs/ROADMAP.md` after the slice lands.

## Non-Goals

- No live policy-based tool dispatch.
- No side-effect permission model yet.
- No changes to `TM` registration, tool schemas, or handler implementations.
- No changes to Claude follow-up API call flow.
- No changes to prompt construction, memory saves, GUI, voice, or runtime state.

---

### Task 1: Add Runtime Tool-Loop Helper Tests

**Files:**
- Modify: `tests/test_tool_dispatch.py`

- [ ] **Step 1: Write failing runtime/mock tests**

Add these tests to `tests/test_tool_dispatch.py`:

```python
class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, tool_use_id, name, tool_input):
        self.id = tool_use_id
        self.name = name
        self.input = tool_input


class _TextBlock:
    type = "text"


def test_build_tool_loop_results_executes_and_formats_tool_use_blocks():
    calls = []
    started = []

    def handler(payload):
        calls.append(payload)
        return {"ok": True, "value": payload["x"]}

    results = tools.build_tool_loop_results(
        [_TextBlock(), _ToolUseBlock("tool-1", "known", {"x": 7})],
        {"known": handler},
        on_tool_use=lambda block: started.append(block.name),
    )

    assert calls == [{"x": 7}]
    assert started == ["known"]
    assert results == [
        {"type": "tool_result", "tool_use_id": "tool-1", "content": '{"ok": true, "value": 7}'}
    ]


def test_build_tool_loop_results_reports_self_tool_result_after_execution():
    reports = []

    results = tools.build_tool_loop_results(
        [_ToolUseBlock("tool-2", "self_patch", {"path": "x.py"})],
        {"self_patch": lambda payload: "patched " + payload["path"]},
        on_self_tool_result=lambda name, result: reports.append((name, result)),
    )

    assert reports == [("self_patch", "patched x.py")]
    assert results == [{"type": "tool_result", "tool_use_id": "tool-2", "content": "patched x.py"}]
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: FAIL because `build_tool_loop_results` does not exist.

---

### Task 2: Implement Runtime Tool-Loop Helper

**Files:**
- Modify: `christine/tools/dispatch.py`
- Modify: `christine/tools/__init__.py`
- Test: `tests/test_tool_dispatch.py`

- [ ] **Step 1: Add minimal helper**

Add to `christine/tools/dispatch.py`:

```python
ToolUseCallback = Callable[[Any], None]
SelfToolResultCallback = Callable[[str, Any], None]


def build_tool_loop_results(
    blocks: Any,
    handlers: ToolHandlerMap,
    *,
    on_tool_use: ToolUseCallback | None = None,
    on_self_tool_result: SelfToolResultCallback | None = None,
) -> list[dict[str, Any]]:
    results = []
    for block in blocks or []:
        if getattr(block, "type", "") != "tool_use":
            continue
        if on_tool_use is not None:
            on_tool_use(block)
        name = block.name
        result = execute_tool_handler(name, block.input, handlers)
        if name.startswith("self_") and on_self_tool_result is not None:
            on_self_tool_result(name, result)
        results.append(format_tool_result_message(block.id, name, result))
    return results
```

Export `build_tool_loop_results` from `christine/tools/__init__.py`.

- [ ] **Step 2: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: PASS.

- [ ] **Step 3: Commit helper slice**

Run: `git add christine/tools/dispatch.py christine/tools/__init__.py tests/test_tool_dispatch.py && git commit -m "refactor: add runtime tool loop helper"`

---

### Task 3: Delegate V10 Tool-Use Block Processing

**Files:**
- Modify: `christine_final.py`
- Modify: `tests/test_tool_dispatch_monolith.py`
- Test: `tests/test_tool_dispatch_monolith.py`

- [ ] **Step 1: Update static guards for final delegation**

Replace the current V10 tool-loop static expectations in `tests/test_tool_dispatch_monolith.py` with:

```python
def test_v10_tool_loop_delegates_runtime_tool_use_path():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import" in block
    assert "build_tool_loop_results" in block
    assert "on_tool_use=_v10_on_tool_use" in block
    assert "on_self_tool_result=_v10_on_self_tool_result" in block
    assert "execute_tool_handler(b.name, b.input, TM)" not in block
    assert "format_tool_result_message(b.id, b.name, r)" not in block
    assert "for b in getattr(resp, \"content\", [])" not in block
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch_monolith.py -q`

Expected: FAIL because V10 still processes tool-use blocks inline.

- [ ] **Step 3: Update V10 imports and callback delegation**

Replace:

```python
from christine.tools.dispatch import execute_tool_handler, format_tool_result_message
```

with:

```python
from christine.tools.dispatch import build_tool_loop_results
```

Inside V10 `ask()`, before the `while getattr(resp, "stop_reason", "")=="tool_use"` loop, add:

```python
    def _v10_on_tool_use(block):
        print(f"\r  {_C.BLU}[>] {block.name}{_C.RST}", end="", flush=True)
        rs(block.name)

    def _v10_on_self_tool_result(name, result):
        print("\n  >> " + name + ": " + str(result)[:100])
```

Replace the inline `for b in getattr(resp, "content", [])` loop body with:

```python
        results = build_tool_loop_results(
            getattr(resp, "content", []),
            TM,
            on_tool_use=_v10_on_tool_use,
            on_self_tool_result=_v10_on_self_tool_result,
        )
```

Keep `loops`, `recent.append(...)`, follow-up `_claude_create(...)`, and offline fallback unchanged.

- [ ] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_ask_routing_monolith.py tests/test_prompt_context_monolith.py -q`

Expected: PASS.

- [ ] **Step 5: Commit monolith delegation**

Run: `git add christine_final.py tests/test_tool_dispatch_monolith.py && git commit -m "refactor: delegate runtime tool loop path"`

---

### Task 4: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Update M1/M2 tracking text**

In `docs/ROADMAP.md`, add this completed M1 slice:

```markdown
- V10 tool-use loop block processing delegates to a runtime-tested helper.
```

In `Immediate Next Slices`, remove:

```markdown
- Add runtime/mock tests for one tool-use loop path.
```

- [ ] **Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

- [ ] **Step 3: Commit roadmap update**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after tool loop runtime test"`

---

### Task 5: Final Verification And Review

**Files:**
- No planned edits.

- [ ] **Step 1: Run focused checks**

Run: `uv run pytest tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_ask_routing_monolith.py tests/test_prompt_context_monolith.py tests/test_runtime_routing_integration_guard.py tests/test_boot_contract.py -q`

Expected: PASS.

- [ ] **Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: PASS.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 3: Review**

Perform subagent code review before merging because this touches V10 runtime tool-loop structure. Check:

- `build_tool_loop_results()` preserves callback order, mapped/unmapped execution, formatting, and self-tool reporting behavior.
- V10 still prints progress and records `rs()` before execution.
- V10 still appends assistant/user tool result messages in the same order.
- No new permission/routing/side-effect policy is enabled.

- [ ] **Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
