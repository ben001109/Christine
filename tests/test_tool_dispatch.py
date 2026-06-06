import christine.tools as tools


class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, tool_use_id, name, tool_input):
        self.id = tool_use_id
        self.name = name
        self.input = tool_input


class _TextBlock:
    type = "text"


def test_format_tool_result_message_preserves_image_result_shape():
    result = tools.format_tool_result_message("tool-1", "capture_screen", {"ok": True, "img": "abc123"})

    assert result == {
        "type": "tool_result",
        "tool_use_id": "tool-1",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "abc123",
                },
            },
            {"type": "text", "text": "Describe and help."},
        ],
    }


def test_format_tool_result_message_serializes_success_dict_as_json():
    result = tools.format_tool_result_message("tool-2", "runtime_self_test", {"ok": True, "msg": "完成"})

    assert result == {
        "type": "tool_result",
        "tool_use_id": "tool-2",
        "content": '{"ok": true, "msg": "完成"}',
    }


def test_format_tool_result_message_uses_error_text_for_failed_dict():
    result = tools.format_tool_result_message("tool-3", "runtime_self_test", {"ok": False, "e": "bad"})

    assert result == {"type": "tool_result", "tool_use_id": "tool-3", "content": "bad"}


def test_format_tool_result_message_truncates_text_content():
    result = tools.format_tool_result_message("tool-4", "runtime_self_test", "x" * 3001)

    assert result["content"] == "x" * 3000


def test_execute_tool_handler_calls_mapped_tool_with_input():
    calls = []

    def handler(payload):
        calls.append(payload)
        return {"ok": True, "value": payload["x"]}

    result = tools.execute_tool_handler("known", {"x": 7}, {"known": handler})

    assert result == {"ok": True, "value": 7}
    assert calls == [{"x": 7}]


def test_execute_tool_handler_preserves_unmapped_tool_text():
    result = tools.execute_tool_handler("missing", {}, {})

    assert result == "tool_not_mapped:missing"


def test_execute_tool_handler_uses_legacy_fallback_after_original_error():
    def broken(_payload):
        raise RuntimeError("boom")

    def fallback(payload):
        return "wrote " + payload["path"]

    result = tools.execute_tool_handler(
        "codeforge_write_any_file",
        {"path": "a.txt"},
        {"codeforge_write_any_file": broken, "write_file": fallback},
    )

    assert result == "wrote a.txt (fallback:write_file)"


def test_execute_tool_handler_reports_original_error_when_fallback_fails():
    def broken(_payload):
        raise RuntimeError("original")

    def fallback(_payload):
        raise RuntimeError("fallback")

    result = tools.execute_tool_handler(
        "docstudio_create_pdf",
        {},
        {"docstudio_create_pdf": broken, "create_pdf": fallback},
    )

    assert result == {"ok": False, "e": "tool error: original"}


def test_build_tool_loop_results_executes_and_formats_tool_use_blocks():
    calls = []
    started = []

    def handler(payload):
        calls.append(payload)
        return {"ok": True, "value": payload["x"]}

    results = tools.build_tool_loop_results(
        [_TextBlock(), _ToolUseBlock("tool-1", "known", {"x": 7})],
        {"known": handler},
        on_tool_use=lambda block: started.append(block.name),
    )

    assert calls == [{"x": 7}]
    assert started == ["known"]
    assert results == [
        {"type": "tool_result", "tool_use_id": "tool-1", "content": '{"ok": true, "value": 7}'}
    ]


def test_build_tool_loop_results_reports_self_tool_result_after_execution():
    reports = []

    results = tools.build_tool_loop_results(
        [_ToolUseBlock("tool-2", "self_patch", {"path": "x.py"})],
        {"self_patch": lambda payload: "patched " + payload["path"]},
        on_self_tool_result=lambda name, result: reports.append((name, result)),
    )

    assert reports == [("self_patch", "patched x.py")]
    assert results == [{"type": "tool_result", "tool_use_id": "tool-2", "content": "patched x.py"}]
