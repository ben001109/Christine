from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .contracts import Fact, ResearchPacket
from .utils import clean, jaccard, tokens


@dataclass(frozen=True)
class Facet:
    name: str
    title: str
    facts: tuple[Fact, ...]
    relevance: float
    confidence: float
    novelty: float
    priority: float


@dataclass(frozen=True)
class ResponsePlan:
    mode: str
    facets: tuple[Facet, ...]
    token_budget: int
    diversity_score: float
    coverage_score: float


class PRISMPlanner:
    """Perspective-Rich Information Synthesis Model.

    Deterministic answer planner. It chooses multiple non-redundant views of
    the fact graph instead of forcing every answer into one fixed template.
    """

    FACET_MAP = {
        "identity": "身分輪廓",
        "definition": "核心定義",
        "position": "公開經歷",
        "timeline": "時間線",
        "feature": "功能與特點",
        "activity": "主要活動",
        "experience": "經驗",
        "social": "公開社群",
        "service": "服務／委託",
        "interest": "興趣",
        "impact": "影響與重要性",
        "controversy": "爭議／不同說法",
        "status": "目前狀態",
        "relationship": "關係網",
        "evidence": "證據品質",
    }

    def plan(self, *, question: str, subject: str, facts: list[Fact], packet: ResearchPacket | None, token_budget: int = 1000) -> ResponsePlan:
        grouped = self._group(facts)
        desired = self._desired_facets(question, grouped)
        qt = tokens(question)
        candidates: list[Facet] = []

        for category, group in grouped.items():
            if not group:
                continue
            relevance = self._facet_relevance(qt, category, group, desired)
            confidence = self._facet_confidence(group)
            novelty = self._facet_novelty(group)
            bonus = 1.0 if category in {"identity", "definition", "position", "feature", "impact", "status"} else .65
            priority = .42 * relevance + .33 * confidence + .15 * novelty + .10 * bonus
            candidates.append(Facet(category, self.FACET_MAP.get(category, category), tuple(group), relevance, confidence, novelty, priority))

        source_count = len({s for f in facts for s in f.sources})
        if packet is not None and (packet.confidence < .78 or source_count < 2):
            priority = .42*.88 + .33*packet.confidence + .15 + .10
            candidates.append(Facet("evidence", "證據品質", (), .88, packet.confidence, 1.0, priority))

        selected: list[Facet] = []
        used = 0
        for facet in sorted(candidates, key=lambda x: x.priority, reverse=True):
            est = self._estimate_tokens(facet)
            if selected and used + est > token_budget:
                continue
            redundancy = max((self._facet_similarity(facet, old) for old in selected), default=0.0)
            adjusted = .82 * facet.priority - .18 * redundancy
            if adjusted < .18:
                continue
            selected.append(facet)
            used += est
            if len(selected) >= 6:
                break

        mode = self._mode(question, selected)
        return ResponsePlan(mode, tuple(selected), token_budget, self._diversity(selected), self._coverage(desired, selected))

    @staticmethod
    def _group(facts: list[Fact]) -> dict[str, list[Fact]]:
        grouped: dict[str, list[Fact]] = defaultdict(list)
        for fact in facts:
            grouped[fact.category].append(fact)
        for values in grouped.values():
            values.sort(key=lambda f: f.confidence, reverse=True)
        return grouped

    @staticmethod
    def _desired_facets(question: str, grouped: dict[str, list[Fact]]) -> set[str]:
        q = clean(question)
        desired: set[str] = set()
        if re.search(r"(是誰|是什麼|介紹|哪位|身分|身份)", q):
            desired |= {"identity", "definition", "position", "status", "impact"}
        if re.search(r"(做過|經歷|生涯|歷程|以前|曾經)", q):
            desired |= {"position", "timeline", "experience"}
        if re.search(r"(現在|目前|最近|現況)", q):
            desired |= {"status", "position"}
        if re.search(r"(為什麼重要|影響|意義|貢獻|作用)", q):
            desired |= {"impact", "feature", "relationship"}
        if re.search(r"(爭議|爭論|不同說法|批評)", q):
            desired |= {"controversy", "evidence"}
        if re.search(r"(興趣|喜歡)", q):
            desired.add("interest")
        if re.search(r"(功能|能做什麼|有什麼能力|特色)", q):
            desired |= {"feature", "definition"}
        return desired or set(grouped.keys())

    @staticmethod
    def _facet_relevance(qt: set[str], category: str, group: list[Fact], desired: set[str]) -> float:
        semantic = max((jaccard(qt, tokens(f"{f.subject} {f.predicate} {f.value}")) for f in group), default=0.0)
        target = 1.0 if category in desired else .35
        return min(1.0, .55*target + .45*semantic)

    @staticmethod
    def _facet_confidence(group: list[Fact]) -> float:
        independent = len({s for f in group[:4] for s in f.sources})
        base = sum(f.confidence for f in group[:3]) / min(3, len(group))
        return min(1.0, base + .04*max(0, independent-1))

    @staticmethod
    def _facet_novelty(group: list[Fact]) -> float:
        values = {re.sub(r"\W+", "", f.value.casefold()) for f in group}
        return min(1.0, .55 + .12*len(values))

    @staticmethod
    def _estimate_tokens(facet: Facet) -> int:
        chars = sum(len(f.value) for f in facet.facts[:3]) + len(facet.title)
        return max(45, min(220, chars//2))

    @staticmethod
    def _facet_similarity(a: Facet, b: Facet) -> float:
        return jaccard(tokens(" ".join(f.value for f in a.facts)), tokens(" ".join(f.value for f in b.facts)))

    @staticmethod
    def _mode(question: str, selected: list[Facet]) -> str:
        if re.search(r"(詳細|深入|完整|深度)", question):
            return "deep"
        if re.search(r"(簡單|簡短|一句話)", question):
            return "compact"
        if any(f.name == "timeline" for f in selected):
            return "timeline"
        return "profile" if len(selected) >= 4 else "balanced"

    @staticmethod
    def _coverage(desired: set[str], selected: list[Facet]) -> float:
        return 1.0 if not desired else len(desired & {f.name for f in selected}) / len(desired)

    @staticmethod
    def _diversity(selected: list[Facet]) -> float:
        if len(selected) <= 1:
            return 0.0
        sims = []
        for i, a in enumerate(selected):
            for b in selected[i+1:]:
                sims.append(PRISMPlanner._facet_similarity(a, b))
        return 1.0 - (sum(sims)/len(sims) if sims else 0.0)


class PRISMNarrator:
    """Writes from a response plan; never receives raw search snippets."""

    def narrate(self, *, subject: str, question: str, plan: ResponsePlan, packet: ResearchPacket | None) -> str:
        if not plan.facets:
            return f"目前還沒有足夠可靠的資料，讓我完整回答「{question}」。"
        paragraphs = [self._facet_paragraph(subject, f, packet) for f in plan.facets]
        paragraphs = [p for p in paragraphs if p]
        return " ".join(paragraphs[:2]) if plan.mode == "compact" else "\n\n".join(paragraphs)

    def _facet_paragraph(self, subject: str, facet: Facet, packet: ResearchPacket | None) -> str:
        facts = list(facet.facts)
        if facet.name in {"identity", "definition"} and facts:
            return f"先抓核心來看，{subject}可以概括為{self._smooth(facts[0].value)}。"
        if facet.name == "position" and facts:
            return "如果看公開經歷，較重要的節點包括：" + "；".join(self._unique([f.value for f in facts], 4)) + "。"
        if facet.name == "status" and facts:
            return "就目前狀態而言，公開資料主要指向" + "、".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "feature" and facts:
            return "功能／特點方面，可以分成幾個方向理解：" + "；".join(self._unique([f.value for f in facts], 4)) + "。"
        if facet.name == "experience" and facts:
            return "經驗層面，資料提到" + "、".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "activity" and facts:
            return "實際活動方面，較明確的資訊有" + "、".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "interest" and facts:
            return f"比較偏個人面向的資料則顯示，{subject}的興趣包含" + "、".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "impact" and facts:
            return "如果問『為什麼值得注意』，較有代表性的影響是" + "；".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "controversy" and facts:
            return "另一方面，公開資料中也存在不同說法或爭議：" + "；".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "relationship" and facts:
            return f"放進關係網來看，{subject}還和" + "、".join(self._unique([f.value for f in facts], 3)) + "有明顯連結。"
        if facet.name == "display_name" and facts:
            return f"這個社群帳號 {subject} 目前可確認的公開名稱是「{facts[0].value}」。"
        if facet.name == "bio" and facts:
            return f"從 {subject} 的公開自介／摘要來看，" + "；".join(self._unique([f.value for f in facts], 2)) + "。"
        if facet.name == "social" and facts:
            return "公開社群方面，目前能確認的資訊是" + "、".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "service" and facts:
            return "若看服務／委託資訊，資料提到" + "；".join(self._unique([f.value for f in facts], 3)) + "。"
        if facet.name == "evidence":
            if packet is None:
                return "這一輪主要依據本地記憶與已匯入文件，因此缺乏外部交叉驗證的部分仍需保留不確定性。"
            if packet.confidence >= .86:
                return "證據品質方面，多個來源的核心資訊一致，整體可信度相對高；細節仍以原始來源為準。"
            if packet.confidence >= .70:
                return "證據品質中等：核心輪廓已有支持，但部分細節仍只出現在單一來源，因此不宜講得太絕對。"
            return "目前證據仍偏分散，我只能把上面的內容當成較有根據的公開線索，而不是全部已確認的事實。"
        if facts:
            return f"{facet.title}方面，較值得保留的資訊是" + "；".join(self._unique([f.value for f in facts], 3)) + "。"
        return ""

    @staticmethod
    def _smooth(value: str) -> str:
        return re.sub(r"^(?:一位|一名|一個)", "", clean(value).strip("，,。"))

    @staticmethod
    def _unique(values: Iterable[str], limit: int) -> list[str]:
        out, seen = [], set()
        for value in values:
            value = clean(value)
            key = re.sub(r"\W+", "", value.casefold())
            if value and key not in seen:
                seen.add(key); out.append(value)
            if len(out) >= limit:
                break
        return out
