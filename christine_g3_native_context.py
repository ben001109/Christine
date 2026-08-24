from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.parse
from collections import deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import christine_g3_frontier as g3
import christine_g3_web138 as v11


NATIVE_SYNTHESIS = True
FIVED9A_TOKEN_CAPACITY = v11.FIVED9A_TOKEN_CAPACITY
THREAD_STATE_PATH = Path(
    os.environ.get("CHRISTINE_G3_THREAD_STATE", "data/g3_thread_state.json")
)


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"^\s*(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}\s+\d{1,2}:\d{2}\s*)", "", text)
    return text


def _domain(source: str) -> str:
    try:
        return urllib.parse.urlparse(source).netloc.casefold() or source
    except Exception:
        return source


@dataclass
class ThreadTurn:
    user_input: str
    resolved_goal: str
    operation: str
    output_kind: str
    answer_summary: str = ""
    evidence_sources: tuple[str, ...] = ()
    timestamp: float = field(default_factory=time.time)


@dataclass
class ThreadResolution:
    contract: g3.TaskContract
    resolved_goal: str
    followup: bool
    inherited_from: str = ""


class THREADContext:
    """
    Conversation continuity without dumping previous assistant prose into the next prompt.

    Stores only:
      - prior task contract
      - resolved goal/topic
      - artifact kind
      - compact answer summary
      - evidence/source metadata
    """

    FOLLOWUP = re.compile(
        r"^(還有|還會|還能|再|另外|其他|那|那這個|這個|它|他呢|那呢|然後|繼續|接著|也可以|也會|呢|嗎|可以嗎)",
        re.I,
    )
    REFERENCE = re.compile(r"(剛剛|上一個|前面|之前|那個|這個|它|同樣|一樣|其他的|更多)", re.I)

    def __init__(self, max_turns: int = 12, state_path: Path | None = THREAD_STATE_PATH) -> None:
        self.turns: deque[ThreadTurn] = deque(maxlen=max_turns)
        self.state_path = state_path
        self._load()

    @property
    def last(self) -> ThreadTurn | None:
        return self.turns[-1] if self.turns else None

    def is_followup(self, text: str) -> bool:
        raw = _clean(text)
        if not self.last:
            return False
        if self.FOLLOWUP.search(raw):
            return True
        if len(raw) <= 28 and self.REFERENCE.search(raw):
            return True
        if len(raw) <= 16 and raw.endswith(("嗎", "呢", "?", "？")):
            return True
        return False

    def resolve(self, raw: str, parser: g3.ContractParser) -> ThreadResolution:
        current = _clean(raw)
        direct = parser.parse(current)
        if not self.is_followup(current) or self.last is None:
            return ThreadResolution(direct, direct.goal, False)

        prev = self.last
        if direct.operation in {"create", "compute", "research"} and len(current) > 18:
            return ThreadResolution(direct, direct.goal, False)

        resolved_goal = f"{prev.resolved_goal}；目前追問：{current}"
        inherited = g3.TaskContract(
            goal=resolved_goal,
            operation=prev.operation,
            output_kind=prev.output_kind,
            requires_facts=(prev.operation in {"answer", "research"}),
            requires_current_info=False,
            requires_web=False,
            language="python" if prev.output_kind == "code" else "",
            success_conditions=(
                "continue the previous topic coherently",
                "answer the new follow-up instead of restarting the old turn",
            ),
        )
        if prev.operation == "research":
            inherited = replace(inherited, requires_facts=True, requires_web=True)

        return ThreadResolution(
            inherited,
            resolved_goal,
            True,
            inherited_from=prev.resolved_goal,
        )

    def commit(
        self,
        *,
        user_input: str,
        contract: g3.TaskContract,
        resolved_goal: str,
        answer: str,
        evidence: list[g3.Evidence],
    ) -> None:
        summary = self._summary(answer)
        sources = tuple(dict.fromkeys(e.source for e in evidence if e.source))[:12]
        self.turns.append(
            ThreadTurn(
                user_input=user_input,
                resolved_goal=resolved_goal,
                operation=contract.operation,
                output_kind=contract.output_kind,
                answer_summary=summary,
                evidence_sources=sources,
            )
        )
        self._save()

    @staticmethod
    def _summary(answer: str) -> str:
        text = _clean(answer)
        return text[:280]

    def _save(self) -> None:
        if self.state_path is None:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [
                {
                    "user_input": t.user_input,
                    "resolved_goal": t.resolved_goal,
                    "operation": t.operation,
                    "output_kind": t.output_kind,
                    "answer_summary": t.answer_summary,
                    "evidence_sources": list(t.evidence_sources),
                    "timestamp": t.timestamp,
                }
                for t in self.turns
            ]
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.state_path)
        except Exception:
            pass

    def _load(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            for item in data[-self.turns.maxlen:]:
                self.turns.append(
                    ThreadTurn(
                        user_input=str(item.get("user_input", "")),
                        resolved_goal=str(item.get("resolved_goal", "")),
                        operation=str(item.get("operation", "answer")),
                        output_kind=str(item.get("output_kind", "text")),
                        answer_summary=str(item.get("answer_summary", "")),
                        evidence_sources=tuple(item.get("evidence_sources", ())),
                        timestamp=float(item.get("timestamp", time.time())),
                    )
                )
        except Exception:
            self.turns.clear()


@dataclass
class EvidenceCluster:
    representative: g3.Evidence
    members: list[g3.Evidence]
    independent_sources: tuple[str, ...]
    confidence: float
    relevance: float


class SAGENativeSynthesizer:
    """
    SAGE = Source-Aware Grounded Expression.

    Native-only synthesis:
      - no Ollama
      - no external/open-source language model
      - no raw search-result dumping

    Pipeline:
      relevance recalibration -> dedupe -> cluster -> source fusion
      -> clause abstraction -> Christine-style verbalization.
    """

    BOILERPLATE = (
        "cookie", "privacy policy", "terms of service", "sign in", "log in",
        "訂閱", "登入", "隱私權", "使用條款", "廣告",
    )

    def synthesize(
        self,
        *,
        goal: str,
        evidence: list[g3.Evidence],
        packet: g3.ResearchPacket | None,
        followup: bool = False,
        exclude_sources: set[str] | None = None,
    ) -> tuple[str, list[g3.Evidence], dict[str, Any]]:
        exclude_sources = exclude_sources or set()
        filtered = self._relevant(goal, evidence)
        deduped = self._dedupe(filtered)
        if followup and exclude_sources:
            fresh = [e for e in deduped if e.source not in exclude_sources]
            if fresh:
                deduped = fresh

        clusters = self._cluster(deduped)
        clusters.sort(
            key=lambda c: c.confidence * (0.55 + 0.45 * c.relevance),
            reverse=True,
        )

        if not clusters:
            return (
                "我已整理目前取得的資料，但沒有找到和這個問題足夠直接相關、可以可靠重述的內容。",
                [],
                {"clusters": 0, "sources": 0},
            )

        chosen = clusters[:6]
        used = [m for c in chosen for m in c.members]
        unique_domains = tuple(dict.fromkeys(
            d for c in chosen for d in c.independent_sources if d
        ))

        lines: list[str] = []
        if followup:
            lines.append("有，我延續上一輪的主題再整理一次；下面只列尚未重複的重點。")
        else:
            lines.append("我把查到的資料去重、交叉比對後，整理成這幾個重點：")

        for idx, cluster in enumerate(chosen, 1):
            statement = self._paraphrase(cluster.representative.content)
            support_n = len(cluster.independent_sources)
            if support_n >= 2:
                suffix = f"（{support_n} 個獨立來源互相支持）"
            elif cluster.confidence >= 0.70:
                suffix = "（目前有較強單一來源支持）"
            else:
                suffix = "（目前仍屬單一線索）"
            lines.append(f"{idx}. {statement}{suffix}")

        if packet is not None:
            confidence = packet.confidence
        else:
            confidence = max(c.confidence for c in chosen)

        if confidence >= 0.82:
            judgement = "整體證據一致性高，可以把上面的內容視為目前較可靠的結論。"
        elif confidence >= 0.65:
            judgement = "整體證據已有一定交叉支持，但部分細節仍建議保留不確定性。"
        else:
            judgement = "目前證據還不夠集中，我會把上面內容視為可追查的線索，而不是確定事實。"
        lines.append("")
        lines.append("我的判斷：" + judgement)

        lines.append("")
        lines.append("主要來源：")
        source_rows = []
        for c in chosen:
            for item in c.members:
                if item.source.startswith(("http://", "https://")) and item.source not in source_rows:
                    source_rows.append(item.source)
        for src in source_rows[:6]:
            lines.append(f"- {src}")

        return "\n".join(lines), used, {
            "clusters": len(clusters),
            "chosen_clusters": len(chosen),
            "sources": len(unique_domains),
            "confidence": confidence,
        }

    def _relevant(self, goal: str, evidence: list[g3.Evidence]) -> list[g3.Evidence]:
        q = g3._tokens(goal)
        scored = []
        for e in evidence:
            text = _clean(e.content)
            if not text:
                continue
            low = text.casefold()
            if any(b in low for b in self.BOILERPLATE) and len(text) < 180:
                continue
            rel_now = g3._jaccard(q, g3._tokens(text))
            blended = max(rel_now, e.relevance * 0.65)
            if blended < 0.015:
                continue
            scored.append(
                g3.Evidence(
                    content=text,
                    source=e.source,
                    confidence=e.confidence,
                    relevance=blended,
                )
            )
        return sorted(
            scored,
            key=lambda x: x.confidence * (0.45 + 0.55 * x.relevance),
            reverse=True,
        )

    def _dedupe(self, evidence: list[g3.Evidence]) -> list[g3.Evidence]:
        out: list[g3.Evidence] = []
        seen_exact: set[tuple[str, str]] = set()
        for e in evidence:
            norm = re.sub(r"\W+", "", e.content.casefold())
            key = (_domain(e.source), norm[:300])
            if key in seen_exact:
                continue
            seen_exact.add(key)

            tokens = g3._tokens(e.content)
            duplicate = False
            for old in out:
                if g3._jaccard(tokens, g3._tokens(old.content)) >= 0.80:
                    duplicate = True
                    break
            if not duplicate:
                out.append(e)
        return out

    def _cluster(self, evidence: list[g3.Evidence]) -> list[EvidenceCluster]:
        clusters: list[list[g3.Evidence]] = []
        for e in evidence:
            et = g3._tokens(e.content)
            best_i = None
            best_sim = 0.0
            for i, cluster in enumerate(clusters):
                sim = g3._jaccard(et, g3._tokens(cluster[0].content))
                if sim > best_sim:
                    best_i, best_sim = i, sim
            if best_i is not None and best_sim >= 0.30:
                clusters[best_i].append(e)
            else:
                clusters.append([e])

        result: list[EvidenceCluster] = []
        for members in clusters:
            members.sort(
                key=lambda x: x.confidence * (0.4 + 0.6 * x.relevance),
                reverse=True,
            )
            domains: dict[str, float] = {}
            for e in members:
                d = _domain(e.source)
                domains[d] = max(domains.get(d, 0.0), e.confidence)

            p_not = 1.0
            for score in sorted(domains.values(), reverse=True)[:6]:
                p_not *= 1.0 - max(0.0, min(1.0, score))
            confidence = 1.0 - p_not
            relevance = max(e.relevance for e in members)

            result.append(
                EvidenceCluster(
                    representative=members[0],
                    members=members,
                    independent_sources=tuple(domains),
                    confidence=confidence,
                    relevance=relevance,
                )
            )
        return result

    def _paraphrase(self, raw: str) -> str:
        text = _clean(raw)
        text = re.sub(r"^[•\-–—\d.)\s]+", "", text)
        text = re.sub(r"[「」『』【】]", "", text)
        text = re.sub(r"\([^)]{0,120}\)", "", text)
        text = _clean(text)

        parts = re.split(r"\s*(?:[:：]| - | — | \| )\s*", text, maxsplit=1)
        if len(parts) == 2 and len(parts[1]) >= 18 and len(parts[0]) <= 50:
            text = parts[1]

        clauses = [
            _clean(x)
            for x in re.split(r"(?<=[。！？.!?])\s+|[；;]\s*", text)
            if _clean(x)
        ]
        if clauses:
            text = max(
                clauses[:4],
                key=lambda x: min(len(x), 180) * (1 + len(g3._tokens(x))),
            )

        relation_patterns = [
            (r"^(.{2,45}?)(?:被|由)(.{2,80}?)(?:建立|創立|開發|推出)(.*)$",
             lambda m: f"可整理為：{m.group(1).strip()}的建立／推出與{m.group(2).strip()}有關{m.group(3).strip()}。"),
            (r"^(.{2,45}?)(?:是|為)(.{3,120})$",
             lambda m: f"核心意思是，{m.group(1).strip()}可被理解為{m.group(2).strip()}。"),
            (r"^(.{2,45}?)(?:指出|表示|顯示|宣布)(.{3,120})$",
             lambda m: f"資料反映出：{m.group(1).strip()}{m.group(2).strip()}。"),
            (r"^(.{2,45}?)(?:提供|支援|包含|具有)(.{3,120})$",
             lambda m: f"其中一個可確認的重點是，{m.group(1).strip()}具備／涵蓋{m.group(2).strip()}。"),
        ]
        for pattern, fn in relation_patterns:
            m = re.match(pattern, text)
            if m:
                return _clean(fn(m))[:260]

        if len(text) > 170:
            text = text[:167].rstrip("，,;； ") + "…"
        return f"目前資料能支持的重點是：{text.rstrip('。.!！')}。"


class Direct138MemoryBridge(v11.Memory138Bridge):
    """138B memory contract without initializing an OSS LLM."""

    def __init__(self) -> None:
        super().__init__(engine=None)
        self._rows = self._load_rows()

    def _load_rows(self) -> list[dict[str, Any]]:
        candidates = [
            Path("data/christine_v42/permanent_folder_memory.json"),
            Path("data/permanent_folder_memory.json"),
        ]
        for path in candidates:
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict):
                rows = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        rows.append({"key": key, **value})
                    else:
                        rows.append({"key": key, "content": str(value)})
                return rows
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
        return []

    def retrieve(self, query: str, limit: int = 12) -> list[g3.Evidence]:
        if not self._rows:
            return []
        q = g3._tokens(query)
        scored = []
        for row in self._rows:
            content = str(
                row.get("content")
                or row.get("content_summary")
                or row.get("summary")
                or row.get("value")
                or ""
            )
            if not content:
                continue
            rel = g3._jaccard(q, g3._tokens(content))
            if rel <= 0:
                continue
            scored.append(
                g3.Evidence(
                    content=_clean(content),
                    source="5d9a-local",
                    confidence=0.70,
                    relevance=rel,
                )
            )
        scored.sort(key=lambda e: e.relevance, reverse=True)
        return scored[:limit]


class ChristineG3NativeContextRuntime:
    """
    G3 v1.2

    Text answering path:
      THREAD -> 138B evidence -> ORBIT -> SAGE -> ARGUS

    No Ollama/open-source model is used for evidence synthesis.
    """

    def __init__(
        self,
        *,
        memory: Any | None = None,
        web: Any | None = None,
        thread: THREADContext | None = None,
        sage: SAGENativeSynthesizer | None = None,
    ) -> None:
        self.contracts = g3.ContractParser()
        self.memory = memory or Direct138MemoryBridge()
        self.web = web or g3.ORBITWeb(timeout=10.0)
        self.thread = thread or THREADContext()
        self.sage = sage or SAGENativeSynthesizer()
        self.argus = g3.ARGUS()

    def ask(self, user_input: str) -> tuple[str, g3.TurnEnvelope]:
        raw = _clean(user_input)
        resolution = self.thread.resolve(raw, self.contracts)

        turn = g3.TurnEnvelope(user_input=raw)
        turn.contract = resolution.contract
        c = turn.contract

        turn.trace.append(f"thread:{'followup' if resolution.followup else 'new'}")
        turn.trace.append(f"contract:{c.operation}/{c.output_kind}")
        if resolution.followup:
            turn.trace.append("context:inherited-task")

        if c.operation == "compute":
            result = g3.ChristineG3Runtime._calculate(raw)
            if result is not None:
                self.thread.commit(
                    user_input=raw,
                    contract=c,
                    resolved_goal=resolution.resolved_goal,
                    answer=result,
                    evidence=[],
                )
                return result, turn

        if resolution.followup and c.operation in {"create", "converse"} and c.output_kind != "text":
            last = self.thread.last
            answer = self._creative_followup(raw, last)
            self.thread.commit(
                user_input=raw,
                contract=c,
                resolved_goal=resolution.resolved_goal,
                answer=answer,
                evidence=[],
            )
            turn.trace.append("answer:thread-native")
            return answer, turn

        query_goal = (
            resolution.inherited_from
            if resolution.followup and resolution.inherited_from
            else c.goal
        )

        if c.operation in {"answer", "research"}:
            turn.memory_evidence = self.memory.retrieve(query_goal, limit=12)
            turn.trace.append(f"memory:{len(turn.memory_evidence)}/138B")

        memory_strength = max(
            (e.confidence * max(0.15, e.relevance) for e in turn.memory_evidence),
            default=0.0,
        )

        explicit_web = c.requires_web or c.requires_current_info
        auto_web = (
            c.requires_facts
            and memory_strength < 0.60
            and c.operation in {"answer", "research"}
        )

        if explicit_web or auto_web:
            mode = "mandatory" if explicit_web else "auto"
            turn.trace.append(f"web:{mode}")
            turn.web_packet = self.web.research(query_goal)
            turn.trace.append(
                f"web:evidence={len(turn.web_packet.evidence)} conf={turn.web_packet.confidence:.2f}"
            )

        evidence = list(turn.memory_evidence)
        if turn.web_packet:
            evidence.extend(turn.web_packet.evidence)

        if c.operation in {"answer", "research"}:
            previous_sources = set(self.thread.last.evidence_sources) if (resolution.followup and self.thread.last) else set()
            candidate, used, meta = self.sage.synthesize(
                goal=query_goal,
                evidence=evidence,
                packet=turn.web_packet,
                followup=resolution.followup,
                exclude_sources=previous_sources,
            )
            turn.trace.append(
                f"sage:clusters={meta.get('chosen_clusters', 0)} sources={meta.get('sources', 0)}"
            )
            ok, reason = self.argus.verify(c, candidate, used)
            turn.trace.append(f"argus:{reason}")
            if not ok and c.requires_web and not used:
                candidate = "我有延續這一輪的網路查詢，但目前沒有足夠直接相關的證據可以可靠整理。"
            self.thread.commit(
                user_input=raw,
                contract=c,
                resolved_goal=resolution.resolved_goal,
                answer=candidate,
                evidence=used,
            )
            return candidate, turn

        if c.operation == "converse":
            candidate = self._conversation_reply(raw)
            self.thread.commit(
                user_input=raw,
                contract=c,
                resolved_goal=resolution.resolved_goal,
                answer=candidate,
                evidence=[],
            )
            turn.trace.append("answer:thread-native")
            return candidate, turn

        if c.output_kind == "code":
            candidate = (
                "我已保留這個程式任務的上下文，但 G3 v1.2 的目前設定是 native-only，"
                "不會偷偷呼叫 Ollama 或其他開源模型。要讓我直接生成任意程式碼，"
                "需要把你自己的 Christine 原生 decoder 接到 NativeGenerator 介面。"
            )
        elif c.output_kind == "image":
            candidate = (
                "我已辨識這是圖片生成任務；G3 v1.2 不會用文字假裝圖片已生成。"
                "需要把 Christine 自己的影像生成器註冊成 ImageArtifact capability。"
            )
        else:
            candidate = self._conversation_reply(raw)

        self.thread.commit(
            user_input=raw,
            contract=c,
            resolved_goal=resolution.resolved_goal,
            answer=candidate,
            evidence=[],
        )
        return candidate, turn

    def _creative_followup(self, raw: str, last: ThreadTurn | None) -> str:
        if last is None:
            return "可以，請告訴我你想延續哪一個主題。"

        if last.output_kind == "code":
            return (
                f"會。你上一輪的主題是「{last.resolved_goal}」。"
                f"你這句「{raw}」我會理解成要延續同一個程式方向，而不是重新搜尋網路。"
                "你可以直接指定「再一個不同架構」、「改成非同步版本」或「提高難度」，"
                "我會沿用同一個任務脈絡。"
            )
        if last.output_kind == "image":
            return (
                f"可以。我會延續上一輪「{last.resolved_goal}」的視覺方向，"
                "不把這句追問當成新的網路搜尋。你可以直接說要換構圖、風格或內容。"
            )
        return f"可以，我會接著上一輪「{last.resolved_goal}」繼續，不重新開一個無關主題。"

    def _conversation_reply(self, raw: str) -> str:
        last = self.thread.last
        if last and self.thread.is_followup(raw):
            return (
                f"我有接住上下文。上一輪的核心是「{last.resolved_goal}」；"
                f"你現在問「{raw}」，我會在同一個主題裡繼續回答。"
            )
        if re.search(r"^(你好|嗨|哈囉|hi|hello)", raw, re.I):
            return "你好，我在。這個 G3 v1.2 會保留對話脈絡，也會把網路證據先整理再回答。"
        return "我在聽。你可以直接接著上一句講，我會維持同一個對話脈絡。"


def main() -> int:
    print("=" * 86)
    print(" Christine G3 v1.2 — Native SAGE + THREAD + ORBIT + 5D9A 138B")
    print(" No Ollama/open-source model is used for web evidence synthesis.")
    print(f" 5D9A global address space: {FIVED9A_TOKEN_CAPACITY:,} tokens")
    print("=" * 86)
    runtime = ChristineG3NativeContextRuntime()
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
        print(f"  [G3 v1.2 trace: {' | '.join(turn.trace)} | {elapsed:.2f}s]\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
