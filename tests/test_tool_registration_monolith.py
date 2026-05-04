from pathlib import Path


def _runtime_capability_block() -> str:
    text = Path("christine_final.py").read_text(encoding="utf-8")
    start = text.index("# runtime capability tools")
    end = text.index("def pick(inp):", start)
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
