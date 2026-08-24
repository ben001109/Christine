from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .contracts import ContextResolution, Evidence, Fact, Intent
from .utils import clean, clamp01, jaccard, stable_id, tokens


# ================================================================
# 5D9A-OMEGA
# ================================================================
# 5D = Semantic / Temporal / Relational / Personal / Epistemic
# 9A = Acquire / Abstract / Assess / Access / Assemble /
#      Architect / Act / Audit / Adapt
#
# OMEGA is a cognitive-control algorithm, not a text generator.
# It decides HOW MUCH cognition to spend, WHICH memory deserves
# activation, WHICH tool/skill family to prefer, HOW many competing
# hypotheses/plans to keep alive, and WHEN the result is trustworthy
# enough to commit back into memory.
# ================================================================


@dataclass(frozen=True)
class FiveDWeights:
    semantic: float
    temporal: float
    relational: float
    personal: float
    epistemic: float

    def normalized(self) -> "FiveDWeights":
        total = self.semantic + self.temporal + self.relational + self.personal + self.epistemic
        if total <= 0:
            return FiveDWeights(.2, .2, .2, .2, .2)
        return FiveDWeights(
            self.semantic / total,
            self.temporal / total,
            self.relational / total,
            self.personal / total,
            self.epistemic / total,
        )

    def as_tuple(self) -> tuple[float, float, float, float, float]:
        return (self.semantic, self.temporal, self.relational, self.personal, self.epistemic)


@dataclass(frozen=True)
class CognitiveDemand:
    uncertainty: float
    novelty: float
    freshness: float
    verification: float
    contradiction: float
    domain_shift: float
    goal_complexity: float
    personal_need: float
    multi_hop: float

    @property
    def pressure(self) -> float:
        return clamp01(
            .21 * self.uncertainty
            + .17 * self.novelty
            + .11 * self.freshness
            + .14 * self.verification
            + .13 * self.contradiction
            + .08 * self.domain_shift
            + .10 * self.goal_complexity
            + .06 * self.multi_hop
        )


@dataclass(frozen=True)
class CognitiveBudget:
    memory_k: int
    active_evidence_k: int
    active_token_budget: int
    web_query_budget: int
    hypothesis_width: int
    plan_beam_width: int
    graph_hops: int
    max_reasoning_steps: int


@dataclass(frozen=True)
class DomainVector:
    factual: float = 0.0
    science: float = 0.0
    math: float = 0.0
    code: float = 0.0
    self_knowledge: float = 0.0
    social: float = 0.0
    planning: float = 0.0
    creative: float = 0.0

    def dominant(self) -> str:
        values = asdict(self)
        return max(values, key=values.get) if values else "factual"


@dataclass(frozen=True)
class EvidenceScore5D:
    evidence_id: str
    final_score: float
    semantic: float
    temporal: float
    relational: float
    personal: float
    epistemic: float
    directness: float
    coverage: float
    redundancy_penalty: float
    conflict_penalty: float
    hygiene_multiplier: float


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    claim: str
    prior: float
    support: float
    contradiction: float
    posterior: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class SkillState:
    name: str
    alpha: float = 2.0
    beta: float = 2.0
    transfer: float = 0.5
    cost: float = 0.3
    risk: float = 0.2

    @property
    def success(self) -> float:
        return self.alpha / (self.alpha + self.beta)


@dataclass(frozen=True)
class PlanStep:
    action: str
    score: float
    expected_gain: float
    expected_verification_gain: float
    cost: float
    risk: float
    rationale: str


@dataclass(frozen=True)
class CognitivePlan:
    steps: tuple[PlanStep, ...]
    expected_success: float
    estimated_cost: float
    exploration: float


@dataclass(frozen=True)
class CognitiveFrame:
    query: str
    subject: str
    domain: DomainVector
    demand: CognitiveDemand
    weights: FiveDWeights
    budget: CognitiveBudget
    plan: CognitivePlan
    query_signature: str


@dataclass(frozen=True)
class AuditResult:
    grounding: float
    coverage: float
    epistemic_quality: float
    diversity: float
    contradiction: float
    reasoning_efficiency: float
    total_quality: float
    should_commit: bool
    should_escalate: bool


@dataclass
class OMEGALedger:
    recent_queries: deque[str] = field(default_factory=lambda: deque(maxlen=128))
    skill_stats: dict[str, dict[str, float]] = field(default_factory=dict)
    outcomes: deque[dict] = field(default_factory=lambda: deque(maxlen=256))


class OMEGA5D9A:
    """Central cognitive-field controller designed specifically for 5D9A.

    The algorithm is deliberately model-agnostic. A neural decoder may propose
    language/actions, but OMEGA controls memory activation, reasoning budget,
    exploration, evidence competition, hypothesis survival, and adaptation.

    Main invariants:
      * Personal relevance may change retrieval priority, never truth confidence.
      * High uncertainty expands cognition instead of increasing answer confidence.
      * Contradictory evidence widens search and lowers certainty.
      * Expensive cognition must earn information/goal gain.
      * Only audited outcomes are allowed to update long-term skill statistics.
    """

    DEFAULT_ACTIONS = (
        "retrieve_memory", "retrieve_longdoc", "search_web", "resolve_entities",
        "decompose_question", "compare_sources", "build_fact_graph",
        "build_hypotheses", "symbolic_reason", "native_reason", "generate_code",
        "verify", "ask_clarification", "self_map",
    )

    def __init__(self, state_path: str | Path | None = Path("data/g3v2_omega_state.json"), field_dims: int = 64):
        self.state_path = Path(state_path) if state_path is not None else None
        self.field_dims = max(16, int(field_dims))
        self.ledger = OMEGALedger()
        self._load()

    # A1 Acquire + A2 Abstract + A3 Assess
    def preflight(self, intent: Intent, ctx: ContextResolution, *, subject: str = "") -> CognitiveFrame:
        query = clean(intent.goal or ctx.topic)
        domain = self._domain_vector(query, intent)
        demand = self._demand(query, intent, ctx, domain)
        weights = self._dynamic_weights(demand, domain)
        budget = self._budget(demand, domain)
        plan = self._architect_plan(intent, domain, demand, budget)
        signature = self._signature(query)
        return CognitiveFrame(query, subject, domain, demand, weights, budget, plan, signature)

    def _demand(self, query: str, intent: Intent, ctx: ContextResolution, domain: DomainVector) -> CognitiveDemand:
        scores = [float(v) for v in (intent.scores or {}).values() if isinstance(v, (int, float))]
        max_score = max(scores, default=.5)
        classifier_uncertainty = clamp01(1.0 - max_score)
        clause_count = len(re.findall(r"[，,；;：:]|以及|而且|但是|如果|並且|與|和", query))
        symbol_count = len(re.findall(r"[=<>+\-*/^%{}\[\]()∑∫√→⇒⇔]", query))
        goal_complexity = clamp01(.18*min(4, clause_count) + .08*min(6, symbol_count) + .015*min(40, len(tokens(query))))
        freshness = 1.0 if intent.requires_current else (.85 if re.search(r"(現在|目前|最新|今天|最近|即時|現任)", query) else .15)
        verification = clamp01(.25 + .45*float(intent.requires_facts) + .20*float(intent.requires_web) + .15*domain.math + .15*domain.code)
        novelty = self._novelty(query)
        domain_shift = self._domain_shift(query)
        personal_need = clamp01(.75*ctx.continuity + .35*float(bool(re.search(r"(我|我的|之前|剛剛|上次|我們)", query))))
        multi_hop = clamp01(.22*len(re.findall(r"(關係|影響|因果|為什麼|如何|經過|導致|因此|之間|比較)", query)) + .30*goal_complexity)
        contradiction = .65 if re.search(r"(矛盾|衝突|不同說法|爭議|到底哪個|誰對|真假)", query) else .05
        uncertainty = clamp01(.55*classifier_uncertainty + .22*novelty + .13*domain_shift + .10*goal_complexity)
        return CognitiveDemand(uncertainty, novelty, freshness, verification, contradiction, domain_shift, goal_complexity, personal_need, multi_hop)

    # dynamic 5D field
    def _dynamic_weights(self, d: CognitiveDemand, domain: DomainVector) -> FiveDWeights:
        semantic = 1.15 + .80*d.novelty + .35*d.domain_shift + .25*domain.science + .25*domain.math
        temporal = .45 + 1.55*d.freshness
        relational = .70 + 1.00*d.multi_hop + .45*d.goal_complexity + .25*domain.planning
        personal = .12 + 1.30*d.personal_need
        epistemic = .90 + 1.15*d.verification + 1.00*d.contradiction + .55*d.uncertainty
        vals = self._softmax((semantic, temporal, relational, personal, epistemic))
        return FiveDWeights(*vals)

    def _budget(self, d: CognitiveDemand, domain: DomainVector) -> CognitiveBudget:
        pressure = d.pressure
        p = self._sigmoid(6.0 * (pressure - .48))
        memory_k = self._lerp_int(16, 128, p)
        active_k = self._lerp_int(8, 40, p)
        active_tokens = self._lerp_int(5000, 24000, p)
        web_queries = self._lerp_int(1, 6, p) if (d.freshness > .55 or d.uncertainty > .45) else 0
        hypotheses = self._lerp_int(2, 8, p)
        beam = self._lerp_int(4, 32, p)
        hops = self._lerp_int(1, 4, max(p, d.multi_hop))
        steps = self._lerp_int(4, 18, max(p, d.goal_complexity))
        if domain.math > .65:
            beam = max(beam, 16); hypotheses = max(hypotheses, 4)
        if domain.code > .65:
            steps = max(steps, 8)
        return CognitiveBudget(memory_k, active_k, active_tokens, web_queries, hypotheses, beam, hops, steps)

    # A4 Access: 5D evidence competition
    def select_evidence(self, frame: CognitiveFrame, evidence: Sequence[Evidence]) -> tuple[list[Evidence], list[EvidenceScore5D]]:
        if not evidence:
            return [], []
        base_scores = [self._score_evidence(frame, e, selected=()) for e in evidence]
        by_id = {e.evidence_id: e for e in evidence}
        selected: list[Evidence] = []
        remaining = set(by_id)
        used_tokens = 0
        while remaining and len(selected) < frame.budget.active_evidence_k:
            best_id = None; best_value = -1e9; best_score = None
            for eid in remaining:
                e = by_id[eid]
                rescored = self._score_evidence(frame, e, selected=selected)
                cost_tokens = max(1, len(clean(e.content)) // 3)
                if selected and used_tokens + cost_tokens > frame.budget.active_token_budget:
                    continue
                value = rescored.final_score - .00002*cost_tokens
                if value > best_value:
                    best_id, best_value, best_score = eid, value, rescored
            if best_id is None:
                break
            chosen = by_id[best_id]
            if selected and best_score is not None and best_score.final_score < .12:
                break
            selected.append(chosen)
            used_tokens += max(1, len(clean(chosen.content)) // 3)
            remaining.remove(best_id)
        return selected, base_scores

    def _score_evidence(self, frame: CognitiveFrame, evidence: Evidence, *, selected: Sequence[Evidence]) -> EvidenceScore5D:
        query_t = tokens(frame.query); content_t = tokens(evidence.content)
        semantic = max(float(evidence.relevance), jaccard(query_t, content_t))
        temporal = clamp01(float(getattr(evidence, "freshness", 1.0)))
        subject_tokens = tokens(frame.subject)
        relational = max(float(getattr(evidence, "entity_match", 0.0)), jaccard(subject_tokens, content_t) if subject_tokens else 0.0)
        personal = clamp01(frame.demand.personal_need * (1.0 if evidence.origin in {"memory", "5d9a", "atlas", "long-document"} else .45))
        epistemic = clamp01(float(evidence.confidence) * (.55 + .45*float(evidence.trust)))
        directness = self._directness(evidence.origin)
        coverage = self._coverage(query_t, content_t)
        hygiene = self._hygiene_multiplier(frame, evidence)
        redundancy = max((jaccard(content_t, tokens(old.content)) for old in selected), default=0.0)
        conflict = self._local_conflict_penalty(evidence, selected)
        w = frame.weights
        positive = w.semantic*semantic + w.temporal*temporal + w.relational*relational + w.personal*personal + w.epistemic*epistemic + .08*directness + .08*coverage
        score = clamp01(hygiene*positive - .18*redundancy - .20*conflict)
        return EvidenceScore5D(evidence.evidence_id, score, semantic, temporal, relational, personal, epistemic, directness, coverage, redundancy, conflict, hygiene)

    # Global memory-field sketch. ATLAS may precompute the same aggregate per shard/global field.
    def field_state(self, frame: CognitiveFrame, evidence: Sequence[Evidence]) -> tuple[float, ...]:
        qphi = self._feature_map(frame.query)
        if not evidence:
            return tuple(0.0 for _ in range(5))
        numerator = [0.0]*5; denom = 1e-9
        for e in evidence:
            kphi = self._feature_map(e.content)
            kernel = max(0.0, sum(a*b for a,b in zip(qphi,kphi)))
            vals = (
                max(float(e.relevance), jaccard(tokens(frame.query), tokens(e.content))),
                clamp01(float(getattr(e,"freshness",1.0))),
                clamp01(float(getattr(e,"entity_match",0.0))),
                frame.demand.personal_need if e.origin in {"memory","5d9a","atlas"} else .0,
                clamp01(float(e.confidence)*float(e.trust)),
            )
            denom += kernel
            for i,value in enumerate(vals): numerator[i] += kernel*value
        return tuple(clamp01(x/denom) for x in numerator)

    # A5 Assemble: contradiction graph + competing hypotheses
    def contradiction_entropy(self, evidence: Sequence[Evidence]) -> float:
        if len(evidence)<2:return 0.0
        contradictory_pairs=0; comparable_pairs=0
        for i,a in enumerate(evidence):
            ta=tokens(a.content)
            for b in evidence[i+1:]:
                sim=jaccard(ta,tokens(b.content))
                if sim<.12:continue
                comparable_pairs += 1
                if self._opposite_stance(a.content,b.content):contradictory_pairs += 1
        if comparable_pairs==0:return 0.0
        p=contradictory_pairs/comparable_pairs
        if p<=0.0 or p>=1.0:return p
        return clamp01(-(p*math.log2(p)+(1-p)*math.log2(1-p)))

    def hypotheses(self, frame: CognitiveFrame, evidence: Sequence[Evidence]) -> list[Hypothesis]:
        if not evidence:return []
        clusters: list[list[Evidence]]=[]
        for e in evidence:
            et=tokens(e.content);best=None;best_sim=0.0
            for i,cluster in enumerate(clusters):
                sim=jaccard(et,tokens(cluster[0].content))
                if sim>best_sim:best,best_sim=i,sim
            if best is not None and best_sim>=.22:clusters[best].append(e)
            else:clusters.append([e])
        out=[]
        for cluster in clusters[:frame.budget.hypothesis_width]:
            support=self._independent_support(cluster)
            contradiction=self._cluster_contradiction(cluster,evidence)
            prior=.50
            logit=self._logit(prior)+2.6*support-2.8*contradiction
            posterior=self._sigmoid(logit)
            representative=max(cluster,key=lambda e:e.confidence*max(.1,e.relevance))
            claim=self._compact_claim(representative.content)
            out.append(Hypothesis(stable_id("hyp",frame.query_signature,claim),claim,prior,support,contradiction,posterior,tuple(e.evidence_id for e in cluster)))
        return sorted(out,key=lambda h:h.posterior,reverse=True)

    # A6 Architect: diversity-aware cognitive skill plan
    def _architect_plan(self, intent: Intent, domain: DomainVector, demand: CognitiveDemand, budget: CognitiveBudget) -> CognitivePlan:
        candidates=[]
        for action in self.DEFAULT_ACTIONS:
            if not self._action_applicable(action,intent,domain):continue
            stats=self._skill_state(action)
            goal_gain,verify_gain,info_gain=self._action_gains(action,intent,domain,demand)
            score=.27*goal_gain+.20*verify_gain+.18*info_gain+.16*stats.success+.09*stats.transfer-.06*stats.cost-.04*stats.risk
            candidates.append(PlanStep(action,score,goal_gain,verify_gain,stats.cost,stats.risk,self._rationale(action,demand,domain)))
        selected=[];used_families=set()
        for step in sorted(candidates,key=lambda s:s.score,reverse=True):
            family=self._action_family(step.action);penalty=.08 if family in used_families else 0.0;adjusted=step.score-penalty
            if adjusted<.10:continue
            selected.append(PlanStep(step.action,adjusted,step.expected_gain,step.expected_verification_gain,step.cost,step.risk,step.rationale));used_families.add(family)
            if len(selected)>=min(7,budget.plan_beam_width):break
        expected_success=1.0;cost=0.0
        for step in selected:
            p=clamp01(.35+.65*self._skill_state(step.action).success);expected_success*=p;cost+=step.cost
        if selected:expected_success=expected_success**(1.0/len(selected))
        return CognitivePlan(tuple(selected),expected_success,cost,demand.pressure)

    def should_search_web(self, frame: CognitiveFrame, evidence: Sequence[Evidence]) -> bool:
        if frame.demand.freshness>=.75:return True
        if not evidence and frame.domain.factual+frame.domain.science>.45:return True
        strength=max((e.confidence*e.trust*max(.1,e.relevance) for e in evidence),default=0.0)
        contradiction=self.contradiction_entropy(evidence)
        trigger=.38*frame.demand.uncertainty+.24*frame.demand.novelty+.22*(1.0-strength)+.16*contradiction
        return trigger>=.48 and frame.budget.web_query_budget>0

    def should_use_native_reasoner(self, frame: CognitiveFrame, *, evidence_count: int, fact_count: int) -> bool:
        compositional=max(frame.demand.goal_complexity,frame.demand.multi_hop)
        if frame.domain.math>.55 or frame.domain.code>.55 or frame.domain.planning>.55:return True
        if fact_count==0 and evidence_count>0:return True
        return compositional>=.42

    # A8 Audit
    def audit(self, frame: CognitiveFrame, *, evidence: Sequence[Evidence], facts: Sequence[Fact], truth_grounding: float, truth_accepted: bool, latency_seconds: float = 0.0) -> AuditResult:
        coverage=self._answer_coverage(frame,evidence,facts)
        epistemic=self._epistemic_quality(evidence)
        contradiction=self.contradiction_entropy(evidence)
        diversity=self._evidence_diversity(evidence)
        efficiency=1.0/(1.0+max(0.0,latency_seconds)/8.0+len(evidence)/80.0)
        grounding=clamp01(truth_grounding)
        total=grounding**.28*max(.05,coverage)**.18*max(.05,epistemic)**.20*max(.05,diversity)**.10*max(.05,1.0-contradiction)**.14*max(.05,efficiency)**.10
        should_commit=bool(truth_accepted and total>=.66 and grounding>=.70)
        should_escalate=bool(total<.52 and frame.demand.pressure>=.45)
        return AuditResult(grounding,coverage,epistemic,diversity,contradiction,efficiency,total,should_commit,should_escalate)

    # A9 Adapt
    def adapt(self, frame: CognitiveFrame, audit: AuditResult, *, successful_actions: Iterable[str] = (), failed_actions: Iterable[str] = ()) -> None:
        self.ledger.recent_queries.append(frame.query)
        for action in successful_actions:
            stat=self.ledger.skill_stats.setdefault(action,{"alpha":2.0,"beta":2.0,"transfer":.5,"cost":.3,"risk":.2});stat["alpha"]=float(stat.get("alpha",2.0))+1.0
        for action in failed_actions:
            stat=self.ledger.skill_stats.setdefault(action,{"alpha":2.0,"beta":2.0,"transfer":.5,"cost":.3,"risk":.2});stat["beta"]=float(stat.get("beta",2.0))+1.0
        self.ledger.outcomes.append({"time":time.time(),"signature":frame.query_signature,"domain":frame.domain.dominant(),"pressure":frame.demand.pressure,"quality":audit.total_quality,"grounding":audit.grounding,"coverage":audit.coverage,"epistemic":audit.epistemic_quality,"contradiction":audit.contradiction})
        self._save()

    def status(self) -> dict:
        return {"name":"5D9A-OMEGA","dimensions":("semantic","temporal","relational","personal","epistemic"),"cycle":("Acquire","Abstract","Assess","Access","Assemble","Architect","Act","Audit","Adapt"),"field_dims":self.field_dims,"recent_queries":len(self.ledger.recent_queries),"learned_skill_stats":len(self.ledger.skill_stats),"outcomes":len(self.ledger.outcomes)}

    # helpers
    def _domain_vector(self, query: str, intent: Intent) -> DomainVector:
        q=query.casefold()
        def hit(pattern:str)->float:return min(1.0,.28*len(re.findall(pattern,q,re.I)))
        math_v=hit(r"(證明|方程|矩陣|行列式|模|質數|積分|微分|機率|幾何|函數|定理|\d+\s*[+*/^%-])")
        code_v=hit(r"(python|程式|code|演算法|cache|trie|tree|sort|dp|api|class|function|函式|debug|外掛)")
        science_v=hit(r"(量子|物理|化學|生物|宇宙|epr|糾纏|相對論|細胞|原子|分子|實驗)")
        self_v=hit(r"(christine|5d9a|prism|atlas|nova|orbit|你的架構|你自己|self-map|truth gate)")
        social_v=hit(r"(threads|instagram|facebook|帳號|這個人|@)")
        planning_v=hit(r"(計畫|規劃|步驟|怎麼做|策略|設計|架構|最佳化|優化)")
        creative_v=hit(r"(小說|故事|角色|創作|畫|設計圖|世界觀)")
        factual_v=clamp01(.35+.45*float(intent.requires_facts)+.20*hit(r"(是誰|是什麼|什麼意思|解釋|介紹)"))
        return DomainVector(factual_v,science_v,math_v,code_v,self_v,social_v,planning_v,creative_v)

    def _novelty(self, query: str) -> float:
        if not self.ledger.recent_queries:return .70
        qt=tokens(query);similarity=max((jaccard(qt,tokens(old)) for old in self.ledger.recent_queries),default=0.0)
        return clamp01(1.0-similarity)

    def _domain_shift(self, query: str) -> float:
        recent=list(self.ledger.recent_queries)[-12:]
        if not recent:return .60
        sim=sum(jaccard(tokens(query),tokens(x)) for x in recent)/len(recent)
        return clamp01(1.0-sim)

    def _skill_state(self, action: str) -> SkillState:
        raw=self.ledger.skill_stats.get(action) or {}
        return SkillState(action,float(raw.get("alpha",2.0)),float(raw.get("beta",2.0)),float(raw.get("transfer",.5)),float(raw.get("cost",self._default_cost(action))),float(raw.get("risk",self._default_risk(action))))

    def _action_applicable(self, action: str, intent: Intent, domain: DomainVector) -> bool:
        if action=="search_web":return bool(intent.requires_web or intent.requires_current or domain.factual>.45 or domain.science>.35)
        if action=="generate_code":return domain.code>.45 or intent.output_kind=="code"
        if action=="symbolic_reason":return domain.math>.35
        if action=="self_map":return domain.self_knowledge>.35
        if action=="ask_clarification":return bool(intent.missing_slots)
        if action=="native_reason":return domain.math+domain.code+domain.planning+domain.science>.40
        return True

    def _action_gains(self, action: str, intent: Intent, domain: DomainVector, d: CognitiveDemand) -> tuple[float,float,float]:
        goal=.45;verify=.25;info=.35
        if action in {"retrieve_memory","retrieve_longdoc","search_web"}:info=clamp01(.45+.45*d.uncertainty+.25*d.novelty);goal=clamp01(.40+.30*float(intent.requires_facts))
        if action=="verify":verify=clamp01(.70+.30*d.verification);goal=.35
        if action=="compare_sources":verify=clamp01(.55+.40*d.contradiction);info=.55
        if action=="decompose_question":goal=clamp01(.50+.45*d.goal_complexity);info=.50
        if action=="build_hypotheses":goal=clamp01(.45+.35*d.multi_hop);info=clamp01(.45+.30*d.uncertainty)
        if action=="symbolic_reason":goal=clamp01(.55+.40*domain.math);verify=.65
        if action=="generate_code":goal=clamp01(.55+.40*domain.code);verify=.50
        if action=="self_map":goal=clamp01(.55+.40*domain.self_knowledge);verify=.85
        return goal,verify,info

    @staticmethod
    def _action_family(action:str)->str:
        if action.startswith("retrieve") or action=="search_web":return "retrieve"
        if action in {"verify","compare_sources"}:return "verify"
        if action in {"symbolic_reason","native_reason","build_hypotheses"}:return "reason"
        if action=="generate_code":return "create"
        if action in {"resolve_entities","decompose_question","build_fact_graph"}:return "structure"
        return action

    @staticmethod
    def _default_cost(action:str)->float:
        return {"retrieve_memory":.10,"retrieve_longdoc":.18,"search_web":.55,"resolve_entities":.16,"decompose_question":.18,"compare_sources":.24,"build_fact_graph":.20,"build_hypotheses":.28,"symbolic_reason":.35,"native_reason":.42,"generate_code":.45,"verify":.22,"ask_clarification":.08,"self_map":.12}.get(action,.25)

    @staticmethod
    def _default_risk(action:str)->float:
        return {"search_web":.22,"native_reason":.38,"generate_code":.34,"symbolic_reason":.16,"verify":.06,"self_map":.04}.get(action,.12)

    @staticmethod
    def _rationale(action:str,d:CognitiveDemand,domain:DomainVector)->str:
        if action=="search_web":return f"freshness={d.freshness:.2f}, uncertainty={d.uncertainty:.2f}"
        if action=="decompose_question":return f"goal_complexity={d.goal_complexity:.2f}"
        if action=="compare_sources":return f"contradiction={d.contradiction:.2f}, verification={d.verification:.2f}"
        if action=="symbolic_reason":return f"math={domain.math:.2f}"
        if action=="generate_code":return f"code={domain.code:.2f}"
        return f"pressure={d.pressure:.2f}"

    @staticmethod
    def _directness(origin:str)->float:
        return {"self-map":1.0,"direct-url":.92,"wikipedia":.80,"web-page":.82,"search-snippet":.48,"memory":.72,"5d9a":.74,"atlas":.78,"long-document":.88}.get(origin,.55)

    @staticmethod
    def _coverage(query_t:set[str],content_t:set[str])->float:
        if not query_t:return .5
        return clamp01(len(query_t&content_t)/max(1,len(query_t)))

    @staticmethod
    def _hygiene_multiplier(frame:CognitiveFrame,evidence:Evidence)->float:
        text=evidence.content.casefold();code_like=bool(re.search(r"\b(def|class|import|return|traceback)\b|\.py:\d+|if .*:",text));internal=bool(re.search(r"(g3 v|argus|nova|_ood_gate|expected shard token|christine_g3)",text))
        if (code_like or internal) and frame.domain.code<.30 and frame.domain.self_knowledge<.35:return .08
        return 1.0

    @staticmethod
    def _local_conflict_penalty(e:Evidence,selected:Sequence[Evidence])->float:
        penalty=0.0
        for old in selected:
            sim=jaccard(tokens(e.content),tokens(old.content))
            if sim>=.15 and OMEGA5D9A._opposite_stance(e.content,old.content):penalty=max(penalty,sim)
        return clamp01(penalty)

    @staticmethod
    def _opposite_stance(a:str,b:str)->bool:
        neg=r"(不是|並非|沒有|未|不會|錯誤|否認|false|not )"
        return bool(re.search(neg,a,re.I))!=bool(re.search(neg,b,re.I))

    def _independent_support(self,cluster:Sequence[Evidence])->float:
        groups={}
        for e in cluster:
            group=e.independent_group or e.source or e.evidence_id;groups[group]=max(groups.get(group,0.0),clamp01(e.confidence*e.trust))
        p_not=1.0
        for score in sorted(groups.values(),reverse=True)[:6]:p_not*=1.0-.80*score
        return clamp01(1.0-p_not)

    def _cluster_contradiction(self,cluster:Sequence[Evidence],all_evidence:Sequence[Evidence])->float:
        rep=cluster[0].content;penalties=[]
        for e in all_evidence:
            sim=jaccard(tokens(rep),tokens(e.content))
            if sim>=.15 and self._opposite_stance(rep,e.content):penalties.append(sim*e.confidence*e.trust)
        return clamp01(max(penalties,default=0.0))

    @staticmethod
    def _compact_claim(text:str)->str:
        text=clean(text);sentence=re.split(r"(?<=[。！？.!?])\s+",text)[0];return sentence[:240]

    @staticmethod
    def _answer_coverage(frame:CognitiveFrame,evidence:Sequence[Evidence],facts:Sequence[Fact])->float:
        qt=tokens(frame.query);material=set()
        for e in evidence:material|=tokens(e.content)
        for f in facts:material|=tokens(f"{f.subject} {f.predicate} {f.value}")
        return OMEGA5D9A._coverage(qt,material)

    @staticmethod
    def _epistemic_quality(evidence:Sequence[Evidence])->float:
        if not evidence:return 0.0
        groups={}
        for e in evidence:
            group=e.independent_group or e.source or e.evidence_id;groups[group]=max(groups.get(group,0.0),e.confidence*e.trust)
        vals=sorted(groups.values(),reverse=True)[:5]
        return clamp01(sum(vals)/len(vals)) if vals else 0.0

    @staticmethod
    def _evidence_diversity(evidence:Sequence[Evidence])->float:
        if len(evidence)<=1:return 1.0 if evidence else 0.0
        sims=[]
        for i,a in enumerate(evidence):
            for b in evidence[i+1:]:sims.append(jaccard(tokens(a.content),tokens(b.content)))
        return clamp01(1.0-sum(sims)/len(sims)) if sims else 1.0

    def _feature_map(self,text:str)->tuple[float,...]:
        vec=[0.0]*self.field_dims
        for term in tokens(text):
            digest=hashlib.blake2b(term.encode("utf-8","replace"),digest_size=8).digest();h=int.from_bytes(digest,"big");idx=h%self.field_dims;vec[idx]+=1.0 if ((h>>9)&1) else -1.0
        norm=math.sqrt(sum(x*x for x in vec)) or 1.0
        return tuple((x/norm+1.0)/2.0 for x in vec)

    @staticmethod
    def _signature(query:str)->str:return hashlib.blake2b(clean(query).casefold().encode("utf-8","replace"),digest_size=12).hexdigest()
    @staticmethod
    def _softmax(vals:Sequence[float])->tuple[float,...]:
        m=max(vals);exps=[math.exp(v-m) for v in vals];total=sum(exps) or 1.0;return tuple(x/total for x in exps)
    @staticmethod
    def _sigmoid(x:float)->float:
        if x>=0:z=math.exp(-x);return 1.0/(1.0+z)
        z=math.exp(x);return z/(1.0+z)
    @staticmethod
    def _logit(p:float)->float:p=min(.999999,max(.000001,p));return math.log(p/(1.0-p))
    @staticmethod
    def _lerp_int(lo:int,hi:int,t:float)->int:return int(round(lo+(hi-lo)*clamp01(t)))

    def _save(self)->None:
        if self.state_path is None:return
        try:
            self.state_path.parent.mkdir(parents=True,exist_ok=True);payload={"recent_queries":list(self.ledger.recent_queries),"skill_stats":self.ledger.skill_stats,"outcomes":list(self.ledger.outcomes)};tmp=self.state_path.with_suffix(".tmp");tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(self.state_path)
        except Exception:pass

    def _load(self)->None:
        if self.state_path is None or not self.state_path.exists():return
        try:
            raw=json.loads(self.state_path.read_text(encoding="utf-8"));self.ledger.recent_queries.extend(str(x) for x in raw.get("recent_queries",[])[-128:]);self.ledger.skill_stats.update(raw.get("skill_stats",{}));self.ledger.outcomes.extend(x for x in raw.get("outcomes",[])[-256:] if isinstance(x,dict))
        except Exception:self.ledger=OMEGALedger()
