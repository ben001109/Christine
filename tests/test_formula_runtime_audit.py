from pathlib import Path

from christine.runtime.formula_audit import (
    LEGACY_FORMULA_ARTIFACTS,
    RUNTIME_FORMULA_AUDIT_TARGETS,
    audit_formula_runtime_dependencies,
)


def test_formula_runtime_audit_reports_forbidden_runtime_token(tmp_path):
    runtime_file = tmp_path / "christine_final.py"
    runtime_file.write_text("class V1450FiveTensorEmpathyEngine: pass\n", encoding="utf-8")

    findings = audit_formula_runtime_dependencies(
        root=tmp_path,
        runtime_targets=(Path("christine_final.py"),),
        legacy_artifacts=(),
    )

    assert [(finding.kind, finding.path, finding.token, finding.line_number) for finding in findings] == [
        ("forbidden_token", Path("christine_final.py"), "V1450FiveTensorEmpathyEngine", 1)
    ]


def test_formula_runtime_audit_reports_legacy_artifacts(tmp_path):
    artifact = tmp_path / "brain" / "intersubjective.py"
    artifact.parent.mkdir()
    artifact.write_text("legacy", encoding="utf-8")

    findings = audit_formula_runtime_dependencies(
        root=tmp_path,
        runtime_targets=(),
        legacy_artifacts=(Path("brain/intersubjective.py"),),
    )

    assert [(finding.kind, finding.path, finding.token) for finding in findings] == [
        ("legacy_artifact", Path("brain/intersubjective.py"), "exists")
    ]


def test_formula_runtime_audit_default_targets_cover_current_runtime_entrypoints():
    assert Path("boot_christine.py") in RUNTIME_FORMULA_AUDIT_TARGETS
    assert Path("christine_final.py") in RUNTIME_FORMULA_AUDIT_TARGETS
    assert Path("brain/brain.py") in RUNTIME_FORMULA_AUDIT_TARGETS
    assert Path("brain/intersubjective.py") in LEGACY_FORMULA_ARTIFACTS


def test_current_runtime_formula_audit_has_no_findings():
    assert audit_formula_runtime_dependencies() == []
