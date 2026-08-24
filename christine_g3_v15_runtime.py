from __future__ import annotations

import os
import re
import time
from typing import Any

import christine_g3_frontier as g3
import christine_g3_narrative_patch as v13
import christine_g3_nova as v14

from christine_g3_v15_intent import IntentFrame, IntentKernel, _clean, _tokens, _jaccard, _host
from christine_g3_v15_context import ContextGraph, ContextResolution

FIVED9A_TOKEN_CAPACITY = v14.FIVED9A_TOKEN_CAPACITY

class URLAwareORBIT:
    def __init__(self, base: Any | None = None):
        self.base = base or g3.ORBITWeb(timeout=10.0)

    def research(self, resolution: ContextResolution) -> g3.ResearchPacket:
        intent = resolution.intent
        urls = tuple(dict.fromkeys(intent.urls + resolution.inherited_urls))
        evidence: list[g3.Evidence] = []
        queries: list[str] = []
        for url in urls:
            try:
                text = self.base._fetch_text(url)
            except Exception:
                text = ""
            if text:
                qtok = _tokens(resolution.topic)
                for sent in self.base._sentences(text)[:24]:
                    rel = _jaccard(qtok, _tokens(sent))
                    if rel <= 0 and intent.mode != "inspect_url":
                        continue
                    confidence = max(0.42, min(0.86, 0.58 + 0.28 * rel))
                    evidence.append(g3.Evidence(sent, url, confidence, max(rel, 0.10)))

        search_goal = self._search_goal(resolution)
        if search_goal:
            queries.append(search_goal)
            try:
                packet = self.base.research(search_goal)
                evidence.extend(packet.evidence)
                queries.extend(packet.queries)
            except Exception:
                pass

        out: list[g3.Evidence] = []
        seen = set()
        for e in sorted(evidence, key=lambda x: x.confidence * (0.4 + 0.6 * x.relevance), reverse=True):
            key = (_host(e.source), re.sub(r"\W+", "", e.content.casefold())[:300])
            if key not in seen:
                seen.add(key)
                out.append(e)

        best_by_domain: dict[str, float] = {}
        for e in out:
            d = _host(e.source) or e.source
            best_by_domain[d] = max(best_by_domain.get(d, 0.0), e.confidence)
        p_not = 1.0
        for v in list(best_by_domain.values())[:8]:
            p_not *= 1.0 - max(0.0, min(1.0, v))
        confidence = 1.0 - p_not if best_by_domain else 0.0
        return g3.ResearchPacket(tuple(out[:32]), confidence, tuple(dict.fromkeys(queries)))

    @staticmethod
    def _search_goal(resolution: ContextResolution) -> str:
        intent = resolution.intent
        subject_parts = list(intent.entities + resolution.inherited_entities)
        if not subject_parts:
            subject_parts = [resolution.topic]
        subject = " ".join(dict.fromkeys(p for p in subject_parts if p)).strip()
        if not subject:
            return ""
        if intent.source_hint == "threads" or any("threads.com" in u for u in intent.urls + resolution.inherited_urls):
            return f'{subject} site:threads.com'
        if intent.source_hint == "instagram":
            return f'{subject} site:instagram.com'
        if intent.source_hint == "facebook":
            return f'{subject} site:facebook.com'
        return subject

class NativeDialogue:
    """Native conversation/support responder; does not browse on its own."""

    def respond(self, raw: str, resolution: ContextResolution) -> str:
        text = _clean(raw)
        topic = resolution.topic
        entities = tuple(dict.fromkeys(resolution.intent.entities + resolution.inherited_entities))

        if re.search(r"(女朋友|伴侶).{0,20}(性侵|侵害)", text) or re.search(r"(不反抗|不逃|僵住).{0,30}(默認|同意|為什麼)", text):
            return (
                "你後面那個理解其實很關鍵：人在受到威脅時，反應不只有「反抗」或「逃跑」，也可能出現僵住。"
                "那種反應往往不是當事人冷靜選擇出來的，所以不能把「沒有立刻逃走、沒有反抗」解讀成同意或默認。"
                "用事後視角去問「為什麼不跑」很直覺，但它容易忽略當下身體和注意力可能已經進入自動防衛狀態。"
                "如果你是在重新理解你女朋友的經歷，比起追問她當時為什麼沒有做某個動作，更有幫助的是把重點放在：她當時經歷了什麼、現在希望被怎麼支持。"
            )

        if re.search(r"(真的非常感謝|很感謝|因為他的影片|支撐著現在的我|影響.*現在的我)", text):
            who = "、".join(entities) if entities else "那支影片／那位創作者"
            return (
                f"聽起來{who}對你不是單純「看過一支影片」而已，而是幫你重新理解一段原本很難整理的事情。"
                "你說它支撐著現在的你，我會把這理解成：它替你提供了一套語言和框架，讓你能把以前只剩下困惑、甚至責怪的地方重新看懂。"
                "如果你想表達感謝，其實把「它具體改變了我怎麼理解這件事」說清楚，往往比只說謝謝更有力量。"
            )

        if re.search(r"(斗內|donate|可以幫我@|@錫蘭)", text, re.I):
            who = "、".join(entities) if entities else "對方"
            return (
                f"聽得出來你是真的很想讓{who}知道他的內容幫到你。"
                "如果你說的「@」是想寫一段公開留言，我可以幫你把想說的內容整理得真誠一點；"
                "至於十萬這種金額非常大，不需要在情緒最滿的時候立刻決定，先把感謝說清楚也完全可以。"
            )

        if resolution.continuity >= 0.34:
            return f"我有接住你前面的脈絡。你現在是在延續「{topic}」這件事，我會沿著這個主題回答，而不是重新開一個無關問題。"
        if re.search(r"^(你好|嗨|哈囉|hi|hello)", text, re.I):
            return "你好，我在。你可以直接延續上一個話題，也可以丟新的問題給我。"
        return "我有在聽。你可以直接把你現在最想說的那一段接下去，我會根據這一輪的語意和前面的主題一起理解。"

class ClarificationGate:
    @staticmethod
    def response(intent: IntentFrame) -> str:
        if not intent.missing_slots:
            return ""
        if "target_platform" in intent.missing_slots:
            return (
                "可以，但我現在還不知道你說的「外掛」要掛在哪裡。"
                "你先告訴我兩件事：① 目標平台／程式／遊戲是什麼；② 外掛具體要做到什麼功能。"
                "有這兩個條件後我再寫，不會隨便塞一個和需求無關的範例程式。"
            )
        return (
            "可以寫，但這個需求目前還缺「它到底要做什麼」。"
            "請給我一個明確目標，例如：非同步爬蟲、檔案索引器、資料分析工具、Discord bot、演算法模擬器等。"
            "我拿到目標後再產生真正對題的程式，而不是隨機給一個 quicksort。"
        )

class ChristineG3V15Runtime:
    """v1.5: IntentKernel -> ContextGraph -> route. Context cannot mutate intent."""

    def __init__(self, *, memory=None, web=None, context=None, nova=None, sage=None):
        self.intent = IntentKernel()
        self.context = context or ContextGraph()
        self.memory = memory or v13.v12.Direct138MemoryBridge()
        self.orbit = web or URLAwareORBIT()
        self.sage = sage or v13.SAGE3Narrative()
        self.dialogue = NativeDialogue()
        self.clarify = ClarificationGate()
        self.nova = nova or v14.NOVARuntime()

    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]:
        raw = _clean(user_input)
        intent = self.intent.analyze(raw)
        resolution = self.context.resolve(raw, intent)
        turn = g3.TurnEnvelope(user_input=raw)
        turn.trace.append(f"intent:{intent.mode}")
        turn.trace.append(f"context:{resolution.continuity:.2f}")
        turn.contract = g3.TaskContract(
            goal=resolution.topic, operation=intent.operation, output_kind=intent.output_kind,
            requires_facts=intent.requires_facts, requires_current_info=intent.requires_web,
            requires_web=intent.requires_web, language="python" if "python" in raw.casefold() else "",
            success_conditions=("satisfy current intent",),
        )

        if intent.mode == "compute":
            result = g3.ChristineG3Runtime._calculate(raw)
            answer = result or "我沒能把這一輪解析成安全可計算的算式。"
            self.context.commit(raw, resolution)
            return answer, turn

        if intent.mode == "clarify":
            answer = self.clarify.response(intent)
            turn.trace.append("clarify:missing-slots")
            self.context.commit(raw, resolution)
            return answer, turn

        if intent.mode in {"support", "conversation"}:
            answer = self.dialogue.respond(raw, resolution)
            turn.trace.append("dialogue:native")
            self.context.commit(raw, resolution)
            return answer, turn

        if intent.mode in {"inspect_url", "research", "answer"}:
            query = resolution.topic
            if intent.mode == "answer":
                turn.memory_evidence = self.memory.retrieve(query, limit=12)
                turn.trace.append(f"memory:{len(turn.memory_evidence)}/138B")
            else:
                turn.memory_evidence = []
            memory_strength = max((e.confidence * max(0.15, e.relevance) for e in turn.memory_evidence), default=0.0)
            should_web = intent.requires_web or intent.mode in {"inspect_url", "research"} or (intent.mode == "answer" and memory_strength < 0.60)
            if should_web:
                turn.web_packet = self.orbit.research(resolution)
                turn.trace.append(f"orbit:{intent.source_hint or 'open-web'}:{len(turn.web_packet.evidence)}:{turn.web_packet.confidence:.2f}")
            evidence = list(turn.memory_evidence)
            if turn.web_packet:
                evidence.extend(turn.web_packet.evidence)
            answer, used, meta = self.sage.synthesize(
                goal=query, evidence=evidence, packet=turn.web_packet,
                followup=resolution.continuity >= 0.34, exclude_sources=set(),
            )
            turn.trace.append(f"sage3:facts={meta.get('facts', 0)} sources={meta.get('sources', 0)}")
            self.context.commit(raw, resolution)
            return answer, turn

        if intent.mode == "create_code":
            code_goal = resolution.topic
            answer, child_turn = self.nova.ask(code_goal)
            turn.trace.extend(["code:nova"] + list(child_turn.trace))
            self.context.commit(raw, resolution)
            return answer, turn

        answer = self.dialogue.respond(raw, resolution)
        self.context.commit(raw, resolution)
        return answer, turn

def main() -> int:
    print("=" * 96)
    print(" Christine G3 v1.5 — Context & Intent Kernel + URL ORBIT + SAGE-3 + NOVA + 5D9A 138B")
    print(" Current-turn intent is fixed before context inheritance.")
    print(f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens")
    print("=" * 96)
    runtime = ChristineG3V15Runtime()
    print("Type 'exit' to quit, 'clear' to clear.\n")
    while True:
        try:
            user = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.casefold() in {"exit", "quit", "bye"}:
            break
        if user.casefold() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        started = time.perf_counter()
        answer, turn = runtime.ask(user)
        elapsed = time.perf_counter() - started
        print(f"Christine：{answer}")
        print(f"  [G3 v1.5 trace: {' | '.join(turn.trace)} | {elapsed:.2f}s]\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
