from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOKEN_CAPACITY_5D9A = 138_000_000_000

@dataclass(frozen=True)
class Intent:
    kind: str
    operation: str
    output_kind: str
    goal: str
    confidence: float = 1.0
    requires_facts: bool = False
    requires_web: bool = False
    requires_current: bool = False
    emotional_support: bool = False
    source_hint: str = ""
    urls: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    missing_slots: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class ContextResolution:
    topic: str
    continuity: float
    inherited_entities: tuple[str, ...] = ()
    inherited_urls: tuple[str, ...] = ()

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    content: str
    source: str
    relevance: float
    confidence: float
    trust: float = 0.5
    freshness: float = 1.0
    entity_match: float = 0.0
    independent_group: str = ""
    origin: str = "web"

@dataclass(frozen=True)
class ResearchPacket:
    evidence: tuple[Evidence, ...]
    confidence: float
    queries: tuple[str, ...]
    stop_reason: str = ""

@dataclass(frozen=True)
class Fact:
    category: str
    subject: str
    predicate: str
    value: str
    confidence: float
    sources: tuple[str, ...]
    evidence_ids: tuple[str, ...]

@dataclass
class TurnState:
    raw: str
    intent: Intent | None = None
    context: ContextResolution | None = None
    evidence: list[Evidence] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    artifact: Any = None

@dataclass(frozen=True)
class Artifact:
    kind: str
    content: str
    language: str = ""
    path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Verification:
    accepted: bool
    score: float
    reason: str
