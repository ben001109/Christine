# Christine Optional Dependency Status Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a pure runtime status boundary for optional dependencies seen during full startup.

**Architecture:** Create `christine.runtime.optional_dependencies` as an import-safe module that describes optional Python modules and service checks without importing heavy packages. Python modules are checked through injected or stdlib `importlib.util.find_spec`; service checks such as Ollama are represented by injectable callables so tests do not open sockets.

**Tech Stack:** Python 3.10+, dataclasses, importlib, stdlib only, uv, pytest.

---

## Requirements Captured

- Address full startup diagnostics for missing optional components: `torch`, `pynput`, `sentence_transformers`, and Ollama.
- Do not install dependencies.
- Do not import heavy optional modules during status checks.
- Do not change `boot_christine.py`, `christine_final.py`, launchers, runtime state, or generated files.
- Keep the module pure and testable through dependency injection.
- Preserve current startup behavior; this batch only adds a reusable status boundary.

## Non-Goals

- No network calls in tests.
- No live boot integration.
- No package changes in `pyproject.toml` or `uv.lock`.
- No decision about whether to install optional dependencies.

---

### Task 1: Add Optional Dependency Status Tests

**Files:**
- Create: `tests/test_optional_dependencies.py`

**Step 1: Write failing tests**

```python
from christine.runtime.optional_dependencies import (
    OptionalDependencyStatus,
    check_optional_module,
    check_optional_service,
    optional_dependency_report,
)


def test_check_optional_module_uses_injected_finder_without_importing_module():
    calls = []

    def finder(name):
        calls.append(name)
        return object() if name == "torch" else None

    status = check_optional_module("torch", purpose="GPU acceleration", finder=finder)

    assert status == OptionalDependencyStatus("torch", True, "GPU acceleration", "available")
    assert calls == ["torch"]


def test_check_optional_module_reports_missing_dependency():
    status = check_optional_module("pynput", purpose="global hotkeys", finder=lambda name: None)

    assert status.name == "pynput"
    assert status.available is False
    assert status.message == "missing"


def test_check_optional_service_uses_injected_checker():
    status = check_optional_service("ollama", purpose="local LLM", checker=lambda: (False, "connection refused"))

    assert status.name == "ollama"
    assert status.available is False
    assert status.message == "connection refused"


def test_optional_dependency_report_contains_startup_diagnostics():
    report = optional_dependency_report(
        finder=lambda name: object() if name == "torch" else None,
        service_checkers={"ollama": lambda: (False, "connection refused")},
    )

    by_name = {status.name: status for status in report}

    assert set(by_name) == {"torch", "pynput", "sentence_transformers", "ollama"}
    assert by_name["torch"].available is True
    assert by_name["pynput"].available is False
    assert by_name["sentence_transformers"].available is False
    assert by_name["ollama"].message == "connection refused"
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_optional_dependencies.py -q`

Expected: fail with `ModuleNotFoundError: No module named 'christine.runtime.optional_dependencies'`.

**Step 3: Continue to Task 2**

Do not commit RED tests alone unless stopping.

---

### Task 2: Implement Optional Dependency Status Module

**Files:**
- Create: `christine/runtime/optional_dependencies.py`
- Test: `tests/test_optional_dependencies.py`

**Step 1: Add minimal implementation**

```python
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True)
class OptionalDependencyStatus:
    name: str
    available: bool
    purpose: str
    message: str


def check_optional_module(
    name: str,
    *,
    purpose: str,
    finder: Callable[[str], object | None] = find_spec,
) -> OptionalDependencyStatus:
    available = finder(name) is not None
    return OptionalDependencyStatus(name, available, purpose, "available" if available else "missing")


def check_optional_service(
    name: str,
    *,
    purpose: str,
    checker: Callable[[], tuple[bool, str]],
) -> OptionalDependencyStatus:
    available, message = checker()
    return OptionalDependencyStatus(name, available, purpose, message)


def optional_dependency_report(
    *,
    finder: Callable[[str], object | None] = find_spec,
    service_checkers: Mapping[str, Callable[[], tuple[bool, str]]] | None = None,
) -> tuple[OptionalDependencyStatus, ...]:
    service_checkers = service_checkers or {}
    statuses = [
        check_optional_module("torch", purpose="GPU acceleration", finder=finder),
        check_optional_module("pynput", purpose="global hotkeys", finder=finder),
        check_optional_module("sentence_transformers", purpose="semantic embeddings", finder=finder),
    ]
    ollama_checker = service_checkers.get("ollama", lambda: (False, "not checked"))
    statuses.append(check_optional_service("ollama", purpose="local LLM", checker=ollama_checker))
    return tuple(statuses)
```

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_optional_dependencies.py -q`

Expected: all pass.

**Step 3: Commit**

```bash
git add christine/runtime/optional_dependencies.py tests/test_optional_dependencies.py
git commit -m "refactor: add optional dependency status boundary"
```

---

### Task 3: Export Optional Dependency Status API

**Files:**
- Modify: `christine/runtime/__init__.py`
- Modify: `tests/test_optional_dependencies.py`

**Step 1: Add export test**

Append:

```python
def test_runtime_exports_optional_dependency_status_api():
    from christine.runtime import OptionalDependencyStatus, optional_dependency_report

    assert OptionalDependencyStatus.__name__ == "OptionalDependencyStatus"
    assert callable(optional_dependency_report)
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_optional_dependencies.py::test_runtime_exports_optional_dependency_status_api -q`

Expected: fail with import error.

**Step 3: Export symbols**

Modify `christine/runtime/__init__.py` to import and list:

```python
OptionalDependencyStatus,
check_optional_module,
check_optional_service,
optional_dependency_report,
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_optional_dependencies.py tests/test_boot_config.py tests/test_boot_banner.py -q`

Expected: all pass.

**Step 5: Commit**

```bash
git add christine/runtime/__init__.py tests/test_optional_dependencies.py
git commit -m "refactor: export optional dependency status boundary"
```

---

### Task 4: Final Verification Gate

**Files:**
- No planned edits.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_optional_dependencies.py tests/test_boot_config.py tests/test_boot_banner.py -q`

Expected: all pass.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: all pass.

**Step 3: Run compile gate**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0 with no output.

**Step 4: Run fast boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `自檢完成`.

**Step 5: Run whitespace check**

Run: `git diff --check`

Expected: exit 0.

**Step 6: Request code review**

Ask for blocker-focused review on the optional dependency status branch.

**Step 7: Finish branch**

Use the finishing branch workflow after review and verification.

## Future Work After This Plan

- Add a local runtime health/status adapter that formats this report for the UI or CLI.
- Only wire into boot after preserving existing startup output with tests.
