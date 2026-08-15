from pathlib import Path

from christine_g3v2.atlas138 import ATLAS138Trainer, Coordinate5D, RawRecord
from christine_g3v2.contracts import Fact, ResearchPacket
from christine_g3v2.prism import PRISMPlanner, PRISMNarrator


def fact(cat, value, conf=.9, src=("a",)):
    return Fact(cat, "測試人物", "x", value, conf, src, ("e",))


def test_prism_multi_facet_profile():
    facts = [
        fact("identity", "臺灣政治人物、醫師", .95, ("wiki", "news")),
        fact("position", "曾任臺北市市長", .94, ("wiki", "bbc")),
        fact("position", "曾任政黨主席", .90, ("wiki", "news")),
        fact("status", "目前擔任某組織職務", .82, ("news", "official")),
        fact("impact", "在公共議題中具有高度知名度", .78, ("news", "paper")),
    ]
    packet = ResearchPacket((), .91, ("x",))
    plan = PRISMPlanner().plan(question="測試人物是誰，詳細介紹一下", subject="測試人物", facts=facts, packet=packet, token_budget=1200)
    assert len(plan.facets) >= 3
    text = PRISMNarrator().narrate(subject="測試人物", question="測試人物是誰", plan=plan, packet=packet)
    assert "臺灣政治人物" in text
    assert "曾任臺北市市長" in text
    assert "\n\n" in text


def test_prism_compact_vs_deep():
    facts = [fact("identity", "臺灣政治人物、醫師"), fact("position", "曾任市長")]
    planner = PRISMPlanner()
    assert planner.plan(question="一句話介紹測試人物是誰", subject="測試人物", facts=facts, packet=None).mode == "compact"
    assert planner.plan(question="詳細介紹測試人物是誰", subject="測試人物", facts=facts, packet=None).mode == "deep"


def test_atlas_has_all_training_objectives(tmp_path):
    objectives = ATLAS138Trainer(tmp_path).training_objectives()
    assert {"semantic", "temporal", "relational", "personal", "epistemic", "retrieval_policy", "consolidation"} <= set(objectives)


def test_atlas_training_stream(tmp_path):
    trainer = ATLAS138Trainer(tmp_path, leaf_chars=80, shard_leaf_limit=2)
    rows = [
        RawRecord("Alpha 是一個測試系統。它提供資料索引功能。" * 10, "source-a", source_trust=.9),
        RawRecord("Beta 是另一個測試系統。它具有不同功能。" * 10, "source-b", source_trust=.7),
    ]
    stats = trainer.train_stream(rows, snapshot_name="s1")
    assert stats.records_seen == 2
    assert stats.leaves_written >= 2
    assert Path(stats.snapshot_path, "manifest.json").exists()


def test_atlas_online_verified(tmp_path):
    trainer = ATLAS138Trainer(tmp_path)
    leaf = trainer.online_assimilate(RawRecord("經過驗證的新事實。", "verified-source", source_trust=.9), verified=True)
    assert leaf is not None and leaf.verified
    assert (tmp_path / "hot_verified.jsonl").exists()


def test_5d_score():
    c = Coordinate5D(.9, .7, .8, .6, .95)
    score = ATLAS138Trainer.five_d_score(c, weights=(.3, .1, .2, .1, .3))
    assert .7 < score <= 1.0
