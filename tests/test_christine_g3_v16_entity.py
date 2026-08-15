import christine_g3_frontier as g3
import christine_g3_v16_entity as v16
import christine_g3_v16_runtime as rt16


def test_url_lexer_stops_before_cjk_suffix():
    urls, residual = v16.extract_urls_and_residual(
        "https://www.threads.com/@tt_duuss看一下這人是誰"
    )
    assert urls == ("https://www.threads.com/@tt_duuss",)
    assert residual == "看一下這人是誰"


def test_url_handle_not_duplicated():
    i = v16.IntentKernelV16().analyze(
        "https://www.threads.com/@tt_duuss看一下這人是誰"
    )
    assert i.entities == ("@tt_duuss",)
    assert i.source_hint == "threads"
    assert i.mode == "research"


def test_named_identity_entity_is_clean():
    i = v16.IntentKernelV16().analyze("柯文哲是誰")
    assert "柯文哲" in i.entities
    assert i.mode == "answer"


class FakeWiki:
    def probe(self, label):
        if label == "測試人物":
            return [
                g3.Evidence(
                    "測試人物（1970年—），臺灣政治人物、醫師，曾任測試市市長。",
                    "https://zh.wikipedia.org/wiki/test",
                    0.88,
                    0.95,
                )
            ]
        return []


class FakeBase:
    def _search(self, query, limit):
        return [
            (
                "https://news.example/a",
                "測試人物是誰",
                "測試人物是臺灣政治人物、醫師，曾任測試市市長。",
            ),
            (
                "https://noise.example/x",
                "IG hts unrelated",
                "完全無關的 IG hts 雜訊。",
            ),
        ]

    def _fetch_text(self, url):
        if "news.example" in url:
            return "測試人物是臺灣政治人物、醫師，曾任測試市市長。"
        return ""

    def _sentences(self, text):
        return [text] if text else []


def test_entity_orbit_filters_unrelated_noise():
    req = v16.EntityRequest(
        label="測試人物", handles=(), urls=(), source_hint="",
        question="測試人物是誰", identity_query=True,
    )
    orbit = v16.EntityORBIT(base=FakeBase(), wiki=FakeWiki())
    packet = orbit.research(req)
    assert packet.evidence
    assert all("IG hts" not in e.content for e in packet.evidence)
    assert any("政治人物" in e.content for e in packet.evidence)


def test_entity_narrative_general_public_person():
    req = v16.EntityRequest(
        label="測試人物", handles=(), urls=(), source_hint="",
        question="測試人物是誰", identity_query=True,
    )
    evidence = (
        g3.Evidence(
            "測試人物（1970年—），臺灣政治人物、醫師，曾任測試市市長。",
            "https://zh.wikipedia.org/wiki/test", 0.88, 0.95,
        ),
        g3.Evidence(
            "測試人物是臺灣政治人物、醫師，曾任測試市市長。",
            "https://news.example/a", 0.80, 0.90,
        ),
    )
    answer, used, meta = v16.EntityNarrative().synthesize(
        req, g3.ResearchPacket(evidence, 0.90, ("測試人物",))
    )
    assert "臺灣政治人物" in answer
    assert "醫師" in answer
    assert "測試市市長" in answer
    assert "IG" not in answer
    assert meta["sources"] >= 2


def test_threads_profile_insufficient_is_honest():
    req = v16.EntityRequest(
        label="@tt_duuss", handles=("@tt_duuss",),
        urls=("https://www.threads.com/@tt_duuss",),
        source_hint="threads", question="這個人在幹嘛", identity_query=True,
    )
    answer, used, meta = v16.EntityNarrative().synthesize(
        req, g3.ResearchPacket((), 0.0, ('"tt_duuss"',))
    )
    assert "@tt_duuss" in answer
    assert "不足" in answer
    assert "真實" in answer or "公開" in answer


class FakeEntityOrbit:
    def research(self, request):
        evidence = (
            g3.Evidence(
                "測試人物（1970年—），臺灣政治人物、醫師，曾任測試市市長。",
                "https://zh.wikipedia.org/wiki/test", .88, .95
            ),
            g3.Evidence(
                "測試人物是臺灣政治人物、醫師。",
                "https://news.example/a", .80, .90
            ),
        )
        return g3.ResearchPacket(evidence, .90, ("測試人物",))


def test_runtime_routes_entity_to_entity_pipeline():
    runtime = rt16.ChristineG3V16Runtime(
        entity_orbit=FakeEntityOrbit(),
        context=v16.ContextGraphV16(state_path=None),
    )
    answer, turn = runtime.ask("測試人物是誰")
    assert "政治人物" in answer
    assert any(x.startswith("entity-orbit:") for x in turn.trace)
    assert any(x.startswith("entity-facts:") for x in turn.trace)


def test_138b_preserved():
    assert rt16.FIVED9A_TOKEN_CAPACITY == 138_000_000_000
