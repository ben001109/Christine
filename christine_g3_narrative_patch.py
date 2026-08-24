from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

import christine_g3_frontier as g3
import christine_g3_native_context as v12

FIVED9A_TOKEN_CAPACITY = v12.FIVED9A_TOKEN_CAPACITY


def _domain(source: str) -> str:
    try:
        return urllib.parse.urlparse(source).netloc.casefold().removeprefix("www.") or source
    except Exception:
        return source


def _prob_union(values):
    p = 1.0
    for v in values:
        p *= 1.0 - max(0.0, min(1.0, float(v)))
    return 1.0 - p


@dataclass
class FactFrame:
    category: str
    subject: str
    value: str
    confidence: float
    relevance: float
    sources: tuple[str, ...]
    evidence: tuple[g3.Evidence, ...]


class SAGE3Narrative(v12.SAGENativeSynthesizer):
    """Fact-graph narrative synthesizer. No OSS/open-source LLM is used."""

    def synthesize(self, *, goal, evidence, packet, followup=False, exclude_sources=None):
        exclude_sources = exclude_sources or set()
        subject = self._subject(goal)
        rows = self._relevant(goal, evidence)
        rows = self._dedupe(rows)
        if followup and exclude_sources:
            fresh = [e for e in rows if e.source not in exclude_sources]
            if fresh:
                rows = fresh
        facts = self._merge(self._extract_facts(subject, rows))
        facts.sort(key=lambda f: f.confidence * (0.55 + 0.45 * f.relevance), reverse=True)
        answer = self._write_narrative(subject, facts, packet, followup)
        if not self._guard(answer, rows):
            answer = self._minimal(subject, facts)
        used, seen = [], set()
        for f in facts[:8]:
            for e in f.evidence:
                k = (e.source, e.content)
                if k not in seen:
                    seen.add(k); used.append(e)
        return answer, used, {
            "facts": len(facts),
            "sources": len({_domain(e.source) for e in used}),
            "mode": "fact-graph-narrative",
        }

    def _extract_facts(self, subject, rows):
        out = []
        for e in rows:
            text = v12._clean(e.content)
            src = _domain(e.source)
            base = max(0.05, min(1.0, e.confidence * (0.55 + 0.45 * e.relevance)))

            for m in re.finditer(r"(?:我是|本人是)\s*([^，,。]{1,20})[，,]\s*(?:一個|一位)?\s*([^。]{3,100})", text):
                desc = self._trim(m.group(2))
                if desc:
                    out.append(FactFrame("identity", subject or m.group(1), desc, base, e.relevance, (src,), (e,)))

            if subject:
                for m in re.finditer(rf"{re.escape(subject)}\s*(?:是|為)\s*([^。；;]{{3,120}})", text):
                    val = self._trim(m.group(1))
                    if val and not self._noise(val):
                        out.append(FactFrame("identity", subject, val, base, e.relevance, (src,), (e,)))

            if re.search(r"台灣.{0,35}(?:coser|cosplay)", text, re.I):
                out.append(FactFrame("role", subject, "台灣的 coser／cosplay 創作者", base, e.relevance, (src,), (e,)))
            m = re.search(r"(?:C齡|cosplay.{0,8}(?:經驗|資歷)|coser.{0,8}(?:經驗|資歷))\s*(?:約|大約)?\s*([一二三四五六七八九十\d]+)\s*年", text, re.I)
            if m:
                out.append(FactFrame("experience", subject, f"約{m.group(1)}年的 cosplay 經驗", base, e.relevance, (src,), (e,)))
            m = re.search(r"目前(?:只|主要)?出\s*([^\s，,。；;]{1,20})", text)
            if m:
                out.append(FactFrame("activity", subject, f"目前主要扮演{self._trim(m.group(1))}", base, e.relevance, (src,), (e,)))
            actions = []
            if re.search(r"可以約拍|接受約拍|可約拍", text): actions.append("接受約拍")
            if re.search(r"可以委[託托]|接受委[託托]|可委[託托]", text): actions.append("接受委託")
            if actions:
                out.append(FactFrame("activity", subject, "、".join(actions), base, e.relevance, (src,), (e,)))

            m = re.search(r"(?:興趣|喜歡)\s*(?:是|包括|包含)?\s*([^。]{3,100})", text)
            if m:
                val = self._trim(m.group(1))
                if val and not self._noise(val):
                    out.append(FactFrame("interest", subject, val, base * 0.92, e.relevance, (src,), (e,)))

            handles = []
            for p in ("Instagram", "IG", "Threads", "FB", "Facebook"):
                for m in re.finditer(rf"{p}\s*[:：]?\s*@?([A-Za-z0-9_.]{{3,40}})", text, re.I):
                    h = m.group(1).strip(".")
                    if h.casefold() not in {"all", "rights", "reserved", "say", "more"}:
                        handles.append(f"{p} {h}")
            if handles:
                vals = list(dict.fromkeys(handles))[:4]
                out.append(FactFrame("social", subject, "、".join(vals), base * 0.95, e.relevance, (src,), (e,)))

            if re.search(r"衣服需自備|收取\s*\d+\s*(?:一日|日)|牽手|擁抱|陪伴期間", text):
                vals = []
                if "衣服需自備" in text: vals.append("服裝原則上需自備")
                m = re.search(r"收取\s*(\d+)\s*(?:一日|日)", text)
                if m: vals.append(f"資料中出現每日 {m.group(1)} 元的費用描述")
                if re.search(r"牽手|擁抱", text): vals.append("陪伴內容提到牽手或擁抱等互動")
                if vals:
                    out.append(FactFrame("service", subject, "；".join(vals), base * 0.78, e.relevance, (src,), (e,)))
        return out

    def _merge(self, facts):
        merged = []
        for f in facts:
            target, best = None, 0.0
            ft = g3._tokens(f.value)
            for i, old in enumerate(merged):
                if old.category != f.category: continue
                sim = g3._jaccard(ft, g3._tokens(old.value))
                if sim > best: target, best = i, sim
            if target is not None and best >= 0.48:
                old = merged[target]
                sources = tuple(dict.fromkeys(old.sources + f.sources))
                factor = 0.85 if set(old.sources) & set(f.sources) else 1.0
                conf = _prob_union([old.confidence, f.confidence * factor])
                evidence = tuple(dict.fromkeys(old.evidence + f.evidence))
                value = min((old.value, f.value), key=len)
                merged[target] = FactFrame(old.category, old.subject or f.subject, value, conf,
                                           max(old.relevance, f.relevance), sources, evidence)
            else:
                merged.append(f)
        return merged

    def _write_narrative(self, subject, facts, packet, followup):
        if not facts:
            return f"目前能找到的公開資料太零散，還不足以可靠說明{subject or '這個主題'}。"
        by = {}
        for f in facts: by.setdefault(f.category, []).append(f)
        for arr in by.values(): arr.sort(key=lambda x: x.confidence, reverse=True)
        domains = tuple(dict.fromkeys(s for f in facts for s in f.sources if s))
        confidence = packet.confidence if packet is not None else max(f.confidence for f in facts)

        identity = (by.get("role") or by.get("identity") or [])
        if identity:
            desc = self._np(identity[0].value)
            if confidence >= 0.78 and len(domains) >= 2:
                first = f"綜合目前找到的公開資料，{subject or '這個對象'}比較可能是{desc}。"
            else:
                first = (f"目前網路上的資料比較像社群自介，而不是正式人物介紹。"
                         f"從可找到的頁面看，{subject or '這個對象'}自我描述成{desc}。")
        else:
            first = (f"目前還沒有足夠資料能完整確認{subject or '這個對象'}的身分，"
                     "不過幾個公開頁面透露出一些可以交叉整理的線索。")

        details = []
        if by.get("experience"): details.append(f"資料提到{by['experience'][0].value}")
        if by.get("activity"):
            vals = list(dict.fromkeys(f.value for f in by["activity"]))[:2]
            details.append("另外也" + "，並".join(vals))
        if details: first += " " + "，".join(details) + "。"
        paragraphs = [first]

        extra = []
        if by.get("interest"): extra.append(f"興趣方面，頁面提到{by['interest'][0].value}")
        if by.get("social"): extra.append(f"社群資訊則出現{by['social'][0].value}")
        if by.get("service"): extra.append(f"另外還有委託／陪伴相關描述，例如{by['service'][0].value}")
        if extra: paragraphs.append("。".join(x.rstrip("。") for x in extra) + "。")

        if confidence < 0.72 or len(domains) < 2:
            paragraphs.append("不過，這些資訊目前主要來自個人頁或社群頁，而且來源之間不一定真正獨立，"
                              "所以我還不能把所有內容都當成已確認的身分資料。比較穩妥的做法，是把上面內容視為目前最有根據的公開線索。")
        elif confidence < 0.86:
            paragraphs.append("幾個來源的方向大致一致，但仍有部分細節只出現在單一頁面；因此核心輪廓可以暫時採信，細節則保留一點不確定性。")

        if domains:
            paragraphs.append("我這次主要參考的公開來源是 " + "、".join(domains[:6]) + "。")
        if followup: paragraphs[0] = "接著上一輪來看，" + paragraphs[0]
        return "\n\n".join(paragraphs)

    def _minimal(self, subject, facts):
        if not facts: return f"目前還沒有足夠可靠的公開資料可以說明{subject or '這個問題'}。"
        phrases = []
        for f in facts[:3]:
            if f.category in {"identity", "role"}: phrases.append(f"{subject or '這個對象'}較可能和{self._np(f.value)}這個描述有關")
            elif f.category == "experience": phrases.append(f"資料提到{f.value}")
            elif f.category == "activity": phrases.append(f.value)
        return "把目前能確認的內容合在一起看，" + "；另外，".join(phrases) + "。這些資訊仍需要更多獨立來源才能完全確認。"

    def _guard(self, answer, rows):
        if len(re.findall(r"(?m)^\s*\d+\.\s", answer)) >= 2: return False
        low = answer.casefold()
        if any(x in low for x in ("all rights reserved", "created by lit.link", "say more")): return False
        for e in rows:
            raw = v12._clean(e.content)
            if len(raw) >= 90 and raw[:90] in answer: return False
        return True

    @staticmethod
    def _subject(goal):
        text = v12._clean(goal)
        text = re.sub(r"^(?:去)?(?:網上|網路|上網)?\s*(?:查|搜尋|找|幫我查|查一下)?\s*", "", text)
        text = re.sub(r"(?:是誰|是什麼|的資料|的資訊|資料|資訊)[？?]?$", "", text).strip(" ：:，,。")
        if "；目前追問：" in text: text = text.split("；目前追問：", 1)[0]
        return text[:50]

    @staticmethod
    def _trim(text):
        text = v12._clean(text)
        text = re.split(r"(?i)\b(?:instagram|threads|facebook|fb|all rights reserved|created by)\b", text)[0]
        return text.strip(" ，,；;。")[:150]

    @staticmethod
    def _noise(text):
        low = text.casefold()
        return any(x in low for x in ("all rights", "created by", "say more", "メイク", "美容", "趣味 個人"))

    @staticmethod
    def _np(value):
        return re.sub(r"^(?:一個|一位)", "", v12._clean(value).strip("，,。"))


class ChristineG3NarrativeRuntime(v12.ChristineG3NativeContextRuntime):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.sage = SAGE3Narrative()


def main() -> int:
    print("=" * 88)
    print(" Christine G3 v1.3 — SAGE-3 Narrative + THREAD + ORBIT + 5D9A 138B")
    print(" Search evidence is converted into a fact graph before narration.")
    print(" No Ollama/open-source LLM is used for factual narrative synthesis.")
    print(f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens")
    print("=" * 88)
    rt = ChristineG3NarrativeRuntime()
    print("Type 'exit' to quit, 'clear' to clear.\n")
    while True:
        try: user = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not user: continue
        if user.casefold() in {"exit", "quit", "bye"}: break
        if user.casefold() == "clear":
            import os; os.system("cls" if os.name == "nt" else "clear"); continue
        t0 = time.perf_counter()
        answer, turn = rt.ask(user)
        print(f"Christine：{answer}")
        print(f"  [G3 v1.3 trace: {' | '.join(turn.trace)} | {time.perf_counter()-t0:.2f}s]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
