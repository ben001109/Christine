from pathlib import Path

import pytest

from christine.modelization import (
    ModelArtifactRecord,
    validate_model_artifact_path,
    validate_model_eval_report_path,
)


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


def test_model_eval_report_path_must_stay_under_artifacts_evals():
    assert validate_model_eval_report_path("artifacts/evals/adapter.json") == Path("artifacts/evals/adapter.json")
    with pytest.raises(ValueError, match="artifacts/evals"):
        validate_model_eval_report_path("evals/adapter.json")
    with pytest.raises(ValueError, match="repository-relative"):
        validate_model_eval_report_path("../adapter.json")


def test_model_artifact_record_rejects_invalid_adapter_path():
    with pytest.raises(ValueError, match="artifacts/models"):
        ModelArtifactRecord(
            name="bad-adapter",
            base_model="Qwen/Qwen2.5-7B-Instruct",
            adapter_path="models/bad-adapter",
            eval_report="artifacts/evals/bad-adapter.json",
        )


def test_model_artifact_record_rejects_invalid_eval_report_path():
    with pytest.raises(ValueError, match="artifacts/evals"):
        ModelArtifactRecord(
            name="bad-eval",
            base_model="Qwen/Qwen2.5-7B-Instruct",
            adapter_path="artifacts/models/bad-eval",
            eval_report="evals/bad-eval.json",
        )
