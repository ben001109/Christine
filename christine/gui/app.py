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

    def has_commands(self) -> bool:
        return bool(self._commands)

    def submit_output(self, text: str) -> None:
        self._outputs.append(text)

    def next_output(self):
        return self._outputs.popleft() if self._outputs else None

    def has_outputs(self) -> bool:
        return bool(self._outputs)

    def drain_outputs(self) -> list[str]:
        items = list(self._outputs)
        self._outputs.clear()
        return items


class _LegacyQueueAdapter:
    def __init__(self, append_fn, pop_fn, has_items_fn):
        self._append_fn = append_fn
        self._pop_fn = pop_fn
        self._has_items_fn = has_items_fn

    def append(self, item):
        self._append_fn(item)

    def pop(self, index=0):
        if index != 0:
            raise IndexError("legacy GUI queues only support pop(0)")
        return self._pop_fn()

    def __bool__(self):
        return self._has_items_fn()


def create_legacy_queue_adapters():
    queues = GuiQueues()
    input_queue = _LegacyQueueAdapter(
        queues.submit_command,
        queues.next_command,
        lambda: queues.has_commands(),
    )
    output_queue = _LegacyQueueAdapter(
        queues.submit_output,
        queues.next_output,
        lambda: queues.has_outputs(),
    )
    return queues, input_queue, output_queue
