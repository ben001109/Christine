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
    _ = inp
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
