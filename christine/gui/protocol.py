"""Strict, toolkit-free JSON Lines protocol for the desktop GUI boundary.

The protocol deliberately returns one content-free error for every malformed
frame.  Callers must keep user text, file paths, and raw frames out of errors
and logs unless a later, explicitly reviewed boundary authorizes them.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Final

PROTOCOL_VERSION: Final = 1
MAX_FRAME_BYTES: Final = 64 * 1024
MAX_TEXT_CHARS: Final = 16 * 1024
MAX_PATH_CHARS: Final = 4 * 1024
MAX_REQUEST_ID_CHARS: Final = 128

_INVALID_FRAME_MESSAGE: Final = "invalid-gui-protocol-frame"
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_DIALOGS: Final = frozenset({"open_image", "generate_image"})
_ERROR_CODES: Final = frozenset({"invalid_request", "operation_failed", "unavailable"})
_SCHEMAS: Final = {
    "ready": frozenset({"version", "kind"}),
    "command": frozenset({"version", "kind", "request_id", "command"}),
    "reply": frozenset({"version", "kind", "request_id", "text"}),
    "dialog_request": frozenset({"version", "kind", "request_id", "dialog"}),
    "dialog_result": frozenset(
        {"version", "kind", "request_id", "dialog", "selected_path"}
    ),
    "close": frozenset({"version", "kind", "request_id"}),
    "error": frozenset({"version", "kind", "request_id", "code"}),
}


class GuiProtocolError(ValueError):
    """Raised for every invalid protocol frame without exposing its contents."""

    def __init__(self) -> None:
        super().__init__(_INVALID_FRAME_MESSAGE)


def encode_frame(frame: Mapping[str, object]) -> bytes:
    """Validate and encode one protocol frame as a UTF-8 JSON Lines record."""
    normalized = _validated_frame(frame)
    try:
        encoded = json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise GuiProtocolError() from exc
    if len(encoded) + 1 > MAX_FRAME_BYTES:
        raise GuiProtocolError()
    return encoded + b"\n"


def decode_frame(line: bytes | str) -> dict[str, object]:
    """Decode and validate exactly one UTF-8 JSON Lines record."""
    try:
        raw = line.encode("utf-8") if isinstance(line, str) else bytes(line)
    except (TypeError, UnicodeEncodeError, ValueError) as exc:
        raise GuiProtocolError() from exc
    if len(raw) > MAX_FRAME_BYTES:
        raise GuiProtocolError()
    if not raw.endswith(b"\n") or raw[:-1].find(b"\n") != -1:
        raise GuiProtocolError()
    try:
        decoded = json.loads(
            raw[:-1].decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuiProtocolError() from exc
    return _validated_frame(decoded)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise GuiProtocolError()
        result[key] = value
    return result


def _reject_non_json_constant(_value: str) -> None:
    raise GuiProtocolError()


def _validated_frame(frame: object) -> dict[str, object]:
    if not isinstance(frame, Mapping):
        raise GuiProtocolError()
    candidate = dict(frame)
    version = candidate.get("version")
    kind = candidate.get("kind")
    if type(version) is not int or version != PROTOCOL_VERSION or not isinstance(kind, str):
        raise GuiProtocolError()
    expected_keys = _SCHEMAS.get(kind)
    if expected_keys is None or set(candidate) != expected_keys:
        raise GuiProtocolError()
    if kind != "ready":
        _validate_request_id(candidate["request_id"])
    if kind in {"command", "reply"}:
        _validate_text(candidate["command"] if kind == "command" else candidate["text"])
    elif kind in {"dialog_request", "dialog_result"}:
        _validate_dialog(candidate["dialog"])
        if kind == "dialog_result":
            _validate_selected_path(candidate["selected_path"])
    elif kind == "error":
        _validate_error_code(candidate["code"])
    return candidate


def _validate_request_id(value: object) -> None:
    if not isinstance(value, str) or not _REQUEST_ID.fullmatch(value):
        raise GuiProtocolError()


def _validate_text(value: object) -> None:
    if not isinstance(value, str) or len(value) > MAX_TEXT_CHARS:
        raise GuiProtocolError()


def _validate_dialog(value: object) -> None:
    if value not in _DIALOGS:
        raise GuiProtocolError()


def _validate_selected_path(value: object) -> None:
    if value is not None and (not isinstance(value, str) or len(value) > MAX_PATH_CHARS):
        raise GuiProtocolError()


def _validate_error_code(value: object) -> None:
    if value not in _ERROR_CODES:
        raise GuiProtocolError()


__all__ = [
    "GuiProtocolError",
    "MAX_FRAME_BYTES",
    "MAX_PATH_CHARS",
    "MAX_REQUEST_ID_CHARS",
    "MAX_TEXT_CHARS",
    "PROTOCOL_VERSION",
    "decode_frame",
    "encode_frame",
]
