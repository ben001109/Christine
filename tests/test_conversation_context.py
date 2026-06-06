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

    assert summarized == [
        [
            {"role": "user", "content": "old-1"},
            {"role": "assistant", "content": "old-2"},
            {"role": "user", "content": "old-3"},
        ]
    ]
    assert recent == [
        {"role": "user", "content": "[歷史摘要] 更新後摘要"},
        {"role": "assistant", "content": "recent-1"},
        {"role": "user", "content": "recent-2"},
    ]
