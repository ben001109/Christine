import json

from christine.platform.evidence import EvidenceProvenance, PlatformEvidence, collect_native_evidence, write_evidence_atomically
from tools.collect_platform_evidence import FOCUSED_TEST_TARGETS, main, run_focused_suite


def test_fixture_evidence_is_serializable_and_host_independent():
    evidence = collect_native_evidence(fixture=True)

    assert json.loads(evidence.to_json()) == evidence.to_dict()
    assert evidence.identity == "linux"
    assert evidence.provenance.mode == "fixture"
    assert "host" not in evidence.to_json()


def test_atomic_write_keeps_prior_document_when_replace_fails(tmp_path, monkeypatch):
    destination = tmp_path / "evidence.json"
    destination.write_text("previous", encoding="utf-8")
    monkeypatch.setattr("christine.platform.evidence.os.replace", lambda *_: (_ for _ in ()).throw(OSError()))

    receipt = write_evidence_atomically(destination, collect_native_evidence(fixture=True))

    assert receipt.status == "failed"
    assert destination.read_text(encoding="utf-8") == "previous"
    assert "previous" not in json.dumps(receipt.to_dict())
    assert not list(tmp_path.glob(".platform-evidence-*"))


def test_invalid_evidence_returns_a_content_free_rejected_receipt(tmp_path):
    invalid_evidence = PlatformEvidence(
        identity="untrusted-identity",
        capabilities={},
        provenance=EvidenceProvenance(),
    )

    receipt = write_evidence_atomically(tmp_path / "evidence.json", invalid_evidence)

    assert receipt.to_dict() == {"schema_version": 1, "status": "rejected", "digest": ""}


def test_collector_dry_run_and_focused_suite_contract(capsys):
    assert main(["--dry-run", "--fixture"]) == 0
    assert json.loads(capsys.readouterr().out)["provenance"]["mode"] == "fixture"

    observed: list[list[str]] = []

    class Result:
        returncode = 0

    assert run_focused_suite(lambda command, check: observed.append(command) or Result()) is True
    assert tuple(observed[0][3:]) == (
        "tests/platform",
        "tests/test_platform_capabilities.py",
        "tests/test_platform_runtime_gates.py",
        "tests/test_startup_platform_imports.py",
        "tests/test_boot_contract.py",
    )
    assert FOCUSED_TEST_TARGETS == tuple(observed[0][3:])


def test_collector_reports_a_generic_focused_suite_failure(capsys):
    class Result:
        returncode = 1

    assert main(["--run-suite"], runner=lambda command, check: Result()) == 1
    assert capsys.readouterr().out == '{"status":"focused-suite-failed"}\n'


def test_collector_preserves_argparse_exit_codes(capsys):
    assert main(["--help"]) == 0
    assert "usage:" in capsys.readouterr().out

    assert main(["--not-an-option"]) == 2
    assert "unrecognized arguments" in capsys.readouterr().err
