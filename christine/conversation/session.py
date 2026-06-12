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
