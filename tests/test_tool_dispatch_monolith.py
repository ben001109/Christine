from pathlib import Path


def _v10_ask_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_tool_loop_delegates_tool_result_formatting():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import" in block
    assert "format_tool_result_message" in block
    assert "format_tool_result_message(b.id, b.name, r)" in block
    assert 'media_type":"image/png' not in block
    assert "json.dumps(r, ensure_ascii=False)" not in block
    assert "rx[:3000]" not in block


def test_v10_tool_loop_delegates_tool_execution():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import" in block
    assert "execute_tool_handler" in block
    assert "execute_tool_handler(b.name, b.input, TM)" in block
    assert "fallback_map={" not in block
    assert "TM[b.name](b.input)" not in block
    assert "tool_not_mapped:" not in block
