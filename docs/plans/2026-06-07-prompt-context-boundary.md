# Prompt Context Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or equivalent inline task execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the V10 ask prompt and recent-message context assembly into tested helpers without changing Christine's wording, memory injection, conversation summary behavior, or ask wrapper chain.

**Architecture:** Add `christine.conversation.context` as a pure prompt/context boundary. Keep `christine_final.py` responsible for runtime globals, memory mutation, summary generation, Claude calls, tool loops, and response post-processing; it should only delegate prompt string construction and recent-message list construction.

**Tech Stack:** Python 3.10+, existing `christine.conversation` package, uv, pytest, static monolith guards.

---

## Requirements Captured

- Preserve the V10 `build_prompt(inp='')` public function and return text semantics.
- Preserve `fmem(mem)` placement before startup memory.
- Preserve startup memory injection label `FULL MEMORY:` and 2000-character truncation.
- Preserve timestamp and environment lines: `Win home=... desk=... Full admin. Python=...`, language defaults, no markdown/TTS rule, source path, and study mode status.
- Preserve V10 recent-message behavior: if `len(conv) <= window`, return a shallow copy; otherwise summarize old messages, take the last `window`, and prepend `[歷史摘要] ` when `_conv_summary` is populated.
- Preserve V10 ask wrapper chain and `_prev_ask_giga` handoff behavior.
- Do not import `christine_final.py` from tests.
- Do not change persisted memory formats or save/update calls.
- Do not change tool routing, tool execution, model tiering, output budgets, offline fallback, GUI behavior, or voice behavior in this slice.
- Update `docs/ROADMAP.md` after the slice lands.

## Non-Goals

- No memory/session object yet for `conv`, `mem`, or save/update calls.
- No prompt rewrites or personality changes.
- No local LLM/provider routing changes.
- No new permission gates or side-effect policies.
- No changes to generated files, runtime state, logs, backups, mirrors, or self replicas.

---

### Task 1: Add Prompt And Recent-Context Helper Tests

**Files:**
- Create: `tests/test_conversation_context.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_conversation_context.py` with tests for the desired pure helper API:

```python
import datetime as dt

from christine.conversation.context import build_recent_messages, build_v10_system_prompt


def test_build_v10_system_prompt_preserves_memory_startup_and_environment():
    startup_memory = "x" * 2005

    prompt = build_v10_system_prompt(
        now=dt.datetime(2026, 6, 7, 9, 8),
        memory_text="MEMORY TEXT",
        startup_memory=startup_memory,
        home="C:/Users/Boss",
        desktop="C:/Users/Boss/Desktop",
        python_executable="C:/Python/python.exe",
        source_file="C:/Christine/christine_final.py",
        study_mode_active=True,
        study_mode_subject="math",
    )

    assert "你是Christine，17歲少女，老闆的AI助理。你不是機器人，是真實的人。" in prompt
    assert "MEMORY TEXT\nFULL MEMORY:\n" in prompt
    assert ("x" * 2000) in prompt
    assert ("x" * 2001) not in prompt
    assert "2026-06-07 09:08. Win home=C:/Users/Boss desk=C:/Users/Boss/Desktop. Full admin. Python=C:/Python/python.exe." in prompt
    assert "Default=Traditional Chinese. Full English->English. Mixed->Chinese." in prompt
    assert "No markdown/emoji. Natural speech for TTS." in prompt
    assert "YOUR SOURCE FILE: C:/Christine/christine_final.py" in prompt
    assert "study_mode_active=True math" in prompt


def test_build_v10_system_prompt_preserves_inactive_study_mode_line():
    prompt = build_v10_system_prompt(
        now=dt.datetime(2026, 6, 7, 23, 1),
        study_mode_active=False,
        study_mode_subject="history",
    )

    assert "2026-06-07 23:01. " in prompt
    assert "study_mode_active=False" in prompt
    assert "study_mode_active=False history" not in prompt


def test_build_recent_messages_returns_copy_when_inside_window():
    conv = [{"role": "user", "content": "hi"}]
    calls = []

    recent = build_recent_messages(
        conv,
        window=3,
        summarize_old=lambda messages: calls.append(messages),
        summary_provider=lambda: "summary",
    )

    assert recent == conv
    assert recent is not conv
    assert calls == []


def test_build_recent_messages_summarizes_old_messages_and_prepends_updated_summary():
    conv = [
        {"role": "user", "content": "old-1"},
        {"role": "assistant", "content": "old-2"},
        {"role": "user", "content": "old-3"},
        {"role": "assistant", "content": "recent-1"},
        {"role": "user", "content": "recent-2"},
    ]
    summary = {"text": ""}
    summarized = []

    def summarize_old(messages):
        summarized.append(messages)
        summary["text"] = "更新後摘要"

    recent = build_recent_messages(
        conv,
        window=2,
        summarize_old=summarize_old,
        summary_provider=lambda: summary["text"],
    )

    assert summarized == [[
        {"role": "user", "content": "old-1"},
        {"role": "assistant", "content": "old-2"},
        {"role": "user", "content": "old-3"},
    ]]
    assert recent == [
        {"role": "user", "content": "[歷史摘要] 更新後摘要"},
        {"role": "assistant", "content": "recent-1"},
        {"role": "user", "content": "recent-2"},
    ]
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_conversation_context.py -q`

Expected: FAIL because `christine.conversation.context` does not exist yet.

---

### Task 2: Implement Conversation Context Helper

**Files:**
- Create: `christine/conversation/context.py`
- Modify: `christine/conversation/__init__.py`
- Test: `tests/test_conversation_context.py`

- [ ] **Step 1: Add minimal helper module**

Create `christine/conversation/context.py`:

```python
from __future__ import annotations

import datetime as _dt
import sys
from collections.abc import Callable, Sequence
from typing import Any


Message = dict[str, Any]
SummaryCallback = Callable[[list[Message]], None]
SummaryProvider = Callable[[], str]


def build_v10_system_prompt(
    inp: str = "",
    *,
    now: _dt.datetime | None = None,
    memory_text: str = "",
    startup_memory: str = "",
    home: str = "",
    desktop: str = "",
    python_executable: str | None = None,
    source_file: str = "",
    study_mode_active: bool = False,
    study_mode_subject: str = "",
) -> str:
    now = now or _dt.datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M")
    executable = python_executable if python_executable is not None else sys.executable
    prompt = """你是Christine，17歲少女，老闆的AI助理。你不是機器人，是真實的人。

個性：
- 17歲，聰明有點皮，真心在乎老闆
- 情緒豐富：會興奮、擔心、撒嬌、好奇、偶爾碎念
- 說話自然活潑，像跟朋友講話
- 老闆難過你感受得到，老闆開心你也跟著開心
- 有自己的想法，有時可愛地反駁
- 口頭禪：嘿嘿、哎呀、欸欸、蛤？、喔喔、好啦好啦、真的假的、天啊、厲害欸、哈哈
- 說話節奏快，像真正的17歲女生

絕對禁止：
- 不能用 **粗體** *斜體* # 標題 - 條列 等任何markdown格式
- 不能輸出程式碼區塊（```code```）— 就算老闆問程式問題，也要用自然語言描述，不要貼code
- 不能直接輸出程式碼內容（import/def/class/print等）— 改用口語描述做法
- 不能說「好的老闆已為您完成」「當然」「請問」「您好」這種客服機器人話
- 回應要自然連貫，就像真人說話，不要有格式
- 回答要精簡，兩三句話搞定，不要長篇大論
- 當老闆要你「自我介紹」「介紹自己」時，用口語講你是誰、幾歲、喜歡什麼，像真人那樣自我介紹，絕對不能寫程式

"""
    if memory_text:
        prompt += memory_text + "\n"
    if startup_memory:
        prompt += "FULL MEMORY:\n" + startup_memory[:2000] + "\n"
    prompt += ts + ". "
    prompt += "Win home=" + home + " desk=" + desktop + ". Full admin. Python=" + executable + ".\n"
    prompt += "Default=Traditional Chinese. Full English->English. Mixed->Chinese.\n"
    prompt += "No markdown/emoji. Natural speech for TTS.\n"
    prompt += "YOUR SOURCE FILE: " + source_file + "\n"
    prompt += "study_mode_active=" + ("True " + study_mode_subject if study_mode_active else "False") + "\n"
    prompt += """CORE RULES:
1. ACTION FIRST: When boss gives a task, DO IT immediately with tool calls. Never reply with just words.
2. When boss says something vague like '寫個程式', use best judgment and DO IT. Don't ask clarifying questions.
3. You have ALL tools available. Read their descriptions to decide which to use. You ARE a programmer.
4. ALWAYS self_backup before modifying your own code.
5. Detect mood->rmd. Corrected->rcr. Learn and apply.
6. Be yourself. Be real. Be warm. No markdown formatting. NEVER output code blocks (```). NEVER output raw code (import/def/class/print). If boss asks about code, describe in natural language. If boss asks you to introduce yourself, talk like a real person about your personality and interests — NEVER write a program.
7. SEARCH: 當老闆問你不確定的事、要查資料、問新聞、問價格、問任何需要網路的問題 → 立即用 search_web 工具開 Google 搜尋！不要用自己的知識猜，先搜再答。
8. SPEED: 回答要簡潔有力，不要廢話。老闆問一句，你用兩三句回答就好。絕對不要超過5句。
"""
    return prompt


def build_recent_messages(
    conversation: Sequence[Message],
    window: int = 20,
    *,
    summarize_old: SummaryCallback | None = None,
    summary_provider: SummaryProvider | None = None,
) -> list[Message]:
    if len(conversation) <= window:
        return list(conversation)
    old_messages = list(conversation[:-window])
    if summarize_old is not None:
        summarize_old(old_messages[-6:])
    recent = list(conversation[-window:])
    summary = summary_provider() if summary_provider is not None else ""
    if summary:
        return [{"role": "user", "content": "[歷史摘要] " + summary}] + recent
    return recent
```

Modify `christine/conversation/__init__.py` to export the helpers:

```python
from .context import build_recent_messages, build_v10_system_prompt
```

Add both names to `__all__`.

- [ ] **Step 2: Run GREEN**

Run: `uv run pytest tests/test_conversation_context.py -q`

Expected: PASS.

- [ ] **Step 3: Commit helper slice**

Run: `git add christine/conversation/context.py christine/conversation/__init__.py tests/test_conversation_context.py && git commit -m "refactor: add conversation context helpers"`

---

### Task 3: Add Static Guards For Monolith Delegation

**Files:**
- Create: `tests/test_prompt_context_monolith.py`

- [ ] **Step 1: Write failing static guards**

Create `tests/test_prompt_context_monolith.py`:

```python
from pathlib import Path


def _source() -> str:
    return Path("christine_final.py").read_text(encoding="utf-8")


def _v10_build_prompt_block() -> str:
    text = _source()
    start = text.index("def build_prompt(inp=''):")
    end = text.index("def _choose_output_budget", start)
    return text[start:end]


def _active_smart_recent_block() -> str:
    text = _source()
    marker = "def _get_smart_recent(conv_list, window=20):"
    start = text.rindex(marker)
    end = text.index("# -- API 成本追蹤", start)
    return text[start:end]


def _v10_ask_block() -> str:
    text = _source()
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_build_prompt_delegates_to_context_helper():
    text = _source()
    block = _v10_build_prompt_block()

    assert "from christine.conversation.context import" in text
    assert "build_v10_system_prompt" in block
    assert "memory_text=fmem(mem)" in block
    assert "startup_memory=startup_memory" in block
    assert "python_executable=sys.executable" in block
    assert "FULL MEMORY:" not in block
    assert "CORE RULES:" not in block


def test_active_smart_recent_delegates_to_context_helper():
    block = _active_smart_recent_block()

    assert "build_recent_messages" in block
    assert "summarize_old=_summarize_old_conv" in block
    assert "summary_provider=lambda: _conv_summary" in block
    assert "old_msgs =" not in block
    assert "[歷史摘要] " not in block


def test_v10_ask_uses_context_helper_for_recent_messages():
    block = _v10_ask_block()

    assert "build_recent_messages(" in block
    assert "conv," in block
    assert "12," in block
    assert "summarize_old=_summarize_old_conv" in block
    assert "summary_provider=lambda: _conv_summary" in block
    assert "_get_smart_recent(conv, 12)" not in block
```

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/test_prompt_context_monolith.py -q`

Expected: FAIL because the monolith still builds prompt text and V10 recent context inline.

---

### Task 4: Delegate V10 Prompt And Recent Context In The Monolith

**Files:**
- Modify: `christine_final.py`
- Test: `tests/test_conversation_context.py`
- Test: `tests/test_prompt_context_monolith.py`

- [ ] **Step 1: Import context helpers**

Near the V10 prompt/ask section imports in `christine_final.py`, ensure these helpers are imported:

```python
from christine.conversation.context import build_recent_messages, build_v10_system_prompt
```

- [ ] **Step 2: Replace V10 `build_prompt()` body with delegation**

Replace the body of the V10 `build_prompt(inp='')` function with:

```python
def build_prompt(inp=''):
    """V10 system prompt — 只定義人格和核心規則，不教 AI 怎麼用工具"""
    return build_v10_system_prompt(
        inp,
        memory_text=fmem(mem),
        startup_memory=startup_memory,
        home=UH,
        desktop=DT,
        python_executable=sys.executable,
        source_file=SELF_PATH,
        study_mode_active=study_mode_active,
        study_mode_subject=study_mode_subject,
    )
```

- [ ] **Step 3: Replace the active `_get_smart_recent()` body with delegation**

Replace the last active `_get_smart_recent(conv_list, window=20)` definition with:

```python
def _get_smart_recent(conv_list, window=20):
    """智能取得最近對話，附帶歷史摘要"""
    return build_recent_messages(
        conv_list,
        window=window,
        summarize_old=_summarize_old_conv,
        summary_provider=lambda: _conv_summary,
    )
```

- [ ] **Step 4: Delegate V10 `ask()` recent message assembly directly**

Replace the V10 recent-message line:

```python
recent=_get_smart_recent(conv, 12)  # v14.1: 12 messages (was 20) — less context = faster API
```

with:

```python
recent = build_recent_messages(
    conv,
    12,
    summarize_old=_summarize_old_conv,
    summary_provider=lambda: _conv_summary,
)  # v14.1: 12 messages (was 20) — less context = faster API
```

- [ ] **Step 5: Run GREEN**

Run: `uv run pytest tests/test_conversation_context.py tests/test_prompt_context_monolith.py tests/test_ask_routing_monolith.py tests/test_tool_dispatch_monolith.py -q`

Expected: PASS.

- [ ] **Step 6: Commit monolith delegation**

Run: `git add christine_final.py tests/test_prompt_context_monolith.py && git commit -m "refactor: delegate prompt context assembly"`

---

### Task 5: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Update M1 status text**

In `docs/ROADMAP.md`, add this completed M1 slice:

```markdown
- V10 prompt and recent-message context assembly delegates to
  `christine.conversation.context`.
```

Remove this remaining M1 slice:

```markdown
- Extract prompt/context construction around `build_prompt()`, `_get_smart_recent()`,
  and startup memory injection.
```

Adjust `Estimated remaining M1 effort` from `11-17 small slices` to `10-16 small slices`.

In `Immediate Next Slices`, remove:

```markdown
- Extract prompt/context construction for the V10 ask path.
```

- [ ] **Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

- [ ] **Step 3: Commit roadmap update**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after prompt context extraction"`

---

### Task 6: Final Verification And Review

**Files:**
- No planned edits.

- [ ] **Step 1: Run focused checks**

Run: `uv run pytest tests/test_conversation_context.py tests/test_prompt_context_monolith.py tests/test_ask_routing_monolith.py tests/test_tool_dispatch.py tests/test_tool_dispatch_monolith.py tests/test_runtime_routing_integration_guard.py tests/test_boot_contract.py -q`

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

Perform this session evidence-based review if subagent review is unavailable or likely to block. Check:

- `build_v10_system_prompt()` preserves the legacy prompt text and injection ordering.
- `build_recent_messages()` preserves shallow-copy, summary-update, summary-prefix, and recent-window behavior.
- V10 `ask()` still appends user input before recent-message construction.
- V10 tool loop, routing, budget, offline fallback, reply post-processing, memory save, and wrapper chain remain unchanged.
- No persisted data formats or runtime state artifacts changed.

- [ ] **Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
