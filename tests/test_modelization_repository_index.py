from hashlib import sha256

import pytest

from christine.modelization.repository_index import (
    CorpusDocument,
    CorpusManifest,
    build_corpus_document,
    build_corpus_manifest,
)


def test_build_corpus_document_records_stable_metadata(tmp_path):
    root = tmp_path
    document = root / "docs" / "plan.md"
    document.parent.mkdir(parents=True)
    document.write_text("Christine\n", encoding="utf-8")

    assert build_corpus_document(root, "docs/plan.md") == CorpusDocument(
        path="docs/plan.md",
        suffix=".md",
        size_bytes=10,
        sha256=sha256(b"Christine\n").hexdigest(),
    )


@pytest.mark.parametrize(
    "relative_path",
    ["../outside.md", "/tmp/outside.md", "C:\\outside.md", "C:outside.md"],
)
def test_build_corpus_document_rejects_non_relative_repository_paths(tmp_path, relative_path):
    with pytest.raises(ValueError, match="repository-relative"):
        build_corpus_document(tmp_path, relative_path)


def test_build_corpus_manifest_uses_safe_iterator_and_deterministic_order(tmp_path):
    files = {
        "docs/b.md": "B",
        "docs/a.md": "A",
        "data/private.md": "private",
        "brain/generated/area.py": "generated",
        "secrets/config.py": "secret",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    manifest = build_corpus_manifest(tmp_path)

    assert isinstance(manifest, CorpusManifest)
    assert manifest.schema_version == 1
    assert [document.path for document in manifest.documents] == ["docs/a.md", "docs/b.md"]
    assert manifest.document_count == 2
    assert manifest.total_size_bytes == 2


def test_corpus_manifest_serializes_without_file_contents(tmp_path):
    document = tmp_path / "docs" / "plan.md"
    document.parent.mkdir(parents=True)
    document.write_text("secret-free text", encoding="utf-8")

    payload = build_corpus_manifest(tmp_path).to_dict()

    assert payload["schema_version"] == 1
    assert payload["document_count"] == 1
    assert payload["documents"][0]["path"] == "docs/plan.md"
    assert "secret-free text" not in repr(payload)
