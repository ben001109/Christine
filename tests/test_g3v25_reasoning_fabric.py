from christine_g3v2.context import ContextGraph
from christine_g3v2.contracts import Artifact,Evidence,ResearchPacket
from christine_g3v2.kernel_v25 import UnifiedKernel
from christine_g3v2.lexer_intent import IntentKernel
from christine_g3v2.logos_m9 import LOGOSM9
from christine_g3v2.mosaic_q import MOSAICQ
from christine_g3v2.verify_nova import NoveltyGate


def test_spec_gate_lru_is_direct_code():
    i=IntentKernel().analyze('用 Python 實作 LRU Cache，get/put 要 O(1)');assert i.kind=='create_code';assert not i.missing_slots

def test_spec_gate_trie_is_direct_code():assert IntentKernel().analyze('實作 Trie 資料結構').kind=='create_code'
def test_vague_python_still_clarifies():assert IntentKernel().analyze('寫一個超難的 python 腳本').kind=='clarify'
def test_logos_modpow():r=LOGOSM9().solve('計算 7^222 mod 13');assert r.success and r.verified and '= 12' in r.answer
def test_logos_determinant():r=LOGOSM9().solve('求行列式 det [[1,2],[3,4]]');assert r.success and r.verified and '-2' in r.answer
def test_logos_quadratic():r=LOGOSM9().solve('解方程 x^2-5x+6=0');assert r.success and r.verified and '2' in r.answer and '3' in r.answer
def test_logos_inverse():r=LOGOSM9().solve('求 3 在 mod 11 的逆元');assert r.success and r.verified and '4' in r.answer
def test_logos_fermat():r=LOGOSM9().solve('解釋費馬小定理');assert r.success and r.verified and 'a^(p-1)' in r.answer

def test_mosaic_epr():
    g=MOSAICQ().decompose('量子糾纏與愛因斯坦提出的 EPR 佯謬有什麼關係？');assert 'EPR' in g.entities;assert 'relationship' in g.relations;assert len(g.queries)>=2


class FakeMemory:
    def status(self):return {'capacity_tokens':138_000_000_000,'leaf_count':134_765_625,'indexed_tokens':0,'address_coverage':0,'loaded_records':0,'resident_sparse_tokens_estimate':0}
    def retrieve(self,q,limit=16):return []
    def note_active(self,e):pass
    def remember_verified(self,f):pass
class FakeResearch:
    def __init__(self):self.calls=[]
    def research(self,intent,ctx):
        self.calls.append(intent.goal);e=Evidence('e'+str(len(self.calls)),f'{intent.goal} 的測試證據，說明兩個概念之間存在理論關係。','https://science.example/'+str(len(self.calls)),.8,.8,trust=.8,independent_group='s'+str(len(self.calls)));return ResearchPacket((e,),.75,(intent.goal,))
class FakeGenerator:
    ready=True
    def code(self,goal,context):return Artifact('code',"```python\nclass Trie:\n    def __init__(self): self.root={}\n    def insert(self, word):\n        node=self.root\n        for ch in word: node=node.setdefault(ch,{})\n        node['#']={}\n```",'python')
    def image(self,goal,context):return None
    def reason(self,goal,context):return None

def runtime():return UnifiedKernel(context=ContextGraph(state_path=None),memory=FakeMemory(),research=FakeResearch(),generator=FakeGenerator(),novelty=NoveltyGate(state_path=None))

def test_kernel_math_uses_logos_without_web():
    rt=runtime();answer,turn=rt.ask('計算 7^222 mod 13');assert '= 12' in answer;assert 'logos:' in '|'.join(turn.trace);assert len(rt._research_base.calls)==0

def test_kernel_science_uses_mosaic():
    rt=runtime();answer,turn=rt.ask('量子糾纏與愛因斯坦提出的 EPR 佯謬有什麼關係？');assert 'mosaic:' in '|'.join(turn.trace);assert len(rt._research_base.calls)>=2

def test_kernel_code_uses_cedar():
    rt=runtime();answer,turn=rt.ask('用 Python 實作 Trie 資料結構');assert 'class Trie' in answer;assert 'cedar:' in '|'.join(turn.trace)
