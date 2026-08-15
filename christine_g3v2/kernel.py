from __future__ import annotations
import ast,os,re
from pathlib import Path
from .capabilities import Clarifier,NativeGeneratorAdapter
from .context import ContextGraph
from .contracts import TurnState
from .dialogue import NativeDialogue
from .lexer_intent import IntentKernel
from .longform import LongFormStore
from .memory138 import Memory138
from .research import ResearchEngine
from .synthesis import FactGraph
from .prism import PRISMPlanner,PRISMNarrator
from .utils import clean
from .verify_nova import NoveltyGate,Verifier

class UnifiedKernel:
    """G3 v2.1 single state machine with PRISM multi-view factual synthesis."""
    def __init__(self,*,context=None,memory=None,research=None,documents=None,generator=None,novelty=None):
        self.intent_kernel=IntentKernel();self.context=context or ContextGraph();self.memory=memory or Memory138();self.research=research or ResearchEngine();self.documents=documents or LongFormStore();self.generator=generator or NativeGeneratorAdapter();self.facts=FactGraph();self.prism=PRISMPlanner();self.narrator=PRISMNarrator();self.dialogue=NativeDialogue();self.clarifier=Clarifier();self.verifier=Verifier();self.novelty=novelty or NoveltyGate()
    def ask(self,raw):
        raw=clean(raw);turn=TurnState(raw);intent=self.intent_kernel.analyze(raw);turn.intent=intent;turn.trace.append(f'intent:{intent.kind}');ctx=self.context.resolve(raw,intent);turn.context=ctx;turn.trace.append(f'context:{ctx.continuity:.2f}')
        if intent.kind=='compute':ans=self._calculate(intent.goal);self.context.commit(raw,intent,ctx);return ans,turn
        if intent.kind=='clarify':ans=self.clarifier.respond(intent);turn.trace.append('clarify');self.context.commit(raw,intent,ctx);return ans,turn
        if intent.kind in {'support','conversation'}:ans=self.dialogue.respond(raw,intent,ctx);turn.trace.append('dialogue:native');self.context.commit(raw,intent,ctx);return ans,turn
        if intent.kind in {'answer','research','inspect_url'}:ans=self._factual(turn);self.context.commit(raw,intent,ctx);return ans,turn
        if intent.kind=='create_code':ans=self._code(turn);self.context.commit(raw,intent,ctx);return ans,turn
        if intent.kind=='create_image':ans=self._image(turn);self.context.commit(raw,intent,ctx);return ans,turn
        ans='我理解到這是一個任務，但目前還沒有對應的可靠執行路徑。';self.context.commit(raw,intent,ctx);return ans,turn
    def _factual(self,turn):
        intent,ctx=turn.intent,turn.context;mem=self.memory.retrieve(ctx.topic,16);turn.evidence.extend(mem);turn.trace.append(f'memory:{len(mem)}/138B');docs=self.documents.retrieve(ctx.topic,token_budget=12000);turn.evidence.extend(docs);turn.trace.append(f'longdoc:{len(docs)}') if docs else None
        strength=max((e.confidence*max(.15,e.relevance) for e in mem+docs),default=0);packet=None;should=intent.requires_web or intent.kind in {'research','inspect_url'} or (intent.requires_facts and strength<.60)
        if should:packet=self.research.research(intent,ctx);turn.evidence.extend(packet.evidence);turn.trace.append(f'orbit:{len(packet.evidence)}:{packet.confidence:.2f}')
        subject=self._subject(intent,ctx);facts=self.facts.extract(subject,turn.evidence);turn.facts=facts;turn.trace.append(f'facts:{len(facts)}');plan=self.prism.plan(question=intent.goal or ctx.topic,subject=subject,facts=facts,packet=packet,token_budget=1200);turn.trace.append(f'prism:{plan.mode}:{len(plan.facets)}:cov={plan.coverage_score:.2f}:div={plan.diversity_score:.2f}');answer=self.narrator.narrate(subject=subject,question=intent.goal or ctx.topic,plan=plan,packet=packet)
        v=self.verifier.verify_text(answer);turn.trace.append(f'verify:{v.reason}')
        if not v.accepted:return '我這輪有取得資料，但整理結果沒有通過輸出驗證，所以先不輸出可能損壞的內容。'
        n=self.novelty.accept(intent.goal or ctx.topic,'text',answer);turn.trace.append(f'nova:{n.reason}')
        if not n.accepted:return '這一輪查到的可靠核心資訊和前面相同，沒有新的獨立證據值得重複一遍。'
        self.memory.remember_verified([{'content':f'{f.subject} {f.predicate} {f.value}','source':','.join(f.sources),'confidence':f.confidence} for f in facts if f.confidence>=.86]);return answer
    def _code(self,turn):
        intent,ctx=turn.intent,turn.context;artifact=self.generator.code(intent.goal,{'topic':ctx.topic,'entities':intent.entities+ctx.inherited_entities,'memory':self.memory.retrieve(ctx.topic,8)})
        if artifact is None:return '這是一個具體程式任務，但目前沒有接上 Christine 自己的 NativeGenerator。v2.1 不會再用 quicksort 或固定模板冒充完成；把你的原生生成器提供成 `christine_native_generator.generate_code(goal, context)` 後，這條路會直接使用它。'
        turn.artifact=artifact;v=self.verifier.verify_artifact(artifact);turn.trace.append(f'verify:{v.reason}')
        if not v.accepted:return 'Christine 原生生成器有輸出程式碼，但沒有通過語法／artifact 驗證，所以我沒有顯示它。'
        n=self.novelty.accept(intent.goal or ctx.topic,'code',artifact.content);turn.trace.append(f'nova:{n.reason}')
        if not n.accepted:return '原生生成器這次產出的程式和先前版本在內容或 AST 結構上高度重複，因此 NOVA 已阻止重貼。'
        return artifact.content
    def _image(self,turn):
        intent,ctx=turn.intent,turn.context;artifact=self.generator.image(intent.goal,{'topic':ctx.topic})
        if artifact is None:return '我已確認這是圖片生成任務，但目前沒有接上 Christine 自己的 Native Image Generator。v2.1 不會用一句「已生成」假裝完成。'
        turn.artifact=artifact;v=self.verifier.verify_artifact(artifact);turn.trace.append(f'verify:{v.reason}');return artifact.path if v.accepted else '圖片生成器有回傳結果，但 artifact 驗證失敗。'
    @staticmethod
    def _subject(intent,ctx):
        entities=tuple(dict.fromkeys(intent.entities+ctx.inherited_entities))
        if entities:return entities[0]
        m=re.search(r'([^\s，。？！?：:]{2,30})\s*是誰',ctx.topic);return m.group(1) if m else ctx.topic[:60]
    @staticmethod
    def _calculate(text):
        m=re.search(r'([0-9().+\-*/% ]{3,})',text)
        if not m:return '我沒有解析到可安全計算的算式。'
        expr=m.group(1).strip()
        try:tree=ast.parse(expr,mode='eval')
        except SyntaxError:return '算式語法無法解析。'
        allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.FloorDiv,ast.Mod,ast.Pow,ast.UAdd,ast.USub,ast.Load)
        if any(not isinstance(n,allowed) for n in ast.walk(tree)):return '這個算式包含不允許的運算。'
        try:value=eval(compile(tree,'<calc>','eval'),{'__builtins__':{}},{})
        except Exception:return '計算失敗。'
        return f'{expr} = {value}'
    def ingest_file(self,path):
        p=Path(path).expanduser()
        if not p.exists() or not p.is_file():return f'找不到檔案：{p}'
        try:text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:text=p.read_text(encoding='utf-8-sig')
            except Exception:return '目前 /ingest 只直接支援可讀取的文字檔。'
        return f'已匯入 {p.name}，建立 {self.documents.ingest(p.name,text)} 個長文區塊。'
