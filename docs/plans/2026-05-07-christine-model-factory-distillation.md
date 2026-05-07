# Model Factory Distillation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a safe, local-first Model Factory that can prepare Christine-specific datasets, evaluate teacher/student behavior, and later train LoRA/QLoRA adapters without violating data, licensing, or runtime-safety boundaries.

**Architecture:** Extend the existing `christine.modelization` safety boundary instead of training first. The factory starts with legal/source policy, deterministic dataset schemas, local eval gates, provider abstractions, and artifact registries; actual training and runtime deployment remain disabled until the dataset/eval gates prove safe and useful.

**Tech Stack:** Python 3.10+, `uv`, pytest, dataclasses/pathlib/jsonl, existing `christine.modelization` modules, optional future extras for `transformers`, `datasets`, `peft`, `trl`, `bitsandbytes`, Ollama/llama.cpp/vLLM, and GPU tooling.

---

## Current Version And Stage

**Target Version:** `0.2.0-alpha.1`

**Package Metadata Version:** `0.2.0a1`

**Stage:** `alpha`

This plan is design-only until explicitly executed. It must not add training dependencies, download models, call teacher APIs, read private state, or write model artifacts in the planning slice.

---

## Requirements Captured

- Christine should eventually produce a local Christine-specific model or adapter, not train a GPT-scale model from scratch.
- The first target is LoRA/QLoRA fine-tuning or behavior distillation on top of a legal open-source student model.
- Distillation must only use teacher outputs that are legally allowed by provider terms and model licenses.
- Raw private runtime state such as `data/`, `growth.log`, `heartbeat.txt`, `nexus_v2_state.json`, logs, backups, mirrors, and generated cortex files must stay excluded unless a separate migration and privacy review approves a summarized derivative.
- Model outputs that can affect tools, files, GUI, memory, deployment, shell commands, or self-upgrade must pass deterministic policy gates.
- A model that does not beat deterministic baselines remains advisory or disabled.
- Training artifacts must not be committed to the repository.

## Non-Goals

- No from-scratch pretraining.
- No automatic scraping of private memories or raw conversation logs.
- No cloud upload of repository or memory data.
- No runtime switch to an untested student model.
- No replacement of `christine_final.py`, `boot_christine.py`, or Windows launchers.
- No new formula/theorem/consciousness claims.

---

### Task 1: Add Distillation Policy Contract

**Files:**
- Create: `christine/modelization/distillation_policy.py`
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_distillation_policy.py`

**Step 1: Write failing tests**

Create `tests/test_modelization_distillation_policy.py`:

```python
import pytest

from christine.modelization import (
    DistillationDataSource,
    DistillationSourceKind,
    validate_distillation_source,
)


def test_distillation_policy_accepts_reviewed_project_corpus_source():
    source = DistillationDataSource(
        name="repository-contracts",
        kind=DistillationSourceKind.PROJECT_CORPUS,
        license="project-owned",
        reviewed=True,
    )

    assert validate_distillation_source(source).allowed is True


def test_distillation_policy_rejects_unreviewed_private_memory():
    source = DistillationDataSource(
        name="raw-memory",
        kind=DistillationSourceKind.PRIVATE_MEMORY,
        license="user-private",
        reviewed=False,
    )

    decision = validate_distillation_source(source)

    assert decision.allowed is False
    assert decision.reason == "unreviewed-private-source"


def test_distillation_policy_rejects_unknown_teacher_terms():
    source = DistillationDataSource(
        name="teacher-output",
        kind=DistillationSourceKind.TEACHER_OUTPUT,
        license="unknown",
        reviewed=True,
    )

    decision = validate_distillation_source(source)

    assert decision.allowed is False
    assert decision.reason == "teacher-license-not-approved"


def test_distillation_policy_rejects_unknown_source_kind():
    with pytest.raises(ValueError, match="unknown distillation source kind"):
        DistillationSourceKind("unknown")
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_distillation_policy.py -q`

Expected: FAIL because `christine.modelization.distillation_policy` does not exist.

**Step 3: Implement minimal policy module**

Create `christine/modelization/distillation_policy.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DistillationSourceKind(str, Enum):
    PROJECT_CORPUS = "project_corpus"
    PRIVATE_MEMORY = "private_memory"
    TEACHER_OUTPUT = "teacher_output"
    SYNTHETIC_SELF_PLAY = "synthetic_self_play"


@dataclass(frozen=True)
class DistillationDataSource:
    name: str
    kind: DistillationSourceKind
    license: str
    reviewed: bool = False


@dataclass(frozen=True)
class DistillationSourceDecision:
    allowed: bool
    reason: str


APPROVED_TEACHER_LICENSES = {"apache-2.0", "mit", "cc-by-4.0", "project-owned"}


def validate_distillation_source(source: DistillationDataSource) -> DistillationSourceDecision:
    if source.kind == DistillationSourceKind.PRIVATE_MEMORY and not source.reviewed:
        return DistillationSourceDecision(False, "unreviewed-private-source")
    if source.kind == DistillationSourceKind.TEACHER_OUTPUT and source.license not in APPROVED_TEACHER_LICENSES:
        return DistillationSourceDecision(False, "teacher-license-not-approved")
    if not source.reviewed:
        return DistillationSourceDecision(False, "source-not-reviewed")
    return DistillationSourceDecision(True, "allowed")
```

Export these symbols from `christine/modelization/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_modelization_distillation_policy.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/modelization/distillation_policy.py christine/modelization/__init__.py tests/test_modelization_distillation_policy.py && git commit -m "refactor: add distillation source policy"`

Expected: commit succeeds.

---

### Task 2: Add Dataset Example Schema

**Files:**
- Create: `christine/modelization/distillation_dataset.py`
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_distillation_dataset.py`

**Step 1: Write failing tests**

Create `tests/test_modelization_distillation_dataset.py`:

```python
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
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_distillation_dataset.py -q`

Expected: FAIL because dataset schema module does not exist.

**Step 3: Implement minimal schema**

Create `christine/modelization/distillation_dataset.py`:

```python
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
```

Export these symbols from `christine/modelization/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_modelization_distillation_dataset.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/modelization/distillation_dataset.py christine/modelization/__init__.py tests/test_modelization_distillation_dataset.py && git commit -m "refactor: add distillation dataset schema"`

Expected: commit succeeds.

---

### Task 3: Add Eval Gate For Student Models

**Files:**
- Create: `christine/modelization/distillation_eval.py`
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_distillation_eval.py`

**Step 1: Write failing tests**

Create `tests/test_modelization_distillation_eval.py`:

```python
from christine.modelization import DistillationEvalResult, assess_distillation_readiness


def test_distillation_eval_requires_all_thresholds():
    result = DistillationEvalResult(
        personality_score=0.92,
        routing_accuracy=0.88,
        safety_score=1.0,
        regression_passed=True,
    )

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is True
    assert readiness.reason == "ready"


def test_distillation_eval_blocks_low_safety_even_when_personality_is_good():
    result = DistillationEvalResult(
        personality_score=0.95,
        routing_accuracy=0.95,
        safety_score=0.7,
        regression_passed=True,
    )

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is False
    assert readiness.reason == "safety-below-threshold"


def test_distillation_eval_blocks_failed_regression_suite():
    result = DistillationEvalResult(1.0, 1.0, 1.0, regression_passed=False)

    readiness = assess_distillation_readiness(result)

    assert readiness.ready is False
    assert readiness.reason == "regression-failed"
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_distillation_eval.py -q`

Expected: FAIL because eval module does not exist.

**Step 3: Implement readiness gate**

Create `christine/modelization/distillation_eval.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DistillationEvalResult:
    personality_score: float
    routing_accuracy: float
    safety_score: float
    regression_passed: bool


@dataclass(frozen=True)
class DistillationReadiness:
    ready: bool
    reason: str


def assess_distillation_readiness(
    result: DistillationEvalResult,
    *,
    min_personality: float = 0.85,
    min_routing_accuracy: float = 0.8,
    min_safety: float = 1.0,
) -> DistillationReadiness:
    if not result.regression_passed:
        return DistillationReadiness(False, "regression-failed")
    if result.safety_score < min_safety:
        return DistillationReadiness(False, "safety-below-threshold")
    if result.personality_score < min_personality:
        return DistillationReadiness(False, "personality-below-threshold")
    if result.routing_accuracy < min_routing_accuracy:
        return DistillationReadiness(False, "routing-below-threshold")
    return DistillationReadiness(True, "ready")
```

Export these symbols from `christine/modelization/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_modelization_distillation_eval.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/modelization/distillation_eval.py christine/modelization/__init__.py tests/test_modelization_distillation_eval.py && git commit -m "refactor: add distillation eval gate"`

Expected: commit succeeds.

---

### Task 4: Add Artifact Registry Boundary

**Files:**
- Create: `christine/modelization/model_registry.py`
- Modify: `christine/modelization/__init__.py`
- Modify: `.gitignore`
- Test: `tests/test_modelization_model_registry.py`

**Step 1: Write failing tests**

Create `tests/test_modelization_model_registry.py`:

```python
from pathlib import Path

import pytest

from christine.modelization import ModelArtifactRecord, validate_model_artifact_path


def test_model_artifact_record_keeps_metadata_out_of_repo_artifacts():
    record = ModelArtifactRecord(
        name="christine-qwen-lora-alpha",
        base_model="Qwen/Qwen2.5-7B-Instruct",
        adapter_path="artifacts/models/christine-qwen-lora-alpha",
        eval_report="artifacts/evals/christine-qwen-lora-alpha.json",
    )

    assert record.name == "christine-qwen-lora-alpha"
    assert record.base_model == "Qwen/Qwen2.5-7B-Instruct"


def test_model_artifact_path_must_stay_under_artifacts_models():
    assert validate_model_artifact_path("artifacts/models/adapter") == Path("artifacts/models/adapter")
    with pytest.raises(ValueError, match="artifacts/models"):
        validate_model_artifact_path("models/adapter")
    with pytest.raises(ValueError, match="repository-relative"):
        validate_model_artifact_path("../adapter")
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_model_registry.py -q`

Expected: FAIL because model registry module does not exist.

**Step 3: Implement minimal registry boundary**

Create `christine/modelization/model_registry.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ModelArtifactRecord:
    name: str
    base_model: str
    adapter_path: str
    eval_report: str


def validate_model_artifact_path(path: str) -> Path:
    posix = PurePosixPath(path.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError("path must be repository-relative")
    if len(posix.parts) < 3 or posix.parts[0] != "artifacts" or posix.parts[1] != "models":
        raise ValueError("model artifacts must live under artifacts/models")
    return Path(posix.as_posix())
```

Export these symbols from `christine/modelization/__init__.py`.

**Step 4: Ignore future artifacts**

Add to `.gitignore`:

```gitignore
artifacts/models/
artifacts/evals/
artifacts/datasets/
```

Do not create these directories in this task.

**Step 5: Run GREEN**

Run: `uv run pytest tests/test_modelization_model_registry.py -q`

Expected: PASS.

**Step 6: Commit**

Run: `git add .gitignore christine/modelization/model_registry.py christine/modelization/__init__.py tests/test_modelization_model_registry.py && git commit -m "refactor: add model artifact registry boundary"`

Expected: commit succeeds.

---

### Task 5: Add Provider Interface Without Training

**Files:**
- Create: `christine/modelization/model_provider.py`
- Modify: `christine/modelization/__init__.py`
- Test: `tests/test_modelization_model_provider.py`

**Step 1: Write failing tests**

Create `tests/test_modelization_model_provider.py`:

```python
from christine.modelization import ModelProviderRequest, ModelProviderResponse, NoopModelProvider


def test_noop_model_provider_is_explicitly_unavailable():
    provider = NoopModelProvider(reason="training disabled")
    response = provider.generate(ModelProviderRequest(prompt="hi"))

    assert response.available is False
    assert response.text == ""
    assert response.reason == "training disabled"


def test_model_provider_request_preserves_prompt_and_metadata():
    request = ModelProviderRequest(prompt="hello", system="sys", metadata={"target": "direct"})

    assert request.prompt == "hello"
    assert request.system == "sys"
    assert request.metadata == {"target": "direct"}
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_model_provider.py -q`

Expected: FAIL because provider module does not exist.

**Step 3: Implement no-op provider interface**

Create `christine/modelization/model_provider.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ModelProviderRequest:
    prompt: str
    system: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelProviderResponse:
    available: bool
    text: str
    reason: str = ""


class ModelProvider(Protocol):
    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse: ...


@dataclass(frozen=True)
class NoopModelProvider:
    reason: str = "model provider not configured"

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        return ModelProviderResponse(False, "", self.reason)
```

Export these symbols from `christine/modelization/__init__.py`.

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_modelization_model_provider.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add christine/modelization/model_provider.py christine/modelization/__init__.py tests/test_modelization_model_provider.py && git commit -m "refactor: add model provider boundary"`

Expected: commit succeeds.

---

### Task 6: Training Integration Plan Gate

**Files:**
- Create: `docs/model_factory/README.md`
- Modify: `tests/test_modelization_distillation_policy.py`

**Step 1: Write failing docs guard**

Add to `tests/test_modelization_distillation_policy.py`:

```python
from pathlib import Path


def test_model_factory_docs_define_training_preconditions():
    text = Path("docs/model_factory/README.md").read_text(encoding="utf-8")

    assert "LoRA" in text
    assert "QLoRA" in text
    assert "legal" in text
    assert "eval gate" in text
    assert "do not commit model artifacts" in text
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_modelization_distillation_policy.py -q`

Expected: FAIL because docs do not exist.

**Step 3: Add concise docs**

Create `docs/model_factory/README.md` with:

```markdown
# Christine Model Factory

The Model Factory prepares Christine-specific local models or adapters. It does
not train from scratch and does not bypass runtime safety gates.

Training preconditions:
- Legal source approval for every dataset and teacher output.
- Corpus filter and privacy review for any memory-derived examples.
- Eval gate passing before runtime use.
- LoRA or QLoRA first; full fine-tuning only after explicit approval.
- Do not commit model artifacts, datasets, checkpoints, eval outputs, or weights.
```

**Step 4: Run GREEN**

Run: `uv run pytest tests/test_modelization_distillation_policy.py -q`

Expected: PASS.

**Step 5: Commit**

Run: `git add docs/model_factory/README.md tests/test_modelization_distillation_policy.py && git commit -m "docs: document model factory preconditions"`

Expected: commit succeeds.

---

### Task 7: Final Verification And Review

**Files:**
- No additional planned edits.

**Step 1: Run focused modelization checks**

Run: `uv run pytest tests/test_modelization_*.py -q`

Expected: all modelization tests pass.

**Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: launcher reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 3: Review**

Request blocker-focused review for:
- `christine/modelization/distillation_policy.py`
- `christine/modelization/distillation_dataset.py`
- `christine/modelization/distillation_eval.py`
- `christine/modelization/model_registry.py`
- `christine/modelization/model_provider.py`
- `docs/model_factory/README.md`
- `.gitignore`
- tests and this plan

**Step 4: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Run merged-main verification.
- Remove the implementation worktree.
- Delete the implementation branch.
- Push `main`.

---

## Future Training Strategy After This Plan

Only after Tasks 1-7 are implemented and verified:

- Choose a legal student model, likely `Qwen2.5-7B-Instruct` or a smaller Qwen/Gemma/Mistral model depending on GPU memory.
- Start with adapter training, not full model training.
- Use JSONL examples from reviewed project docs, tests, safe repository summaries, explicit user-approved dialogue samples, and synthetic self-play generated by approved local/open teachers.
- Evaluate on personality preservation, Chinese conversation, tool-routing decisions, repository factuality, safety refusal for side effects, and regression tests.
- Deploy through Ollama/llama.cpp/vLLM only after the eval gate passes.
- Keep cloud/API teacher use optional and legally reviewed; do not distill from providers whose terms prohibit training competitors or derivative models.
