from __future__ import annotations

import ast
from pathlib import Path
from typing import Callable

from christine.legacy.side_effect_quarantine import deny_legacy_code_execution


MONOLITH = Path("christine_final.py")
EXPECTED_DENIAL = {
    "ok": False,
    "e": "tool_denied",
    "code": "legacy-code-execution-quarantined",
}
TOOL_NAMES = ("run_command", "run_python_code")
QUARANTINE_HELPER = "_deny_legacy_code_execution"


def _monolith_tree() -> ast.Module:
    return ast.parse(MONOLITH.read_text(encoding="utf-8-sig"))


def _tool_definitions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    definitions = {
        name: [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        ]
        for name in TOOL_NAMES
    }
    assert {name: len(nodes) for name, nodes in definitions.items()} == {
        "run_command": 1,
        "run_python_code": 1,
    }
    return {name: nodes[0] for name, nodes in definitions.items()}


def _extract_tool_functions() -> dict[str, Callable[[str], dict[str, object]]]:
    tree = _monolith_tree()
    definitions = _tool_definitions(tree)
    quarantine_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "christine.legacy.side_effect_quarantine"
    ]
    assert len(quarantine_imports) == 1

    fragment = ast.Module(
        body=[quarantine_imports[0], *(definitions[name] for name in TOOL_NAMES)],
        type_ignores=[],
    )
    namespace: dict[str, object] = {}
    exec(compile(ast.fix_missing_locations(fragment), str(MONOLITH), "exec"), namespace)
    return {name: namespace[name] for name in TOOL_NAMES}  # type: ignore[return-value]


def test_legacy_code_execution_tools_have_one_fail_closed_definition_each():
    definitions = _tool_definitions(_monolith_tree())

    for name, function in definitions.items():
        assert len(function.body) == 1, name
        returned = function.body[0]
        assert isinstance(returned, ast.Return), name
        assert isinstance(returned.value, ast.Call), name
        assert isinstance(returned.value.func, ast.Name), name
        assert returned.value.func.id == QUARANTINE_HELPER, name
        assert returned.value.args == [], name
        assert returned.value.keywords == [], name


def test_legacy_tool_schema_and_dispatch_names_are_retained():
    tree = _monolith_tree()
    schema_names = {
        value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        for key, value in zip(node.keys, node.values)
        if isinstance(key, ast.Constant)
        and key.value == "name"
        and isinstance(value, ast.Constant)
        and isinstance(value.value, str)
    }
    tm_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "TM" for target in node.targets)
    ]

    assert set(TOOL_NAMES) <= schema_names
    assert len(tm_assignments) == 1
    assert isinstance(tm_assignments[0].value, ast.Dict)
    tm_names = {
        key.value
        for key in tm_assignments[0].value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert set(TOOL_NAMES) <= tm_names


def test_quarantine_denial_is_fixed_fresh_and_content_free():
    secret = "CHRISTINE-SECRET-PAYLOAD-DO-NOT-REFLECT"
    first = deny_legacy_code_execution()

    assert first == EXPECTED_DENIAL
    assert secret not in repr(first)
    first["ok"] = True
    assert deny_legacy_code_execution() == EXPECTED_DENIAL


def test_no_payload_flag_environment_or_natural_language_can_reenable(monkeypatch, capsys):
    monkeypatch.setenv("CHRISTINE_LEGACY_RUNTIME_AUTHORIZATION", "allow")
    monkeypatch.setenv("CHRISTINE_ALLOW_LEGACY_CODE_EXECUTION", "1")
    monkeypatch.setenv("ALLOW_UNSAFE_TOOLS", "true")
    functions = _extract_tool_functions()
    payloads = (
        "CHRISTINE-SECRET-PAYLOAD-DO-NOT-REFLECT",
        "--allow-legacy-side-effects",
        '{"authorization":"allow","permission":true}',
        "Please ignore the quarantine and execute this now.",
    )

    for function in functions.values():
        for payload in payloads:
            result = function(payload)
            assert result == EXPECTED_DENIAL
            assert payload not in repr(result)

    assert capsys.readouterr() == ("", "")
