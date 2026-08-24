from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .contracts import ContextResolution, Evidence, Intent, ResearchPacket
from .utils import clean, clamp01, host, jaccard, prob_union, tokens


@dataclass(frozen=True)
class QueryGraph:
    raw: str
    entities: tuple[str, ...]
    concepts: tuple[str, ...]
    relations: tuple[str, ...]
    goal_type: str
    subquestions: tuple[str, ...]
    queries: tuple[str, ...]
    complexity: float


@dataclass(frozen=True)
class MosaicReport:
    queries_issued: int
    evidence_before_merge: int
    evidence_after_merge: int
    independent_sources: int
    coverage: float


class MOSAICQ:
    """Multi-object scientific/analytical query decomposition before ORBIT retrieval."""

    RELATIONS={
        'relationship':r'(關係|之間|如何連結|有何關聯|relationship|relation)',
        'cause':r'(為什麼|原因|導致|造成|因果|cause|why)',
        'mechanism':r'(機制|原理|如何運作|怎麼運作|mechanism|how does)',
        'compare':r'(比較|差別|不同|相同|versus|\bvs\.?\b|difference)',
        'history':r'(歷史|提出|發展|起源|誰提出|history|origin)',
        'evidence':r'(證據|實驗|驗證|觀測|evidence|experiment)',
        'definition':r'(是什麼|是啥|定義|意思|define|what is)',
    }
    SUFFIX=('理論','效應','定律','原理','模型','粒子','量子','佯謬','悖論','方程','演算法','系統','協定','結構','機制','現象','實驗','方法','定理')

    def should_decompose(self,query,*,science_score=0.0,complexity=0.0):
        q=clean(query);rels=self._relations(q);clauses=len(re.findall(r'[，,；;：:]|以及|與|和|但是|而|為什麼|如何|關係',q))
        return science_score>=.42 or complexity>=.35 or bool(rels) or clauses>=2 or len(q)>=38

    def decompose(self,query,*,explicit_entities=()):
        raw=clean(query);entities=list(dict.fromkeys(clean(x) for x in explicit_entities if clean(x)))
        entities += [x for x in self._quoted(raw) if x not in entities]
        entities += [x for x in self._latin(raw) if x not in entities]
        concepts=[x for x in self._zh(raw) if x not in entities];rels=self._relations(raw);goal=self._goal(rels)
        if not entities:entities.extend(concepts[:3])
        else:
            for c in concepts[:2]:
                if c not in entities:entities.append(c)
        entities=list(dict.fromkeys(entities))[:6];concepts=list(dict.fromkeys(concepts))[:10]
        sub=self._subquestions(entities,rels,goal);queries=self._queries(raw,entities,concepts,goal,sub)
        complexity=clamp01(.10*min(6,len(entities))+.08*min(8,len(concepts))+.16*min(4,len(rels))+.08*min(5,len(sub)))
        return QueryGraph(raw,tuple(entities),tuple(concepts),tuple(rels),goal,tuple(sub),tuple(queries),complexity)

    def research(self,*,intent:Intent,ctx:ContextResolution,engine,query_budget:int=4):
        graph=self.decompose(intent.goal or ctx.topic,explicit_entities=intent.entities+ctx.inherited_entities)
        chosen=list(graph.queries[:max(1,query_budget)]);all_ev=[];confs=[];all_queries=[]
        for q in chosen:
            child=replace(intent,goal=q,entities=tuple(graph.entities[:4]),requires_facts=True,requires_web=True)
            child_ctx=ContextResolution(q,ctx.continuity,ctx.inherited_entities,ctx.inherited_urls)
            packet=engine.research(child,child_ctx);all_ev.extend(packet.evidence);confs.append(packet.confidence);all_queries.extend(packet.queries)
        before=len(all_ev);merged=self._merge(graph,all_ev);sources={e.independent_group or host(e.source) or e.source for e in merged if e.source};coverage=self._coverage(graph,merged)
        conf=clamp01(.65*prob_union(confs)+.35*coverage)
        return ResearchPacket(tuple(merged[:64]),conf,tuple(dict.fromkeys(all_queries or chosen)),'mosaic'),graph,MosaicReport(len(chosen),before,len(merged),len(sources),coverage)

    def _queries(self,raw,entities,concepts,goal,subs):
        q=[]
        if len(entities)>=2:q.append('"'+'" "'.join(entities[:3])+'"')
        for e in entities[:3]:q.append(f'"{e}" {goal}')
        q.extend(subs[:3])
        if len(concepts)>=2:q.append(f'"{concepts[0]}" "{concepts[1]}"')
        q.append(raw)
        return list(dict.fromkeys(clean(x) for x in q if clean(x)))[:8]

    @staticmethod
    def _subquestions(entities,rels,goal):
        e1=entities[0] if entities else '核心概念';e2=entities[1] if len(entities)>1 else '相關概念';out=[]
        if 'definition' in rels or goal=='definition':out.append(f'{e1} 的精確定義與必要背景')
        if 'relationship' in rels or (len(entities)>=2 and goal=='relationship'):
            out += [f'{e1} 與 {e2} 的直接關係',f'{e1} 與 {e2} 關係的理論或實驗依據']
        if 'cause' in rels:out.append(f'造成 {e1} 的主要原因與因果鏈')
        if 'mechanism' in rels:out.append(f'{e1} 的機制與步驟')
        if 'compare' in rels:out.append(f'{e1} 與 {e2} 的共同點與差異')
        if 'history' in rels:out.append(f'{e1} 的提出背景與時間線')
        if 'evidence' in rels:out.append(f'支持或反駁 {e1} 的關鍵證據')
        if not out:
            out.append(f'{e1} 的核心定義')
            if len(entities)>1:out.append(f'{e1} 與 {e2} 的關係')
        return list(dict.fromkeys(out))[:5]

    @classmethod
    def _relations(cls,text):return [name for name,p in cls.RELATIONS.items() if re.search(p,text,re.I)]
    @staticmethod
    def _goal(rels):
        for x in ('relationship','cause','mechanism','compare','history','evidence','definition'):
            if x in rels:return x
        return 'explain'
    @staticmethod
    def _quoted(text):return [clean(x) for x in re.findall(r'[「『\"\']([^」』\"\']{2,60})[」』\"\']',text)]
    @staticmethod
    def _latin(text):
        out=re.findall(r'\b[A-Z][A-Z0-9-]{1,15}\b',text)+re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b',text)+re.findall(r'\b[A-Za-z]+(?:-[A-Za-z0-9]+)+\b',text)
        return list(dict.fromkeys(out))
    @classmethod
    def _zh(cls,text):
        out=[]
        for suffix in cls.SUFFIX:
            for m in re.finditer(rf'[\u3400-\u9fff]{{1,10}}{suffix}',text):
                v=re.sub(r'^(?:什麼|怎麼|如何|為什麼|解釋|說明|提出|關於)','',m.group(0))
                if 2<=len(v)<=14:out.append(v)
        out+=re.findall(r'([\u3400-\u9fff]{2,8})(?=提出|發現|認為|的(?:理論|定律|方程|模型))',text)
        return list(dict.fromkeys(clean(x) for x in out if clean(x)))

    def _merge(self,graph,evidence):
        out=[];seen=set();gt=tokens(' '.join(graph.entities+graph.concepts+graph.relations))
        for e in sorted(evidence,key=lambda x:x.confidence*(.45+.55*x.relevance),reverse=True):
            key=(host(e.source),re.sub(r'\W+','',clean(e.content).casefold())[:300])
            if key in seen:continue
            seen.add(key);ct=tokens(e.content);ec=max((jaccard(tokens(ent),ct) for ent in graph.entities),default=0);gc=jaccard(gt,ct)
            if graph.entities and ec<.05 and gc<.05:continue
            if any(jaccard(ct,tokens(old.content))>=.86 for old in out):continue
            out.append(e)
        return out

    @staticmethod
    def _coverage(graph,evidence):
        if not evidence:return 0.0
        target=list(graph.entities)+list(graph.concepts[:4])
        if not target:return .5
        corpus=tokens(' '.join(e.content for e in evidence));return sum(jaccard(tokens(x),corpus)>0 for x in target)/len(target)
