from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from christine_g3_v15_intent import IntentFrame, URL_RE, _clean, _tokens, _jaccard

CONTEXT_STATE_PATH = Path(__import__("os").environ.get("CHRISTINE_G3_CONTEXT_STATE", "data/g3_context_graph.json"))

@dataclass
class ContextEpisode:
    user_input: str
    mode: str
    topic: str
    entities: tuple[str, ...]
    urls: tuple[str, ...]
    output_kind: str
    timestamp: float = field(default_factory=time.time)

@dataclass(frozen=True)
class ContextResolution:
    intent: IntentFrame
    topic: str
    inherited_entities: tuple[str, ...] = ()
    inherited_urls: tuple[str, ...] = ()
    continuity: float = 0.0

class ContextGraph:
    """Context enriches intent; it never overrides the current-turn mode."""

    REFERENCES = re.compile(r"(這個人|這個|那個|那支|他|她|它|剛剛|前面|上一個|那呢|還有|再)", re.I)

    def __init__(self, maxlen: int = 24, state_path: Path | None = CONTEXT_STATE_PATH):
        self.rows: deque[ContextEpisode] = deque(maxlen=maxlen)
        self.state_path = state_path
        self._load()

    @property
    def last(self) -> ContextEpisode | None:
        return self.rows[-1] if self.rows else None

    def resolve(self, raw: str, intent: IntentFrame) -> ContextResolution:
        if not self.last:
            return ContextResolution(intent, self._topic(raw, intent))

        prev = self.last
        current_tokens = _tokens(raw)
        prev_tokens = _tokens(prev.topic)
        lexical = _jaccard(current_tokens, prev_tokens)
        entity_overlap = _jaccard(set(intent.entities), set(prev.entities)) if (intent.entities or prev.entities) else 0.0
        reference = 1.0 if self.REFERENCES.search(raw) else 0.0
        url_ref = 1.0 if (reference and prev.urls) else 0.0
        same_kind = 1.0 if intent.output_kind == prev.output_kind else 0.0
        continuity = min(1.0, 0.30 * lexical + 0.22 * entity_overlap + 0.28 * reference + 0.15 * url_ref + 0.05 * same_kind)

        inherited_entities: tuple[str, ...] = ()
        inherited_urls: tuple[str, ...] = ()
        topic = self._topic(raw, intent)
        if continuity >= 0.34:
            inherited_entities = tuple(e for e in prev.entities if e not in intent.entities)
            inherited_urls = tuple(u for u in prev.urls if u not in intent.urls)
            if reference:
                topic = f"{prev.topic}；目前追問：{raw}"
        return ContextResolution(intent, topic, inherited_entities, inherited_urls, continuity)

    def commit(self, raw: str, resolution: ContextResolution) -> None:
        intent = resolution.intent
        entities = tuple(dict.fromkeys(intent.entities + resolution.inherited_entities))
        urls = tuple(dict.fromkeys(intent.urls + resolution.inherited_urls))
        self.rows.append(ContextEpisode(raw, intent.mode, resolution.topic, entities, urls, intent.output_kind))
        self._save()

    @staticmethod
    def _topic(raw: str, intent: IntentFrame) -> str:
        text = URL_RE.sub(" ", raw)
        text = re.sub(r"(去)?(?:threads|instagram|facebook|github|reddit|網路|網上|上網)(?:上)?(?:查|搜尋)?", " ", text, flags=re.I)
        text = re.sub(r"(幫我查|查一下|查查|搜尋|搜索)", " ", text)
        text = _clean(text)
        return text or (" ".join(intent.entities) if intent.entities else raw)

    def _save(self) -> None:
        if self.state_path is None:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [r.__dict__ for r in self.rows]
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.state_path)
        except Exception:
            pass

    def _load(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            rows = json.loads(self.state_path.read_text(encoding="utf-8"))
            for r in rows[-self.rows.maxlen:]:
                self.rows.append(ContextEpisode(
                    user_input=str(r.get("user_input", "")), mode=str(r.get("mode", "conversation")),
                    topic=str(r.get("topic", "")), entities=tuple(r.get("entities", ())),
                    urls=tuple(r.get("urls", ())), output_kind=str(r.get("output_kind", "text")),
                    timestamp=float(r.get("timestamp", time.time())),
                ))
        except Exception:
            self.rows.clear()
