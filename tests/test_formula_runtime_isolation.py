from pathlib import Path


def test_core_runtime_does_not_import_legacy_formula_engine():
    forbidden_imports = [
        "brain.intersubjective",
        "from .intersubjective",
        "from .philosophy",
    ]
    for path in [Path("boot_christine.py"), Path("brain/brain.py")]:
        text = path.read_text(encoding="utf-8")
        for forbidden in forbidden_imports:
            assert forbidden not in text


def test_legacy_formula_artifacts_are_absent():
    legacy_artifacts = [
        Path("brain/intersubjective.py"),
        Path("brain/intersubjective.py.bak_v6"),
        Path("brain/intersubjective_v6_backup.py"),
        Path("brain/philosophy.py"),
        Path("research/five_tensor/README.md"),
        Path("research/five_tensor/audit/README.md"),
        Path("research/five_tensor/legacy/README.md"),
        Path("research/five_tensor/legacy/intersubjective.py"),
        Path("research/five_tensor/legacy/intersubjective.py.bak_v6"),
        Path("research/five_tensor/legacy/intersubjective_v6_backup.py"),
        Path("research/five_tensor/legacy/philosophy.py"),
        Path("_inter_peek.py"),
        Path("_new_intersubjective.py"),
        Path("_v1455_selftest.py"),
        Path("_diag_isub.py"),
        Path("_cf_peek.py"),
        Path("_brain_peek.py"),
        Path("_brain_integration_test.py"),
    ]
    for path in legacy_artifacts:
        assert not path.exists()


def test_monolith_does_not_embed_five_tensor_formula_blocks():
    text = Path("christine_final.py").read_text(encoding="utf-8")
    forbidden = [
        "V1450FiveTensorEmpathyEngine",
        "V1455Paper4Engine",
        "Five-Tensor Empathy Engine",
        "PAPER-4 FULL EQUATIONS",
    ]
    for token in forbidden:
        assert token not in text
