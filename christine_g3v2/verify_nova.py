from __future__ import annotations
import ast,difflib,hashlib,json,re,time
from collections import deque
from dataclasses import asdict,dataclass
from pathlib import Path
from .contracts import Artifact,Verification
from .utils import jaccard,semantic_normalize,tokens

def extract_code(text):
    m=re.search(r'```(?:python|py)?\s*(.*?)```',str(text or ''),re.S|re.I);return m.group(1).strip() if m else str(text or '').strip()
class Verifier:
    def verify_text(self,text):
        text=str(text or '').strip()
        if not text:return Verification(False,0,'empty-output')
        if '\x00' in text or '\ufffd' in text:return Verification(False,0,'invalid-unicode')
        return Verification(True,1,'text-valid')
    def verify_artifact(self,a):
        if a.kind=='code':
            code=extract_code(a.content)
            if not code:return Verification(False,0,'empty-code')
            if a.language in {'python','py'}:
                try:ast.parse(code)
                except SyntaxError as e:return Verification(False,.05,f'python-syntax:{e.msg}')
            return Verification(True,1,'code-valid')
        if a.kind=='image':return Verification(bool(a.path),1 if a.path else 0,'image-path')
        return Verification(False,0,'unknown-artifact')
@dataclass
class NoveltyRow:task:str;kind:str;answer:str;exact:str;ast_shape:str;timestamp:float
class NoveltyGate:
    def __init__(self,state_path=Path('data/g3v2_novelty.json'),maxlen=128):self.state_path=state_path;self.rows=deque(maxlen=maxlen);self._load()
    def accept(self,task,kind,answer):
        exact=hashlib.blake2b(semantic_normalize(answer).encode(),digest_size=16).hexdigest();shape=self._ast_shape(extract_code(answer)) if kind=='code' else '';best=0
        for old in reversed(self.rows):
            if old.kind!=kind or jaccard(tokens(old.task),tokens(task))<.70:continue
            if old.exact==exact:best=1;break
            if kind=='code' and shape and old.ast_shape:best=max(best,difflib.SequenceMatcher(None,shape,old.ast_shape).ratio())
            else:
                a,b=semantic_normalize(answer),semantic_normalize(old.answer);best=max(best,.55*difflib.SequenceMatcher(None,a,b).ratio()+.45*jaccard(tokens(a),tokens(b)))
        threshold=.76 if kind=='code' else .86
        if best>=threshold:return Verification(False,1-best,f'repeat:{best:.2f}')
        self.rows.append(NoveltyRow(task,kind,answer[:24000],exact,shape[:32000],time.time()));self._save();return Verification(True,1-best,f'novel:{best:.2f}')
    @staticmethod
    def _ast_shape(code):
        try:tree=ast.parse(code)
        except SyntaxError:return ''
        class N(ast.NodeTransformer):
            def visit_Name(self,n):return ast.copy_location(ast.Name(id='_V',ctx=n.ctx),n)
            def visit_arg(self,n):return ast.copy_location(ast.arg(arg='_A'),n)
            def visit_FunctionDef(self,n):n.name='_F';self.generic_visit(n);return n
            def visit_Constant(self,n):
                if isinstance(n.value,str):return ast.copy_location(ast.Constant('_S'),n)
                if isinstance(n.value,(int,float,complex)):return ast.copy_location(ast.Constant(0),n)
                return n
        tree=N().visit(tree);ast.fix_missing_locations(tree);return ast.dump(tree,annotate_fields=False,include_attributes=False)
    def _save(self):
        if self.state_path is None:return
        try:self.state_path.parent.mkdir(parents=True,exist_ok=True);tmp=self.state_path.with_suffix('.tmp');tmp.write_text(json.dumps([asdict(x) for x in self.rows],ensure_ascii=False),encoding='utf-8');tmp.replace(self.state_path)
        except Exception:pass
    def _load(self):
        if self.state_path is None or not self.state_path.exists():return
        try:
            for x in json.loads(self.state_path.read_text(encoding='utf-8'))[-self.rows.maxlen:]:self.rows.append(NoveltyRow(str(x['task']),str(x['kind']),str(x['answer']),str(x['exact']),str(x.get('ast_shape','')),float(x.get('timestamp',0))))
        except Exception:self.rows.clear()
