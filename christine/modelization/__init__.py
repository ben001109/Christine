"""Modelization support boundaries for Christine."""

from .corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    iter_model_corpus_paths,
    should_include_in_model_corpus,
)
from .repository_index import CorpusDocument, CorpusManifest, build_corpus_document, build_corpus_manifest
from .retrieval import RepositorySearchResult, search_repository_corpus
from .routing_eval import ROUTE_TARGETS, RouteEvalExample, RouteEvalResult, RoutePrediction, score_route_predictions

__all__ = [
    "CorpusDecision",
    "decide_model_corpus_path",
    "iter_model_corpus_paths",
    "CorpusDocument",
    "CorpusManifest",
    "ROUTE_TARGETS",
    "RepositorySearchResult",
    "RouteEvalExample",
    "RouteEvalResult",
    "RoutePrediction",
    "build_corpus_document",
    "build_corpus_manifest",
    "should_include_in_model_corpus",
    "search_repository_corpus",
    "score_route_predictions",
]
