from __future__ import annotations

from .cedar import CEDAR
from .kernel import UnifiedKernel as UnifiedKernelV24
from .logos_m9 import LOGOSM9
from .mosaic_q import MOSAICQ
from .utils import clean


class _MosaicResearchProxy:
    def __init__(self, base, mosaic: MOSAICQ):
        self.base = base
        self.mosaic = mosaic
        self.last_report = None
        self.last_graph = None
        self.query_budget = 4

    def research(self, intent, ctx):
        query = intent.goal or ctx.topic
        if self.mosaic.should_decompose(query):
            packet, graph, report = self.mosaic.research(
                intent=intent, ctx=ctx, engine=self.base,
                query_budget=self.query_budget,
            )
            self.last_report = report
            self.last_graph = graph
            return packet
        self.last_report = None
        self.last_graph = None
        return self.base.research(intent, ctx)


class UnifiedKernelV25(UnifiedKernelV24):
    """G3 v2.5 reasoning fabric over the stable v2.4 OMEGA kernel.

    LOGOS-M9 gets first refusal on formal mathematics.
    CEDAR owns code specification/planning/static verification.
    MOSAIC-Q decomposes long scientific/factual research before ORBIT.
    """

    def __init__(self, *args, logos=None, cedar=None, mosaic=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logos = logos or LOGOSM9()
        self.cedar = cedar or CEDAR()
        self.mosaic = mosaic or MOSAICQ()
        self._research_base = self.research
        self._mosaic_proxy = _MosaicResearchProxy(self._research_base, self.mosaic)
        self.research = self._mosaic_proxy

    def ask(self, raw):
        raw = clean(raw)
        intent = self.intent_kernel.analyze(raw)
        ctx = self.context.resolve(raw, intent)
        subject = self._subject(intent, ctx)
        frame = self.omega.preflight(intent, ctx, subject=subject)
        if self.logos.can_handle(raw, frame.domain.math) and frame.domain.math >= .28:
            result = self.logos.solve(raw, max_steps=frame.budget.max_reasoning_steps)
            if result.success and result.verified:
                from .contracts import TurnState
                turn = TurnState(raw)
                turn.intent = intent
                turn.context = ctx
                turn.omega_frame = frame
                turn.trace.extend([
                    f"intent:{intent.kind}", f"context:{ctx.continuity:.2f}",
                    f"omega:{frame.domain.dominant()}:p={frame.demand.pressure:.2f}:k={frame.budget.memory_k}",
                    f"logos:{result.ir.domain if result.ir else 'math'}:{result.method}:verified=1",
                ])
                answer = result.render()
                surface = self.verifier.verify_text(answer)
                turn.trace.append(f"verify:{surface.reason}")
                if surface.accepted:
                    novelty = self.novelty.accept(intent.goal or ctx.topic or raw, "text", answer)
                    turn.trace.append(f"nova:{novelty.reason}")
                    audit = self.omega.audit(frame, evidence=(), facts=(), truth_grounding=1.0, truth_accepted=True)
                    self.omega.adapt(frame, audit, successful_actions=("symbolic_reason", "verify"))
                    turn.trace.append(f"omega:audit={audit.total_quality:.2f}")
                    self.context.commit(raw, intent, ctx)
                    return answer, turn
        return super().ask(raw)

    def _factual(self, turn):
        frame = getattr(turn, "omega_frame", None)
        if frame is not None:
            self._mosaic_proxy.query_budget = max(1, frame.budget.web_query_budget or 3)
        answer = super()._factual(turn)
        report = self._mosaic_proxy.last_report
        if report is not None:
            turn.trace.append(
                f"mosaic:q={report.queries_issued}:e={report.evidence_after_merge}:"
                f"src={report.independent_sources}:cov={report.coverage:.2f}"
            )
            turn.mosaic_graph = self._mosaic_proxy.last_graph
        return answer

    def _code(self, turn):
        intent, ctx = turn.intent, turn.context
        frame = getattr(turn, "omega_frame", self.omega.preflight(intent, ctx, subject=self._subject(intent, ctx)))
        raw_memory = self.memory.retrieve(ctx.topic, min(frame.budget.memory_k, 48))
        code_context, report = self.hygiene.sanitize(
            query=intent.goal or ctx.topic,
            subject=self._subject(intent, ctx),
            evidence=list(raw_memory),
        )
        turn.trace.append(f"hygiene:code:{report.kept}/{report.kept + report.rejected}")
        artifact, cedar_report, cedar_plan = self.cedar.generate(
            goal=intent.goal,
            context={
                "topic": ctx.topic,
                "entities": intent.entities + ctx.inherited_entities,
                "memory": code_context,
                "omega": self._frame_payload(frame),
                "plan": [step.action for step in frame.plan.steps],
            },
            generator=self.generator,
            max_repairs=2,
        )
        turn.cedar_plan = cedar_plan
        turn.trace.append(
            f"cedar:spec={cedar_plan.spec.specificity:.2f}:syntax={int(cedar_report.syntax_ok)}:"
            f"if={cedar_report.interface_coverage:.2f}:req={cedar_report.requirement_coverage:.2f}"
        )
        if artifact is None:
            if cedar_plan.spec.missing_slots:
                return self.clarifier.respond(intent)
            return "CEDAR 已完成 TaskSpec 與架構規劃，但目前沒有可用的 Christine NativeGenerator，因此不會用固定模板冒充完成。"
        turn.artifact = artifact
        verified = self.verifier.verify_artifact(artifact)
        turn.trace.append(f"verify:{verified.reason}")
        if not verified.accepted or not cedar_report.accepted:
            return f"原生生成器有輸出程式碼，但 CEDAR/Artifact 驗證未通過，因此不顯示可能錯誤的版本。原因：{cedar_report.reason}"
        novelty = self.novelty.accept(intent.goal or ctx.topic, "code", artifact.content)
        turn.trace.append(f"nova:{novelty.reason}")
        if not novelty.accepted:
            return "CEDAR 判定這次程式與先前版本高度重複，因此 NOVA 已阻止重貼。"
        audit = self.omega.audit(frame, evidence=code_context, facts=(), truth_grounding=1.0, truth_accepted=True)
        self.omega.adapt(frame, audit, successful_actions=("retrieve_memory", "generate_code", "verify"))
        turn.trace.append(f"omega:audit={audit.total_quality:.2f}")
        return artifact.content


UnifiedKernel = UnifiedKernelV25
