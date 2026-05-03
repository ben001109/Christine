# Christine GUI Queue Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract legacy GUI input/output queue behavior and GUI command handling from `christine_final.py` into `christine.gui` while preserving the existing chat window commands, Chinese prompts, and launch entry points.

**Architecture:** Keep `christine_final.py` as the runtime compatibility surface. Move FIFO queue semantics and GUI command dispatch into small tested modules under `christine/gui/`, then replace duplicated monolith listener internals with wrappers. Do not redesign the UI in this wave; this wave only makes the queue and command seam independent from Tkinter.

**Tech Stack:** Python stdlib (`collections.deque`, `dataclasses`, `threading`, `time`), pytest, uv.

---

## Current Legacy Behavior

Production seams in `christine_final.py`:

- `christine_final.py:1858-1962` defines legacy fallback GUI state, `_gui_input_queue`, `_gui_output_queue`, `launch_chat_window()`, and button callbacks that append raw command strings.
- `christine_final.py:9960-9979` starts a GUI listener thread in `main()` that pops `_gui_input_queue`, handles raw command prefixes, calls `ask()`, and appends replies or `err:` strings to `_gui_output_queue`.
- `christine_final.py:13473-13493` contains a duplicated GUI listener in the `main_v38()` compatibility wrapper.
- `christine_final.py:104552-104558`, `christine_final.py:104637-104643`, and `christine_final.py:104656-104659` use the same raw queues inside the V550/V600 modern UI class.

Raw command formats to preserve:

- Plain user text: pass directly to `ask(text)`.
- Image input: `__IMAGE__<path>` should call `understand_image(path)` and then `ask("老闆傳了一張圖片給你看，內容是：" + desc + "，幫老闆分析或描述這張圖片。")`.
- Image generation: `__GENIMAGE__<prompt>||<style>` should call `generate_image_style(prompt, style)` and then `ask("圖片生成結果：" + result)`.
- Screen capture: `__SCREENCAP__` should call `ask("幫老闆分析目前螢幕上的畫面")`.
- Exceptions should become output text prefixed with `err:`.

Do not import `christine_final.py` in tests. It has heavy import-time side effects. Use pure module tests plus static wrapper smoke tests.

---

### Task 1: Extend GUI Queue Contract For Raw Commands

**Files:**

- Modify: `christine/gui/app.py`
- Modify: `tests/test_gui_contract.py`

**Step 1: Write the failing tests**

Add tests without opening Tkinter:

```python
def test_gui_queues_store_raw_commands_and_outputs_fifo():
    queues = GuiQueues()

    queues.submit_command("hello")
    queues.submit_command("__SCREENCAP__")
    queues.submit_output("hi")
    queues.submit_output("screen reply")

    assert queues.next_command() == "hello"
    assert queues.next_command() == "__SCREENCAP__"
    assert queues.next_command() is None
    assert queues.drain_outputs() == ["hi", "screen reply"]
    assert queues.drain_outputs() == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail with missing `submit_command`, `next_command`, `submit_output`, or `drain_outputs`.

**Step 3: Implement minimal queue methods**

Update `GuiQueues`:

```python
class GuiQueues:
    def __init__(self):
        self._user = deque()
        self._assistant = deque()
        self._commands = deque()
        self._outputs = deque()

    def submit_command(self, text: str) -> None:
        self._commands.append(text)

    def next_command(self):
        return self._commands.popleft() if self._commands else None

    def submit_output(self, text: str) -> None:
        self._outputs.append(text)

    def drain_outputs(self) -> list[str]:
        items = list(self._outputs)
        self._outputs.clear()
        return items
```

Keep existing `submit_user`, `submit_assistant`, `next_user`, and `next_assistant` unchanged.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/gui/app.py tests/test_gui_contract.py
git commit -m "refactor: extend GUI queue contract"
```

---

### Task 2: Extract Pure GUI Command Handling

**Files:**

- Create: `christine/gui/commands.py`
- Modify: `tests/test_gui_contract.py`

**Step 1: Write failing command tests**

Add imports:

```python
from christine.gui.commands import handle_gui_command
```

Add tests:

```python
def test_handle_gui_command_routes_plain_text_to_ask():
    calls = []

    def ask(text):
        calls.append(text)
        return "reply"

    reply = handle_gui_command("hello", ask=ask)

    assert reply == "reply"
    assert calls == ["hello"]


def test_handle_gui_command_routes_image_command():
    ask_calls = []

    def ask(text):
        ask_calls.append(text)
        return "image reply"

    def understand_image(path):
        assert path == "photo.png"
        return "一隻貓"

    reply = handle_gui_command("__IMAGE__photo.png", ask=ask, understand_image=understand_image)

    assert reply == "image reply"
    assert ask_calls == ["老闆傳了一張圖片給你看，內容是：一隻貓，幫老闆分析或描述這張圖片。"]


def test_handle_gui_command_routes_generation_and_screen_commands():
    ask_calls = []

    def ask(text):
        ask_calls.append(text)
        return "reply:" + text

    def generate_image_style(prompt, style):
        assert prompt == "cat"
        assert style == "anime"
        return "圖片已生成"

    gen_reply = handle_gui_command(
        "__GENIMAGE__cat||anime",
        ask=ask,
        generate_image_style=generate_image_style,
    )
    screen_reply = handle_gui_command("__SCREENCAP__", ask=ask)

    assert gen_reply == "reply:圖片生成結果：圖片已生成"
    assert screen_reply == "reply:幫老闆分析目前螢幕上的畫面"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail with missing `christine.gui.commands`.

**Step 3: Implement minimal command handler**

Create `christine/gui/commands.py`:

```python
from __future__ import annotations

from collections.abc import Callable


def _missing_dependency(name: str):
    raise RuntimeError(f"GUI command dependency is missing: {name}")


def handle_gui_command(
    command: str,
    *,
    ask: Callable[[str], str],
    understand_image: Callable[[str], str] | None = None,
    generate_image_style: Callable[[str, str], str] | None = None,
) -> str:
    if command.startswith("__IMAGE__"):
        if understand_image is None:
            _missing_dependency("understand_image")
        path = command[9:]
        desc = understand_image(path)
        return ask("老闆傳了一張圖片給你看，內容是：" + desc + "，幫老闆分析或描述這張圖片。")
    if command.startswith("__GENIMAGE__"):
        if generate_image_style is None:
            _missing_dependency("generate_image_style")
        parts = command[12:].split("||")
        prompt = parts[0]
        style = parts[1] if len(parts) > 1 else "realistic"
        result = generate_image_style(prompt, style)
        return ask("圖片生成結果：" + result)
    if command == "__SCREENCAP__":
        return ask("幫老闆分析目前螢幕上的畫面")
    return ask(command)
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/gui/commands.py tests/test_gui_contract.py
git commit -m "refactor: extract GUI command handling"
```

---

### Task 3: Add A Tested Listener Loop Boundary

**Files:**

- Modify: `christine/gui/commands.py`
- Modify: `tests/test_gui_contract.py`

**Step 1: Write failing listener test**

Add:

```python
from christine.gui.commands import process_next_gui_command


def test_process_next_gui_command_moves_reply_to_output_queue():
    queues = GuiQueues()
    queues.submit_command("hello")

    processed = process_next_gui_command(queues, ask=lambda text: "reply:" + text)

    assert processed is True
    assert queues.drain_outputs() == ["reply:hello"]
    assert process_next_gui_command(queues, ask=lambda text: text) is False
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail with missing `process_next_gui_command`.

**Step 3: Implement minimal processor**

Add to `christine/gui/commands.py`:

```python
def process_next_gui_command(queues, **dependencies) -> bool:
    command = queues.next_command()
    if command is None:
        return False
    try:
        reply = handle_gui_command(command, **dependencies)
    except Exception as exc:
        reply = "err:" + str(exc)
    queues.submit_output(reply)
    return True
```

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/gui/commands.py tests/test_gui_contract.py
git commit -m "refactor: add GUI command processor"
```

---

### Task 4: Add Legacy List-Compatible Queue Adapters

**Files:**

- Modify: `christine/gui/app.py`
- Modify: `tests/test_gui_contract.py`

**Step 1: Write failing adapter test**

Add:

```python
from christine.gui.app import create_legacy_queue_adapters


def test_legacy_queue_adapters_preserve_list_style_append_pop_bool():
    queues, input_queue, output_queue = create_legacy_queue_adapters()

    assert not input_queue
    input_queue.append("hello")
    output_queue.append("reply")

    assert input_queue
    assert input_queue.pop(0) == "hello"
    assert input_queue.pop(0) is None
    assert output_queue.pop(0) == "reply"
    assert queues.next_command() is None
    assert queues.drain_outputs() == []
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail with missing `create_legacy_queue_adapters`.

**Step 3: Implement adapter**

Add to `christine/gui/app.py`:

```python
class _LegacyQueueAdapter:
    def __init__(self, append_fn, pop_fn, has_items_fn):
        self._append_fn = append_fn
        self._pop_fn = pop_fn
        self._has_items_fn = has_items_fn

    def append(self, item):
        self._append_fn(item)

    def pop(self, index=0):
        if index != 0:
            raise IndexError("legacy GUI queues only support pop(0)")
        return self._pop_fn()

    def __bool__(self):
        return self._has_items_fn()


def create_legacy_queue_adapters():
    queues = GuiQueues()
    input_queue = _LegacyQueueAdapter(
        queues.submit_command,
        queues.next_command,
        lambda: queues.has_commands(),
    )
    output_queue = _LegacyQueueAdapter(
        queues.submit_output,
        queues.next_output,
        lambda: queues.has_outputs(),
    )
    return queues, input_queue, output_queue
```

Also add `has_commands()`, `has_outputs()`, and `next_output()` to `GuiQueues`.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: pass.

**Step 5: Commit**

Run:

```bash
git add christine/gui/app.py tests/test_gui_contract.py
git commit -m "refactor: add legacy GUI queue adapters"
```

---

### Task 5: Delegate Monolith GUI Listener To Extracted Processor

**Files:**

- Modify: `christine_final.py:1858-1962`
- Modify: `christine_final.py:9960-9979`
- Modify: `christine_final.py:13473-13493`
- Modify: `tests/test_gui_contract.py`

**Step 1: Add static wrapper smoke test**

Because importing `christine_final.py` has side effects, add a source-level smoke test:

```python
def test_monolith_gui_queues_delegate_to_christine_gui_modules():
    text = Path("christine_final.py").read_text(encoding="utf-8")

    assert "from christine.gui.app import create_legacy_queue_adapters" in text
    assert "from christine.gui.commands import process_next_gui_command" in text
    assert "_christine_gui_queues, _gui_input_queue, _gui_output_queue = create_legacy_queue_adapters()" in text
    assert "process_next_gui_command(" in text
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gui_contract.py -q`

Expected: fail because the monolith still owns queue lists and inline listener logic.

**Step 3: Add imports near top-level GUI imports**

Add near existing Tkinter imports:

```python
from christine.gui.app import create_legacy_queue_adapters
from christine.gui.commands import process_next_gui_command
```

**Step 4: Replace queue globals only**

Replace:

```python
_gui_input_queue=[]
_gui_output_queue=[]
```

with:

```python
_christine_gui_queues, _gui_input_queue, _gui_output_queue = create_legacy_queue_adapters()
```

Do not rewrite the Tkinter callbacks in this task; their existing `.append(...)` calls should continue to work through the adapters.

**Step 5: Replace duplicated listener bodies**

In both `main()` and `main_v38()`, replace the inner `_gui_listener()` body with:

```python
def _gui_listener():
    while True:
        process_next_gui_command(
            _christine_gui_queues,
            ask=ask,
            understand_image=understand_image,
            generate_image_style=generate_image_style,
        )
        time.sleep(0.1)
```

This preserves the existing thread startup sites and the existing `err:` behavior in the extracted processor.

**Step 6: Run focused verification**

Run:

```bash
uv run pytest tests/test_gui_contract.py tests/test_boot_contract.py -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
```

Expected: pass.

**Step 7: Commit**

Run:

```bash
git add christine/gui/app.py christine/gui/commands.py tests/test_gui_contract.py christine_final.py
git commit -m "refactor: delegate GUI queue listener"
```

---

## Final Verification

Run before reporting this wave complete:

```bash
uv run pytest tests/test_gui_contract.py tests/test_boot_contract.py tests/test_platform_capabilities.py tests/test_formula_runtime_isolation.py -q
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py
uv run python boot_christine.py --check --notorch --fast --no-banner
git diff --check
```

Expected: all pass.

## Not In This Wave

- Do not redesign V550/V600 UI layout.
- Do not replace `launch_chat_window()` with a new Tkinter implementation.
- Do not change user-facing Chinese GUI wording.
- Do not change image generation, screen capture, or ask routing behavior.
- Do not import `christine_final.py` in tests.
