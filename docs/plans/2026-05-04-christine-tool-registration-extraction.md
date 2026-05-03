# Christine Tool Registration Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a tested tool registration contract and use it for the first small monolith tool-registration seam without changing Christine's tool behavior.

**Architecture:** Add `christine.tools.registry` as a pure helper module for declarative tool registrations. Keep the giant legacy `CORE`, `EXTRA`, `ALL`, `KW`, and `TM` structures in `christine_final.py` for this wave, but delegate the small `runtime capability tools` block through the new registry helpers.

**Tech Stack:** Python 3.10+, stdlib dataclasses/typing, uv, pytest. No new runtime dependencies.

---

## Requirements Captured

- Preserve all existing tool names, schemas, handlers, and keyword behavior.
- Do not import `christine_final.py` from tests.
- Do not rewrite the 200+ tool registry all at once.
- Do not change Claude tool schema shape.
- Do not change persisted state or runtime artifacts.
- Keep this wave limited to a small, reviewable registration seam.
- Create a tool contract test before changing registration code.

## Current Facts

- The primary legacy tool schemas live in `christine_final.py` as `CORE`, `EXTRA`, and `ALL` around `christine_final.py:5131-5395`.
- Primary handlers live in the giant `TM` dict around `christine_final.py:5398-5609`.
- A small existing registration seam starts at `christine_final.py:5613` under `# runtime capability tools`.
- That seam currently:
  - Extends `EXTRA` with `capabilities_summary` and `runtime_self_test` schemas.
  - Rebuilds `ALL = CORE + EXTRA`.
  - Adds capability/self-test keywords to `KW` if missing.
  - Adds two handlers to `TM` with `TM.update(...)`.
- The safest first extraction is to leave all tool implementations in place and move only registration mechanics into a pure module.

## Out Of Scope

- Moving individual tool implementation functions.
- Moving the full `CORE`, `EXTRA`, `TM`, `_TOOL_CATEGORIES`, or `_ALWAYS_TOOLS` structures.
- Changing `pick()` or `_smart_pick()` behavior.
- Deleting legacy self-modification tooling.
- Reformatting the giant `TM` dict.

---

### Task 1: Add Tool Registry Contract Tests

**Files:**
- Create: `tests/test_tool_registry.py`
- Create later: `christine/tools/__init__.py`
- Create later: `christine/tools/registry.py`

**Step 1: Write failing tests for schema construction**

Create `tests/test_tool_registry.py`:

```python
from christine.tools.registry import ToolRegistration, apply_tool_registrations, tool_schema


def test_tool_schema_builds_legacy_anthropic_shape():
    schema = tool_schema(
        "runtime_self_test",
        "run local runtime diagnostics",
        properties={"topic": {"type": "string"}},
        required=[],
    )

    assert schema == {
        "name": "runtime_self_test",
        "description": "run local runtime diagnostics",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": [],
        },
    }
```

**Step 2: Write failing tests for registration application**

```python
def test_apply_tool_registrations_extends_schemas_handlers_and_keywords():
    extra = []
    tm = {}
    kw = ["existing"]

    registration = ToolRegistration(
        schema=tool_schema("capabilities_summary", "summarize", required=[]),
        handler=lambda args: f"topic={args.get('topic', '')}",
        keywords=("能力", "existing", "capabilities"),
    )

    all_tools = apply_tool_registrations(
        core=[{"name": "get_current_time"}],
        extra=extra,
        handlers=tm,
        keywords=kw,
        registrations=[registration],
    )

    assert extra == [registration.schema]
    assert all_tools == [{"name": "get_current_time"}, registration.schema]
    assert tm["capabilities_summary"]({"topic": "tools"}) == "topic=tools"
    assert kw == ["existing", "能力", "capabilities"]
```

**Step 3: Write failing test for schema-only registrations**

```python
def test_apply_tool_registrations_allows_schema_without_handler():
    extra = []
    tm = {"old": lambda args: "old"}
    kw = []

    registration = ToolRegistration(schema=tool_schema("schema_only", "schema only"))

    apply_tool_registrations([], extra, tm, kw, [registration])

    assert extra == [registration.schema]
    assert sorted(tm) == ["old"]
```

**Step 4: Run RED**

Run: `uv run pytest tests/test_tool_registry.py -q`

Expected: fail with missing `christine.tools` module.

---

### Task 2: Implement Tool Registry Helpers

**Files:**
- Create: `christine/tools/__init__.py`
- Create: `christine/tools/registry.py`
- Modify: `tests/test_tool_registry.py` only if needed for import/style.

**Step 1: Create package init**

Create `christine/tools/__init__.py`:

```python
"""Tool registration helpers for Christine runtime."""

from .registry import ToolRegistration, apply_tool_registrations, tool_schema

__all__ = ["ToolRegistration", "apply_tool_registrations", "tool_schema"]
```

**Step 2: Implement `tool_schema` and `ToolRegistration`**

Create `christine/tools/registry.py`:

```python
from __future__ import annotations

from collections.abc import Callable, Iterable, MutableMapping
from dataclasses import dataclass
from typing import Any


ToolHandler = Callable[[dict[str, Any]], Any]


def tool_schema(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
        },
    }


@dataclass(frozen=True)
class ToolRegistration:
    schema: dict[str, Any]
    handler: ToolHandler | None = None
    keywords: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return str(self.schema.get("name", ""))
```

**Step 3: Implement `apply_tool_registrations`**

Add to `registry.py`:

```python
def apply_tool_registrations(
    core: Iterable[dict[str, Any]],
    extra: list[dict[str, Any]],
    handlers: MutableMapping[str, ToolHandler],
    keywords: list[str],
    registrations: Iterable[ToolRegistration],
) -> list[dict[str, Any]]:
    for registration in registrations:
        extra.append(registration.schema)
        if registration.handler is not None and registration.name:
            handlers[registration.name] = registration.handler
        for keyword in registration.keywords:
            if keyword not in keywords:
                keywords.append(keyword)
    return list(core) + extra
```

This preserves the current runtime capability seam: schemas are appended, handlers are registered/updated, keywords are append-if-missing, and `ALL` is rebuilt from `CORE + EXTRA`.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_tool_registry.py -q`

Expected: pass.

**Step 5: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 6: Commit**

Commit message: `refactor: add tool registration helpers`

---

### Task 3: Delegate Runtime Capability Tool Registration

**Files:**
- Modify: `christine_final.py:5613-5627`
- Create: `tests/test_tool_registration_monolith.py`

**Step 1: Add static smoke tests for monolith delegation**

Create `tests/test_tool_registration_monolith.py`:

```python
from pathlib import Path


def _runtime_capability_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("# runtime capability tools")
    end = text.index("def pick(inp):", start)
    return text[start:end]


def test_runtime_capability_tools_use_tool_registry_helper():
    block = _runtime_capability_block()

    assert "ToolRegistration" in block
    assert "apply_tool_registrations" in block
    assert "tool_schema" in block
    assert "ALL = apply_tool_registrations" in block
    assert "EXTRA.extend" not in block
    assert "TM.update" not in block


def test_runtime_capability_tool_names_and_keywords_preserved():
    block = _runtime_capability_block()

    assert "capabilities_summary" in block
    assert "runtime_self_test" in block
    assert "功能" in block
    assert "self test" in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_registration_monolith.py -q`

Expected: fail because the monolith still uses `EXTRA.extend` and `TM.update` directly.

**Step 3: Replace the runtime capability registration block only**

Replace the existing block at `christine_final.py:5613-5627` with:

```python
# runtime capability tools
from christine.tools.registry import ToolRegistration, apply_tool_registrations, tool_schema

_RUNTIME_CAPABILITY_KEYWORDS = (
    "功能", "能力", "capability", "capabilities", "你會什麼", "會什麼",
    "自檢", "檢測", "健康檢查", "診斷", "runtime", "self test",
)

_RUNTIME_CAPABILITY_TOOLS = (
    ToolRegistration(
        schema=tool_schema(
            "capabilities_summary",
            "summarize current capabilities",
            properties={"topic": {"type": "string"}},
            required=[],
        ),
        handler=lambda a: capabilities_summary(a.get("topic", "")),
        keywords=_RUNTIME_CAPABILITY_KEYWORDS,
    ),
    ToolRegistration(
        schema=tool_schema(
            "runtime_self_test",
            "run local runtime diagnostics",
            required=[],
        ),
        handler=lambda a: runtime_self_test(),
    ),
)

ALL = apply_tool_registrations(CORE, EXTRA, TM, KW, _RUNTIME_CAPABILITY_TOOLS)
```

Do not touch `CORE`, `EXTRA`, `TM`, `KW`, or `pick()` elsewhere.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q`

Expected: pass.

**Step 5: Run compile and boot smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: both pass.

**Step 6: Commit**

Commit message: `refactor: delegate runtime tool registration`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q`

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

- Tool schema shape preserved.
- Runtime capability tool names preserved.
- Runtime capability handlers preserved.
- Keyword append-if-missing behavior preserved.
- `ALL = CORE + EXTRA` effective behavior preserved through the helper return value.
- No broad rewrite of giant tool structures.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Wave

```bash
uv run pytest tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if registration changes regress.
- Do not modify runtime state artifacts.
- Do not edit generated MegaCortex files.
- If monolith delegation is risky, keep `christine.tools.registry` and revert only the `christine_final.py` delegation commit.
