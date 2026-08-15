from __future__ import annotations
import json,os
from pathlib import Path
from .contracts import Evidence,TOKEN_CAPACITY_5D9A
from .utils import clean,hierarchy_counts,jaccard,stable_id,tokens

class Memory138:
    def __init__(self):
        self.capacity_tokens=int(os.environ.get('CHRISTINE_5D9A_TOKEN_CAPACITY',str(TOKEN_CAPACITY_5D9A))); self.hierarchy=hierarchy_counts(self.capacity_tokens); self.rows=self._load_rows(); self.verified_path=Path('data/g3v2_verified_facts.jsonl')
    def status(self): return {'capacity_tokens':self.capacity_tokens,'leaf_tokens':1024,'leaf_count':self.hierarchy[0],'levels':self.hierarchy,'loaded_records':len(self.rows)}
    def retrieve(self,query,limit=16):
        q=tokens(query); scored=[]
        for idx,row in enumerate(self.rows):
            content=clean(str(row.get('content') or row.get('content_summary') or row.get('summary') or row.get('value') or ''))
            if not content: continue
            rel=jaccard(q,tokens(content))
            if rel<=0: continue
            conf=float(row.get('confidence',.70) or .70); src=str(row.get('source') or '5d9a-local')
            scored.append((rel*conf,Evidence(stable_id('5d9a',str(idx),content),content,src,rel,conf,trust=.72,entity_match=rel,independent_group=src,origin='memory')))
        scored.sort(key=lambda x:x[0],reverse=True); return [e for _,e in scored[:limit]]
    def remember_verified(self,facts):
        try:
            self.verified_path.parent.mkdir(parents=True,exist_ok=True)
            with self.verified_path.open('a',encoding='utf-8') as fh:
                for fact in facts:
                    if float(fact.get('confidence',0))>=.86: fh.write(json.dumps(fact,ensure_ascii=False)+'\n')
        except Exception: pass
    @staticmethod
    def _load_rows():
        rows=[]
        for path in (Path('data/christine_v42/permanent_folder_memory.json'),Path('data/permanent_folder_memory.json'),Path('data/g3v2_verified_facts.jsonl')):
            if not path.exists(): continue
            try:
                if path.suffix=='.jsonl': rows.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()); continue
                data=json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data,list): rows.extend(x for x in data if isinstance(x,dict))
                elif isinstance(data,dict): rows.extend(({"key":k,**v} if isinstance(v,dict) else {"key":k,"content":str(v)}) for k,v in data.items())
            except Exception: continue
        return rows
