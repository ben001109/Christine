from pathlib import Path


def _v10_ask_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("V10 ask()")
    end = text.index("# ╔", start + 1)
    return text[start:end]


def test_v10_ask_uses_router_tool_dedupe_helper():
    block = _v10_ask_block()

    assert "from christine.conversation.router import" in block
    assert "dedupe_tool_specs" in block
    assert "tools = dedupe_tool_specs(tools)" in block
    assert "_seen_names" not in block
