"""Toolkit-free parent-side contracts for the Christine desktop GUI."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol

from .app import GuiQueues


@dataclass(frozen=True)
class GuiHostResult:
    """Content-free outcome for a GUI host lifecycle operation."""

    available: bool
    code: str


class GuiHost(Protocol):
    """The parent-side interface; implementations must not require a toolkit here."""

    def launch(self) -> GuiHostResult: ...

    def next_event(self) -> dict[str, object] | None: ...

    def send_reply(self, request_id: str, text: str) -> GuiHostResult: ...

    def close(self) -> GuiHostResult: ...


class GuiQueueBridge:
    """Move one child command and one matching backend reply per parent tick."""

    def __init__(self, queues: GuiQueues, host: GuiHost) -> None:
        self._queues = queues
        self._host = host
        self._pending_request_ids: deque[str] = deque()

    def sync_once(self) -> tuple[bool, GuiHostResult | None]:
        """Transfer at most one incoming command and one correlated reply.

        Backend output is left untouched until an incoming child command provides
        a request id to correlate it with.  This preserves the existing queue
        ownership for callers that have not yet opted into the desktop host.
        """
        received_command = self._receive_next_command()
        if not self._pending_request_ids or not self._queues.has_outputs():
            return received_command, None
        request_id = self._pending_request_ids.popleft()
        text = self._queues.next_output()
        if text is None:
            return received_command, None
        return received_command, self._host.send_reply(request_id, text)

    def _receive_next_command(self) -> bool:
        event = self._host.next_event()
        if event is None or event.get("kind") != "command":
            return False
        request_id = event.get("request_id")
        command = event.get("command")
        if not isinstance(request_id, str) or not isinstance(command, str):
            return False
        self._pending_request_ids.append(request_id)
        self._queues.submit_command(command)
        return True


__all__ = ["GuiHost", "GuiHostResult", "GuiQueueBridge"]
