from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import Evidence
from .utils import clean, jaccard, tokens


@dataclass(frozen=True)
class HygieneReport:
    kept: int
    rejected: int
    code_rejected: int
    internal_rejected: int
    relevance_rejected: int
    entity_rejected: int


class EvidenceHygiene:
    """Query-conditioned firewall between retrieved memory and FactGraph."""

    CODE_MARKERS = re.compile(
        r"(?m)(^|\s)(def\s+\w+\s*\(|class\s+\w+|import\s+\w+|from\s+\w+\s+import|"
        r"return\s+|elif\s+|async\s+def|await\s+|assert\s+|pytest|"
        r"if\s+.+:\s*$|for\s+\w+\s+in\s+.+:\s*$)|"
        r"```(?:python|py|js|javascript|typescript|c\+\+|rust|go)?|"
        r"\b[A-Za-z_][A-Za-z0-9_]*\([^)]*\)\s*->|"
        r"\b(?:True|False|None)\b|==|!=|<=|>=|::",
        re.I,
    )
    INTERNAL_MARKERS = re.compile(
        r"(G3\s*v\d|trace:|argus|nova:|prism:|5D9A|"
        r"_ood_gate|expected shard token|enable_escalate|"
        r"stack trace|traceback|line \d+|\.py:\d+|"
        r"commit sha|pull request|pytest|compileall|"
        r"christine_g3|runtime|router|fallback|gate\s+[A-Z])",
        re.I,
    )
    TECH_QUERY = re.compile(
        r"(python|程式|程式碼|腳本|code|debug|除錯|演算法|函式|api|"
        r"runtime|router|模型架構|5D9A|Christine\s*(?:內部|架構|程式)|"
        r"GitHub|repo|repository|commit|PR\b)",
        re.I,
    )

    def sanitize(self, *, query: str, subject: str, evidence: list[Evidence]) -> tuple[list[Evidence], HygieneReport]:
        technical_query = bool(self.TECH_QUERY.search(query))
        q_tokens = tokens(query)
        s_tokens = tokens(subject)
        kept: list[Evidence] = []
        rejected = code_rejected = internal_rejected = relevance_rejected = entity_rejected = 0

        for item in evidence:
            text = clean(item.content)
            if not text:
                rejected += 1
                relevance_rejected += 1
                continue

            code_score = self._code_score(text)
            internal_score = self._internal_score(text)

            if not technical_query and code_score >= .42:
                rejected += 1
                code_rejected += 1
                continue
            if not technical_query and internal_score >= .35:
                rejected += 1
                internal_rejected += 1
                continue

            query_rel = max(item.relevance, jaccard(q_tokens, tokens(text)))
            subject_rel = jaccard(s_tokens, tokens(text)) if s_tokens else 0.0
            subject_exact = bool(subject and subject.casefold() in text.casefold())
            entity_support = max(item.entity_match, subject_rel, 1.0 if subject_exact else 0.0)

            if item.origin in {"memory", "long-document"}:
                if subject and not technical_query and entity_support < .18 and query_rel < .08:
                    rejected += 1
                    entity_rejected += 1
                    continue
                if query_rel < .025 and entity_support < .25:
                    rejected += 1
                    relevance_rejected += 1
                    continue
            elif query_rel < .015 and entity_support < .15:
                rejected += 1
                relevance_rejected += 1
                continue

            relevance = max(.0, min(1.0, .62 * query_rel + .38 * entity_support))
            confidence = item.confidence
            if item.origin == "memory" and not subject_exact and entity_support < .35:
                confidence *= .82

            kept.append(Evidence(
                item.evidence_id,
                text,
                item.source,
                relevance,
                confidence,
                trust=item.trust,
                freshness=item.freshness,
                entity_match=entity_support,
                independent_group=item.independent_group,
                origin=item.origin,
            ))

        kept.sort(
            key=lambda e: e.confidence * (.45 + .35 * e.relevance + .20 * e.entity_match),
            reverse=True,
        )
        return kept, HygieneReport(
            len(kept), rejected, code_rejected, internal_rejected,
            relevance_rejected, entity_rejected,
        )

    @classmethod
    def _code_score(cls, text: str) -> float:
        matches = len(cls.CODE_MARKERS.findall(text))
        punctuation = len(re.findall(r"[{}[\]();_=<>]", text))
        lines = max(1, text.count("\n") + 1)
        return min(1.0, .16 * matches + .018 * punctuation + .04 * (lines >= 4))

    @classmethod
    def _internal_score(cls, text: str) -> float:
        return min(1.0, .22 * len(cls.INTERNAL_MARKERS.findall(text)))
