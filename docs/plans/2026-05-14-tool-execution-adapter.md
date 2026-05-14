# Tool Execution Adapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the V10 ask tool execution lookup/fallback/error-shaping seam into a small helper without changing which tools run or when side effects happen.

**Architecture:** Keep `christine_final.py` responsible for the Claude tool loop, progress printing, self-tool logging, result formatting, and follow-up API calls. Add `execute_tool_handler()` under `christine.tools.dispatch` so the monolith delegates only `TM` lookup, legacy fallback aliases, and legacy error text shaping; this helper still calls the same handlers with the same input and does not add permissioning or policy routing.

**Tech Stack:** Python 3.10+, existing `christine.tools.dispatch`, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve V10 `ask()` tool loop behavior.
- Preserve `TM[b.name](b.input)` semantics for mapped tools.
- Preserve `"tool_not_mapped:" + tool_name` for unmapped tools.
- Preserve legacy fallback aliases only after the original mapped tool raises.
- Preserve error text: `{"ok": False, "e": "tool error: " + str(original_error)}`.
- Do not add permission gates, routing policy, GUI/worker dispatch, or side-effect changes in this slice.
- Do not change `format_tool_result_message()` behavior.
- Do not import `christine_final.py` from tests.
- Update `docs/ROADMAP.md` after the slice lands.

## Non-Goals

- No live policy-based tool dispatch.
- No side-effect permission model yet.
- No changes to `TM` registration or tool schemas.
- No retry behavior beyond the legacy fallback alias attempt.
- No runtime logs or persisted state writes.

---

### Task 1: Add Tool Execution Adapter Tests

**Files:**
- Modify: `tests/test_tool_dispatch.py`

**Step 1: Write failing tests**

Add tests that access the helper through the public `christine.tools` package:

```python
def test_execute_tool_handler_calls_mapped_tool_with_input():
    calls = []

    def handler(payload):
        calls.append(payload)
        return {"ok": True, "value": payload["x"]}

    result = tools.execute_tool_handler("known", {"x": 7}, {"known": handler})

    assert result == {"ok": True, "value": 7}
    assert calls == [{"x": 7}]


def test_execute_tool_handler_preserves_unmapped_tool_text():
    result = tools.execute_tool_handler("missing", {}, {})

    assert result == "tool_not_mapped:missing"


def test_execute_tool_handler_uses_legacy_fallback_after_original_error():
    def broken(_payload):
        raise RuntimeError("boom")

    def fallback(payload):
        return "wrote " + payload["path"]

    result = tools.execute_tool_handler(
        "codeforge_write_any_file",
        {"path": "a.txt"},
        {"codeforge_write_any_file": broken, "write_file": fallback},
    )

    assert result == "wrote a.txt (fallback:write_file)"


def test_execute_tool_handler_reports_original_error_when_fallback_fails():
    def broken(_payload):
        raise RuntimeError("original")

    def fallback(_payload):
        raise RuntimeError("fallback")

    result = tools.execute_tool_handler(
        "docstudio_create_pdf",
        {},
        {"docstudio_create_pdf": broken, "create_pdf": fallback},
    )

    assert result == {"ok": False, "e": "tool error: original"}
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: FAIL because `execute_tool_handler` does not exist.

---

### Task 2: Implement Tool Execution Adapter

**Files:**
- Modify: `christine/tools/dispatch.py`
- Modify: `christine/tools/__init__.py`
- Test: `tests/test_tool_dispatch.py`

**Step 1: Add minimal helper**

Add to `christine/tools/dispatch.py`:

```python
from collections.abc import Callable, Mapping


ToolHandlerMap = Mapping[str, Callable[[Any], Any]]


LEGACY_TOOL_FALLBACK_ALIASES = {
    "codeforge_write_any_file": "write_file",
    "codeforge_patch_any_file": "write_file",
    "docstudio_create_pdf": "create_pdf",
    "docstudio_create_docx": "create_pdf",
}


def execute_tool_handler(
    tool_name: str,
    tool_input: Any,
    handlers: ToolHandlerMap,
    *,
    fallback_aliases: Mapping[str, str] = LEGACY_TOOL_FALLBACK_ALIASES,
) -> Any:
    if tool_name not in handlers:
        return "tool_not_mapped:" + tool_name
    try:
        return handlers[tool_name](tool_input)
    except Exception as tool_error:
        fallback_name = fallback_aliases.get(tool_name)
        if fallback_name and fallback_name in handlers:
            try:
                return str(handlers[fallback_name](tool_input)) + " (fallback:" + fallback_name + ")"
            except Exception:
                pass
        return {"ok": False, "e": "tool error: " + str(tool_error)}
```

Export `execute_tool_handler` from `christine/tools/__init__.py`.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: PASS.

**Step 3: Commit**

Run: `git add christine/tools/dispatch.py christine/tools/__init__.py tests/test_tool_dispatch.py && git commit -m "refactor: add tool execution adapter"`

---

### Task 3: Delegate V10 Tool Execution To Adapter

**Files:**
- Modify: `christine_final.py`
- Modify: `tests/test_tool_dispatch_monolith.py`
- Test: `tests/test_tool_dispatch_monolith.py`

**Step 1: Update static guard**

Add a test to `tests/test_tool_dispatch_monolith.py`:

```python
def test_v10_tool_loop_delegates_tool_execution():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import execute_tool_handler" in block
    assert "execute_tool_handler(b.name, b.input, TM)" in block
    assert "fallback_map={" not in block
    assert "TM[b.name](b.input)" not in block
    assert "tool_not_mapped:" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch_monolith.py -q`

Expected: FAIL because V10 still performs execution inline.

**Step 3: Update V10 import and loop**

In `christine_final.py`, replace the dispatch import:

```python
from christine.tools.dispatch import format_tool_result_message
```

with:

```python
from christine.tools.dispatch import execute_tool_handler, format_tool_result_message
```

Then replace the inline `try/except` execution block with:

```python
r = execute_tool_handler(b.name, b.input, TM)
```

Keep the progress print, `rs(b.name)`, self-tool print, result formatting, and follow-up `_claude_create()` code unchanged.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_ask_routing_monolith.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine_final.py tests/test_tool_dispatch_monolith.py && git commit -m "refactor: delegate tool execution lookup"`

---

### Task 4: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

**Step 1: Update M1 status text**

Add `V10 tool execution lookup/fallback/error shaping delegates to execute_tool_handler()` under completed M1 slices.

Remove the immediate next slice bullet for creating a tool execution adapter.

Optionally adjust `Estimated remaining M1 effort` from `12-18` to `11-17`.

**Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

**Step 3: Commit**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after tool execution adapter"`

---

### Task 5: Final Verification And Review

**Files:**
- No planned edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_tool_registry.py tests/test_tool_registration_monolith.py tests/test_ask_routing_monolith.py tests/test_boot_contract.py -q`

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

**Step 3: Review**

Perform this session review if subagent review is unavailable or likely to block. Check:
- `execute_tool_handler()` preserves legacy mapped/unmapped/fallback/error behavior.
- V10 still prints progress and self-tool output in the same place.
- No new permission/routing/side-effect policy is enabled.
- `format_tool_result_message()` output is unchanged.

**Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
