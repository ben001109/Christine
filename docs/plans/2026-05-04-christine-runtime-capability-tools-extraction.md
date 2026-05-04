# Christine Runtime Capability Tools Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the stable runtime capability tool registrations from `christine_final.py` into `christine.tools` without changing tool names, schemas, keywords, or handler behavior.

**Architecture:** Add `christine/tools/runtime_capabilities.py` as a pure registration factory. The monolith keeps owning runtime functions (`capabilities_summary`, `runtime_self_test`) and injects them into the factory, so the new module does not import `christine_final.py` or perform side effects.

**Tech Stack:** Python 3.10+, dataclasses/typing already in `christine.tools.registry`, uv, pytest. No new dependencies.

---

## Requirements Captured

- Preserve tool names: `capabilities_summary`, `runtime_self_test`.
- Preserve Anthropic-style schema shape and descriptions.
- Preserve keywords including Chinese triggers: `功能`, `能力`, `你會什麼`, `會什麼`, `自檢`, `檢測`, `健康檢查`, `診斷`.
- Do not import `christine_final.py` from tests or new modules.
- Do not move implementations of `capabilities_summary()` or `runtime_self_test()` in this wave.
- Keep `christine_final.py` compatibility seam: `ALL = apply_tool_registrations(CORE, EXTRA, TM, KW, ...)`.
- No broad tool-system rewrite and no changes to `pick()`.

## Current Facts

- `christine/tools/registry.py` owns `ToolRegistration`, `tool_schema()`, and `apply_tool_registrations()`.
- `christine_final.py:5618-5647` defines `_RUNTIME_CAPABILITY_KEYWORDS`, `_RUNTIME_CAPABILITY_TOOLS`, and applies them to `CORE/EXTRA/TM/KW`.
- `tests/test_tool_registry.py` verifies generic registry helpers.
- `tests/test_tool_registration_monolith.py` statically verifies the monolith runtime capability seam.

## Out Of Scope

- Extracting all `TM`, `EXTRA`, `KW`, or `pick()` logic.
- Extracting browser, GUI, file, platform, self-modification, or evolution tools.
- Changing self-test/capability summary output text.
- Changing any persisted data, runtime state, or launcher behavior.

---

### Task 1: Add Runtime Capability Registration Tests

**Files:**
- Create: `tests/test_runtime_capability_tools.py`
- Later create: `christine/tools/runtime_capabilities.py`

**Step 1: Write failing registration test**

Create `tests/test_runtime_capability_tools.py`:

```python
from christine.tools.registry import ToolRegistration
from christine.tools.runtime_capabilities import (
    RUNTIME_CAPABILITY_KEYWORDS,
    build_runtime_capability_registrations,
)


def test_runtime_capability_registrations_preserve_schema_names_and_keywords():
    registrations = build_runtime_capability_registrations(
        capabilities_summary=lambda topic: "summary:" + topic,
        runtime_self_test=lambda: "self-test",
    )

    assert all(isinstance(registration, ToolRegistration) for registration in registrations)
    assert [registration.name for registration in registrations] == ["capabilities_summary", "runtime_self_test"]
    assert registrations[0].schema == {
        "name": "capabilities_summary",
        "description": "summarize current capabilities",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": [],
        },
    }
    assert registrations[1].schema == {
        "name": "runtime_self_test",
        "description": "run local runtime diagnostics",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
    assert registrations[0].keywords == RUNTIME_CAPABILITY_KEYWORDS
    assert "功能" in RUNTIME_CAPABILITY_KEYWORDS
    assert "self test" in RUNTIME_CAPABILITY_KEYWORDS
```

**Step 2: Write failing handler behavior test**

Append:

```python
def test_runtime_capability_handlers_delegate_to_injected_functions():
    calls = []

    def capabilities_summary(topic):
        calls.append(("summary", topic))
        return "summary:" + topic

    def runtime_self_test():
        calls.append(("self_test", None))
        return "self-test"

    registrations = build_runtime_capability_registrations(capabilities_summary, runtime_self_test)

    assert registrations[0].handler({"topic": "tools"}) == "summary:tools"
    assert registrations[1].handler({}) == "self-test"
    assert calls == [("summary", "tools"), ("self_test", None)]
```

**Step 3: Run RED**

Run: `uv run pytest tests/test_runtime_capability_tools.py -q`

Expected: fail because `christine.tools.runtime_capabilities` does not exist.

---

### Task 2: Implement Runtime Capability Registration Factory

**Files:**
- Create: `christine/tools/runtime_capabilities.py`
- Modify: `christine/tools/__init__.py` if present, otherwise leave package implicit.

**Step 1: Implement module**

Create `christine/tools/runtime_capabilities.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .registry import ToolRegistration, tool_schema


RUNTIME_CAPABILITY_KEYWORDS = (
    "功能",
    "能力",
    "capability",
    "capabilities",
    "你會什麼",
    "會什麼",
    "自檢",
    "檢測",
    "健康檢查",
    "診斷",
    "runtime",
    "self test",
)


def build_runtime_capability_registrations(
    capabilities_summary: Callable[[str], Any],
    runtime_self_test: Callable[[], Any],
) -> tuple[ToolRegistration, ...]:
    return (
        ToolRegistration(
            schema=tool_schema(
                "capabilities_summary",
                "summarize current capabilities",
                properties={"topic": {"type": "string"}},
                required=[],
            ),
            handler=lambda args: capabilities_summary(args.get("topic", "")),
            keywords=RUNTIME_CAPABILITY_KEYWORDS,
        ),
        ToolRegistration(
            schema=tool_schema(
                "runtime_self_test",
                "run local runtime diagnostics",
                required=[],
            ),
            handler=lambda args: runtime_self_test(),
        ),
    )
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_runtime_capability_tools.py tests/test_tool_registry.py -q`

Expected: pass.

**Step 3: Run compile check**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine`

Expected: pass.

**Step 4: Commit**

Commit message: `refactor: add runtime capability tool factory`

---

### Task 3: Delegate Monolith Runtime Capability Tools

**Files:**
- Modify: `tests/test_tool_registration_monolith.py`
- Modify: `christine_final.py:5618-5647`

**Step 1: Update static monolith test for new seam**

Modify `tests/test_tool_registration_monolith.py`:

```python
def test_runtime_capability_tools_use_runtime_capability_factory():
    block = _runtime_capability_block()

    assert "from christine.tools.runtime_capabilities import build_runtime_capability_registrations" in block
    assert "build_runtime_capability_registrations(" in block
    assert "ALL = apply_tool_registrations" in block
    assert "ToolRegistration(" not in block
    assert "tool_schema(" not in block
    assert "EXTRA.extend" not in block
    assert "TM.update" not in block
```

Keep the existing name/keyword preservation test, but update it to assert the builder call still references `capabilities_summary` and `runtime_self_test`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_tool_registration_monolith.py -q`

Expected: fail because monolith still declares inline `ToolRegistration` objects.

**Step 3: Replace monolith inline runtime capability declarations**

In `christine_final.py`, replace lines around `# runtime capability tools` with:

```python
# runtime capability tools
from christine.tools.registry import apply_tool_registrations
from christine.tools.runtime_capabilities import build_runtime_capability_registrations

_RUNTIME_CAPABILITY_TOOLS = build_runtime_capability_registrations(
    capabilities_summary=capabilities_summary,
    runtime_self_test=runtime_self_test,
)

ALL = apply_tool_registrations(CORE, EXTRA, TM, KW, _RUNTIME_CAPABILITY_TOOLS)
```

Do not change `def pick(inp):` or any surrounding tool maps.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_runtime_capability_tools.py tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q`

Expected: pass.

**Step 5: Run compile and boot smoke**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: both pass; boot smoke prints `自檢完成`.

**Step 6: Commit**

Commit message: `refactor: delegate runtime capability tools`

---

### Task 4: Final Verification And Review

**Files:**
- No new implementation files expected.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_runtime_capability_tools.py tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q`

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

- Tool names, schemas, keywords, and handlers are preserved.
- `christine_final.py` does not inline runtime capability `ToolRegistration` objects anymore.
- New module does not import `christine_final.py` and has no import-time side effects.
- `pick()` and broader `TM/EXTRA/KW` behavior unchanged.
- No new dependencies.

**Step 7: Fix review findings if needed**

Use TDD for behavior fixes, verify focused tests, and commit each verified fix.

**Step 8: Finish branch**

Use `finishing-a-development-branch` after review and verification are clean.

---

## Verification Gate For This Slice

```bash
uv run pytest tests/test_runtime_capability_tools.py tests/test_tool_registry.py tests/test_tool_registration_monolith.py -q
uv run pytest -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

## Rollback Notes

- Revert only this branch's commits if tool registration changes regress runtime behavior.
- Do not touch unrelated tool groups.
- Do not change `CORE`, `EXTRA`, `TM`, `KW`, `ALL`, or `pick()` except the runtime capability registration source.
