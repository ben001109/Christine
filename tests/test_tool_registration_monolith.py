from pathlib import Path


def _runtime_capability_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("# runtime capability tools")
    end = text.index("def pick(inp):", start)
    return text[start:end]


def _pick_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("def pick(inp):")
    end = text.index("def listen_wake():", start)
    return text[start:end]


def test_runtime_capability_tools_use_runtime_capability_factory():
    block = _runtime_capability_block()

    assert "from christine.tools.runtime_capabilities import build_runtime_capability_registrations" in block
    assert "build_runtime_capability_registrations(" in block
    assert "apply_tool_registrations" in block
    assert "ALL = apply_tool_registrations" in block
    assert "ToolRegistration(" not in block
    assert "tool_schema(" not in block
    assert "EXTRA.extend" not in block
    assert "TM.update" not in block


def test_runtime_capability_tool_names_and_keywords_preserved():
    block = _runtime_capability_block()

    assert "capabilities_summary" in block
    assert "runtime_self_test" in block
    assert "capabilities_summary=capabilities_summary" in block
    assert "runtime_self_test=runtime_self_test" in block


def test_pick_delegates_to_tool_selection_helper():
    text = Path("christine_final.py").read_text(encoding="utf-8")
    block = _pick_block()

    assert "from christine.tools.selection import pick_all_tools" in text
    assert "return pick_all_tools(inp, ALL)" in block
    assert "return ALL" not in block
