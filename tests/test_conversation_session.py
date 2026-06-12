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
