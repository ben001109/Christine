import json
from christine_g3v2.contracts import Evidence
from christine_g3v2.memory138 import Memory138
from christine_g3v2.self_map import SelfMap
from christine_g3v2.truth_gate import TruthGate


def test_truth_rejects_zero_grounding_certainty():
    report = TruthGate().evaluate(
        "這是已驗證的結論，邏輯與事實嚴謹無誤。",
        evidence=[], facts=[], verifier_backed=False,
    )
    assert not report.accepted
    assert report.reason in {"zero-grounding", "unsupported-certainty"}


def test_truth_accepts_grounded_claim():
    evidence = Evidence(
        "e1", "PRISMPlanner 負責多視角回答規劃。",
        "self-code://prism.py", .95, .99,
        trust=1.0, independent_group="self-code:prism", origin="self-map",
    )
    report = TruthGate().evaluate(
        "PRISMPlanner 負責多視角回答規劃。",
        evidence=[evidence], facts=[], verifier_backed=True,
    )
    assert report.accepted


def test_selfmap_parses_current_package():
    self_map = SelfMap()
    status = self_map.status()
    assert status["modules"] >= 5
    assert status["classes"] >= 5
    assert self_map.is_self_query("介紹一下你自己的架構")
    answer, evidence = self_map.describe("介紹一下你自己的架構")
    assert evidence
    assert "原始碼" in answer or "架構" in answer


def test_real_138_accounting_distinguishes_capacity_and_indexed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    snapshot = tmp_path / "data" / "5d9a_138b" / "snapshot-test"
    snapshot.mkdir(parents=True)
    (snapshot / "manifest.json").write_text(json.dumps({
        "created_at": 1,
        "tokens_estimated": 1_000_000,
        "leaves_written": 1000,
    }), encoding="utf-8")
    memory = Memory138()
    status = memory.status()
    assert status["capacity_tokens"] == 138_000_000_000
    assert status["indexed_tokens"] == 1_000_000
    assert status["indexed_tokens"] != status["capacity_tokens"]
    assert 0 < status["address_coverage"] < 1


def test_global_field_unknown_until_manifest_reports_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert Memory138().status()["global_field_coverage"] is None
