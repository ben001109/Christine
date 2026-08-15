from __future__ import annotations
import re
from collections import defaultdict
from .contracts import Evidence,Fact,ResearchPacket
from .utils import clean,host,jaccard,prob_union,tokens

class FactGraph:
    def extract(self,subject,evidence):
        facts=[]; label=subject.lstrip('@')
        for e in evidence:
            text=clean(e.content); src=host(e.source) or e.source; score=min(.97,e.confidence*(.60+.40*max(e.relevance,.1)))
            if label and not subject.startswith('@'):
                m=re.search(rf'{re.escape(label)}\s*[（(][^）)]{{0,120}}[）)]\s*[，,]\s*([^。]{{5,220}})',text,re.I)
                if m:
                    identity,positions=self._split(m.group(1));
                    if identity:facts.append(self._fact('identity',label,'is',identity,score,(src,),(e.evidence_id,)))
                    for p in positions:facts.append(self._fact('position',label,'role',p,score*.96,(src,),(e.evidence_id,)))
                for m in re.finditer(rf'{re.escape(label)}\s*(?:是|為|是一種|是一個)\s*([^。；;]{{4,180}})',text,re.I):
                    identity,positions=self._split(m.group(1));
                    if identity:facts.append(self._fact('identity',label,'is',identity,score,(src,),(e.evidence_id,)))
                    for p in positions:facts.append(self._fact('position',label,'role',p,score*.95,(src,),(e.evidence_id,)))
                for m in re.finditer(r'(曾任|曾擔任|現任|目前擔任|擔任)\s*([^，,；;。]{2,100})',text):
                    role=self._trim(m.group(1)+m.group(2))
                    if role:facts.append(self._fact('position',label,'role',role,score*.92,(src,),(e.evidence_id,)))
                    if m.group(1) in {'現任','目前擔任'} and role:facts.append(self._fact('status',label,'current_role',role,score*.94,(src,),(e.evidence_id,)))
                for m in re.finditer(r'(?:19|20)\d{2}年[^。]{0,110}',text):
                    val=self._trim(m.group(0))
                    if val and (label in val or re.search(r'(任|創立|成立|當選|卸任|加入|離開)',val)):
                        facts.append(self._fact('timeline',label,'event',val,score*.82,(src,),(e.evidence_id,)))
                for m in re.finditer(r'(?:推動|倡議|創辦|創立|發起|主導|帶領|促成|影響)\s*([^。；;]{4,150})',text):
                    val=self._trim(m.group(0))
                    if val:facts.append(self._fact('impact',label,'impact',val,score*.78,(src,),(e.evidence_id,)))
                for m in re.finditer(r'(?:加入|隸屬|創立|創辦)\s*([^。；;，,]{2,100}(?:黨|組織|協會|公司|團隊|基金會))',text):
                    val=self._trim(m.group(0))
                    if val:facts.append(self._fact('relationship',label,'relation',val,score*.76,(src,),(e.evidence_id,)))
                if re.search(r'(爭議|批評|質疑|不同說法|案件|起訴)',text):
                    for m in re.finditer(r'[^。]{0,70}(?:爭議|批評|質疑|不同說法|案件|起訴)[^。]{0,100}',text):
                        val=self._trim(m.group(0))
                        if val and label in val:facts.append(self._fact('controversy',label,'controversy',val,score*.70,(src,),(e.evidence_id,)))
            if subject.startswith('@'):
                handle=re.escape(subject.lstrip('@')); m=re.search(rf'([^。]{{1,80}}?)\s*\(@?{handle}\)',text,re.I)
                if m:
                    val=self._trim(m.group(1));
                    if val:facts.append(self._fact('display_name',subject,'display_name',val,score,(src,),(e.evidence_id,)))
            if label:
                for verb in ('提供','支援','包含','具有'):
                    m=re.search(rf'(?:{re.escape(label)}.{{0,30}})?{verb}\s*([^。；;]{{4,150}})',text,re.I)
                    if m:
                        val=self._trim(m.group(1));
                        if val:facts.append(self._fact('feature',label,verb,val,score*.82,(src,),(e.evidence_id,)))
        return self._merge(facts)
    def _merge(self,facts):
        merged=[]
        for f in facts:
            target=None;best=0
            for i,o in enumerate(merged):
                if o.category!=f.category or o.subject!=f.subject:continue
                sim=jaccard(tokens(o.value),tokens(f.value))
                if sim>best:best,target=sim,i
            if target is not None and best>=.42:
                o=merged[target]; independent=1.0 if set(o.sources).isdisjoint(f.sources) else .82; conf=prob_union([o.confidence,f.confidence*independent]); merged[target]=Fact(o.category,o.subject,o.predicate,min((o.value,f.value),key=len),min(.98,conf),tuple(dict.fromkeys(o.sources+f.sources)),tuple(dict.fromkeys(o.evidence_ids+f.evidence_ids)))
            else:merged.append(f)
        return sorted(merged,key=lambda x:x.confidence,reverse=True)
    @staticmethod
    def _fact(c,s,p,v,conf,sources,ids):return Fact(c,s,p,clean(v).strip('，,。')[:220],conf,sources,ids)
    @staticmethod
    def _split(text):
        text=clean(text); positions=[clean(m.group(1)+m.group(2)) for m in re.finditer(r'(曾任|曾擔任|現任|擔任)\s*([^，,；;。]{2,100})',text)]; m=re.search(r'(.+?)(?=(?:曾任|曾擔任|現任|擔任))',text); identity=m.group(1).strip('，,；; ') if m else text; return identity[:180],positions
    @staticmethod
    def _trim(text):return re.sub(r'(?i)(?:cookie|privacy policy|all rights reserved).*$', '', clean(text)).strip(' ，,；;。')[:220]

class NativeNarrator:
    def narrate(self,*,subject,facts,packet,social=False):
        if not facts:return f'我有針對「{subject or "這個問題"}」做記憶與公開資料查找，但目前還沒有足夠一致的證據可以可靠下結論。'
        by=defaultdict(list)
        for f in facts:by[f.category].append(f)
        p=[];identity=by['identity']
        if identity:p.append(f'綜合目前較可靠的資料，{subject}可概括為{re.sub(r"^(?:一位|一名|一個)","",identity[0].value)}。')
        if by['position']:p.append('公開經歷中，'+'；另外'.join(list(dict.fromkeys(x.value for x in by['position']))[:3])+'。')
        return '\n\n'.join(p)
