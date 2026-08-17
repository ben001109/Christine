from __future__ import annotations
import ast,re
from dataclasses import dataclass
from pathlib import Path
from .contracts import Evidence
from .utils import clean,jaccard,stable_id,tokens
@dataclass(frozen=True)
class SelfNode:
    kind:str; name:str; module:str; doc:str; imports:tuple[str,...]
class SelfMap:
    SELF_TERMS=('christine','你自己','你的架構','你的系統','你的功能','5d9a','prism','atlas','nova','orbit','truth gate','truth-gate','memory hygiene','self-map','unifiedkernel','nativegenerator','factgraph','logos','logos-m9','cedar','mosaic','mosaic-q')
    def __init__(self,package_dir=None):self.package_dir=Path(package_dir) if package_dir else Path(__file__).resolve().parent;self.nodes=[];self.parse_errors=[];self.refresh()
    def refresh(self):
        self.nodes.clear();self.parse_errors.clear()
        for path in sorted(self.package_dir.glob('*.py')):
            if path.name.startswith('__'):continue
            try:source=path.read_text(encoding='utf-8');tree=ast.parse(source)
            except Exception as exc:self.parse_errors.append(f'{path.name}:{type(exc).__name__}');continue
            module=path.stem;imports=[]
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
                elif isinstance(n,ast.ImportFrom) and n.module:imports.append(n.module)
            self.nodes.append(SelfNode('module',module,module,clean(ast.get_docstring(tree) or ''),tuple(dict.fromkeys(imports))))
            for n in tree.body:
                if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    self.nodes.append(SelfNode('class' if isinstance(n,ast.ClassDef) else 'function',n.name,module,clean(ast.get_docstring(n) or ''),tuple(dict.fromkeys(imports))))
    def status(self):return {'modules':sum(n.kind=='module' for n in self.nodes),'classes':sum(n.kind=='class' for n in self.nodes),'functions':sum(n.kind=='function' for n in self.nodes),'parse_errors':tuple(self.parse_errors)}
    def is_self_query(self,q):q=clean(q).casefold();return any(t in q for t in self.SELF_TERMS)
    def retrieve(self,query,limit=12):
        qt=tokens(query);sc=[]
        for n in self.nodes:
            text=f"{n.name} {n.module} {n.doc} {' '.join(n.imports)}";rel=jaccard(qt,tokens(text))
            if n.name.casefold() in query.casefold() or n.module.casefold() in query.casefold():rel=max(rel,.95)
            if rel<=0:continue
            content=self._sentence(n);sc.append((rel,Evidence(stable_id('self-map',n.module,n.kind,n.name),content,f'self-code://christine_g3v2/{n.module}.py',rel,.99,trust=1.0,entity_match=rel,independent_group=f'self-code:{n.module}',origin='self-map')))
        sc.sort(key=lambda x:x[0],reverse=True);return [e for _,e in sc[:limit]]
    def describe(self,query):
        ev=self.retrieve(query,10);s=self.status();q=query.casefold()
        if not ev and any(x in q for x in ('你自己','你的架構','你的系統','你的功能','christine')):
            preferred={'UnifiedKernel','Memory138','ResearchEngine','FactGraph','PRISMPlanner','NoveltyGate','TruthGate','SelfMap','LOGOSM9','CEDAR','MOSAICQ'}
            chosen=[n for n in self.nodes if n.name in preferred][:10]
            ev=[Evidence(stable_id('self-map',n.module,n.kind,n.name),self._sentence(n),f'self-code://christine_g3v2/{n.module}.py',.90,.99,trust=1.0,entity_match=.90,independent_group=f'self-code:{n.module}',origin='self-map') for n in chosen]
        if any(x in q for x in ('prism','atlas','5d9a','nova','orbit','hygiene','truth','logos','cedar','mosaic')):
            label=next((x for x in ('PRISM','ATLAS/5D9A','NOVA','ORBIT','Memory Hygiene','Truth Gate','LOGOS-M9','CEDAR','MOSAIC-Q') if x.split('/')[0].casefold() in q or (x=='ATLAS/5D9A' and '5d9a' in q)), '架構模組')
            if not ev:return f'我在目前原始碼中沒有找到足夠資訊來可靠描述 {label}。',ev
            return f'依照我目前實際載入的原始碼，{label} 可以整理為：'+'；'.join(clean(e.content) for e in ev[:4])+'。',ev
        core=self._names(('UnifiedKernel','Memory138','ResearchEngine','FactGraph','PRISMPlanner','NoveltyGate','TruthGate','SelfMap','LOGOSM9','CEDAR','MOSAICQ'))
        ans=f"我是 Christine G3 的目前執行核心。我的架構由意圖辨識、上下文、5D9A 記憶／長文／網路取證、事實圖譜、回答規劃、驗證與防重複等模組協作。我剛剛直接掃描目前的 christine_g3v2 原始碼，辨識到 {s['modules']} 個模組、{s['classes']} 個 class、{s['functions']} 個頂層 function。"
        if core:ans+=' 目前可直接確認的核心符號包括：'+'、'.join(core)+'。'
        return ans,ev
    def _names(self,p):a={n.name for n in self.nodes};return [x for x in p if x in a]
    @staticmethod
    def _sentence(n):
        base=f'{n.name} 是 christine_g3v2/{n.module}.py 中的 {n.kind}'
        if n.doc:return base+f'，其原始碼說明為：{n.doc[:220]}'
        if n.imports:return base+'，此模組直接連結：'+'、'.join(n.imports[:8])
        return base+'。'
