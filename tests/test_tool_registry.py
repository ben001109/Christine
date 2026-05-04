from christine.tools.registry import ToolRegistration, apply_tool_registrations, tool_schema


def test_tool_schema_builds_legacy_anthropic_shape():
    schema = tool_schema(
        "runtime_self_test",
        "run local runtime diagnostics",
        properties={"topic": {"type": "string"}},
        required=[],
    )

    assert schema == {
        "name": "runtime_self_test",
        "description": "run local runtime diagnostics",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": [],
        },
    }


def test_apply_tool_registrations_extends_schemas_handlers_and_keywords():
    extra = []
    tm = {}
    kw = ["existing"]

    registration = ToolRegistration(
        schema=tool_schema("capabilities_summary", "summarize", required=[]),
        handler=lambda args: f"topic={args.get('topic', '')}",
        keywords=("能力", "existing", "capabilities"),
    )

    all_tools = apply_tool_registrations(
        core=[{"name": "get_current_time"}],
        extra=extra,
        handlers=tm,
        keywords=kw,
        registrations=[registration],
    )

    assert extra == [registration.schema]
    assert all_tools == [{"name": "get_current_time"}, registration.schema]
    assert tm["capabilities_summary"]({"topic": "tools"}) == "topic=tools"
    assert kw == ["existing", "能力", "capabilities"]


def test_apply_tool_registrations_allows_schema_without_handler():
    extra = []
    tm = {"old": lambda args: "old"}
    kw = []

    registration = ToolRegistration(schema=tool_schema("schema_only", "schema only"))

    apply_tool_registrations([], extra, tm, kw, [registration])

    assert extra == [registration.schema]
    assert sorted(tm) == ["old"]
