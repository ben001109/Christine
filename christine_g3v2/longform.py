from __future__ import annotations
import re
from dataclasses import dataclass
from .contracts import Evidence
from .utils import clean,jaccard,stable_id,tokens
@dataclass
class Block: block_id:str;doc_id:str;section:str;text:str;token_estimate:int
class LongFormStore:
    def __init__(self,chunk_chars=5000):self.chunk_chars=chunk_chars;self.blocks=[]
    def ingest(self,doc_id,text):
        count=0
        for section,body in self._sections(text):
            for i in range(0,len(body),self.chunk_chars):
                chunk=body[i:i+self.chunk_chars].strip()
                if not chunk:continue
                self.blocks.append(Block(stable_id(doc_id,section,str(i),chunk),doc_id,section,chunk,max(1,len(chunk)//3)));count+=1
        return count
    def retrieve(self,query,token_budget=16000,max_blocks=32):
        q=tokens(query); scored=[]
        for b in self.blocks:
            rel=max(jaccard(q,tokens(b.section)),jaccard(q,tokens(b.text)))
            if rel>0:scored.append((rel,b))
        scored.sort(reverse=True,key=lambda x:x[0]);selected=[];used=0
        for rel,b in scored[:max_blocks]:
            if used+b.token_estimate>token_budget:continue
            redundancy=max((jaccard(tokens(b.text),tokens(e.content)) for e in selected),default=0)
            if .82*rel-.18*redundancy<=0:continue
            selected.append(Evidence(b.block_id,b.text,f'document:{b.doc_id}#{b.section}',rel,.90,trust=.95,independent_group=b.doc_id,origin='long-document'));used+=b.token_estimate
        return selected
    @staticmethod
    def _sections(text):
        lines=text.splitlines();out=[];section='root';buf=[]
        for line in lines:
            m=re.match(r'^(#{1,6})\s+(.+)$',line.strip())
            if m:
                if buf:out.append((section,'\n'.join(buf)));buf=[]
                section=m.group(2).strip()
            else:buf.append(line)
        if buf:out.append((section,'\n'.join(buf)))
        return out or [('root',text)]
