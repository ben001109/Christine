from hashlib import sha256

import pytest

from christine.modelization.repository_index import CorpusDocument, build_corpus_document


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
