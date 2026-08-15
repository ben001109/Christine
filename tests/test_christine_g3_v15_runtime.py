import christine_g3_frontier as g3
import christine_g3_context_intent as v15


class FakeMemory:
    def retrieve(self, query, limit=12):
        return []


class FakeOrbit:
    def __init__(self):
        self.calls = []

    def research(self, resolution):
        self.calls.append(resolution)
        subject = " ".join(resolution.intent.entities + resolution.inherited_entities) or resolution.topic
        source = resolution.intent.urls[0] if resolution.intent.urls else (resolution.inherited_urls[0] if resolution.inherited_urls else "https://threads.com/test")
        evidence = (g3.Evidence(f"{subject} 的公開頁面顯示這是一個測試用社群帳號，近期內容主要是日常貼文。", source, 0.82, 0.76),)
        return g3.ResearchPacket(evidence, 0.82, (subject,))


class FakeSage:
    def synthesize(self, *, goal, evidence, packet, followup=False, exclude_sources=None):
        if not evidence:
            return "沒有足夠證據。", [], {"facts": 0, "sources": 0}
        return f"整理後：{goal}。目前公開資料顯示這個帳號主要發布日常內容。", list(evidence), {"facts": 1, "sources": 1}


class FakeNova:
    def __init__(self):
        self.calls = []

    def ask(self, goal):
        self.calls.append(goal)
        turn = g3.TurnEnvelope(user_input=goal)
        turn.contract = g3.TaskContract(goal=goal, operation="create", output_kind="code")
        return "```python\nprint('ok')\n```", turn


def runtime():
    return v15.ChristineG3V15Runtime(memory=FakeMemory(), web=FakeOrbit(), context=v15.ContextGraph(state_path=None), nova=FakeNova(), sage=FakeSage())


def test_url_then_person_followup_reuses_url():
    rt = runtime()
    rt.ask("https://www.threads.com/@tt_duuss")
    answer, _ = rt.ask("這個人在幹嘛")
    assert len(rt.orbit.calls) == 2
    assert rt.orbit.calls[1].inherited_urls
    assert "@tt_duuss" in " ".join(rt.orbit.calls[1].intent.entities + rt.orbit.calls[1].inherited_entities)
    assert "日常" in answer


def test_threads_explicit_lookup_calls_orbit():
    rt = runtime()
    answer, _ = rt.ask("花栗鼠🍋是誰 去threads上查")
    assert len(rt.orbit.calls) == 1
    assert rt.orbit.calls[0].intent.source_hint == "threads"
    assert "整理後" in answer


def test_donation_conversation_does_not_call_orbit():
    rt = runtime()
    answer, _ = rt.ask("可以幫我@錫蘭嗎，我都想斗內十萬塊了")
    assert len(rt.orbit.calls) == 0
    assert "十萬" in answer
    assert "感謝" in answer


def test_reflection_after_donation_stays_support_no_web():
    rt = runtime()
    rt.ask("可以幫我@錫蘭嗎，我都想斗內十萬塊了")
    answer, turn = rt.ask("那支PUA影片多少支撐著現在的我")
    assert len(rt.orbit.calls) == 0
    assert "支撐" in answer or "重新理解" in answer
    assert "orbit:" not in " | ".join(turn.trace)


def test_trauma_reflection_gets_actual_support_response():
    rt = runtime()
    answer, _ = rt.ask("其實我也有同樣的困惑，為什麼我女朋友不反抗？不逃？為什麼會僵住，甚至讓別人感覺默認，但其實完全不是這樣的")
    assert len(rt.orbit.calls) == 0
    assert "僵住" in answer
    assert "不等於" in answer or "不能把" in answer
    assert "自動防衛" in answer


def test_vague_plugin_never_calls_generator():
    rt = runtime()
    answer, _ = rt.ask("寫一個外掛程式")
    assert len(rt.nova.calls) == 0
    assert "目標平台" in answer
    assert "功能" in answer


def test_specific_crawler_calls_generator_once():
    rt = runtime()
    answer, _ = rt.ask("寫一個 asyncio 爬蟲，同時抓十個網址並整理 title")
    assert len(rt.nova.calls) == 1
    assert "print" in answer
