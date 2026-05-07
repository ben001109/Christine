from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class DistillationExample:
    instruction: str
    response: str
    source: str
    target: str = "direct"
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.instruction.strip() or not self.response.strip():
            raise ValueError("distillation examples require instruction and response")


def serialize_distillation_example_jsonl(example: DistillationExample) -> str:
    return json.dumps(
        {
            "instruction": example.instruction,
            "response": example.response,
            "source": example.source,
            "target": example.target,
            "tags": list(example.tags),
        },
        ensure_ascii=False,
    )
