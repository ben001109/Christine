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


def _v1484_ask_wrapper_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("_v180_prev_ask = globals().get(\"ask\")")
    end = text.index("ask.__v180_wrapped__ = True", start)
    return text[start:end]


def test_v1484_ask_wrapper_uses_observed_router_voice_hint_helper():
    block = _v1484_ask_wrapper_block()

    assert "route_observed_voice_then_fallback" in block
    assert "_v180_try_voice" in block
    assert "_v180_prev_ask" in block
    assert "brain_hint(as_prompt=True)" in block
    assert "_v180_observe_runtime_route(inp)" not in block
