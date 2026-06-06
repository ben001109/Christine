from pathlib import Path


def _v10_ask_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V10 ask()")
    end = text.index("# === BUILT-IN EVOLUTION ADDON ===", start)
    return text[start:end]


def test_v10_tool_loop_delegates_runtime_tool_use_path():
    block = _v10_ask_block()

    assert "from christine.tools.dispatch import" in block
    assert "build_tool_loop_results" in block
    assert "on_tool_use=_v10_on_tool_use" in block
    assert "on_self_tool_result=_v10_on_self_tool_result" in block
    assert "execute_tool_handler(b.name, b.input, TM)" not in block
    assert "format_tool_result_message(b.id, b.name, r)" not in block
    assert "for b in getattr(resp, \"content\", [])" not in block
