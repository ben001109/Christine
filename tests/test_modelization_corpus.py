import pytest

from christine.modelization.corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    should_include_in_model_corpus,
)


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "boot_christine.py",
        "christine/modelization/corpus.py",
        "brain/runtime.py",
        "docs/plans/x.md",
        "tests/test_modelization_corpus.py",
        "Start_Christine.bat",
        "啟動Christine.ps1",
        "pyproject.toml",
    ],
)
def test_model_corpus_includes_conservative_source_docs_and_tests(path):
    assert should_include_in_model_corpus(path)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "config/credentials.json",
        "config/api_token.txt",
        "browser/Cookies",
        "data/private_memory.json",
        "level5_logs/run.log",
        "growth.log",
        "heartbeat.txt",
        "nexus_v2_state.json",
        "brain/generated/area_000001.py",
        "ARC-AGI/data.json",
        "backups/christine_final.py",
        "mirrors/a/christine_final.py",
        "self_replicas/christine_final.py",
        ".worktrees/feature/christine_final.py",
        ".venv/lib/site-packages/pkg.py",
        ".pytest_cache/v/cache/nodeids",
        "v42_export/model.safetensors",
        "models/local.pt",
        "notes/archive.zip",
        "image.png",
        "uv.lock",
    ],
)
def test_model_corpus_excludes_private_generated_bulk_and_binary_paths(path):
    assert not should_include_in_model_corpus(path)


def test_model_corpus_returns_reasoned_decisions():
    assert decide_model_corpus_path("christine/modelization/corpus.py") == CorpusDecision(
        include=True,
        reason="included",
    )

    assert decide_model_corpus_path("data/private_memory.json") == CorpusDecision(
        include=False,
        reason="excluded-path-part:data",
    )

    assert decide_model_corpus_path("config/credentials.json") == CorpusDecision(
        include=False,
        reason="excluded-secret-name",
    )
