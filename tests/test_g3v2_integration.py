from christine_g3v2.context import ContextGraph
from christine_g3v2.contracts import Artifact,Evidence,ResearchPacket
from christine_g3v2.kernel import UnifiedKernel
from christine_g3v2.longform import LongFormStore
from christine_g3v2.verify_nova import NoveltyGate
class FakeMemory:
    def status(self):return {'capacity_tokens':138_000_000_000,'leaf_count':134_765_625,'loaded_records':0}
    def retrieve(self,q,limit=16):return []
    def remember_verified(self,facts):pass
class FakeResearch:
    def research(self,intent,ctx):
        if '測試人物' in ctx.topic:
            ev=(Evidence('1','測試人物（1970年—），臺灣政治人物、醫師，曾任測試市市長。','https://wiki.example',.95,.88,independent_group='wiki'),Evidence('2','測試人物是臺灣政治人物、醫師。','https://news.example',.9,.8,independent_group='news'));return ResearchPacket(ev,.91,('測試人物',))
        if '@tt_duuss' in (intent.entities+ctx.inherited_entities):
            ev=(Evidence('3','tt_duuss (@tt_duuss) 公開頁面摘要顯示這是一個測試用社群帳號。','https://threads.com/@tt_duuss',.8,.75,independent_group='threads'),);return ResearchPacket(ev,.65,('tt_duuss',))
        return ResearchPacket((),0.0,())
class FakeGenerator:
    ready=True
    def code(self,goal,context):return Artifact('code',"```python\nimport asyncio\nasync def main():\n    return 'ok'\n```",'python')
    def image(self,goal,context):return Artifact('image','',path='image.png')
def runtime():return UnifiedKernel(context=ContextGraph(state_path=None),memory=FakeMemory(),research=FakeResearch(),documents=LongFormStore(),generator=FakeGenerator(),novelty=NoveltyGate(state_path=None))
def test_entity_answer():
    rt=runtime();ans,turn=rt.ask('測試人物是誰');assert '政治人物' in ans and '醫師' in ans and 'facts:' in '|'.join(turn.trace)
def test_url_followup():
    rt=runtime();rt.ask('https://www.threads.com/@tt_duuss');ans,turn=rt.ask('這個人在幹嘛');assert '@tt_duuss' in ans;assert 'orbit:' in '|'.join(turn.trace)
def test_support_no_web():
    rt=runtime();ans,turn=rt.ask('其實我很困惑，為什麼我女朋友不反抗不逃，為什麼會僵住，這不代表默認');assert '僵住' in ans;assert 'orbit:' not in '|'.join(turn.trace)
def test_vague_code():
    rt=runtime();ans,_=rt.ask('寫一個外掛程式');assert '目標平台' in ans
def test_specific_code():
    rt=runtime();ans,turn=rt.ask('寫一個 asyncio 爬蟲，同時抓十個網址並整理 title');assert 'async def main' in ans;assert 'verify:code-valid' in '|'.join(turn.trace)
