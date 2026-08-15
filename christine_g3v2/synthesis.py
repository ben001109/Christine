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
        if not facts:
            return (f'我已針對 {subject or "這個社群帳號"} 做直接頁面與定向搜尋，但目前公開可讀資訊不足以可靠確認真實姓名或主要活動。我不會拿無關搜尋結果硬湊成答案。' if social else f'我有針對「{subject or "這個問題"}」做記憶與公開資料查找，但目前還沒有足夠一致的證據可以可靠下結論。')
        by=defaultdict(list)
        for f in facts:by[f.category].append(f)
        p=[]
        if social:
            lead=f'這個帳號是 {subject}。';
            if by['display_name']:lead+=f' 公開頁面顯示它使用的名稱是「{by["display_name"][0].value}」。'
            p.append(lead)
        else:
            identity=by['identity']
            if identity:p.append(f'綜合目前較可靠的資料，{subject}可概括為{re.sub(r"^(?:一位|一名|一個)","",identity[0].value)}。')
            elif by['position']:p.append(f'目前能確認的資訊主要集中在{subject}的公開職務與經歷。')
        if by['position']:
            vals=list(dict.fromkeys(x.value for x in by['position']))[:3];p.append('公開經歷中，'+'；另外'.join(vals)+'。')
        if by['feature']:
            vals=list(dict.fromkeys(x.value for x in by['feature']))[:3];p.append('功能／特點方面，資料主要提到'+'、'.join(vals)+'。')
        domains=tuple(dict.fromkeys(s for f in facts for s in f.sources)); conf=packet.confidence if packet else max(f.confidence for f in facts)
        if conf<.72 or len(domains)<2:p.append('目前獨立來源仍不算多，所以我會保留部分不確定性，而不是把零碎資訊說成已確認事實。')
        elif conf<.86:p.append('幾個來源的核心方向一致，但部分細節仍只出現在單一來源。')
        if domains:p.append('這次主要交叉參考：'+'、'.join(domains[:6])+'。')
        return '\n\n'.join(p)
