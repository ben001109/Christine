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

    def submit_user(self, text: str) -> None:
        self._user.append(GuiMessage("user", text))

    def submit_assistant(self, text: str) -> None:
        self._assistant.append(GuiMessage("assistant", text))

    def next_user(self):
        return self._user.popleft() if self._user else None

    def next_assistant(self):
        return self._assistant.popleft() if self._assistant else None
