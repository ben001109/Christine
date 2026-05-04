from pathlib import Path


def _runtime_capability_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("# runtime capability tools")
    end = text.index("def pick(inp):", start)
    return text[start:end]


def test_runtime_capability_tools_use_tool_registry_helper():
    block = _runtime_capability_block()

    assert "ToolRegistration" in block
    assert "apply_tool_registrations" in block
    assert "tool_schema" in block
    assert "ALL = apply_tool_registrations" in block
    assert "EXTRA.extend" not in block
    assert "TM.update" not in block


def test_runtime_capability_tool_names_and_keywords_preserved():
    block = _runtime_capability_block()

    assert "capabilities_summary" in block
    assert "runtime_self_test" in block
    assert "功能" in block
    assert "self test" in block
