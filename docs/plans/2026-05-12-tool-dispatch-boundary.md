# Tool Dispatch Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the V10 ask tool-result formatting seam into a pure helper so future tool dispatch work can move out of `christine_final.py` incrementally.

**Architecture:** Keep `christine_final.py` responsible for selecting tools, calling `_claude_create()`, executing `TM` handlers, and preserving the existing fallback map. Add a pure `format_tool_result_message()` helper under `christine.tools.dispatch` that only converts a tool name, tool-use id, and handler return value into the legacy Anthropic `tool_result` message shape.

**Tech Stack:** Python 3.10+, stdlib `json`, existing `christine.tools` package, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve V10 `ask()` tool loop behavior and output shape.
- Preserve image result shape for `capture_screen` and `capture_camera` when handler returns `{"ok": True, "img": ...}`.
- Preserve text result shape for dict success, dict error, and non-dict values.
- Preserve the 3000-character truncation used by the current V10 tool loop.
- Do not move tool execution, `TM`, fallback maps, GUI, worker, files, or side effects in this slice.
- Do not wire policy routing or `route_with_policy()` into the monolith.
- Do not import `christine_final.py` from tests.

## Non-Goals

- No live tool dispatch policy.
- No permission model changes.
- No handler registry migration.
- No change to `TM` mapping or fallback aliases.
- No persistent logs or runtime-state writes.

---

### Task 1: Add Pure Tool Result Formatting Tests

**Files:**
- Create: `tests/test_tool_dispatch.py`

**Step 1: Write failing tests**

Create `tests/test_tool_dispatch.py`:

```python
from christine.tools import format_tool_result_message


def test_format_tool_result_message_preserves_image_result_shape():
    result = format_tool_result_message("tool-1", "capture_screen", {"ok": True, "img": "abc123"})

    assert result == {
        "type": "tool_result",
        "tool_use_id": "tool-1",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "abc123",
                },
            },
            {"type": "text", "text": "Describe and help."},
        ],
    }


def test_format_tool_result_message_serializes_success_dict_as_json():
    result = format_tool_result_message("tool-2", "runtime_self_test", {"ok": True, "msg": "完成"})

    assert result == {
        "type": "tool_result",
        "tool_use_id": "tool-2",
        "content": '{"ok": true, "msg": "完成"}',
    }


def test_format_tool_result_message_uses_error_text_for_failed_dict():
    result = format_tool_result_message("tool-3", "runtime_self_test", {"ok": False, "e": "bad"})

    assert result == {"type": "tool_result", "tool_use_id": "tool-3", "content": "bad"}


def test_format_tool_result_message_truncates_text_content():
    result = format_tool_result_message("tool-4", "runtime_self_test", "x" * 3001)

    assert result["content"] == "x" * 3000
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: FAIL because `format_tool_result_message` does not exist.

---

### Task 2: Implement Pure Tool Result Formatting Helper

**Files:**
- Create: `christine/tools/dispatch.py`
- Modify: `christine/tools/__init__.py`
- Test: `tests/test_tool_dispatch.py`

**Step 1: Add minimal implementation**

Create `christine/tools/dispatch.py`:

```python
from __future__ import annotations

import json
from typing import Any


IMAGE_RESULT_TOOLS = frozenset({"capture_screen", "capture_camera"})


def format_tool_result_message(
    tool_use_id: str,
    tool_name: str,
    result: Any,
    *,
    text_limit: int = 3000,
) -> dict[str, Any]:
    if tool_name in IMAGE_RESULT_TOOLS and isinstance(result, dict) and result.get("ok"):
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result["img"],
                    },
                },
                {"type": "text", "text": "Describe and help."},
            ],
        }
    if isinstance(result, dict):
        text = result.get("e", "err") if not result.get("ok", True) else json.dumps(result, ensure_ascii=False)
    else:
        text = str(result)
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": text[:text_limit]}
```

Export it from `christine/tools/__init__.py`.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py -q`

Expected: PASS.

**Step 3: Commit**

Run: `git add christine/tools/dispatch.py christine/tools/__init__.py tests/test_tool_dispatch.py && git commit -m "refactor: add tool result formatter"`

---

### Task 3: Delegate V10 Tool Result Formatting To Helper

**Files:**
- Modify: `christine_final.py`
- Create: `tests/test_tool_dispatch_monolith.py`
- Test: `tests/test_tool_dispatch_monolith.py`

**Step 1: Write static monolith guard**

Create `tests/test_tool_dispatch_monolith.py`:

```python
from pathlib import Path


def _v10_ask_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_tool_loop_delegates_tool_result_formatting():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import format_tool_result_message" in block
    assert "format_tool_result_message(b.id, b.name, r)" in block
    assert "media_type\":\"image/png" not in block
    assert "json.dumps(r, ensure_ascii=False)" not in block
    assert "rx[:3000]" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_dispatch_monolith.py -q`

Expected: FAIL because V10 still formats tool results inline.

**Step 3: Update `christine_final.py`**

Near the existing V10 import:

```python
from christine.conversation.router import dedupe_tool_specs
```

add:

```python
from christine.tools.dispatch import format_tool_result_message
```

Then replace the inline formatter block:

```python
if b.name in("capture_screen","capture_camera") and isinstance(r,dict) and r.get("ok"):
    results.append(...)
else:
    ...
    results.append({"type":"tool_result","tool_use_id":b.id,"content":rx[:3000]})
```

with:

```python
results.append(format_tool_result_message(b.id, b.name, r))
```

Do not move the `TM` call, fallback map, self-tool print, `recent.append()`, or `_claude_create()` calls.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_ask_routing_monolith.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine_final.py tests/test_tool_dispatch_monolith.py && git commit -m "refactor: delegate tool result formatting"`

---

### Task 4: Final Verification And Review

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

**Step 3: Request review**

Request blocker-focused review for:
- `christine/tools/dispatch.py`
- `christine/tools/__init__.py`
- `christine_final.py`
- `tests/test_tool_dispatch.py`
- `tests/test_tool_dispatch_monolith.py`

**Step 4: Finish branch**

If review has no blocking findings, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
