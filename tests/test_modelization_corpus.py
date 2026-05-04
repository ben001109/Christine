import pytest

import christine.modelization.corpus as corpus_module
from christine.modelization.corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    iter_model_corpus_paths,
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


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("/tmp/outside_repo/notes.py", "excluded-absolute-path"),
        ("C:\\Users\\ben\\outside_repo\\notes.py", "excluded-absolute-path"),
        ("C:Users\\ben\\outside_repo\\notes.py", "excluded-absolute-path"),
        ("C:secrets.py", "excluded-absolute-path"),
        ("Z:/outside_repo/notes.py", "excluded-absolute-path"),
        ("../outside_repo/notes.py", "excluded-path-traversal"),
        ("docs/../data/private.py", "excluded-path-traversal"),
        ("secrets/config.py", "excluded-secret-name"),
        ("credentials/settings.py", "excluded-secret-name"),
        ("docs/passwords.txt", "excluded-secret-name"),
        ("notes/passwd_rotation.md", "excluded-secret-name"),
        ("config/private_key_notes.md", "excluded-secret-name"),
        ("notes/ssh_key_rotation.md", "excluded-secret-name"),
        ("tokens/readme.md", "excluded-secret-name"),
        ("Data/private.py", "excluded-path-part:data"),
        ("Backups/christine_final.py", "excluded-path-part:backups"),
        ("Brain/generated/area_000001.py", "excluded-prefix:brain/generated"),
    ],
)
def test_model_corpus_rejects_unsafe_path_shapes(path, reason):
    assert decide_model_corpus_path(path) == CorpusDecision(include=False, reason=reason)


def test_iter_model_corpus_paths_prunes_excluded_directories(tmp_path):
    files = {
        "AGENTS.md": "guide",
        "christine/modelization/corpus.py": "source",
        "docs/plans/modelization.md": "plan",
        "tests/test_modelization_corpus.py": "tests",
        "data/private_memory.json": "private",
        "brain/generated/area_000001.py": "generated",
        "mirrors/a/christine_final.py": "mirror",
        ".worktrees/feature/christine_final.py": "worktree",
        "v42_export/model.safetensors": "weights",
        "secrets/config.py": "secret",
        "Data/private.py": "private uppercase",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    assert list(iter_model_corpus_paths(tmp_path)) == [
        "AGENTS.md",
        "christine/modelization/corpus.py",
        "docs/plans/modelization.md",
        "tests/test_modelization_corpus.py",
    ]


def test_iter_model_corpus_paths_skips_symlink_files(tmp_path):
    private_target = tmp_path / "data" / "private_memory.md"
    private_target.parent.mkdir(parents=True)
    private_target.write_text("private", encoding="utf-8")

    safe_link = tmp_path / "docs" / "notes.md"
    safe_link.parent.mkdir(parents=True)
    try:
        safe_link.symlink_to(private_target)
    except OSError:
        pytest.skip("symlinks are not supported in this environment")

    assert list(iter_model_corpus_paths(tmp_path)) == []


def test_iter_model_corpus_paths_prunes_secret_directories_before_descent(tmp_path, monkeypatch):
    visited_secret_dirs = []

    def fake_walk(root_path):
        dirs = ["secrets"]
        yield root_path, dirs, []
        if "secrets" in dirs:
            visited_secret_dirs.append("secrets")
            yield root_path / "secrets", [], ["config.py"]

    monkeypatch.setattr(corpus_module.os, "walk", fake_walk)

    assert list(iter_model_corpus_paths(tmp_path)) == []
    assert visited_secret_dirs == []
