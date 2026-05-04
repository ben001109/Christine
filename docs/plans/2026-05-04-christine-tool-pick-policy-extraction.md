# Christine Tool Pick Policy Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract Christine's stable default tool selection policy from `christine_final.py` into `christine.tools` while preserving the `pick(inp)` compatibility function.

**Architecture:** Add a pure helper `christine.tools.selection.pick_all_tools(inp, all_tools)` that returns the complete tool list unchanged. Keep `christine_final.py` defining `pick(inp)` because later legacy patches refer to that symbol, but make the function delegate to the helper.

**Tech Stack:** Python 3.10+, uv, pytest. No new dependencies.

---

## Requirements Captured

- Preserve V43 behavior: `pick(inp)` always returns `ALL`.
- Preserve `pick(inp)` name in `christine_final.py`; later monkey patches and call sites depend on it.
- Do not change `ALL`, `CORE`, `EXTRA`, `TM`, `KW`, or runtime capability registration.
- Do not touch `_smart_pick` variants or later legacy tool selection patches.
- Do not import `christine_final.py` from tests.
- Keep the new helper pure and import-side-effect free.

## Current Facts

- `christine_final.py:5629-5636` defines `pick(inp)` with a Chinese V43 docstring and `return ALL`.
- `christine_final.py` later has legacy patches that call or wrap `pick` / `old_pick`.
- Tests currently only use static checks around the runtime capability block ending at `def pick(inp):`.
- `christine/tools/` now contains registry helpers and runtime capability registration factory.

## Out Of Scope

- Rewriting tool routing, `_smart_pick`, or tool sanitization.
- Reintroducing keyword-based filtering.
- Changing prompt construction or `ask()` tool loop.
- Adding model/routing policy logic.

---

### Task 1: Add Pure Tool Pick Policy Tests

**Files:**
- Create: `tests/test_tool_selection.py`
- Later create: `christine/tools/selection.py`

**Step 1: Write failing test for complete tool selection**

Create `tests/test_tool_selection.py`:

```python
from christine.tools.selection import pick_all_tools


def test_pick_all_tools_returns_complete_tool_list_for_any_input():
    all_tools = [{"name": "a"}, {"name": "b"}]

    assert pick_all_tools("hello", all_tools) is all_tools
    assert pick_all_tools("功能", all_tools) is all_tools
    assert pick_all_tools("", all_tools) is all_tools
```

**Step 2: Write failing immutable expectation test**

Append:

```python
def test_pick_all_tools_does_not_copy_or_filter_tools():
    all_tools = [{"name": "only"}]

    picked = pick_all_tools("anything", all_tools)

    picked.append({"name": "new"})
    assert all_tools == [{"name": "only"}, {"name": "new"}]
```

This intentionally documents that legacy `pick()` returned the same `ALL` object, not a copy.

**Step 3: Run RED**

Run: `uv run pytest tests/test_tool_selection.py -q`

Expected: fail because `christine.tools.selection` does not exist.

---

### Task 2: Implement Pure Tool Pick Policy Helper

**Files:**
- Create: `christine/tools/selection.py`
- Modify: `christine/tools/__init__.py`

**Step 1: Implement helper**

Create `christine/tools/selection.py`:

```python
from __future__ import annotations

from typing import TypeVar

ToolList = TypeVar("ToolList")


def pick_all_tools(inp: str, all_tools: ToolList) -> ToolList:
    return all_tools
```

`inp` is intentionally unused to preserve the legacy signature and policy.

**Step 2: Export helper**

Modify `christine/tools/__init__.py`:

```python
from .selection import pick_all_tools
```

Add `pick_all_tools` to `__all__`.

**Step 3: Run focused tests**

Run: `uv run pytest tests/test_tool_selection.py tests/test_tool_registry.py tests/test_runtime_capability_tools.py -q`

Expected: pass.

**Step 4: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 5: Commit**

Commit message: `refactor: add tool pick policy helper`

---

### Task 3: Delegate Monolith `pick()` To Helper

**Files:**
- Modify: `tests/test_tool_registration_monolith.py`
- Modify: `christine_final.py:5629-5636`

**Step 1: Add static monolith delegation test**

Modify `tests/test_tool_registration_monolith.py`:

```python
def _pick_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("def pick(inp):")
    end = text.index("def listen_wake():", start)
    return text[start:end]


def test_pick_delegates_to_tool_selection_helper():
    text = Path("christine_final.py").read_text(encoding="utf-8")
    block = _pick_block()

    assert "from christine.tools.selection import pick_all_tools" in text
    assert "return pick_all_tools(inp, ALL)" in block
    assert "return ALL" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_registration_monolith.py -q`

Expected: fail because monolith still returns `ALL` directly and does not import `pick_all_tools`.

**Step 3: Import helper near tool imports**

In `christine_final.py`, near the runtime capability imports, add:

```python
from christine.tools.selection import pick_all_tools
```

**Step 4: Delegate `pick()`**

Replace the body return line in `def pick(inp):`:

```python
    return pick_all_tools(inp, ALL)
```

Keep the Chinese V43 docstring unchanged.

**Step 5: Run focused tests**

Run: `uv run pytest tests/test_tool_selection.py tests/test_tool_registry.py tests/test_runtime_capability_tools.py tests/test_tool_registration_monolith.py -q`

Expected: pass.

**Step 6: Run compile and boot smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: both pass; boot smoke prints `自檢完成`.

**Step 7: Commit**

Commit message: `refactor: delegate tool pick policy`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_tool_selection.py tests/test_tool_registry.py tests/test_runtime_capability_tools.py tests/test_tool_registration_monolith.py -q`

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

- `pick(inp)` still exists in `christine_final.py`.
- Default behavior still returns the exact `ALL` object.
- The new helper is pure and import-side-effect free.
- No `_smart_pick`, prompt, ask loop, or later monkey patch behavior changed.
- No new dependencies.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Slice

```bash
uv run pytest tests/test_tool_selection.py tests/test_tool_registry.py tests/test_runtime_capability_tools.py tests/test_tool_registration_monolith.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if tool selection regresses.
- Do not touch `_smart_pick` variants or later legacy tool patches.
- Keep `pick(inp)` in the monolith until the later patches are audited and extracted.
