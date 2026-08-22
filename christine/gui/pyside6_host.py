"""Lazy, toolkit-free parent process for the future PySide6 desktop child."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
from collections.abc import Callable
from typing import Any

from .host import GuiHostResult
from .protocol import GuiProtocolError, decode_frame, encode_frame

_CHILD_COMMAND = ("-m", "christine.gui.pyside6_app", "--stdio")
_STREAM_ENDED = object()
_STREAM_FAILED = object()


class PySide6GuiHost:
    """Manage one GUI child without importing PySide6 in the parent process."""

    def __init__(
        self,
        *,
        executable: str | None = None,
        process_factory: Callable[..., Any] = subprocess.Popen,
        thread_factory: Callable[..., threading.Thread] = threading.Thread,
        handshake_timeout: float = 2.0,
        shutdown_timeout: float = 0.5,
    ) -> None:
        self._executable = executable or sys.executable
        self._process_factory = process_factory
        self._thread_factory = thread_factory
        self._handshake_timeout = handshake_timeout
        self._shutdown_timeout = shutdown_timeout
        self._process: Any | None = None
        self._events: queue.Queue[dict[str, object] | object] = queue.Queue()
        self._workers: list[threading.Thread] = []

    def launch(self) -> GuiHostResult:
        if self._is_running():
            return GuiHostResult(available=True, code="already_started")
        self._reset_closed_process()
        try:
            self._process = self._process_factory(
                [self._executable, *_CHILD_COMMAND],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0,
                close_fds=True,
            )
        except OSError:
            self._process = None
            return GuiHostResult(available=False, code="unavailable")
        self._start_readers()
        try:
            event = self._events.get(timeout=self._handshake_timeout)
        except queue.Empty:
            self._stop_process(send_close=False)
            return GuiHostResult(available=False, code="unavailable")
        if not isinstance(event, dict) or event.get("kind") != "ready":
            self._stop_process(send_close=False)
            return GuiHostResult(available=False, code="unavailable")
        return GuiHostResult(available=True, code="started")

    def next_event(self) -> dict[str, object] | None:
        if not self._is_running():
            return None
        try:
            event = self._events.get_nowait()
        except queue.Empty:
            return None
        if not isinstance(event, dict) or event.get("kind") not in {
            "command",
            "dialog_request",
            "close",
        }:
            self._stop_process(send_close=False)
            return None
        return event

    def send_reply(self, request_id: str, text: str) -> GuiHostResult:
        if not self._is_running():
            return GuiHostResult(available=False, code="unavailable")
        try:
            self._write_frame(
                {"version": 1, "kind": "reply", "request_id": request_id, "text": text}
            )
        except (GuiProtocolError, OSError, ValueError):
            self._stop_process(send_close=False)
            return GuiHostResult(available=False, code="unavailable")
        return GuiHostResult(available=True, code="sent")

    def close(self) -> GuiHostResult:
        if self._process is None:
            return GuiHostResult(available=False, code="closed")
        self._stop_process(send_close=True)
        return GuiHostResult(available=False, code="closed")

    def _is_running(self) -> bool:
        if self._process is None:
            return False
        if self._process.poll() is None:
            return True
        self._stop_process(send_close=False)
        return False

    def _reset_closed_process(self) -> None:
        if self._process is not None and self._process.poll() is not None:
            self._stop_process(send_close=False)

    def _start_readers(self) -> None:
        assert self._process is not None
        stdout = self._process.stdout
        stderr = self._process.stderr
        if stdout is None or stderr is None:
            self._stop_process(send_close=False)
            return
        self._workers = [
            self._start_worker(lambda: self._read_protocol(stdout)),
            self._start_worker(lambda: self._discard_stderr(stderr)),
        ]

    def _start_worker(self, target: Callable[[], None]) -> threading.Thread:
        worker = self._thread_factory(target=target, daemon=True)
        worker.start()
        return worker

    def _read_protocol(self, stream: Any) -> None:
        try:
            while True:
                line = stream.readline(65_537)
                if not line:
                    self._events.put(_STREAM_ENDED)
                    return
                self._events.put(decode_frame(line))
        except (GuiProtocolError, OSError, ValueError):
            self._events.put(_STREAM_FAILED)

    @staticmethod
    def _discard_stderr(stream: Any) -> None:
        try:
            while stream.read(4_096):
                pass
        except OSError:
            pass

    def _write_frame(self, frame: dict[str, object]) -> None:
        assert self._process is not None
        stdin = self._process.stdin
        if stdin is None:
            raise OSError("missing child stdin")
        stdin.write(encode_frame(frame))
        stdin.flush()

    def _stop_process(self, *, send_close: bool) -> None:
        process = self._process
        if process is None:
            return
        if send_close and process.poll() is None:
            try:
                self._write_frame({"version": 1, "kind": "close", "request_id": "host-close"})
            except (GuiProtocolError, OSError, ValueError):
                pass
        try:
            process.wait(timeout=self._shutdown_timeout)
        except subprocess.TimeoutExpired:
            try:
                process.terminate()
                process.wait(timeout=self._shutdown_timeout)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    process.kill()
                    process.wait(timeout=self._shutdown_timeout)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        except OSError:
            pass
        self._close_streams(process)
        for worker in self._workers:
            worker.join(timeout=self._shutdown_timeout)
        self._workers = []
        self._process = None

    @staticmethod
    def _close_streams(process: Any) -> None:
        for name in ("stdin", "stdout", "stderr"):
            stream = getattr(process, name, None)
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass


__all__ = ["PySide6GuiHost"]
