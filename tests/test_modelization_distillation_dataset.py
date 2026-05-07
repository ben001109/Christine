import json

import pytest

from christine.modelization import DistillationExample, serialize_distillation_example_jsonl


def test_distillation_example_serializes_chat_and_tool_intent():
    example = DistillationExample(
        instruction="整理 Christine 的版本狀態",
        response="目前版本是 0.2.0-alpha.1。",
        source="repository-contracts",
        target="repository",
        tags=("versioning", "zh-TW"),
    )

    payload = json.loads(serialize_distillation_example_jsonl(example))

    assert payload == {
        "instruction": "整理 Christine 的版本狀態",
        "response": "目前版本是 0.2.0-alpha.1。",
        "source": "repository-contracts",
        "target": "repository",
        "tags": ["versioning", "zh-TW"],
    }


@pytest.mark.parametrize(
    "instruction,response",
    [("", "ok"), ("hi", "")],
)
def test_distillation_example_rejects_empty_instruction_or_response(instruction, response):
    with pytest.raises(ValueError):
        DistillationExample(instruction=instruction, response=response, source="x")
