import christine_g3_frontier as g3
import christine_g3_native_context as v12


class FakeMemory:
    def retrieve(self, query, limit=12):
        return []


class FakeWeb:
    def __init__(self):
        self.queries = []

    def research(self, goal):
        self.queries.append(goal)
        ev = (
            g3.Evidence(
                "Alpha 工具是一套用來測試上下文整理功能的軟體系統。",
                "https://a.example/doc",
                0.85,
                0.80,
            ),
            g3.Evidence(
                "Alpha 工具是一套用來測試上下文整理功能的軟體系統。",
                "https://a.example/doc",
                0.82,
                0.78,
            ),
            g3.Evidence(
                "官方文件表示 Alpha 工具主要提供資料整理與查詢功能。",
                "https://b.example/official",
                0.88,
                0.75,
            ),
        )
        return g3.ResearchPacket(ev, 0.86, (goal,))


def thread():
    return v12.THREADContext(state_path=None)


def test_sage_deduplicates_search_results():
    sage = v12.SAGENativeSynthesizer()
    web = FakeWeb().research("Alpha 工具")
    answer, used, meta = sage.synthesize(
        goal="Alpha 工具是什麼",
        evidence=list(web.evidence),
        packet=web,
    )
    assert answer.count("https://a.example/doc") == 1
    assert "去重、交叉比對" in answer
    assert meta["chosen_clusters"] >= 1


def test_sage_does_not_dump_identical_raw_results():
    sage = v12.SAGENativeSynthesizer()
    web = FakeWeb().research("Alpha 工具")
    answer, _, _ = sage.synthesize(
        goal="Alpha 工具是什麼",
        evidence=list(web.evidence),
        packet=web,
    )
    raw = "Alpha 工具是一套用來測試上下文整理功能的軟體系統。"
    assert answer.count(raw) == 0


def test_followup_inherits_previous_code_contract_without_web():
    t = thread()
    parser = g3.ContractParser()
    first = parser.parse("寫一個 python 爬蟲")
    t.commit(
        user_input="寫一個 python 爬蟲",
        contract=first,
        resolved_goal=first.goal,
        answer="code artifact",
        evidence=[],
    )
    r = t.resolve("還會寫其他的嗎", parser)
    assert r.followup
    assert r.contract.operation == "create"
    assert r.contract.output_kind == "code"
    assert not r.contract.requires_web


def test_followup_research_uses_previous_goal_not_literal_question():
    fw = FakeWeb()
    rt = v12.ChristineG3NativeContextRuntime(
        memory=FakeMemory(),
        web=fw,
        thread=thread(),
    )
    rt.ask("去網上查 Alpha 工具")
    rt.ask("還有其他的嗎")
    assert len(fw.queries) == 2
    assert fw.queries[1] == "去網上查 Alpha 工具"
    assert fw.queries[1] != "還有其他的嗎"


def test_native_runtime_never_constructs_local_reasoner():
    rt = v12.ChristineG3NativeContextRuntime(
        memory=FakeMemory(),
        web=FakeWeb(),
        thread=thread(),
    )
    assert not hasattr(rt, "reasoner")


def test_138b_capacity_preserved():
    assert v12.FIVED9A_TOKEN_CAPACITY == 138_000_000_000


def test_context_reply_is_coherent():
    rt = v12.ChristineG3NativeContextRuntime(
        memory=FakeMemory(),
        web=FakeWeb(),
        thread=thread(),
    )
    c = g3.ContractParser().parse("寫一個 python 爬蟲")
    rt.thread.commit(
        user_input=c.goal,
        contract=c,
        resolved_goal=c.goal,
        answer="previous code",
        evidence=[],
    )
    answer, turn = rt.ask("還會寫其他的嗎")
    assert "上一輪" in answer
    assert "python 爬蟲" in answer
    assert "web:" not in " | ".join(turn.trace)
