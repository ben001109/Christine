from christine_g3v2.context import ContextGraph
from christine_g3v2.contracts import Artifact,Evidence,ResearchPacket
from christine_g3v2.lexer_intent import IntentKernel,split_urls
from christine_g3v2.longform import LongFormStore
from christine_g3v2.memory138 import Memory138
from christine_g3v2.synthesis import FactGraph,NativeNarrator
from christine_g3v2.verify_nova import NoveltyGate,Verifier

def test_url_suffix_not_swallowed():
    urls,res=split_urls('https://www.threads.com/@tt_duuss看一下這人是誰');assert urls==('https://www.threads.com/@tt_duuss',);assert res=='看一下這人是誰'
def test_url_research_handle_once():
    i=IntentKernel().analyze('https://www.threads.com/@tt_duuss看一下這人是誰');assert i.kind=='research';assert i.entities==('@tt_duuss',);assert i.source_hint=='threads'
def test_support_precedes_fact():assert IntentKernel().analyze('其實我也有同樣的困惑，為什麼我女朋友不反抗不逃，為什麼會僵住，但其實完全不是默認').kind=='support'
def test_donation_conversation():assert IntentKernel().analyze('可以幫我@錫蘭嗎，我都想斗內十萬塊了').kind=='conversation'
def test_vague_plugin_clarify():
    i=IntentKernel().analyze('寫一個外掛程式');assert i.kind=='clarify';assert 'purpose' in i.missing_slots and 'target_platform' in i.missing_slots
def test_vague_python_clarify():assert IntentKernel().analyze('寫一個超難的 python 腳本').kind=='clarify'
def test_concrete_code():assert IntentKernel().analyze('寫一個 asyncio 爬蟲，同時抓十個網址並整理 title').kind=='create_code'
def test_math():assert IntentKernel().analyze('1+1110124214是多少').kind=='compute'
def test_context_url_followup():
    k=IntentKernel();c=ContextGraph(state_path=None);a=k.analyze('https://www.threads.com/@tt_duuss');ca=c.resolve(a.goal,a);c.commit(a.goal,a,ca);b=k.analyze('這個人在幹嘛');cb=c.resolve('這個人在幹嘛',b);assert b.kind=='answer';assert cb.inherited_urls
def test_fact_graph_person():
    e1=Evidence('1','測試人物（1970年—），臺灣政治人物、醫師，曾任測試市市長。','https://wiki.example',.95,.88,independent_group='wiki');e2=Evidence('2','測試人物是臺灣政治人物、醫師，曾任測試市市長。','https://news.example',.9,.8,independent_group='news');facts=FactGraph().extract('測試人物',[e1,e2]);text=NativeNarrator().narrate(subject='測試人物',facts=facts,packet=ResearchPacket((e1,e2),.9,('x',)));assert '臺灣政治人物' in text and '醫師' in text and '測試市市長' in text
def test_longform_budget():
    s=LongFormStore(chunk_chars=120);s.ingest('d','# Intro\n'+'Python data analysis '*100);hits=s.retrieve('Python',token_budget=100);assert sum(max(1,len(e.content)//3) for e in hits)<=100
def test_138b():
    m=Memory138();assert m.capacity_tokens==138_000_000_000;assert m.hierarchy[0]==134_765_625;assert m.hierarchy[-1]==1
def test_code_verify():
    v=Verifier();assert v.verify_artifact(Artifact('code',"```python\nprint('hi')\n```",'python')).accepted;assert not v.verify_artifact(Artifact('code','```python\ndef x(\n```','python')).accepted
def test_nova_repeat():
    n=NoveltyGate(state_path=None);assert n.accept('task','text','hello world').accepted;assert not n.accept('task','text','hello world').accepted

def test_v2_kernel_has_no_v1_runtime_imports():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'christine_g3v2'
    text = '\n'.join(p.read_text(encoding='utf-8') for p in root.glob('*.py'))
    assert 'christine_g3_v1' not in text
    assert 'christine_g3_frontier' not in text
