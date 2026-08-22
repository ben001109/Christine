from __future__ import annotations

import subprocess
import sys
from collections import deque
from pathlib import Path

import pytest

from christine.gui.app import GuiQueues
from christine.gui.host import GuiHostResult, GuiQueueBridge
from christine.gui.protocol import encode_frame
from christine.gui.pyside6_host import PySide6GuiHost


class _FakePipe:
    def __init__(self, lines=(), *, fail_write: bool = False):
        self._lines = deque(lines)
        self._fail_write = fail_write
        self.writes: list[bytes] = []
        self.closed = False

    def readline(self, _limit: int) -> bytes:
        return self._lines.popleft() if self._lines else b""

    def read(self, _limit: int) -> bytes:
        return b""

    def write(self, value: bytes) -> int:
        if self._fail_write:
            raise OSError("broken pipe")
        self.writes.append(value)
        return len(value)

    def flush(self) -> None:
        if self._fail_write:
            raise OSError("broken pipe")

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(self, output_lines=(), *, fail_write: bool = False, exit_code=None):
        self.stdin = _FakePipe(fail_write=fail_write)
        self.stdout = _FakePipe(output_lines)
        self.stderr = _FakePipe()
        self.exit_code = exit_code
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.exit_code

    def wait(self, *, timeout: float):
        if self.exit_code is None:
            raise subprocess.TimeoutExpired("fake", timeout)
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True
        self.exit_code = -15

    def kill(self) -> None:
        self.killed = True
        self.exit_code = -9


class _InlineThread:
    def __init__(self, *, target, daemon: bool):
        self._target = target
        self.daemon = daemon

    def start(self) -> None:
        self._target()

    def join(self, *, timeout: float) -> None:
        return None


class _NeverStartingThread(_InlineThread):
    def start(self) -> None:
        return None


class _FakeHost:
    def __init__(self, events=()):
        self._events = deque(events)
        self.replies: list[tuple[str, str]] = []

    def launch(self) -> GuiHostResult:
        return GuiHostResult(available=True, code="started")

    def next_event(self):
        return self._events.popleft() if self._events else None

    def send_reply(self, request_id: str, text: str) -> GuiHostResult:
        self.replies.append((request_id, text))
        return GuiHostResult(available=True, code="sent")

    def close(self) -> GuiHostResult:
        return GuiHostResult(available=False, code="closed")


def _host_for(process: _FakeProcess):
    calls = []

    def factory(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    return PySide6GuiHost(process_factory=factory, thread_factory=_InlineThread), calls


def test_host_is_lazy_and_starts_child_with_no_shell_after_ready_handshake():
    process = _FakeProcess([encode_frame({"version": 1, "kind": "ready"})])
    host, calls = _host_for(process)

    assert calls == []
    assert host.launch() == GuiHostResult(available=True, code="started")
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == ([sys.executable, "-m", "christine.gui.pyside6_app", "--stdio"],)
    assert kwargs == {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": False,
        "bufsize": 0,
        "close_fds": True,
    }


def test_host_returns_content_free_unavailable_for_missing_or_invalid_handshake():
    process = _FakeProcess([encode_frame({"version": 1, "kind": "command", "request_id": "cmd-1", "command": "hello"})])
    host, _calls = _host_for(process)

    assert host.launch() == GuiHostResult(available=False, code="unavailable")
    assert process.terminated is True


def test_host_handshake_timeout_terminates_and_closes_child_streams():
    process = _FakeProcess()
    host = PySide6GuiHost(
        process_factory=lambda *args, **kwargs: process,
        thread_factory=_NeverStartingThread,
        handshake_timeout=0,
    )

    assert host.launch() == GuiHostResult(available=False, code="unavailable")
    assert process.terminated is True
    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_host_forwards_child_command_and_sends_correlated_reply():
    process = _FakeProcess(
        [
            encode_frame({"version": 1, "kind": "ready"}),
            encode_frame({"version": 1, "kind": "command", "request_id": "cmd-1", "command": "你好"}),
        ]
    )
    host, _calls = _host_for(process)

    assert host.launch().available is True
    assert host.next_event() == {"version": 1, "kind": "command", "request_id": "cmd-1", "command": "你好"}
    assert host.send_reply("cmd-1", "收到") == GuiHostResult(available=True, code="sent")
    assert process.stdin.writes == [
        encode_frame({"version": 1, "kind": "reply", "request_id": "cmd-1", "text": "收到"})
    ]


def test_host_broken_pipe_fails_closed_without_exception_content():
    process = _FakeProcess([encode_frame({"version": 1, "kind": "ready"})], fail_write=True)
    host, _calls = _host_for(process)

    assert host.launch().available is True
    assert host.send_reply("cmd-1", "secret") == GuiHostResult(available=False, code="unavailable")
    assert process.terminated is True


@pytest.mark.parametrize("output_lines", [[], [b"{not-json}\n"]])
def test_host_eof_or_malformed_post_ready_frame_fails_closed(output_lines):
    process = _FakeProcess([encode_frame({"version": 1, "kind": "ready"}), *output_lines])
    host, _calls = _host_for(process)

    assert host.launch().available is True
    assert host.next_event() is None
    assert process.terminated is True
    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_host_crash_detection_immediately_reclaims_streams_and_workers():
    process = _FakeProcess([encode_frame({"version": 1, "kind": "ready"})])
    host, _calls = _host_for(process)

    assert host.launch().available is True
    process.exit_code = 1
    assert host.next_event() is None
    assert host.send_reply("cmd-1", "secret") == GuiHostResult(available=False, code="unavailable")
    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_host_close_requests_close_then_terminates_to_avoid_orphans():
    process = _FakeProcess([encode_frame({"version": 1, "kind": "ready"})])
    host, _calls = _host_for(process)

    assert host.launch().available is True
    assert host.close() == GuiHostResult(available=False, code="closed")
    assert process.stdin.writes == [
        encode_frame({"version": 1, "kind": "close", "request_id": "host-close"})
    ]
    assert process.terminated is True
    assert process.stdin.closed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True


def test_queue_bridge_preserves_fifo_correlation_and_does_not_consume_unowned_output():
    queues = GuiQueues()
    queues.submit_output("existing output")
    host = _FakeHost(
        [
            {"version": 1, "kind": "command", "request_id": "cmd-1", "command": "first"},
            {"version": 1, "kind": "command", "request_id": "cmd-2", "command": "second"},
        ]
    )
    bridge = GuiQueueBridge(queues, host)

    assert bridge.sync_once() == (True, GuiHostResult(available=True, code="sent"))
    assert queues.next_command() == "first"
    assert host.replies == [("cmd-1", "existing output")]
    queues.submit_output("second output")
    assert bridge.sync_once() == (True, GuiHostResult(available=True, code="sent"))
    assert queues.next_command() == "second"
    assert host.replies == [("cmd-1", "existing output"), ("cmd-2", "second output")]


def test_queue_bridge_leaves_output_untouched_until_a_child_command_arrives():
    queues = GuiQueues()
    queues.submit_output("backend only")
    bridge = GuiQueueBridge(queues, _FakeHost())

    assert bridge.sync_once() == (False, None)
    assert queues.drain_outputs() == ["backend only"]


def test_parent_host_source_does_not_import_a_gui_toolkit():
    source = Path(__file__).resolve().parents[1] / "christine" / "gui" / "pyside6_host.py"
    text = source.read_text(encoding="utf-8")

    assert "import tkinter" not in text
    assert "import PySide6" not in text
