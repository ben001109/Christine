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
