from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .corpus import iter_model_corpus_paths


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class RepositorySearchResult:
    path: str
    score: int
    snippet: str


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in TOKEN_RE.findall(text))


def _snippet(text: str, query_tokens: tuple[str, ...], snippet_chars: int) -> str:
    lower_text = text.lower()
    first_match = min((lower_text.find(token) for token in query_tokens if token in lower_text), default=0)
    start = max(0, first_match - snippet_chars // 3)
    return text[start : start + snippet_chars].replace("\n", " ")


def _read_text_prefix(path: Path, max_document_bytes: int) -> str:
    with path.open("rb") as handle:
        data = handle.read(max_document_bytes)
    return data.decode("utf-8", errors="replace")


def search_repository_corpus(
    root: str | Path,
    query: str,
    *,
    limit: int = 10,
    snippet_chars: int = 240,
    max_document_bytes: int = 200_000,
) -> tuple[RepositorySearchResult, ...]:
    query_tokens = _tokens(query)
    if not query_tokens or limit <= 0 or snippet_chars <= 0 or max_document_bytes <= 0:
        return ()

    root_path = Path(root)
    results: list[RepositorySearchResult] = []
    for relative in iter_model_corpus_paths(root_path):
        path = root_path / relative
        text = _read_text_prefix(path, max_document_bytes)
        counts = Counter(_tokens(text))
        score = sum(counts[token] for token in query_tokens)
        if score:
            results.append(
                RepositorySearchResult(
                    path=relative,
                    score=score,
                    snippet=_snippet(text, query_tokens, snippet_chars),
                )
            )

    return tuple(sorted(results, key=lambda result: (-result.score, result.path))[:limit])
