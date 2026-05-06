# Christine Boot Optional Diagnostics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Surface optional dependency and Ollama availability during the boot sequence without making missing optional components fatal.

**Architecture:** Extend the existing pure optional dependency boundary with boot-readable rendering and a safe Ollama localhost checker. Wire `boot_christine.py` to print diagnostics after compute budget is applied and before either `--check` returns or normal startup hands off to `christine_final.py`.

**Tech Stack:** Python 3.10+, `uv`, `pytest`, `importlib.util.find_spec`, `urllib.request.urlopen`, existing `christine.runtime` modules.

---

## Requirements

- Keep diagnostics informational: missing optional modules or Ollama connection failure must not change exit status.
- Do not install dependencies or modify `pyproject.toml` / `uv.lock`.
- Do not import heavy optional modules during module availability checks.
- Ollama check is always run from boot diagnostics, but must use a short timeout and be injectable in tests.
- `--no-banner` suppresses only the decorative banner, not boot diagnostics.
- Preserve existing entry points and normal launcher handoff.
- Do not touch `christine_final.py`, Windows launchers, runtime state, or generated files.

## Task 1: Plan Baseline

**Files:**
- Create: `docs/plans/2026-05-06-christine-boot-optional-diagnostics.md`

**Step 1: Verify clean worktree baseline**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output reaches `自檢完成` and exit code is 0.

**Step 2: Commit the plan**

```bash
git add docs/plans/2026-05-06-christine-boot-optional-diagnostics.md
git commit -m "docs: plan boot optional diagnostics"
```

## Task 2: Optional Diagnostic Helpers

**Files:**
- Modify: `tests/test_optional_dependencies.py`
- Modify: `christine/runtime/optional_dependencies.py`

**Step 1: Write failing tests**

Add tests for these desired APIs:

```python
def test_check_ollama_service_reports_available_with_injected_opener():
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def opener(url, timeout):
        calls.append((url, timeout))
        return Response()

    status = check_ollama_service(opener=opener, timeout=0.2)

    assert status == OptionalDependencyStatus("ollama", True, "local LLM", "reachable")
    assert calls == [("http://127.0.0.1:11434/api/tags", 0.2)]


def test_check_ollama_service_reports_connection_failure():
    def opener(url, timeout):
        raise OSError("connection refused")

    status = check_ollama_service(opener=opener, timeout=0.2)

    assert status.name == "ollama"
    assert status.available is False
    assert status.message == "connection refused"


def test_render_optional_dependency_diagnostics_marks_degraded_dependencies():
    lines = render_optional_dependency_diagnostics(
        (
            OptionalDependencyStatus("torch", False, "GPU acceleration", "missing"),
            OptionalDependencyStatus("ollama", True, "local LLM", "reachable"),
        ),
        colors=False,
    )

    text = "\n".join(lines)
    assert "[Optional Dependencies]" in text
    assert "torch" in text
    assert "missing" in text
    assert "GPU acceleration" in text
    assert "ollama" in text
    assert "reachable" in text
```

**Step 2: Verify RED**

Run: `uv run pytest tests/test_optional_dependencies.py -q`

Expected: FAIL because `check_ollama_service` and `render_optional_dependency_diagnostics` are not defined/importable.

**Step 3: Implement minimal helpers**

In `christine/runtime/optional_dependencies.py`:

- Add `from urllib.request import urlopen`.
- Add `check_ollama_service(*, url="http://127.0.0.1:11434/api/tags", timeout=0.2, opener=urlopen)`.
- Catch `Exception` inside this checker and return `(available=False, message=str(exc)[:120])` through `OptionalDependencyStatus`.
- Add `render_optional_dependency_diagnostics(statuses, colors=True) -> list[str]` with stable plain output when `colors=False`.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_optional_dependencies.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add christine/runtime/optional_dependencies.py tests/test_optional_dependencies.py
git commit -m "refactor: add boot optional diagnostic helpers"
```

## Task 3: Runtime Exports

**Files:**
- Modify: `tests/test_optional_dependencies.py`
- Modify: `christine/runtime/__init__.py`

**Step 1: Write failing export test**

Extend `test_runtime_exports_optional_dependency_status_api`:

```python
from christine.runtime import check_ollama_service, render_optional_dependency_diagnostics

assert callable(check_ollama_service)
assert callable(render_optional_dependency_diagnostics)
```

**Step 2: Verify RED**

Run: `uv run pytest tests/test_optional_dependencies.py::test_runtime_exports_optional_dependency_status_api -q`

Expected: FAIL because the new symbols are not exported.

**Step 3: Export helpers**

In `christine/runtime/__init__.py`, import and list `check_ollama_service` and `render_optional_dependency_diagnostics` in `__all__`.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_optional_dependencies.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add christine/runtime/__init__.py tests/test_optional_dependencies.py
git commit -m "refactor: export boot optional diagnostics"
```

## Task 4: Launcher Wiring

**Files:**
- Modify: `tests/test_boot_banner.py`
- Modify: `boot_christine.py`

**Step 1: Write failing static wiring test**

Add a test that reads `boot_christine.py` and verifies:

```python
assert "optional_dependency_report" in text
assert "check_ollama_service" in text
assert "render_optional_dependency_diagnostics" in text
assert "print_optional_dependency_diagnostics" in text
```

**Step 2: Verify RED**

Run: `uv run pytest tests/test_boot_banner.py::test_launcher_prints_optional_dependency_diagnostics -q`

Expected: FAIL because the launcher is not wired yet.

**Step 3: Wire boot diagnostics**

In `boot_christine.py`:

- Import `check_ollama_service`, `optional_dependency_report`, and `render_optional_dependency_diagnostics`.
- Add `print_optional_dependency_diagnostics()` next to `print_boot_banner()`.
- Call it after step 3 messaging and before banner rendering.
- Use `service_checkers={"ollama": lambda: check_ollama_service()}`.
- Keep all diagnostics informational and do not raise.

**Step 4: Verify GREEN**

Run: `uv run pytest tests/test_boot_banner.py::test_launcher_prints_optional_dependency_diagnostics -q`

Expected: PASS.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes `[Optional Dependencies]`, status lines for `torch`, `pynput`, `sentence_transformers`, `ollama`, and `自檢完成`.

**Step 5: Commit**

```bash
git add boot_christine.py tests/test_boot_banner.py
git commit -m "refactor: show optional diagnostics during boot"
```

## Task 5: Final Verification and Review

**Files:**
- All changed files in this branch.

**Step 1: Run focused tests**

Run: `uv run pytest tests/test_optional_dependencies.py tests/test_boot_banner.py tests/test_boot_config.py -q`

Expected: PASS.

**Step 2: Run full suite**

Run: `uv run pytest -q`

Expected: PASS.

**Step 3: Compile launcher/runtime**

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: exit 0, no output.

**Step 4: Boot smoke**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: output includes optional dependency diagnostics and `自檢完成`.

**Step 5: Whitespace check**

Run: `git diff --check`

Expected: exit 0, no output.

**Step 6: Request blocker-focused review**

Use `requesting-code-review` with the base SHA from `main` and this branch head SHA. Ask for blocking findings only.

**Step 7: Merge and push after review**

If verification and review pass:

```bash
git checkout main
git merge --ff-only boot-optional-diagnostics
uv run pytest -q
git push origin main
```

Clean up the worktree and local feature branch after merge.
