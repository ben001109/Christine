from __future__ import annotations
import json,re,time
from collections import deque
from dataclasses import asdict,dataclass
from pathlib import Path
from .contracts import ContextResolution,Intent
from .lexer_intent import split_urls
from .utils import clean,jaccard,tokens

@dataclass
class Episode:
    raw:str; intent_kind:str; topic:str; entities:tuple[str,...]; urls:tuple[str,...]; output_kind:str; timestamp:float

class ContextGraph:
    REFERENCES=re.compile(r"(這個人|這個|那個|那支|他|她|它|剛剛|前面|上一個|那呢|還有|再)",re.I)
    def __init__(self,state_path:Path|None=Path('data/g3v2_context.json'),maxlen:int=32):
        self.state_path=state_path; self.rows=deque(maxlen=maxlen); self._load()
    def resolve(self,raw:str,intent:Intent)->ContextResolution:
        topic=self._topic(raw,intent)
        if not self.rows: return ContextResolution(topic,0.0)
        prev=self.rows[-1]; reference=1.0 if self.REFERENCES.search(raw) else 0.0
        lexical=jaccard(tokens(topic),tokens(prev.topic)); entity=jaccard(set(intent.entities),set(prev.entities)) if (intent.entities or prev.entities) else 0.0
        url_ref=1.0 if reference and prev.urls else 0.0; continuity=min(1.0,.30*lexical+.25*entity+.28*reference+.17*url_ref)
        ie=(); iu=()
        if continuity>=.34:
            ie=tuple(x for x in prev.entities if x not in intent.entities); iu=tuple(x for x in prev.urls if x not in intent.urls)
            if reference: topic=f"{prev.topic}；目前追問：{topic}" if topic else prev.topic
        return ContextResolution(topic or prev.topic,continuity,ie,iu)
    def commit(self,raw,intent,ctx):
        self.rows.append(Episode(raw,intent.kind,ctx.topic,tuple(dict.fromkeys(intent.entities+ctx.inherited_entities)),tuple(dict.fromkeys(intent.urls+ctx.inherited_urls)),intent.output_kind,time.time())); self._save()
    @staticmethod
    def _topic(raw,intent):
        _,res=split_urls(raw); text=re.sub(r"(去)?(?:threads|instagram|facebook|github|reddit|youtube|網路|網上|上網)(?:上)?(?:查|搜尋)?"," ",res,flags=re.I); text=re.sub(r"(幫我查|查一下|查查|搜尋|搜索|看一下)"," ",text); text=clean(text)
        if re.fullmatch(r"(這個人|這人|他|她|它)?\s*(是誰|在幹嘛|做什麼|幹嘛|是什麼)?",text): text=""
        return text or (" ".join(intent.entities) if intent.entities else "")
    def _save(self):
        if self.state_path is None:return
        try:
            self.state_path.parent.mkdir(parents=True,exist_ok=True); tmp=self.state_path.with_suffix('.tmp'); tmp.write_text(json.dumps([asdict(x) for x in self.rows],ensure_ascii=False),encoding='utf-8'); tmp.replace(self.state_path)
        except Exception: pass
    def _load(self):
        if self.state_path is None or not self.state_path.exists():return
        try:
            for x in json.loads(self.state_path.read_text(encoding='utf-8'))[-self.rows.maxlen:]: self.rows.append(Episode(str(x.get('raw','')),str(x.get('intent_kind','conversation')),str(x.get('topic','')),tuple(x.get('entities',())),tuple(x.get('urls',())),str(x.get('output_kind','text')),float(x.get('timestamp',time.time()))))
        except Exception:self.rows.clear()
