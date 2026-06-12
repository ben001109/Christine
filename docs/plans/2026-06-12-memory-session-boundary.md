# Memory Session Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a small tested conversation/session boundary for recording user and assistant turns while preserving existing `conv`, `mem`, and `mem.json` behavior.

**Architecture:** Add `christine.conversation.session` as a pure helper module that mutates caller-owned conversation and memory objects in the same shape the monolith already uses. Refactor only the V10 ask core to delegate its user-message append, assistant-message append, turn counter update, last-chat timestamp update, and memory save call through this helper; later ask wrappers can migrate in follow-up slices.

**Tech Stack:** Python 3.10+, dataclasses-free pure functions, pathlib-free runtime helper, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve the existing `conv` list message shape: `{"role": ..., "content": ...}`.
- Preserve existing `mem` fields and persisted format, especially `tc` and `lc`.
- Preserve the existing local timestamp format: `%Y-%m-%d %H:%M`.
- Keep `christine_final.py`, `boot_christine.py`, and launch behavior working.
- Do not import `christine_final.py` from tests.
- Do not touch runtime state, generated files, logs, backups, mirrors, or self replicas.
- Keep the first slice small: update the V10 ask core only, not every historical ask wrapper.

## Non-Goals

- No migration of `mem.json` or any persisted data format.
- No rewrite of `lm()`, `sm()`, `fmem()`, or memory tool functions like `rui()` / `rpf()`.
- No full conversation manager class.
- No cleanup of all duplicate ask wrappers.
- No behavior changes to API routing, tool execution, GUI, or audio.

---

### Task 1: Add Session Helper Tests

**Files:**
- Create: `tests/test_conversation_session.py`

**Step 1: Write failing tests**

Create `tests/test_conversation_session.py`:

```python
import datetime as dt

from christine.conversation.session import (
    append_assistant_message,
    append_user_message,
    commit_assistant_turn,
    commit_conversation_turn,
    update_turn_memory,
)


def test_append_user_and_assistant_messages_preserve_legacy_shape():
    conversation = []

    user_message = append_user_message(conversation, "hello")
    assistant_message = append_assistant_message(conversation, "hi")

    assert user_message == {"role": "user", "content": "hello"}
    assert assistant_message == {"role": "assistant", "content": "hi"}
    assert conversation == [user_message, assistant_message]


def test_update_turn_memory_preserves_existing_fields_and_saves_once():
    memory = {"ui": {"稱呼": "老闆"}, "tc": 2, "lc": "old"}
    saved = []

    result = update_turn_memory(
        memory,
        now=dt.datetime(2026, 6, 12, 10, 9),
        save_memory=saved.append,
    )

    assert result is memory
    assert memory == {"ui": {"稱呼": "老闆"}, "tc": 3, "lc": "2026-06-12 10:09"}
    assert saved == [memory]


def test_update_turn_memory_defaults_missing_counter_to_one():
    memory = {}

    update_turn_memory(memory, now=dt.datetime(2026, 6, 12, 10, 9))

    assert memory == {"tc": 1, "lc": "2026-06-12 10:09"}


def test_commit_assistant_turn_appends_reply_and_updates_memory():
    conversation = [{"role": "user", "content": "hello"}]
    memory = {"tc": 0}
    saved = []

    reply = commit_assistant_turn(
        conversation,
        memory,
        "hi",
        now=dt.datetime(2026, 6, 12, 10, 9),
        save_memory=saved.append,
    )

    assert reply == {"role": "assistant", "content": "hi"}
    assert conversation == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assert memory["tc"] == 1
    assert memory["lc"] == "2026-06-12 10:09"
    assert saved == [memory]


def test_commit_conversation_turn_appends_user_and_reply_then_updates_memory():
    conversation = []
    memory = {"tc": 4}

    messages = commit_conversation_turn(
        conversation,
        memory,
        "hello",
        "hi",
        now=dt.datetime(2026, 6, 12, 10, 9),
    )

    assert messages == (
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    )
    assert conversation == list(messages)
    assert memory == {"tc": 5, "lc": "2026-06-12 10:09"}
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_session.py -q`

Expected: FAIL because `christine.conversation.session` does not exist.

---

### Task 2: Implement Session Helper

**Files:**
- Create: `christine/conversation/session.py`
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_session.py`

**Step 1: Add minimal helper module**

Create `christine/conversation/session.py`:

```python
from __future__ import annotations

import datetime as _dt
from collections.abc import Callable, MutableMapping
from typing import Any


Message = dict[str, Any]
Conversation = list[Message]
Memory = MutableMapping[str, Any]
SaveMemory = Callable[[Memory], Any]


def append_user_message(conversation: Conversation, content: Any) -> Message:
    message = {"role": "user", "content": content}
    conversation.append(message)
    return message


def append_assistant_message(conversation: Conversation, content: Any) -> Message:
    message = {"role": "assistant", "content": content}
    conversation.append(message)
    return message


def update_turn_memory(
    memory: Memory,
    *,
    now: _dt.datetime | None = None,
    save_memory: SaveMemory | None = None,
) -> Memory:
    timestamp = (now or _dt.datetime.now()).strftime("%Y-%m-%d %H:%M")
    memory["tc"] = memory.get("tc", 0) + 1
    memory["lc"] = timestamp
    if save_memory is not None:
        save_memory(memory)
    return memory


def commit_assistant_turn(
    conversation: Conversation,
    memory: Memory,
    assistant_reply: Any,
    *,
    now: _dt.datetime | None = None,
    save_memory: SaveMemory | None = None,
) -> Message:
    message = append_assistant_message(conversation, assistant_reply)
    update_turn_memory(memory, now=now, save_memory=save_memory)
    return message


def commit_conversation_turn(
    conversation: Conversation,
    memory: Memory,
    user_input: Any,
    assistant_reply: Any,
    *,
    now: _dt.datetime | None = None,
    save_memory: SaveMemory | None = None,
) -> tuple[Message, Message]:
    user_message = append_user_message(conversation, user_input)
    assistant_message = commit_assistant_turn(
        conversation,
        memory,
        assistant_reply,
        now=now,
        save_memory=save_memory,
    )
    return user_message, assistant_message
```

Modify `christine/conversation/__init__.py`:

```python
from .session import (
    append_assistant_message,
    append_user_message,
    commit_assistant_turn,
    commit_conversation_turn,
    update_turn_memory,
)
```

Add those names to `__all__`.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_conversation_session.py -q`

Expected: PASS.

**Step 3: Commit helper slice**

Run: `git add christine/conversation/session.py christine/conversation/__init__.py tests/test_conversation_session.py && git commit -m "refactor: add conversation session boundary"`

---

### Task 3: Refactor V10 Ask Session Updates

**Files:**
- Modify: `christine_final.py`
- Create: `tests/test_memory_session_monolith.py`

**Step 1: Write static monolith guard**

Create `tests/test_memory_session_monolith.py`:

```python
from pathlib import Path


def _source() -> str:
    return Path("christine_final.py").read_text(encoding="utf-8")


def _v10_ask_block() -> str:
    text = _source()
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_ask_delegates_user_message_to_session_helper():
    text = _source()
    block = _v10_ask_block()

    assert "from christine.conversation.session import" in text
    assert "append_user_message(conv, inp)" in block
    assert 'conv.append({"role":"user","content":inp})' not in block


def test_v10_ask_delegates_reply_memory_update_to_session_helper():
    block = _v10_ask_block()

    assert "commit_assistant_turn(" in block
    assert "save_memory=sm" in block
    assert 'conv.append({"role":"assistant","content":reply})' not in block
    assert 'mem["tc"]=mem.get("tc",0)+1' not in block
    assert 'mem["lc"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")' not in block
    assert "sm(mem)" not in block
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_memory_session_monolith.py -q`

Expected: FAIL because `christine_final.py` still performs raw V10 `conv` / `mem` updates.

**Step 3: Refactor imports and V10 ask**

Modify the existing import near `build_recent_messages`:

```python
from christine.conversation.context import build_recent_messages, build_v10_system_prompt
from christine.conversation.session import append_user_message, commit_assistant_turn
```

In V10 `ask(inp)`, replace:

```python
rs("chat"); conv.append({"role":"user","content":inp})
```

with:

```python
rs("chat"); append_user_message(conv, inp)
```

Replace:

```python
conv.append({"role":"assistant","content":reply})
mem["tc"]=mem.get("tc",0)+1
mem["lc"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
sm(mem)
```

with:

```python
commit_assistant_turn(conv, mem, reply, save_memory=sm)
```

Do not change any other ask wrapper in this slice.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_conversation_session.py tests/test_memory_session_monolith.py tests/test_prompt_context_monolith.py -q`

Expected: PASS.

**Step 5: Commit monolith delegation slice**

Run: `git add christine_final.py tests/test_memory_session_monolith.py && git commit -m "refactor: delegate v10 session updates"`

---

### Task 4: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

**Step 1: Update tracking text**

In completed M1 slices, add:

```markdown
- V10 session turn recording delegates to `christine.conversation.session`.
```

Keep the remaining M1 slice but narrow it from:

```markdown
- Add a memory/session boundary for `conv`, `mem`, and save/update calls without
  changing persisted formats.
```

to:

```markdown
- Continue migrating remaining historical ask wrappers and memory tool writes to
  session/memory boundaries without changing persisted formats.
```

Adjust `Estimated remaining M1 effort` from `8-14 small slices` to `7-13 small slices`.

**Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

**Step 3: Commit roadmap update**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after session boundary"`

---

### Task 5: Final Verification And Review

**Files:**
- No planned edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_conversation_session.py tests/test_memory_session_monolith.py tests/test_prompt_context_monolith.py tests/test_boot_contract.py -q`

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

Perform this session review or subagent review. Check:

- The helper preserves legacy message and memory shapes.
- The helper does not read or write files directly.
- `christine_final.py` still owns `conv`, `mem`, and `sm()` persistence.
- No persisted data formats changed.
- Runtime state, generated files, backups, mirrors, and self replicas are untouched.

**Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
