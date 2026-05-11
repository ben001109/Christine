import christine.tools as tools


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
