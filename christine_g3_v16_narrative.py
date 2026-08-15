from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import christine_g3_frontier as g3
import christine_g3_v15_context as v15c
from christine_g3_v16_lexer import clean, host, EntityRequest

@dataclass
class EntityFact:
    category: str
    value: str
    confidence: float
    sources: tuple[str, ...]
    evidence: tuple[g3.Evidence, ...]


class EntityNarrative:
    """Entity-specific fact graph with social-noise suppression."""

    def synthesize(self, request: EntityRequest, packet: g3.ResearchPacket) -> tuple[str, list[g3.Evidence], dict[str, Any]]:
        facts = self._extract(request, list(packet.evidence))
        facts = self._merge(facts)
        facts.sort(key=lambda f: f.confidence, reverse=True)

        if request.handles or request.source_hint in {"threads", "instagram", "facebook"}:
            answer = self._social_narrative(request, facts, packet)
        else:
            answer = self._person_narrative(request, facts, packet)

        used: list[g3.Evidence] = []
        seen = set()
        for fact in facts[:8]:
            for e in fact.evidence:
                k = (e.source, e.content)
                if k not in seen:
                    seen.add(k)
                    used.append(e)

        return answer, used, {
            "facts": len(facts),
            "sources": len({host(e.source) for e in used if e.source}),
            "entity": request.label,
        }

    def _extract(self, request: EntityRequest, evidence: list[g3.Evidence]) -> list[EntityFact]:
        label = request.label.lstrip("@")
        out: list[EntityFact] = []

        for e in evidence:
            text = clean(e.content)
            src = host(e.source) or e.source
            score = max(0.05, min(0.95, e.confidence * (0.60 + 0.40 * e.relevance)))

            if request.handles:
                handle = re.escape(request.handles[0].lstrip("@"))
                m = re.search(rf"搜尋標題：([^。]{{1,80}}?)\s*\(@?{handle}\)", text, re.I)
                if m:
                    display = self._trim(m.group(1))
                    if display:
                        out.append(EntityFact("display_name", display, score, (src,), (e,)))

                m = re.search(r"摘要：(.+)$", text)
                if m:
                    bio = self._trim(m.group(1))
                    if len(bio) >= 18 and not self._noise(bio):
                        out.append(EntityFact("bio", bio, score * 0.90, (src,), (e,)))

            if not label or request.handles:
                continue

            m = re.search(
                rf"{re.escape(label)}\s*[（(][^）)]{{0,120}}[）)]\s*[，,]\s*([^。]{{5,220}})",
                text,
                re.I,
            )
            if m:
                comp = self._trim(m.group(1))
                identity, positions = self._split_identity_positions(comp)
                if identity:
                    out.append(EntityFact("identity", identity, score, (src,), (e,)))
                for pos in positions:
                    out.append(EntityFact("position", pos, score * 0.96, (src,), (e,)))

            for m in re.finditer(rf"{re.escape(label)}\s*(?:是|為)\s*([^。；;]{{4,180}})", text, re.I):
                comp = self._trim(m.group(1))
                identity, positions = self._split_identity_positions(comp)
                if identity:
                    out.append(EntityFact("identity", identity, score, (src,), (e,)))
                for pos in positions:
                    out.append(EntityFact("position", pos, score * 0.95, (src,), (e,)))

            for m in re.finditer(r"(曾任|曾擔任|現任|擔任)\s*([^。；;，,]{2,100})", text):
                val = self._trim(m.group(1) + m.group(2))
                if val and not self._noise(val):
                    out.append(EntityFact("position", val, score * 0.94, (src,), (e,)))

        return out

    def _merge(self, facts: list[EntityFact]) -> list[EntityFact]:
        merged: list[EntityFact] = []
        for f in facts:
            target = None
            best = 0.0
            ft = g3._tokens(f.value)
            for i, old in enumerate(merged):
                if old.category != f.category:
                    continue
                sim = g3._jaccard(ft, g3._tokens(old.value))
                if sim > best:
                    best, target = sim, i
            if target is not None and best >= 0.42:
                old = merged[target]
                sources = tuple(dict.fromkeys(old.sources + f.sources))
                independent = 1.0 if set(old.sources).isdisjoint(f.sources) else 0.82
                conf = 1.0 - (1.0 - old.confidence) * (1.0 - f.confidence * independent)
                evidence = tuple(dict.fromkeys(old.evidence + f.evidence))
                value = min((old.value, f.value), key=len)
                merged[target] = EntityFact(old.category, value, min(0.97, conf), sources, evidence)
            else:
                merged.append(f)
        return merged

    def _person_narrative(self, request: EntityRequest, facts: list[EntityFact], packet: g3.ResearchPacket) -> str:
        label = request.label or "這個人"
        identities = [f for f in facts if f.category == "identity"]
        positions = [f for f in facts if f.category == "position"]

        if not identities and not positions:
            return (
                f"我有針對「{label}」做精確姓名與多來源查詢，但目前抓到的內容不足以可靠建立身分輪廓。"
                "這次我不會拿搜尋頁面的零碎字串或社群帳號片段硬湊答案。"
            )

        parts = []
        if identities:
            identity = identities[0].value
            if identities[0].confidence >= 0.82:
                parts.append(f"綜合目前可交叉確認的公開資料，{label}可確認為{self._natural_identity(identity)}。")
            else:
                parts.append(f"目前較可靠的公開資料將{label}描述為{self._natural_identity(identity)}。")
        else:
            parts.append(f"目前能確認的資料主要集中在{label}的公開職務經歷。")

        if positions:
            unique = []
            for f in positions:
                if f.value not in unique:
                    unique.append(f.value)
            if unique:
                parts.append("他的公開經歷中，" + "，另外".join(unique[:3]) + "。")

        source_domains = tuple(dict.fromkeys(d for fact in facts for d in fact.sources if d))
        if packet.confidence < 0.70 or len(source_domains) < 2:
            parts.append("不過目前獨立來源仍不算多，因此細節我會保留一些不確定性。")

        if source_domains:
            parts.append("這次主要交叉參考：" + "、".join(source_domains[:6]) + "。")
        return "\n\n".join(parts)

    def _social_narrative(self, request: EntityRequest, facts: list[EntityFact], packet: g3.ResearchPacket) -> str:
        handle = request.handles[0] if request.handles else request.label
        displays = [f for f in facts if f.category == "display_name"]
        bios = [f for f in facts if f.category == "bio"]

        if not displays and not bios:
            return (
                f"這個連結指向 {request.source_hint.title() if request.source_hint else '社群'} 帳號 {handle}，"
                "但目前公開可讀內容太少，還不足以可靠判斷真實姓名或帳號主要在做什麼。"
                "我有改用帳號 handle 做站內定向搜尋，但不會把無關搜尋結果硬塞成答案。"
            )

        parts = [f"這個連結對應的是 {request.source_hint.title() if request.source_hint else '社群'} 帳號 {handle}。"]
        if displays:
            parts.append(f"搜尋結果顯示它使用的公開名稱是「{displays[0].value}」。")
        if bios:
            bio = self._clean_bio(bios[0].value)
            if bio:
                parts.append(f"從目前能讀到的公開自介／摘要來看，{bio}。")

        if packet.confidence < 0.72:
            parts.append(
                "不過社群頁面常會限制未登入抓取，而且目前可交叉驗證的獨立來源不多；"
                "所以我只能描述公開頁面可見的帳號資訊，不能據此確認真實身分。"
            )

        return " ".join(parts)

    @staticmethod
    def _split_identity_positions(text: str) -> tuple[str, list[str]]:
        text = clean(text)
        m = re.search(r"(.+?)(?=(?:曾任|曾擔任|現任|擔任))", text)
        if m:
            identity = m.group(1).strip("，,；; ")
        else:
            identity = text

        positions = []
        for m in re.finditer(r"(曾任|曾擔任|現任|擔任)\s*([^，,；;。]{2,100})", text):
            positions.append(clean(m.group(1) + m.group(2)))
        return identity[:180], positions

    @staticmethod
    def _natural_identity(text: str) -> str:
        text = clean(text).strip("，,。")
        text = re.sub(r"^(?:一位|一名|一個)", "", text)
        return text

    @staticmethod
    def _trim(text: str) -> str:
        text = clean(text)
        text = re.sub(r"(?i)(?:cookie|privacy policy|all rights reserved).*$", "", text)
        return text.strip(" ，,；;。")[:220]

    @staticmethod
    def _noise(text: str) -> bool:
        low = text.casefold()
        return any(x in low for x in (
            "all rights reserved", "cookie", "privacy policy",
            "sign in", "log in", "created by",
        ))

    @staticmethod
    def _clean_bio(text: str) -> str:
        text = clean(text)
        text = re.sub(r"^(?:搜尋標題：[^。]+。)?(?:摘要：)?", "", text)
        text = re.sub(r"(?i)(?:instagram|threads|facebook)\s*[:：]?\s*@?[A-Za-z0-9_.-]+", "", text)
        text = clean(text).strip("，,。")
        if len(text) > 220:
            text = text[:217].rstrip("，,；; ") + "…"
        return text


def is_entity_query(resolution: v15c.ContextResolution) -> bool:
    intent = resolution.intent
    if intent.urls or resolution.inherited_urls:
        return True
    if intent.entities or resolution.inherited_entities:
        return bool(re.search(r"(是誰|這個人|這人|介紹|身分|身份|在幹嘛|做什麼|幹嘛)", resolution.topic, re.I))
    return bool(re.search(r"[^\s]{2,30}\s*是誰", resolution.topic))
