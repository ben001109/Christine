from christine_g3v2.contracts import ContextResolution, Evidence, Fact, Intent
from christine_g3v2.omega5d9a import OMEGA5D9A


def intent(goal, *, facts=True, current=False, kind='answer'):
    return Intent(kind, 'answer', 'text', goal, requires_facts=facts,
                  requires_current=current, scores={'factual': .76, 'science': .1})


def ev(i, text, rel=.7, conf=.8, trust=.8, origin='memory', group='g'):
    return Evidence(str(i), text, f'https://{group}.example/{i}', rel, conf,
                    trust=trust, entity_match=rel, independent_group=group, origin=origin)


def test_5d_weights_normalize():
    o=OMEGA5D9A(state_path=None)
    f=o.preflight(intent('量子糾纏是什麼'), ContextResolution('量子糾纏是什麼',0.0), subject='量子糾纏')
    assert abs(sum(f.weights.as_tuple())-1.0)<1e-9


def test_current_query_increases_temporal_weight():
    o=OMEGA5D9A(state_path=None)
    a=o.preflight(intent('柯文哲是誰'), ContextResolution('柯文哲是誰',0.0), subject='柯文哲')
    b=o.preflight(intent('柯文哲目前是誰',current=True), ContextResolution('柯文哲目前是誰',0.0), subject='柯文哲')
    assert b.weights.temporal>a.weights.temporal


def test_unknown_query_expands_budget():
    o=OMEGA5D9A(state_path=None);o.ledger.recent_queries.extend(['Python list 是什麼']*5)
    familiar=o.preflight(intent('Python list 是什麼'), ContextResolution('Python list 是什麼',0), subject='Python list')
    unknown=o.preflight(intent('量子色動力學真空凝聚與拓撲缺陷如何互相影響'), ContextResolution('量子色動力學真空凝聚與拓撲缺陷如何互相影響',0), subject='量子色動力學')
    assert unknown.budget.memory_k>=familiar.budget.memory_k


def test_evidence_selection_penalizes_debug_noise_for_person_query():
    o=OMEGA5D9A(state_path=None);f=o.preflight(intent('柯文哲是誰'), ContextResolution('柯文哲是誰',0), subject='柯文哲')
    good=ev(1,'柯文哲是臺灣政治人物與醫師。',.9,.9,.9,group='wiki')
    noise=ev(2,'if not scored and enable_escalate and not _ood_gate: expected shard token',.8,.9,.9,group='internal')
    selected,scores=o.select_evidence(f,[noise,good]);assert selected[0].evidence_id=='1'
    sm={x.evidence_id:x for x in scores};assert sm['2'].hygiene_multiplier<sm['1'].hygiene_multiplier


def test_contradiction_entropy_detects_opposing_stance():
    o=OMEGA5D9A(state_path=None)
    a=ev(1,'Alpha 是 Beta 系統的一部分。',.8,.8,.8,group='a')
    b=ev(2,'Alpha 並不是 Beta 系統的一部分。',.8,.8,.8,group='b')
    assert o.contradiction_entropy([a,b])>0


def test_hypotheses_have_bounded_posterior():
    o=OMEGA5D9A(state_path=None);f=o.preflight(intent('Alpha 是什麼'), ContextResolution('Alpha 是什麼',0), subject='Alpha')
    hs=o.hypotheses(f,[ev(1,'Alpha 是資料分析工具。',.9,.9,.9,group='a'),ev(2,'Alpha 是資料分析工具。',.9,.8,.8,group='b')])
    assert hs and 0<=hs[0].posterior<=1


def test_audit_geometric_quality_requires_grounding():
    o=OMEGA5D9A(state_path=None);f=o.preflight(intent('Alpha 是什麼'), ContextResolution('Alpha 是什麼',0), subject='Alpha')
    evidence=[ev(1,'Alpha 是資料工具。',.9,.9,.9,group='a')]
    facts=[Fact('identity','Alpha','is','資料工具',.9,('a',),('1',))]
    good=o.audit(f,evidence=evidence,facts=facts,truth_grounding=.95,truth_accepted=True)
    bad=o.audit(f,evidence=evidence,facts=facts,truth_grounding=.05,truth_accepted=False)
    assert good.total_quality>bad.total_quality and not bad.should_commit


def test_adapt_updates_skill_beta_stats():
    o=OMEGA5D9A(state_path=None);f=o.preflight(intent('Alpha 是什麼'), ContextResolution('Alpha 是什麼',0), subject='Alpha')
    audit=o.audit(f,evidence=[],facts=[],truth_grounding=0,truth_accepted=False)
    o.adapt(f,audit,successful_actions=('retrieve_memory',),failed_actions=('search_web',))
    assert o.ledger.skill_stats['retrieve_memory']['alpha']==3.0
    assert o.ledger.skill_stats['search_web']['beta']==3.0


def test_field_state_has_five_dimensions():
    o=OMEGA5D9A(state_path=None);f=o.preflight(intent('Alpha 是什麼'), ContextResolution('Alpha 是什麼',0), subject='Alpha')
    state=o.field_state(f,[ev(1,'Alpha 是資料工具。')])
    assert len(state)==5 and all(0<=x<=1 for x in state)
