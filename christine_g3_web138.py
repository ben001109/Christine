from __future__ import annotations

import math
import os
import re
import time
from typing import Any

import christine_g3_frontier as g3


FIVED9A_TOKEN_CAPACITY = int(os.environ.get("CHRISTINE_5D9A_TOKEN_CAPACITY", "138000000000"))
FIVED9A_LEAF_TOKENS = 1024
FIVED9A_FANOUT = 64
WEB_POLICY = os.environ.get("CHRISTINE_G3_WEB_POLICY", "aggressive").strip().casefold()


def hierarchy_counts(total_tokens: int = FIVED9A_TOKEN_CAPACITY) -> tuple[int, ...]:
    counts = [math.ceil(total_tokens / FIVED9A_LEAF_TOKENS)]
    while counts[-1] > 1:
        counts.append(math.ceil(counts[-1] / FIVED9A_FANOUT))
    return tuple(counts)


class Memory138Bridge(g3.ChristineMemoryBridge):
    """Preserve Christine's 138B-token global-addressable 5D9A memory contract."""

    def __init__(self, engine: Any | None) -> None:
        super().__init__(engine)
        self.capacity_tokens = FIVED9A_TOKEN_CAPACITY
        self.levels = hierarchy_counts()

    def status(self) -> dict[str, Any]:
        return {
            "capacity_tokens": self.capacity_tokens,
            "capacity_label": f"{self.capacity_tokens / 1_000_000_000:.0f}B",
            "leaf_tokens": FIVED9A_LEAF_TOKENS,
            "leaf_count": self.levels[0],
            "levels": self.levels,
            "backend_connected": self.engine is not None,
        }

    def retrieve(self, query: str, limit: int = 12) -> list[g3.Evidence]:
        # Existing storage remains the hot/queryable backend. The global capacity
        # remains 138B; only sparse evidence enters the active context.
        return super().retrieve(query, limit=max(12, limit))


class ChristineG3Web138Runtime:
    """
    G3 v1.1 control plane.

    Fixes the failure visible in the user's screenshot:
      ORBIT did search and found evidence, but the local LLM returned an empty
      string, so ARGUS rejected the turn. This runtime treats a successful web
      search as useful even when Ollama is temporarily unavailable.

    Invariants:
      * explicit web request => web is mandatory
      * factual query + weak memory => auto web in aggressive mode
      * web evidence != final truth; low-confidence packets are labeled
      * 138B is global addressable memory, not a 138B prompt
      * code still requires source-code artifact verification
    """

    SYSTEM = g3.ChristineG3Runtime.SYSTEM

    def __init__(
        self,
        *,
        reasoner: Any | None = None,
        memory: Any | None = None,
        web: Any | None = None,
    ) -> None:
        self.contracts = g3.ContractParser()
        self.reasoner = reasoner or g3.LocalReasoner()
        self.memory = memory or Memory138Bridge(getattr(self.reasoner, "engine", None))
        self.web = web or g3.ORBITWeb(timeout=10.0)
        self.argus = g3.ARGUS()
        self.memory_status = (
            self.memory.status()
            if hasattr(self.memory, "status")
            else {
                "capacity_tokens": FIVED9A_TOKEN_CAPACITY,
                "capacity_label": "138B",
                "leaf_count": hierarchy_counts()[0],
                "levels": hierarchy_counts(),
            }
        )

    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]:
        turn = g3.TurnEnvelope(user_input=str(user_input or "").strip())
        turn.contract = self.contracts.parse(turn.user_input)
        c = turn.contract
        turn.trace.append(f"contract:{c.operation}/{c.output_kind}")

        # Retrieval is current-turn only. Previous assistant output is not put
        # into the new retrieval query.
        if c.operation in {"answer", "research"}:
            turn.memory_evidence = self.memory.retrieve(turn.user_input, limit=12)
            turn.trace.append(
                f"memory:{len(turn.memory_evidence)}/{self.memory_status.get('capacity_label', '138B')}"
            )

        web_score = self._web_need(c, turn.memory_evidence)
        memory_weak = self._memory_strength(turn.memory_evidence) < 0.60
        aggressive_fact_web = (
            WEB_POLICY == "aggressive"
            and c.requires_facts
            and memory_weak
            and c.operation in {"answer", "research"}
        )
        should_web = c.requires_web or c.requires_current_info or aggressive_fact_web or web_score >= 0.42

        if should_web and c.operation not in {"compute", "converse"}:
            mode = "mandatory" if (c.requires_web or c.requires_current_info) else "auto"
            turn.trace.append(f"web:{mode}:score={web_score:.2f}")
            turn.web_packet = self.web.research(turn.user_input)
            turn.trace.append(
                f"web:evidence={len(turn.web_packet.evidence)} conf={turn.web_packet.confidence:.2f}"
            )

        evidence = list(turn.memory_evidence)
        if turn.web_packet:
            evidence.extend(turn.web_packet.evidence)

        if c.requires_web and (turn.web_packet is None or not turn.web_packet.evidence):
            return (
                "我確實已啟動 ORBIT 網路搜尋，但這次沒有取得可驗證的公開證據。"
                "我不會用 5D9A 的『沒有記錄』冒充網路搜尋結果。",
                turn,
            )

        if c.operation == "compute":
            computed = g3.ChristineG3Runtime._calculate(turn.user_input)
            if computed is not None:
                return computed, turn

        if c.output_kind == "code":
            prompt = g3.ChristineG3Runtime._code_prompt(c, evidence)
        else:
            prompt = g3.ChristineG3Runtime._answer_prompt(c, evidence)

        candidate = self.reasoner.generate(prompt, self.SYSTEM, temperature=0.20)

        # Critical v1.1 fix: a successful web retrieval remains useful even when
        # Ollama is not running. No invented prose is added; only retrieved
        # evidence and URLs are exposed.
        if not candidate and evidence and c.output_kind == "text":
            candidate = self._evidence_fallback(evidence, turn.web_packet)
            turn.trace.append("answer:evidence-fallback")
        elif candidate and c.requires_facts and evidence:
            # A fluent but evidence-disconnected answer is less useful than a
            # grounded evidence packet. Replace only when overlap is extremely low.
            if self._answer_evidence_overlap(candidate, evidence) < 0.005:
                candidate = self._evidence_fallback(evidence, turn.web_packet)
                turn.trace.append("answer:grounding-fallback")

        ok, reason = self.argus.verify(c, candidate, evidence)
        turn.trace.append(f"argus:{reason}")

        if not ok:
            repair_prompt = (
                prompt
                + "\n\n上一個候選未通過驗證："
                + reason
                + "。請重新完成原始任務，不得提及無關上一輪內容。"
            )
            candidate = self.reasoner.generate(repair_prompt, self.SYSTEM, temperature=0.10)
            if not candidate and evidence and c.output_kind == "text":
                candidate = self._evidence_fallback(evidence, turn.web_packet)
                turn.trace.append("answer:evidence-repair-fallback")
            ok, reason = self.argus.verify(c, candidate, evidence)
            turn.trace.append(f"argus-repair:{reason}")

        if not ok:
            if c.output_kind == "code":
                return (
                    "我目前沒有可用的生成模型產生並驗證程式碼；"
                    "請啟動 Ollama 後再試，我不會拿普通文字冒充程式。",
                    turn,
                )
            return "我目前沒有足夠可靠的證據完成這一輪回答。", turn

        return candidate, turn

    @staticmethod
    def _memory_strength(memory: list[g3.Evidence]) -> float:
        return max(
            (e.confidence * max(0.15, e.relevance) for e in memory),
            default=0.0,
        )

    @staticmethod
    def _web_need(c: g3.TaskContract, memory: list[g3.Evidence]) -> float:
        if c.operation in {"create", "compute", "converse"} and not c.requires_current_info:
            return 0.0
        base = g3.ChristineG3Runtime._web_need(c, memory)
        if c.requires_web or c.requires_current_info:
            return max(base, 0.95)
        if c.requires_facts and WEB_POLICY == "aggressive" and ChristineG3Web138Runtime._memory_strength(memory) < 0.60:
            return max(base, 0.70)
        return base

    @staticmethod
    def _answer_evidence_overlap(answer: str, evidence: list[g3.Evidence]) -> float:
        atok = g3._tokens(answer)
        return max(
            (g3._jaccard(atok, g3._tokens(e.content)) * e.confidence for e in evidence),
            default=0.0,
        )

    @staticmethod
    def _evidence_fallback(
        evidence: list[g3.Evidence],
        packet: g3.ResearchPacket | None,
    ) -> str:
        ranked = sorted(
            evidence,
            key=lambda e: e.confidence * (0.45 + 0.55 * e.relevance),
            reverse=True,
        )
        web_items = [e for e in ranked if e.source.startswith(("http://", "https://"))]
        chosen = (web_items or ranked)[:5]
        if not chosen:
            return ""

        lines: list[str] = []
        if packet is not None:
            lines.append(
                f"我已實際上網檢索，取得 {len(packet.evidence)} 條可用網路證據；"
                f"目前跨來源證據信心約 {packet.confidence:.0%}。"
            )
        else:
            lines.append("我目前根據可驗證的 5D9A 證據整理如下：")

        lines.append(
            "本地生成模型目前未就緒，所以我先只整理能由證據直接支持的內容，不補寫未驗證資訊："
        )
        for index, item in enumerate(chosen, 1):
            content = re.sub(r"\s+", " ", item.content).strip()
            if len(content) > 420:
                content = content[:417] + "..."
            lines.append(f"{index}. {content}")
            lines.append(f"   來源：{item.source}")

        if packet is not None and packet.confidence < 0.72:
            lines.append(
                "目前交叉支持仍不足，因此我把它們標成線索，而不是已確認的身分或最終結論。"
            )
        return "\n".join(lines)


def main() -> int:
    print("=" * 82)
    print(" Christine G3 Web+138B Runtime")
    print(" Task Contract | ORBIT aggressive web | 5D9A 138B | ARGUS Verify")
    print(
        f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens "
        f"| L0 leaves: {hierarchy_counts()[0]:,}"
    )
    print(f" ORBIT policy: {WEB_POLICY} | factual questions browse when local evidence is weak")
    print("=" * 82)

    runtime = ChristineG3Web138Runtime()
    if not getattr(runtime.reasoner, "ready", False):
        print("[~] Ollama is not ready: grounded web/5D9A evidence fallback is ACTIVE.")
        print("[~] Start Ollama for fully synthesized answers and code generation.")
    print("Type 'exit' to quit, 'clear' to clear the terminal.\n")

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
        print(f"  [G3 v1.1 trace: {' | '.join(turn.trace)} | {elapsed:.2f}s]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
