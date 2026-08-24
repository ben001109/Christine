from __future__ import annotations

import html
import json
import math
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

import christine_g3_frontier as g3
import christine_g3_v15_intent as v15i
import christine_g3_v15_context as v15c


# ASCII-safe URL lexer. Crucially, CJK text appended immediately after a social
# URL is not swallowed into the URL path.
URL_RE_V16 = re.compile(
    r"https?://[A-Za-z0-9.-]+(?::\d+)?"
    r"(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?",
    re.I,
)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize_entity(text: str) -> str:
    return re.sub(r"[\s@：:，,。！？?!「」『』（）()]+", "", str(text or "").casefold())


def extract_urls_and_residual(raw: str) -> tuple[tuple[str, ...], str]:
    text = str(raw or "")
    urls: list[str] = []
    spans: list[tuple[int, int]] = []
    for m in URL_RE_V16.finditer(text):
        url = m.group(0).rstrip(".,;:!?)]}")
        if url:
            urls.append(url)
            spans.append((m.start(), m.start() + len(url)))

    if not spans:
        return (), clean(text)

    chars = list(text)
    for a, b in spans:
        for i in range(a, b):
            chars[i] = " "
    return tuple(dict.fromkeys(urls)), clean("".join(chars))


def host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.casefold().removeprefix("www.")
    except Exception:
        return ""


def handle_from_url(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
    except Exception:
        return ""
    m = re.search(r"/@([A-Za-z0-9_.-]{1,64})(?:/|$)", path)
    if m:
        return "@" + m.group(1)
    return ""


def source_hint_from_urls(urls: tuple[str, ...]) -> str:
    for u in urls:
        h = host(u)
        if "threads.com" in h:
            return "threads"
        if "instagram.com" in h:
            return "instagram"
        if "facebook.com" in h:
            return "facebook"
        if "github.com" in h:
            return "github"
        if "reddit.com" in h:
            return "reddit"
        if "youtube.com" in h or "youtu.be" in h:
            return "youtube"
    return ""


class IntentKernelV16(v15i.IntentKernel):
    """v1.5 intent semantics with a URL lexer/entity parser that cannot eat CJK suffixes."""

    def analyze(self, raw: str) -> v15i.IntentFrame:
        text = clean(raw)
        urls, residual = extract_urls_and_residual(text)

        if not urls:
            return super().analyze(text)

        source_hint = source_hint_from_urls(urls)
        entities = self._entities_v16(residual, urls)
        question_like = bool(
            re.search(
                r"(誰|什麼|在幹嘛|做什麼|幹嘛|怎麼|如何|內容|分析|看看|看一下|查|介紹|這個人|這人|這是)",
                residual,
                re.I,
            )
        )
        mode = "research" if question_like or residual else "inspect_url"
        goal = residual or " ".join(entities) or urls[0]

        return v15i.IntentFrame(
            mode=mode,
            operation="research",
            output_kind="text",
            goal=goal,
            requires_web=True,
            requires_facts=True,
            urls=urls,
            source_hint=source_hint,
            entities=entities,
            scores={"url": 1.0, "research": 1.0},
        )

    @staticmethod
    def _entities_v16(residual: str, urls: tuple[str, ...]) -> tuple[str, ...]:
        entities: list[str] = []
        for url in urls:
            h = handle_from_url(url)
            if h:
                entities.append(h)

        # Only scan the residual text, never the URL itself, so handles are not duplicated.
        for h in re.findall(r"@([A-Za-z0-9_.-]{2,64})", residual):
            entities.append("@" + h)

        # Exact "X 是誰" identity subject.
        m = re.search(r"([^\s，。？！?：:]{2,30})\s*是誰", residual)
        if m:
            subject = m.group(1)
            subject = re.sub(r"^(?:看一下|看看|查一下|幫我查|查查|介紹一下|告訴我)", "", subject)
            subject = subject.strip()
            pronoun_like = (
                subject in {"這個人", "這人", "他", "她", "這個帳號"}
                or subject.endswith("這個人")
                or subject.endswith("這人")
            )
            if subject and not pronoun_like:
                entities.append(subject)

        return tuple(dict.fromkeys(entities))


class ContextGraphV16(v15c.ContextGraph):
    """Same v1.5 context math, but topic stripping uses the v1.6 URL lexer."""

    @staticmethod
    def _topic(raw: str, intent: v15i.IntentFrame) -> str:
        _, residual = extract_urls_and_residual(raw)
        text = re.sub(
            r"(去)?(?:threads|instagram|facebook|github|reddit|youtube|網路|網上|上網)(?:上)?(?:查|搜尋)?",
            " ",
            residual,
            flags=re.I,
        )
        text = re.sub(r"(幫我查|查一下|查查|搜尋|搜索|看一下)", " ", text)
        text = clean(text)

        # Pronoun-only residuals should resolve through entity/url inheritance.
        if re.fullmatch(r"(這個人|這人|他|她|它)?\s*(是誰|在幹嘛|做什麼|幹嘛|是什麼)?", text):
            text = ""

        return text or (" ".join(intent.entities) if intent.entities else raw)


@dataclass(frozen=True)
class EntityRequest:
    label: str
    handles: tuple[str, ...]
    urls: tuple[str, ...]
    source_hint: str
    question: str
    identity_query: bool


class EntityResolver:
    PRONOUNS = {"這個人", "這人", "他", "她", "它", "這個帳號"}

    def from_resolution(self, resolution: v15c.ContextResolution) -> EntityRequest | None:
        intent = resolution.intent
        entities = tuple(dict.fromkeys(intent.entities + resolution.inherited_entities))
        urls = tuple(dict.fromkeys(intent.urls + resolution.inherited_urls))

        handles = tuple(e for e in entities if e.startswith("@"))
        names = [e for e in entities if not e.startswith("@") and e not in self.PRONOUNS]

        if names:
            label = names[0]
        elif handles:
            label = handles[0]
        else:
            # Generic X是誰 from topic, for v1.5 non-URL intent.
            m = re.search(r"([^\s，。？！?：:]{2,30})\s*是誰", resolution.topic)
            label = m.group(1) if m else ""

        if not label and not urls:
            return None

        identity_query = bool(
            re.search(r"(是誰|這個人|這人|身分|身份|介紹|帳號|profile|在幹嘛|做什麼|幹嘛)", resolution.topic, re.I)
            or handles
            or urls
        )

        return EntityRequest(
            label=label,
            handles=handles,
            urls=urls,
            source_hint=intent.source_hint or source_hint_from_urls(urls),
            question=resolution.topic,
            identity_query=identity_query,
        )
