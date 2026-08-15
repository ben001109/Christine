from __future__ import annotations

import html
import json
import math
import re
import time
import urllib.parse
import urllib.request
from typing import Any

import christine_g3_frontier as g3
from christine_g3_v16_lexer import clean, normalize_entity, host, EntityRequest

class WikipediaProbe:
    API = "https://zh.wikipedia.org/w/api.php"

    def __init__(self, timeout: float = 7.0):
        self.timeout = timeout

    def probe(self, label: str) -> list[g3.Evidence]:
        if not label or label.startswith("@"):
            return []
        params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts|info",
            "inprop": "url",
            "redirects": "1",
            "exintro": "1",
            "explaintext": "1",
            "titles": label,
            "format": "json",
            "formatversion": "2",
        })
        req = urllib.request.Request(
            self.API + "?" + params,
            headers={"User-Agent": "Christine-G3/1.6 entity resolver"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception:
            return []

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return []
        page = pages[0]
        if page.get("missing"):
            return []
        title = clean(page.get("title", ""))
        extract = clean(page.get("extract", ""))
        url = page.get("fullurl") or ("https://zh.wikipedia.org/wiki/" + urllib.parse.quote(title))
        if not extract or normalize_entity(label) not in normalize_entity(title + extract[:220]):
            return []

        out = []
        for sentence in re.split(r"(?<=[。！？.!?])\s*", extract)[:8]:
            sentence = clean(sentence)
            if len(sentence) < 18:
                continue
            rel = 0.95 if normalize_entity(label) in normalize_entity(sentence) else 0.68
            out.append(g3.Evidence(sentence, url, 0.88, rel))
        return out


class EntityORBIT:
    """Entity-first web research with exact entity gates and domain consensus."""

    def __init__(self, base: Any | None = None, wiki: WikipediaProbe | None = None):
        self.base = base or g3.ORBITWeb(timeout=10.0)
        self.wiki = wiki or WikipediaProbe()

    def research(self, request: EntityRequest) -> g3.ResearchPacket:
        evidence: list[g3.Evidence] = []
        queries: list[str] = []

        for url in request.urls:
            evidence.extend(self._direct_url(request, url))

        if request.identity_query and request.label and not request.label.startswith("@"):
            evidence.extend(self.wiki.probe(request.label))

        for query in self._queries(request):
            queries.append(query)
            try:
                hits = self.base._search(query, 8)
            except Exception:
                hits = []

            for url, title, snippet in hits:
                match = self._entity_match(request, title + " " + snippet + " " + url)
                if match < 0.18:
                    continue

                trust = self._trust(url, request)
                snippet_text = clean(f"搜尋標題：{title}。摘要：{snippet}")
                if len(snippet_text) >= 20:
                    evidence.append(
                        g3.Evidence(
                            snippet_text,
                            url,
                            min(0.84, trust * (0.62 + 0.38 * match)),
                            match,
                        )
                    )

                if match >= 0.45:
                    try:
                        text = self.base._fetch_text(url)
                    except Exception:
                        text = ""
                    if text:
                        for sent in self.base._sentences(text)[:18]:
                            sm = self._entity_match(request, sent)
                            if sm < 0.15:
                                continue
                            evidence.append(
                                g3.Evidence(
                                    sent,
                                    url,
                                    min(0.90, trust * (0.68 + 0.32 * sm)),
                                    sm,
                                )
                            )

        evidence = self._dedupe_and_gate(request, evidence)
        confidence = self._consensus_confidence(evidence)
        return g3.ResearchPacket(tuple(evidence[:40]), confidence, tuple(dict.fromkeys(queries)))

    def _direct_url(self, request: EntityRequest, url: str) -> list[g3.Evidence]:
        try:
            text = self.base._fetch_text(url)
        except Exception:
            return []
        out = []
        for sent in self.base._sentences(text)[:30]:
            match = self._entity_match(request, sent)
            if request.source_hint in {"threads", "instagram", "facebook"}:
                match = max(match, 0.32)
            if match < 0.15:
                continue
            out.append(g3.Evidence(sent, url, 0.72, match))
        return out

    def _queries(self, request: EntityRequest) -> list[str]:
        label = request.label
        handle = request.handles[0] if request.handles else (label if label.startswith("@") else "")

        queries: list[str] = []
        if request.source_hint == "threads" or any("threads.com" in host(u) for u in request.urls):
            key = handle or label
            clean_handle = key.lstrip("@")
            queries += [
                f'"@{clean_handle}" site:threads.com',
                f'"{clean_handle}" Threads',
                f'"{clean_handle}"',
            ]
        elif request.source_hint == "instagram":
            key = handle or label
            queries += [f'"{key.lstrip("@")}" site:instagram.com', f'"{key.lstrip("@")}" Instagram']
        elif label:
            queries += [
                f'"{label}"',
                f'"{label}" 是誰',
                f'"{label}" 官方',
                f'"{label}" 經歷',
                f'"{label}" site:wikipedia.org',
            ]
        return list(dict.fromkeys(q for q in queries if q.strip()))[:6]

    def _entity_match(self, request: EntityRequest, text: str) -> float:
        hay = normalize_entity(html.unescape(text))
        candidates = [request.label, *request.handles]
        scores = []
        for candidate in candidates:
            needle = normalize_entity(candidate)
            if not needle:
                continue
            if needle in hay:
                scores.append(1.0)
            else:
                scores.append(g3._jaccard(g3._tokens(candidate), g3._tokens(text)))
        return max(scores, default=0.0)

    @staticmethod
    def _trust(url: str, request: EntityRequest) -> float:
        h = host(url)
        if h.endswith(".gov.tw") or h.endswith(".gov") or ".gov." in h:
            return 0.94
        if h.endswith(".edu.tw") or h.endswith(".edu") or ".edu." in h:
            return 0.90
        if "wikipedia.org" in h:
            return 0.86
        if h in {"threads.com", "instagram.com", "facebook.com"}:
            return 0.76 if request.source_hint and request.source_hint in h else 0.66
        if "github.com" in h:
            return 0.82
        return 0.62

    def _dedupe_and_gate(self, request: EntityRequest, rows: list[g3.Evidence]) -> list[g3.Evidence]:
        out: list[g3.Evidence] = []
        seen: set[tuple[str, str]] = set()
        for e in sorted(rows, key=lambda x: x.confidence * (0.45 + 0.55 * x.relevance), reverse=True):
            content = clean(e.content)
            low = content.casefold()
            if any(x in low for x in ("all rights reserved", "cookie policy", "privacy policy")):
                continue
            if len(content) < 14:
                continue
            if self._entity_match(request, content + " " + e.source) < 0.15:
                continue

            key = (host(e.source), re.sub(r"\W+", "", low)[:260])
            if key in seen:
                continue
            seen.add(key)

            near_duplicate = False
            toks = g3._tokens(content)
            for old in out:
                if g3._jaccard(toks, g3._tokens(old.content)) >= 0.84:
                    near_duplicate = True
                    break
            if not near_duplicate:
                out.append(g3.Evidence(content, e.source, e.confidence, e.relevance))
        return out

    @staticmethod
    def _consensus_confidence(rows: list[g3.Evidence]) -> float:
        if not rows:
            return 0.0
        best: dict[str, float] = {}
        for e in rows:
            d = host(e.source) or e.source
            best[d] = max(best.get(d, 0.0), e.confidence * max(0.25, e.relevance))
        p_not = 1.0
        for score in sorted(best.values(), reverse=True)[:8]:
            p_not *= 1.0 - max(0.0, min(0.95, score))
        return 1.0 - p_not
