from __future__ import annotations

from pathlib import Path

import pytest

from christine.gui.protocol import (
    MAX_FRAME_BYTES,
    MAX_PATH_CHARS,
    MAX_TEXT_CHARS,
    GuiProtocolError,
    decode_frame,
    encode_frame,
)


@pytest.mark.parametrize(
    "frame",
    [
        {"version": 1, "kind": "ready"},
        {"version": 1, "kind": "command", "request_id": "cmd-1", "command": "你好\nChristine"},
        {"version": 1, "kind": "reply", "request_id": "cmd-1", "text": "已收到"},
        {"version": 1, "kind": "dialog_request", "request_id": "dialog-1", "dialog": "open_image"},
        {"version": 1, "kind": "dialog_result", "request_id": "dialog-1", "dialog": "open_image", "selected_path": "/tmp/photo.png"},
        {"version": 1, "kind": "dialog_result", "request_id": "dialog-2", "dialog": "open_image", "selected_path": None},
        {"version": 1, "kind": "close", "request_id": "close-1"},
        {"version": 1, "kind": "error", "request_id": "cmd-2", "code": "operation_failed"},
    ],
)
def test_protocol_round_trips_all_v1_frame_types(frame):
    encoded = encode_frame(frame)

    assert encoded.endswith(b"\n")
    assert encoded.count(b"\n") == 1
    assert decode_frame(encoded) == frame


def test_dialog_result_supports_explicit_user_cancellation():
    encoded = encode_frame(
        {
            "version": 1,
            "kind": "dialog_result",
            "request_id": "image-1",
            "dialog": "open_image",
            "selected_path": None,
        }
    )

    assert decode_frame(encoded)["selected_path"] is None


@pytest.mark.parametrize(
    "frame",
    [
        {"version": 2, "kind": "ready"},
        {"version": True, "kind": "ready"},
        {"version": 1, "kind": "unknown"},
        {"version": 1, "kind": "ready", "extra": "nope"},
        {"version": 1, "kind": "command", "request_id": "bad id", "command": "hello"},
        {"version": 1, "kind": "command", "request_id": "cmd-1", "command": 1},
        {"version": 1, "kind": "reply", "request_id": "cmd-1"},
        {"version": 1, "kind": "dialog_request", "request_id": "dialog-1", "dialog": "open_file"},
        {"version": 1, "kind": "dialog_result", "request_id": "dialog-1", "dialog": "open_image", "selected_path": 1},
        {"version": 1, "kind": "error", "request_id": "cmd-1", "code": "payload:secret"},
    ],
)
def test_protocol_rejects_unknown_extra_or_invalid_fields(frame):
    _assert_content_free_invalid_frame(lambda: encode_frame(frame))


@pytest.mark.parametrize(
    "line",
    [
        b'{"version":1,"kind":"ready","kind":"ready"}\n',
        b'{"version":1,"kind":"ready"}\n{"version":1,"kind":"ready"}\n',
        b'{"version":1,"kind":"ready","extra":"secret"}\n',
        b'{"version":NaN,"kind":"ready"}\n',
        b'\xff\n',
        b'{not-json}\n',
        b'{"version":1,"kind":"ready"}',
    ],
)
def test_protocol_rejects_malformed_json_lines_without_echoing_contents(line):
    _assert_content_free_invalid_frame(lambda: decode_frame(line))


def test_protocol_rejects_oversized_text_path_and_frame():
    _assert_content_free_invalid_frame(
        lambda: encode_frame(
            {"version": 1, "kind": "command", "request_id": "cmd-1", "command": "x" * (MAX_TEXT_CHARS + 1)}
        )
    )
    _assert_content_free_invalid_frame(
        lambda: encode_frame(
            {
                "version": 1,
                "kind": "dialog_result",
                "request_id": "dialog-1",
                "dialog": "open_image",
                "selected_path": "x" * (MAX_PATH_CHARS + 1),
            }
        )
    )
    _assert_content_free_invalid_frame(lambda: decode_frame(b"x" * MAX_FRAME_BYTES + b"\n"))


def test_protocol_module_has_no_gui_toolkit_import_boundary():
    source = Path(__file__).resolve().parents[1] / "christine" / "gui" / "protocol.py"
    text = source.read_text(encoding="utf-8")

    assert "tkinter" not in text
    assert "PySide6" not in text


def _assert_content_free_invalid_frame(operation):
    with pytest.raises(GuiProtocolError) as exc_info:
        operation()

    assert str(exc_info.value) == "invalid-gui-protocol-frame"
    assert "secret" not in str(exc_info.value)
