import christine_g3_frontier as g3
import christine_g3_web138 as v11


def test_138b_capacity_is_preserved():
    assert v11.FIVED9A_TOKEN_CAPACITY == 138_000_000_000
    counts = v11.hierarchy_counts()
    assert counts[0] == 134_765_625
    assert counts[-1] == 1


def test_factual_question_with_no_memory_is_web_eager():
    c = g3.ContractParser().parse("陳大坑是誰")
    assert v11.ChristineG3Web138Runtime._web_need(c, []) >= 0.70


class EmptyReasoner:
    engine = None
    ready = False

    def generate(self, prompt, system, temperature=0.25):
        return ""


class NoMemory:
    def status(self):
        return {"capacity_tokens": 138_000_000_000, "capacity_label": "138B"}

    def retrieve(self, query, limit=12):
        return []


class EvidenceWeb:
    def research(self, goal):
        return g3.ResearchPacket(
            evidence=(
                g3.Evidence(
                    content="陳大坑是這個測試來源中描述的人物；此句只用於驗證 ORBIT 的網路證據回覆。",
                    source="https://example.com/a",
                    confidence=0.80,
                    relevance=0.70,
                ),
                g3.Evidence(
                    content="第二個獨立來源也包含陳大坑的相關背景描述，用於交叉驗證搜尋流程。",
                    source="https://example.org/b",
                    confidence=0.76,
                    relevance=0.66,
                ),
            ),
            confidence=0.88,
            queries=("陳大坑", '"陳大坑"'),
        )


def test_explicit_web_still_answers_when_ollama_is_down():
    runtime = v11.ChristineG3Web138Runtime(
        reasoner=EmptyReasoner(),
        memory=NoMemory(),
        web=EvidenceWeb(),
    )
    answer, turn = runtime.ask("去網上查陳大坑")
    assert "實際上網檢索" in answer
    assert "https://example.com/a" in answer
    assert "answer:evidence-fallback" in turn.trace
    assert any(x.startswith("web:mandatory") for x in turn.trace)


def test_plain_fact_question_auto_browses_when_memory_is_weak():
    runtime = v11.ChristineG3Web138Runtime(
        reasoner=EmptyReasoner(),
        memory=NoMemory(),
        web=EvidenceWeb(),
    )
    answer, turn = runtime.ask("陳大坑是誰")
    assert "實際上網檢索" in answer
    assert any(x.startswith("web:auto") for x in turn.trace)


def test_math_still_avoids_web():
    runtime = v11.ChristineG3Web138Runtime(
        reasoner=EmptyReasoner(),
        memory=NoMemory(),
        web=EvidenceWeb(),
    )
    answer, turn = runtime.ask("1+1110124214")
    assert "1110124215" in answer
    assert not any(x.startswith("web:") for x in turn.trace)
