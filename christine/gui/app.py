from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class GuiMessage:
    role: str
    text: str


class GuiQueues:
    def __init__(self):
        self._user = deque()
        self._assistant = deque()
        self._commands = deque()
        self._outputs = deque()

    def submit_user(self, text: str) -> None:
        self._user.append(GuiMessage("user", text))

    def submit_assistant(self, text: str) -> None:
        self._assistant.append(GuiMessage("assistant", text))

    def next_user(self):
        return self._user.popleft() if self._user else None

    def next_assistant(self):
        return self._assistant.popleft() if self._assistant else None

    def submit_command(self, text: str) -> None:
        self._commands.append(text)

    def next_command(self):
        return self._commands.popleft() if self._commands else None

    def submit_output(self, text: str) -> None:
        self._outputs.append(text)

    def drain_outputs(self) -> list[str]:
        items = list(self._outputs)
        self._outputs.clear()
        return items
