from christine_g3v2.contracts import Evidence
from christine_g3v2.lexer_intent import IntentKernel
from christine_g3v2.memory_hygiene import EvidenceHygiene
from christine_g3v2.synthesis import FactGraph


def ev(i, text, *, rel=.8, conf=.85, origin="memory", entity=.0, source="5d9a-local"):
    return Evidence(str(i), text, source, rel, conf, trust=.7, entity_match=entity,
                    independent_group=source, origin=origin)


def test_colloquial_definition_routes_to_factual():
    intent = IntentKernel().analyze("領域展開是啥")
    assert intent.kind == "answer"
    assert "領域展開" in intent.entities


def test_what_does_it_mean_routes_to_factual():
    intent = IntentKernel().analyze("傅立葉轉換啥意思")
    assert intent.kind == "answer"
    assert "傅立葉轉換" in intent.entities


def test_explain_prefix_extracts_subject():
    intent = IntentKernel().analyze("解釋一下量子糾纏")
    assert intent.kind == "answer"
    assert "量子糾纏" in intent.entities


def test_hygiene_rejects_internal_code_for_general_factual_query():
    hygiene = EvidenceHygiene()
    good = ev(1, "測試人物是臺灣政治人物、醫師，曾任測試市市長。", entity=.9)
    bad = ev(2, "測試人物影響分析 if not scored and enable_escalate and not _ood_gate: expected shard token", rel=.7, entity=.8)
    kept, report = hygiene.sanitize(query="測試人物是誰", subject="測試人物", evidence=[good, bad])
    assert any(x.evidence_id == good.evidence_id for x in kept)
    assert all("_ood_gate" not in x.content for x in kept)
    assert report.rejected == 1


def test_hygiene_allows_code_for_code_query():
    hygiene = EvidenceHygiene()
    code = ev(1, "def solve(x):\n    return x + 1", rel=.7)
    kept, _ = hygiene.sanitize(query="寫一個 Python 函式 solve", subject="solve", evidence=[code])
    assert kept


def test_factgraph_requires_subject_linkage():
    unrelated = ev(1, "某套內部程式現任 router，具有 expected shard token 功能。", rel=.7)
    assert FactGraph().extract("測試人物", [unrelated]) == []
