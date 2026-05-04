"""Modelization support boundaries for Christine."""

from .corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    iter_model_corpus_paths,
    should_include_in_model_corpus,
)
from .repository_index import CorpusDocument, build_corpus_document

__all__ = [
    "CorpusDecision",
    "decide_model_corpus_path",
    "iter_model_corpus_paths",
    "CorpusDocument",
    "build_corpus_document",
    "should_include_in_model_corpus",
]
