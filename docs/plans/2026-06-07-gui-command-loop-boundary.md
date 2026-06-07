# GUI Command Loop Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or equivalent inline task execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the duplicated GUI command listener loop around `process_next_gui_command()` into a small tested helper without changing GUI queue behavior or command routing.

**Architecture:** Keep `GuiQueues`, legacy queue adapters, `handle_gui_command()`, and `process_next_gui_command()` semantics unchanged. Add `run_gui_command_listener()` to `christine.gui.commands` so the monolith supplies runtime dependencies and `time.sleep`, while tests can provide a finite `should_continue` callback and fake sleeper.

**Tech Stack:** Python 3.10+, existing `christine.gui` package, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve plain text, image, generated-image, and screen command routing.
- Preserve `process_next_gui_command()` behavior: process at most one queued command, submit one output, return `True`; return `False` when no command exists.
- Preserve error shaping as `"err:" + str(exc)`.
- Preserve legacy GUI queue adapter behavior.
- Preserve the monolith's listener behavior: process one command per tick, sleep `0.1` seconds each loop, and run in daemon threads.
- Do not change GUI UI layout, theme, buttons, message wording, queue data format, image generation behavior, screen command wording, or `ask()` routing.
- Do not add permission gates, GUI policy routing, worker dispatch, persistence, or runtime state writes in this slice.
- Do not import `christine_final.py` from runtime behavior tests; static guards may read it as text.
- Update `docs/ROADMAP.md` after the slice lands.

## Non-Goals

- No GUI redesign.
- No Tkinter thread model rewrite.
- No async queue implementation.
- No cross-platform GUI feature parity changes.
- No changes to audio/voice, memory/session, or tool dispatch.

---

### Task 1: Add GUI Listener Helper Tests

**Files:**
- Modify: `tests/test_gui_contract.py`

- [ ] **Step 1: Write failing tests**

Update the import in `tests/test_gui_contract.py`:

```python
from christine.gui.commands import handle_gui_command, process_next_gui_command, run_gui_command_listener
```

Add tests:

```python
def test_run_gui_command_listener_processes_one_command_per_tick_and_sleeps():
    queues = GuiQueues()
    queues.submit_command("one")
    queues.submit_command("two")
    calls = []
    sleeps = []

    def ask(text):
        calls.append(text)
        return "reply:" + text

    ticks = iter([True, True, False])

    run_gui_command_listener(
        queues,
        ask=ask,
        sleep=sleeps.append,
        should_continue=lambda: next(ticks),
        interval=0.1,
    )

    assert calls == ["one", "two"]
    assert sleeps == [0.1, 0.1]
    assert queues.drain_outputs() == ["reply:one", "reply:two"]


def test_run_gui_command_listener_sleeps_even_when_queue_is_empty():
    queues = GuiQueues()
    sleeps = []
    ticks = iter([True, False])

    run_gui_command_listener(
        queues,
        ask=lambda text: text,
        sleep=sleeps.append,
        should_continue=lambda: next(ticks),
        interval=0.25,
    )

    assert sleeps == [0.25]
    assert queues.drain_outputs() == []
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: FAIL because `run_gui_command_listener` does not exist.

---

### Task 2: Implement GUI Listener Helper

**Files:**
- Modify: `christine/gui/commands.py`
- Test: `tests/test_gui_contract.py`

- [ ] **Step 1: Add minimal helper**

Add to `christine/gui/commands.py`:

```python
def run_gui_command_listener(
    queues,
    *,
    sleep: Callable[[float], None],
    should_continue: Callable[[], bool] | None = None,
    interval: float = 0.1,
    **dependencies,
) -> None:
    keep_running = should_continue or (lambda: True)
    while keep_running():
        process_next_gui_command(queues, **dependencies)
        sleep(interval)
```

- [ ] **Step 2: Run GREEN**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: PASS.

- [ ] **Step 3: Commit helper slice**

Run: `git add christine/gui/commands.py tests/test_gui_contract.py && git commit -m "refactor: add gui command listener helper"`

---

### Task 3: Delegate Monolith GUI Listener Loops

**Files:**
- Modify: `christine_final.py`
- Modify: `tests/test_gui_contract.py`

- [ ] **Step 1: Add static guard for monolith delegation**

Update `test_monolith_gui_queues_delegate_to_christine_gui_modules()` in `tests/test_gui_contract.py`:

```python
def test_monolith_gui_queues_delegate_to_christine_gui_modules():
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "christine_final.py").read_text(encoding="utf-8")

    assert "from christine.gui.app import create_legacy_queue_adapters" in text
    assert "from christine.gui.commands import process_next_gui_command, run_gui_command_listener" in text
    assert "_christine_gui_queues, _gui_input_queue, _gui_output_queue = create_legacy_queue_adapters()" in text
    assert "run_gui_command_listener(" in text
    assert "process_next_gui_command(" not in _gui_listener_blocks(text)
```

Add helper above it:

```python
def _gui_listener_blocks(text: str) -> str:
    blocks = []
    start = 0
    marker = "def _gui_listener():"
    while True:
        try:
            idx = text.index(marker, start)
        except ValueError:
            return "\n".join(blocks)
        end = text.index("threading.Thread(target=_gui_listener", idx)
        blocks.append(text[idx:end])
        start = end + 1
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: FAIL because monolith listener closures still call `process_next_gui_command()` directly.

- [ ] **Step 3: Update monolith import and closures**

Replace:

```python
from christine.gui.commands import process_next_gui_command
```

with:

```python
from christine.gui.commands import process_next_gui_command, run_gui_command_listener
```

Replace each `_gui_listener()` body that currently loops over `process_next_gui_command(...)` and `time.sleep(0.1)` with:

```python
        run_gui_command_listener(
            _christine_gui_queues,
            ask=ask,
            understand_image=understand_image,
            generate_image_style=generate_image_style,
            sleep=time.sleep,
        )
```

Keep `threading.Thread(target=_gui_listener, daemon=True).start()` unchanged.

- [ ] **Step 4: Run GREEN**

Run: `uv run pytest tests/test_gui_contract.py tests/test_gui_theme.py -q`

Expected: PASS.

- [ ] **Step 5: Commit monolith delegation**

Run: `git add christine_final.py tests/test_gui_contract.py && git commit -m "refactor: delegate gui command listener loop"`

---

### Task 4: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Update tracking text**

In completed M1 slices, add:

```markdown
- GUI command listener loops delegate to `christine.gui.commands`.
```

Remove this remaining M1 slice:

```markdown
- Clean up GUI command queue and listener seams around `process_next_gui_command()`.
```

Adjust `Estimated remaining M1 effort` from `10-16 small slices` to `9-15 small slices`.

In `Immediate Next Slices`, remove:

```markdown
- Add GUI command loop cleanup around `process_next_gui_command()`.
```

- [ ] **Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

- [ ] **Step 3: Commit roadmap update**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after gui command loop cleanup"`

---

### Task 5: Final Verification And Review

**Files:**
- No planned edits.

- [ ] **Step 1: Run focused checks**

Run: `uv run pytest tests/test_gui_contract.py tests/test_gui_theme.py tests/test_boot_contract.py -q`

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

Perform subagent code review before merging because this touches GUI listener runtime structure. Check:

- `run_gui_command_listener()` preserves one-command-per-tick behavior and sleeping cadence.
- Monolith listener threads still pass `ask`, `understand_image`, `generate_image_style`, and `time.sleep`.
- `process_next_gui_command()` command routing and error shaping remain unchanged.
- No GUI UI layout, theme, persistence, worker dispatch, or policy routing changed.

- [ ] **Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
