from __future__ import annotations

import ast
import re
from pathlib import Path

from .capabilities import Clarifier, NativeGeneratorAdapter
from .context import ContextGraph
from .contracts import TurnState
from .dialogue import NativeDialogue
from .lexer_intent import IntentKernel
from .longform import LongFormStore
from .memory138 import Memory138
from .memory_hygiene import EvidenceHygiene
from .prism import PRISMPlanner, PRISMNarrator
from .research import ResearchEngine
from .synthesis import FactGraph
from .truth_gate import TruthGate
from .self_map import SelfMap
from .omega5d9a import OMEGA5D9A
from .utils import clean
from .verify_nova import NoveltyGate, Verifier


class UnifiedKernel:
    """G3 v2.4: 5D9A-OMEGA central cognitive-field kernel."""

    def __init__(self, *, context=None, memory=None, research=None, documents=None,
                 generator=None, novelty=None, hygiene=None, truth_gate=None,
                 self_map=None, omega=None):
        self.intent_kernel = IntentKernel()
        self.context = context or ContextGraph()
        self.memory = memory or Memory138()
        self.research = research or ResearchEngine()
        self.documents = documents or LongFormStore()
        self.generator = generator or NativeGeneratorAdapter()
        self.hygiene = hygiene or EvidenceHygiene()
        self.truth_gate = truth_gate or TruthGate()
        self.self_map = self_map or SelfMap()
        self.omega = omega or OMEGA5D9A()
        self.facts = FactGraph()
        self.prism = PRISMPlanner()
        self.narrator = PRISMNarrator()
        self.dialogue = NativeDialogue()
        self.clarifier = Clarifier()
        self.verifier = Verifier()
        self.novelty = novelty or NoveltyGate()

    def ask(self, raw):
        raw = clean(raw)
        turn = TurnState(raw)
        intent = self.intent_kernel.analyze(raw)
        turn.intent = intent
        turn.trace.append(f"intent:{intent.kind}")
        ctx = self.context.resolve(raw, intent)
        turn.context = ctx
        turn.trace.append(f"context:{ctx.continuity:.2f}")

        omega_subject = self._subject(intent, ctx)
        frame = self.omega.preflight(intent, ctx, subject=omega_subject)
        turn.omega_frame = frame
        w = frame.weights
        turn.trace.append(
            f"omega:{frame.domain.dominant()}:p={frame.demand.pressure:.2f}:"
            f"k={frame.budget.memory_k}:w={w.semantic:.2f}/{w.temporal:.2f}/"
            f"{w.relational:.2f}/{w.personal:.2f}/{w.epistemic:.2f}"
        )

        if intent.kind == "compute":
            answer = self._calculate(intent.goal)
            self.context.commit(raw, intent, ctx)
            return answer, turn
        if intent.kind == "clarify":
            answer = self.clarifier.respond(intent)
            turn.trace.append("clarify")
            self.context.commit(raw, intent, ctx)
            return answer, turn
        if intent.kind in {"support", "conversation"}:
            answer = None
            if intent.kind == "conversation" and hasattr(self.generator, "reason"):
                answer = self.generator.reason(intent.goal, {
                    "mode": "conversation",
                    "topic": ctx.topic,
                    "continuity": ctx.continuity,
                    "omega": self._frame_payload(frame),
                })
                if answer:
                    turn.trace.append("native_engine:omega-dialogue")
            if not answer:
                answer = self.dialogue.respond(raw, intent, ctx)
                turn.trace.append("dialogue:native")
            self.context.commit(raw, intent, ctx)
            return answer, turn
        if intent.kind in {"answer", "research", "inspect_url"}:
            answer = self._factual(turn)
            self.context.commit(raw, intent, ctx)
            return answer, turn
        if intent.kind == "create_code":
            answer = self._code(turn)
            self.context.commit(raw, intent, ctx)
            return answer, turn
        if intent.kind == "create_image":
            answer = self._image(turn)
            self.context.commit(raw, intent, ctx)
            return answer, turn
        answer = "我理解到這是一個任務，但目前還沒有對應的可靠執行路徑。"
        self.context.commit(raw, intent, ctx)
        return answer, turn

    def _factual(self, turn):
        intent, ctx = turn.intent, turn.context
        subject = self._subject(intent, ctx)
        if self.self_map.is_self_query(intent.goal or ctx.topic):
            self_answer, self_evidence = self.self_map.describe(intent.goal or ctx.topic)
            turn.evidence.extend(self_evidence)
            turn.trace.append(f"selfmap:{len(self_evidence)}")
            truth = self.truth_gate.evaluate(self_answer, evidence=self_evidence,
                                             facts=(), verifier_backed=True)
            turn.trace.append(
                f"truth:{truth.reason}:gr={truth.grounding_ratio:.2f}:src={truth.independent_sources}"
            )
            if not truth.accepted:
                return self.truth_gate.safe_fallback(subject, truth)
            return self_answer

        frame = getattr(turn, "omega_frame", self.omega.preflight(intent, ctx, subject=subject))
        memory_raw = self.memory.retrieve(ctx.topic, frame.budget.memory_k)
        documents_raw = self.documents.retrieve(ctx.topic, token_budget=12000)
        pre_web, report1 = self.hygiene.sanitize(
            query=intent.goal or ctx.topic, subject=subject,
            evidence=list(memory_raw) + list(documents_raw))
        turn.evidence.extend(pre_web)
        if hasattr(self.memory, "note_active"):
            self.memory.note_active(pre_web)
        turn.trace.append(
            f"hygiene:local:{report1.kept}/{report1.kept + report1.rejected}:reject={report1.rejected}"
        )
        turn.trace.append(f"memory:{len(memory_raw)}/138B")
        if documents_raw:
            turn.trace.append(f"longdoc:{len(documents_raw)}")

        strength = max((e.confidence * max(.15, e.relevance) for e in pre_web), default=0.0)
        packet = None
        should_web = (
            intent.requires_web or intent.kind in {"research", "inspect_url"}
            or (intent.requires_facts and strength < .60)
            or self.omega.should_search_web(frame, pre_web)
        )
        if should_web:
            packet = self.research.research(intent, ctx)
            web_clean, report2 = self.hygiene.sanitize(
                query=intent.goal or ctx.topic, subject=subject,
                evidence=list(packet.evidence))
            turn.evidence.extend(web_clean)
            turn.trace.append(f"orbit:{len(packet.evidence)}:{packet.confidence:.2f}")
            turn.trace.append(
                f"hygiene:web:{report2.kept}/{report2.kept + report2.rejected}:reject={report2.rejected}"
            )

        selected_evidence, omega_scores = self.omega.select_evidence(frame, turn.evidence)
        turn.evidence = selected_evidence
        if hasattr(self.memory, "note_active"):
            self.memory.note_active(selected_evidence)
        field_state = self.omega.field_state(frame, selected_evidence)
        hyps = self.omega.hypotheses(frame, selected_evidence)
        turn.omega_hypotheses = hyps
        turn.trace.append(
            f"omega:activate={len(selected_evidence)}/{len(omega_scores)}:"
            f"field={'/'.join(f'{x:.2f}' for x in field_state)}:hyp={len(hyps)}"
        )

        facts = self.facts.extract(subject, turn.evidence)
        turn.facts = facts
        turn.trace.append(f"facts:{len(facts)}")
        plan = self.prism.plan(question=intent.goal or ctx.topic, subject=subject,
                               facts=facts, packet=packet, token_budget=1200)
        turn.trace.append(
            f"prism:{plan.mode}:{len(plan.facets)}:cov={plan.coverage_score:.2f}:div={plan.diversity_score:.2f}"
        )
        draft_answer = self.narrator.narrate(
            subject=subject, question=intent.goal or ctx.topic,
            plan=plan, packet=packet)
        answer = draft_answer

        if self.omega.should_use_native_reasoner(
            frame, evidence_count=len(turn.evidence), fact_count=len(turn.facts)
        ) and hasattr(self.generator, "reason"):
            native_answer = self.generator.reason(intent.goal or ctx.topic, {
                "mode": "grounded_reasoning",
                "subject": subject,
                "omega": self._frame_payload(frame),
                "plan": [step.action for step in frame.plan.steps],
                "evidence": [
                    {"content": e.content, "source": e.source,
                     "confidence": e.confidence, "trust": e.trust,
                     "origin": e.origin}
                    for e in turn.evidence
                ],
                "facts": [
                    {"category": f.category, "subject": f.subject,
                     "predicate": f.predicate, "value": f.value,
                     "confidence": f.confidence, "sources": list(f.sources)}
                    for f in turn.facts
                ],
                "hypotheses": [
                    {"claim": h.claim, "posterior": h.posterior}
                    for h in hyps[:frame.budget.hypothesis_width]
                ],
                "fallback_draft": draft_answer,
            })
            if native_answer:
                native_surface = self.verifier.verify_text(native_answer)
                native_truth = self.truth_gate.evaluate(
                    native_answer, evidence=turn.evidence,
                    facts=turn.facts, verifier_backed=False)
                if native_surface.accepted and native_truth.accepted:
                    answer = native_answer
                    turn.trace.append(
                        f"native_engine:omega:truth={native_truth.grounding_ratio:.2f}"
                    )
                else:
                    turn.trace.append("native_engine:omega-rejected")

        verified = self.verifier.verify_text(answer)
        turn.trace.append(f"verify:{verified.reason}")
        if not verified.accepted:
            return "我這輪有取得資料，但整理結果沒有通過輸出驗證，所以先不輸出可能損壞的內容。"
        truth = self.truth_gate.evaluate(answer, evidence=turn.evidence,
                                         facts=turn.facts, verifier_backed=False)
        turn.trace.append(
            f"truth:{truth.reason}:gr={truth.grounding_ratio:.2f}:src={truth.independent_sources}"
        )
        if not truth.accepted:
            return self.truth_gate.safe_fallback(subject, truth)
        novelty = self.novelty.accept(intent.goal or ctx.topic, "text", answer)
        turn.trace.append(f"nova:{novelty.reason}")
        if not novelty.accepted:
            return "這一輪查到的可靠核心資訊和前面相同，沒有新的獨立證據值得重複一遍。"

        audit = self.omega.audit(
            frame, evidence=turn.evidence, facts=turn.facts,
            truth_grounding=truth.grounding_ratio, truth_accepted=truth.accepted)
        turn.trace.append(
            f"omega:audit={audit.total_quality:.2f}:cov={audit.coverage:.2f}:"
            f"epi={audit.epistemic_quality:.2f}:conflict={audit.contradiction:.2f}"
        )
        successful = ["retrieve_memory", "build_fact_graph", "verify"]
        if packet is not None:
            successful.append("search_web")
        if "native_engine:omega" in "|".join(turn.trace):
            successful.append("native_reason")
        self.omega.adapt(frame, audit, successful_actions=successful)
        if audit.should_commit:
            self.memory.remember_verified([
                {"content": f"{f.subject} {f.predicate} {f.value}",
                 "source": ",".join(f.sources), "confidence": f.confidence}
                for f in facts if f.confidence >= .86
            ])
        return answer

    def _code(self, turn):
        intent, ctx = turn.intent, turn.context
        frame = getattr(turn, "omega_frame", self.omega.preflight(
            intent, ctx, subject=self._subject(intent, ctx)))
        raw_memory = self.memory.retrieve(ctx.topic, min(frame.budget.memory_k, 48))
        code_context, report = self.hygiene.sanitize(
            query=intent.goal or ctx.topic, subject=self._subject(intent, ctx),
            evidence=list(raw_memory))
        turn.trace.append(f"hygiene:code:{report.kept}/{report.kept + report.rejected}")
        artifact = self.generator.code(intent.goal, {
            "topic": ctx.topic,
            "entities": intent.entities + ctx.inherited_entities,
            "memory": code_context,
            "omega": self._frame_payload(frame),
            "plan": [step.action for step in frame.plan.steps],
        })
        if artifact is None:
            return (
                "這是一個具體程式任務，但目前沒有接上 Christine 自己的 NativeGenerator。"
                "v2.4 不會用 quicksort 或固定模板冒充完成；把你的原生生成器提供成 "
                "`christine_native_generator.generate_code(goal, context)` 後，這條路會直接使用它。"
            )
        turn.artifact = artifact
        verified = self.verifier.verify_artifact(artifact)
        turn.trace.append(f"verify:{verified.reason}")
        if not verified.accepted:
            return "Christine 原生生成器有輸出程式碼，但沒有通過語法／artifact 驗證，所以我沒有顯示它。"
        novelty = self.novelty.accept(intent.goal or ctx.topic, "code", artifact.content)
        turn.trace.append(f"nova:{novelty.reason}")
        if not novelty.accepted:
            return "原生生成器這次產出的程式和先前版本在內容或 AST 結構上高度重複，因此 NOVA 已阻止重貼。"
        code_audit = self.omega.audit(
            frame, evidence=code_context, facts=(),
            truth_grounding=1.0, truth_accepted=True)
        self.omega.adapt(frame, code_audit,
                         successful_actions=("retrieve_memory", "generate_code", "verify"))
        turn.trace.append(f"omega:audit={code_audit.total_quality:.2f}")
        return artifact.content

    def _image(self, turn):
        intent, ctx = turn.intent, turn.context
        artifact = self.generator.image(intent.goal, {"topic": ctx.topic})
        if artifact is None:
            return (
                "我已確認這是圖片生成任務，但目前沒有接上 Christine 自己的 Native Image Generator。"
                "v2.4 不會用一句「已生成」假裝完成。"
            )
        turn.artifact = artifact
        verified = self.verifier.verify_artifact(artifact)
        turn.trace.append(f"verify:{verified.reason}")
        return artifact.path if verified.accepted else "圖片生成器有回傳結果，但 artifact 驗證失敗。"

    @staticmethod
    def _frame_payload(frame):
        return {
            "domain": frame.domain.dominant(),
            "demand": {
                "uncertainty": frame.demand.uncertainty,
                "novelty": frame.demand.novelty,
                "freshness": frame.demand.freshness,
                "verification": frame.demand.verification,
                "contradiction": frame.demand.contradiction,
                "goal_complexity": frame.demand.goal_complexity,
                "pressure": frame.demand.pressure,
            },
            "weights": {
                "semantic": frame.weights.semantic,
                "temporal": frame.weights.temporal,
                "relational": frame.weights.relational,
                "personal": frame.weights.personal,
                "epistemic": frame.weights.epistemic,
            },
            "budget": {
                "memory_k": frame.budget.memory_k,
                "active_evidence_k": frame.budget.active_evidence_k,
                "active_token_budget": frame.budget.active_token_budget,
                "web_query_budget": frame.budget.web_query_budget,
                "hypothesis_width": frame.budget.hypothesis_width,
                "plan_beam_width": frame.budget.plan_beam_width,
                "graph_hops": frame.budget.graph_hops,
                "max_reasoning_steps": frame.budget.max_reasoning_steps,
            },
        }

    @staticmethod
    def _subject(intent, ctx):
        entities = tuple(dict.fromkeys(intent.entities + ctx.inherited_entities))
        if entities:
            return entities[0]
        patterns = (
            r"([^\s，。？！?：:]{2,40})\s*(?:是誰|是什麼|是啥|啥意思|什麼意思|意思是什麼|是幹嘛的)",
            r"^(?:解釋|說明|介紹)(?:一下)?\s*([^，。？！?]{2,40})",
        )
        for pattern in patterns:
            m = re.search(pattern, ctx.topic)
            if m:
                return m.group(1).strip()
        return ctx.topic[:60]

    @staticmethod
    def _calculate(text):
        m = re.search(r"([0-9().+\-*/% ]{3,})", text)
        if not m:
            return "我沒有解析到可安全計算的算式。"
        expr = m.group(1).strip()
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError:
            return "算式語法無法解析。"
        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
            ast.Mod, ast.Pow, ast.UAdd, ast.USub, ast.Load,
        )
        if any(not isinstance(n, allowed) for n in ast.walk(tree)):
            return "這個算式包含不允許的運算。"
        try:
            value = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {})
        except Exception:
            return "計算失敗。"
        return f"{expr} = {value}"

    def ingest_file(self, path):
        p = Path(path).expanduser()
        if not p.exists() or not p.is_file():
            return f"找不到檔案：{p}"
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = p.read_text(encoding="utf-8-sig")
            except Exception:
                return "目前 /ingest 只直接支援可讀取的文字檔。"
        return f"已匯入 {p.name}，建立 {self.documents.ingest(p.name, text)} 個長文區塊。"
