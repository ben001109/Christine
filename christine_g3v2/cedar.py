from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from .contracts import Artifact
from .utils import clean, clamp01


@dataclass(frozen=True)
class TaskSpec:
    raw: str
    language: str
    objective: str
    artifact_kind: str
    named_targets: tuple[str, ...]
    constraints: tuple[str, ...]
    interfaces: tuple[str, ...]
    specificity: float
    missing_slots: tuple[str, ...]


@dataclass(frozen=True)
class CodePlan:
    spec: TaskSpec
    architecture: tuple[str, ...]
    steps: tuple[str, ...]
    acceptance: tuple[str, ...]


@dataclass(frozen=True)
class CEDARReport:
    accepted: bool
    syntax_ok: bool
    interface_coverage: float
    requirement_coverage: float
    structure_score: float
    reason: str


class CEDAR:
    """Code Execution-Driven Adaptive Reasoning; static-safe generation controller."""

    LANG = {
        "python": r"\bpython\b|\.py\b", "javascript": r"\b(?:javascript|js|node(?:\.js)?)\b",
        "typescript": r"\b(?:typescript|ts)\b", "java": r"\bjava\b",
        "cpp": r"\b(?:c\+\+|cpp)\b", "rust": r"\brust\b", "go": r"\bgolang\b|\bgo\b",
    }
    CONSTRAINT_RE = re.compile(
        r"(O\([^)]*\)|thread[- ]?safe|執行緒安全|不可使用[^，。]+|只能使用[^，。]+|"
        r"時間複雜度[^，。]+|空間複雜度[^，。]+|最多\s*\d+|至少\s*\d+|async|非同步|並行)", re.I
    )
    INTERFACE_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)|`([^`]+)`", re.I)

    def parse(self, text: str) -> TaskSpec:
        raw = clean(text); language = self._language(raw); named = self._named(raw)
        constraints = tuple(dict.fromkeys(clean(x) for x in self.CONSTRAINT_RE.findall(raw)))
        interfaces=[]
        for a,b in self.INTERFACE_RE.findall(raw):
            v=clean(a or b)
            if v and v.casefold()!='o': interfaces.append(v)
        interfaces=tuple(dict.fromkeys(interfaces))
        objective=self._objective(raw,named); kind=self._kind(raw)
        specificity=self._specificity(raw,language,objective,named,constraints,interfaces)
        missing=[]
        if specificity<.50 or not objective: missing.append('purpose')
        if re.search(r"(外掛|plugin|addon)",raw,re.I) and not re.search(r"(minecraft|chrome|firefox|discord|vscode|wordpress|unity|unreal|瀏覽器|遊戲|網站|平台)",raw,re.I): missing.append('target_platform')
        return TaskSpec(raw,language,objective,kind,named,constraints,interfaces,specificity,tuple(dict.fromkeys(missing)))

    def is_specific(self,text):
        s=self.parse(text); return s.specificity>=.50 and not s.missing_slots

    def plan(self,spec:TaskSpec)->CodePlan:
        t=' '.join(spec.named_targets).casefold(); arch=[]
        if any(x in t for x in ('cache','dictionary','hash','map')):arch.append('keyed lookup structure')
        if any(x in t for x in ('tree','trie','segment','heap')):arch.append('explicit node/container structure')
        if any(x in t for x in ('graph','bfs','dfs','dijkstra','a*')):arch.append('graph representation + search state')
        if any(x in t for x in ('dp','dynamic','memo')):arch.append('state + recurrence + cache')
        if not arch:arch.append('minimal data model aligned with requested interface')
        steps=('normalize TaskSpec','choose representation','derive invariants','native generation','static AST/interface verify','bounded repair')
        acceptance=['syntax parses','requested behavior represented']+[f'interface:{x}' for x in spec.interfaces]+[f'constraint:{x}' for x in spec.constraints]
        return CodePlan(spec,tuple(arch),steps,tuple(acceptance))

    def generate(self,*,goal:str,context:dict[str,Any],generator,max_repairs:int=2):
        spec=self.parse(goal); plan=self.plan(spec)
        if spec.missing_slots:return None,CEDARReport(False,False,0,0,0,'missing:'+','.join(spec.missing_slots)),plan
        enhanced=dict(context);enhanced['cedar']={'task_spec':spec.__dict__,'architecture':list(plan.architecture),'steps':list(plan.steps),'acceptance':list(plan.acceptance)}
        artifact=generator.code(goal,enhanced)
        if artifact is None:return None,CEDARReport(False,False,0,0,0,'generator-unavailable'),plan
        report=self.verify(artifact,spec);attempt=0
        while not report.accepted and attempt<max_repairs and hasattr(generator,'reason'):
            attempt+=1
            generator.reason(f'Repair generated code. Validation failure: {report.reason}',{'mode':'cedar_repair','previous_code':artifact.content,'validation':report.__dict__,'cedar':enhanced['cedar']})
            nxt=generator.code(goal,{**enhanced,'repair':report.__dict__,'previous_code':artifact.content})
            if nxt is None:break
            artifact=nxt;report=self.verify(artifact,spec)
        return artifact,report,plan

    def verify(self,artifact:Artifact,spec:TaskSpec)->CEDARReport:
        code=self._code(artifact.content)
        if not code:return CEDARReport(False,False,0,0,0,'empty-code')
        tree=None
        if spec.language in {'python',''}:
            try:tree=ast.parse(code)
            except SyntaxError as e:return CEDARReport(False,False,0,0,0,'python-syntax:'+e.msg)
        symbols=set()
        if tree:
            nodes=list(ast.walk(tree))
            for n in nodes:
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):symbols.add(n.name.casefold())
        else:nodes=[]
        ih=sum(1 for x in spec.interfaces if x.casefold().split('(')[0] in symbols or x.casefold() in code.casefold())
        ic=1.0 if not spec.interfaces else ih/len(spec.interfaces)
        terms=[x for x in spec.named_targets if len(x)>=2];hits=sum(1 for x in terms if x.casefold() in code.casefold())
        rc=1.0 if not terms else max(hits/len(terms),.65 if tree is not None and len(nodes)>=6 else 0.0)
        ss=clamp01(.25*bool(any(isinstance(n,ast.ClassDef) for n in nodes))+.25*bool(any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in nodes))+.20*bool(any(isinstance(n,(ast.If,ast.For,ast.While)) for n in nodes))+.15*bool(any(isinstance(n,(ast.Dict,ast.List,ast.Set,ast.Tuple)) for n in nodes))+.15*min(1,len(nodes)/80))
        ok=ic>=.80 and rc>=.60 and (tree is not None or spec.language not in {'python',''})
        return CEDARReport(ok,True,ic,rc,ss,'accepted' if ok else f'coverage:interface={ic:.2f},requirement={rc:.2f}')

    @classmethod
    def specificity_score(cls,text):return cls().parse(text).specificity
    @classmethod
    def likely_specific_code_task(cls,text):return cls().is_specific(text)

    @classmethod
    def _language(cls,text):
        for name,p in cls.LANG.items():
            if re.search(p,text,re.I):return name
        return ''

    @staticmethod
    def _named(text):
        out=[];out+=re.findall(r"\b[A-Z][A-Z0-9+_-]{1,20}\b",text);out+=re.findall(r"\b[A-Z][a-z]+(?:[A-Z][A-Za-z0-9]*)+\b",text)
        m=re.search(r"(?:實作|實現|建立|寫|開發)\s*(?:一個|一套)?\s*([^，。；;]{2,40})",text,re.I)
        if m:
            phrase=re.sub(r"^(?:用|使用)\s*(?:Python|Java|C\+\+|Rust|Go)\s*",'',clean(m.group(1)),flags=re.I)
            if phrase and phrase.casefold() not in {'程式','腳本','外掛','code','program','script','超難的 python 腳本'}:out.append(phrase)
        return tuple(dict.fromkeys(clean(x) for x in out if clean(x)))

    @staticmethod
    def _objective(text,named):
        if named:return 'implement '+', '.join(named[:4])
        r=re.sub(r"(幫我|請|寫|做|建立|生成|實作|實現|開發|用|使用|一個|一套)",' ',text,flags=re.I)
        r=re.sub(r"\b(python|javascript|typescript|java|rust|go|c\+\+)\b|程式|腳本|code|program|script",' ',r,flags=re.I);r=clean(r)
        return r if len(r)>=3 else ''

    @staticmethod
    def _kind(text):
        if re.search(r"(class|類別|資料結構)",text,re.I):return 'library/class'
        if re.search(r"(外掛|plugin|addon)",text,re.I):return 'plugin'
        if re.search(r"(api|server|伺服器)",text,re.I):return 'service'
        return 'program'

    @staticmethod
    def _specificity(text,language,objective,named,constraints,interfaces):
        action=1.0 if re.search(r"(寫|做|建立|生成|實作|實現|開發|implement|build|create)",text,re.I) else 0
        obj=clamp01(.55*bool(named)+.45*bool(objective));lang=1.0 if language else .25;con=min(1,.5*len(constraints));inter=min(1,.5*len(interfaces))
        vague=1.0 if re.fullmatch(r".*(?:超難|厲害|高級)?\s*(?:程式|腳本|外掛|code|script|program)\s*",text,re.I) else 0
        return clamp01(.22*action+.35*obj+.10*lang+.16*con+.17*inter-.25*vague)

    @staticmethod
    def _code(text):
        m=re.search(r"```(?:python|py|javascript|js|typescript|ts|java|cpp|c\+\+|c|rust|go)?\s*(.*?)```",str(text or ''),re.S|re.I)
        return m.group(1).strip() if m else str(text or '').strip()
