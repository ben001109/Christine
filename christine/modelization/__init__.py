"""Modelization support boundaries for Christine."""

from .corpus import (
    CorpusDecision,
    decide_model_corpus_path,
    iter_model_corpus_paths,
    should_include_in_model_corpus,
)
from .repository_index import CorpusDocument, CorpusManifest, build_corpus_document, build_corpus_manifest
from .retrieval import RepositorySearchResult, search_repository_corpus
from .routing_eval import (
    ROUTE_TARGETS,
    RouteEvalExample,
    RouteEvalResult,
    RoutePrediction,
    RouteReadiness,
    assess_route_readiness,
    score_route_predictions,
)
from .routing_fixtures import ROUTING_EVAL_FIXTURES
from .routing_policy import SIDE_EFFECT_TARGETS, RoutePolicy, RoutePolicyDecision, apply_route_policy

__all__ = [
    "CorpusDecision",
    "decide_model_corpus_path",
    "iter_model_corpus_paths",
    "CorpusDocument",
    "CorpusManifest",
    "ROUTE_TARGETS",
    "ROUTING_EVAL_FIXTURES",
    "SIDE_EFFECT_TARGETS",
    "RepositorySearchResult",
    "RouteEvalExample",
    "RouteEvalResult",
    "RoutePolicy",
    "RoutePolicyDecision",
    "RoutePrediction",
    "RouteReadiness",
    "apply_route_policy",
    "assess_route_readiness",
    "build_corpus_document",
    "build_corpus_manifest",
    "should_include_in_model_corpus",
    "search_repository_corpus",
    "score_route_predictions",
]
