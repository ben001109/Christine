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
