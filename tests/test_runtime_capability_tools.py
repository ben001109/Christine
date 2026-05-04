from christine.tools.registry import ToolRegistration
from christine.tools.runtime_capabilities import (
    RUNTIME_CAPABILITY_KEYWORDS,
    build_runtime_capability_registrations,
)


def test_runtime_capability_registrations_preserve_schema_names_and_keywords():
    registrations = build_runtime_capability_registrations(
        capabilities_summary=lambda topic: "summary:" + topic,
        runtime_self_test=lambda: "self-test",
    )

    assert all(isinstance(registration, ToolRegistration) for registration in registrations)
    assert [registration.name for registration in registrations] == ["capabilities_summary", "runtime_self_test"]
    assert registrations[0].schema == {
        "name": "capabilities_summary",
        "description": "summarize current capabilities",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": [],
        },
    }
    assert registrations[1].schema == {
        "name": "runtime_self_test",
        "description": "run local runtime diagnostics",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
    assert registrations[0].keywords == RUNTIME_CAPABILITY_KEYWORDS
    assert "功能" in RUNTIME_CAPABILITY_KEYWORDS
    assert "self test" in RUNTIME_CAPABILITY_KEYWORDS


def test_runtime_capability_handlers_delegate_to_injected_functions():
    calls = []

    def capabilities_summary(topic):
        calls.append(("summary", topic))
        return "summary:" + topic

    def runtime_self_test():
        calls.append(("self_test", None))
        return "self-test"

    registrations = build_runtime_capability_registrations(capabilities_summary, runtime_self_test)

    assert registrations[0].handler({"topic": "tools"}) == "summary:tools"
    assert registrations[1].handler({}) == "self-test"
    assert calls == [("summary", "tools"), ("self_test", None)]
