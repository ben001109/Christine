from christine.modelization.retrieval import search_repository_corpus


def _write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_search_repository_corpus_ranks_safe_matches(tmp_path):
    _write(tmp_path, "docs/runtime.md", "runtime health health check")
    _write(tmp_path, "christine/runtime/health.py", "def runtime_self_test(): return 'health'")
    _write(tmp_path, "data/private.md", "runtime health private memory")

    results = search_repository_corpus(tmp_path, "runtime health")

    assert [result.path for result in results] == [
        "docs/runtime.md",
        "christine/runtime/health.py",
    ]
    assert all("data/private.md" != result.path for result in results)


def test_search_repository_corpus_returns_bounded_snippets(tmp_path):
    _write(tmp_path, "docs/long.md", "alpha " * 100 + "runtime health " + "omega " * 100)

    (result,) = search_repository_corpus(tmp_path, "runtime health", snippet_chars=80)

    assert result.path == "docs/long.md"
    assert "runtime health" in result.snippet
    assert len(result.snippet) <= 80


def test_search_repository_corpus_returns_empty_for_blank_query(tmp_path):
    _write(tmp_path, "docs/runtime.md", "runtime health")

    assert search_repository_corpus(tmp_path, "   ") == ()


def test_search_repository_corpus_matches_traditional_chinese(tmp_path):
    _write(tmp_path, "docs/zh.md", "Christine 的向量檢索需要安全且可驗證的契約")

    (result,) = search_repository_corpus(tmp_path, "向量檢索")

    assert result.path == "docs/zh.md"


def test_modelization_exports_repository_retrieval_boundary():
    from christine.modelization import RepositorySearchResult, search_repository_corpus

    assert RepositorySearchResult.__name__ == "RepositorySearchResult"
    assert callable(search_repository_corpus)
