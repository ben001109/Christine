from __future__ import annotations
import json,os
from pathlib import Path
from .contracts import Evidence,TOKEN_CAPACITY_5D9A
from .utils import clean,hierarchy_counts,jaccard,stable_id,tokens

class Memory138:
    """Sparse runtime bridge with truthful capacity/index/activity accounting."""
    def __init__(self):
        self.capacity_tokens=int(os.environ.get('CHRISTINE_5D9A_TOKEN_CAPACITY',str(TOKEN_CAPACITY_5D9A)))
        self.hierarchy=hierarchy_counts(self.capacity_tokens)
        self.rows=self._load_rows()
        self.verified_path=Path('data/g3v2_verified_facts.jsonl')
        self.atlas_root=Path(os.environ.get('CHRISTINE_5D9A_ATLAS_ROOT','data/5d9a_138b'))
        self._last_active_leaves=0
        self._last_active_tokens=0
        self._manifest=self._latest_manifest()

    def status(self):
        local=sum(self._estimate(self._content(r)) for r in self.rows)
        indexed=int((self._manifest or {}).get('tokens_estimated',0) or 0)
        leaves=int((self._manifest or {}).get('leaves_written',0) or 0)
        field=(self._manifest or {}).get('global_field_leaves')
        field_coverage=min(1.0,float(field)/leaves) if field is not None and leaves>0 else None
        return {
            'capacity_tokens':self.capacity_tokens,
            'leaf_tokens':1024,
            'leaf_count':self.hierarchy[0],
            'levels':self.hierarchy,
            'loaded_records':len(self.rows),
            'resident_sparse_tokens_estimate':local,
            'indexed_tokens':indexed,
            'indexed_leaves':leaves,
            'address_coverage':indexed/self.capacity_tokens if self.capacity_tokens else 0.0,
            'global_field_coverage':field_coverage,
            'active_memory_leaves':self._last_active_leaves,
            'active_memory_tokens_estimate':self._last_active_tokens,
            'atlas_snapshot':(self._manifest or {}).get('_snapshot_path',''),
        }

    def retrieve(self,query,limit=16):
        q=tokens(query);scored=[]
        for idx,row in enumerate(self.rows):
            content=self._content(row)
            if not content:continue
            rel=jaccard(q,tokens(content))
            if rel<=0:continue
            conf=float(row.get('confidence',.70) or .70)
            src=str(row.get('source') or '5d9a-local')
            scored.append((rel*conf,Evidence(stable_id('5d9a',str(idx),content),content,src,rel,conf,trust=.72,entity_match=rel,independent_group=src,origin='memory')))
        scored.sort(key=lambda x:x[0],reverse=True)
        results=[e for _,e in scored[:limit]]
        self.note_active(results)
        return results

    def note_active(self,evidence):
        memory_evidence=[e for e in evidence if getattr(e,'origin','') in {'memory','5d9a','atlas'}]
        self._last_active_leaves=len(memory_evidence)
        self._last_active_tokens=sum(self._estimate(e.content) for e in memory_evidence)

    def remember_verified(self,facts):
        try:
            self.verified_path.parent.mkdir(parents=True,exist_ok=True)
            with self.verified_path.open('a',encoding='utf-8') as fh:
                for fact in facts:
                    if float(fact.get('confidence',0))>=.86:
                        fh.write(json.dumps(fact,ensure_ascii=False)+'\n')
        except Exception:pass

    def _latest_manifest(self):
        if not self.atlas_root.exists():return None
        manifests=list(self.atlas_root.glob('*/manifest.json'))
        direct=self.atlas_root/'manifest.json'
        if direct.exists():manifests.append(direct)
        parsed=[]
        for path in manifests:
            try:
                data=json.loads(path.read_text(encoding='utf-8'))
                data['_snapshot_path']=str(path.parent)
                parsed.append((float(data.get('created_at',path.stat().st_mtime)),data))
            except Exception:continue
        return sorted(parsed,key=lambda x:x[0],reverse=True)[0][1] if parsed else None

    @staticmethod
    def _estimate(text):return max(0,len(clean(text))//3)

    @staticmethod
    def _content(row):
        return clean(str(row.get('content') or row.get('content_summary') or row.get('summary') or row.get('value') or ''))

    @staticmethod
    def _load_rows():
        rows=[]
        for path in (Path('data/christine_v42/permanent_folder_memory.json'),Path('data/permanent_folder_memory.json'),Path('data/g3v2_verified_facts.jsonl')):
            if not path.exists():continue
            try:
                if path.suffix=='.jsonl':
                    rows.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip())
                    continue
                data=json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data,list):rows.extend(x for x in data if isinstance(x,dict))
                elif isinstance(data,dict):rows.extend(({"key":k,**v} if isinstance(v,dict) else {"key":k,"content":str(v)}) for k,v in data.items())
            except Exception:continue
        return rows
