from pathlib import Path

from christine.runtime.formula_audit import (
    LEGACY_FORMULA_ARTIFACTS,
    LEGACY_FORMULA_IMPORTS,
    LEGACY_FORMULA_TOKENS,
    RUNTIME_FORMULA_AUDIT_TARGETS,
    audit_formula_runtime_dependencies,
)


def test_core_runtime_does_not_import_legacy_formula_engine():
    for path in [Path("boot_christine.py"), Path("brain/brain.py")]:
        text = path.read_text(encoding="utf-8")
        for forbidden in LEGACY_FORMULA_IMPORTS:
            assert forbidden not in text


def test_legacy_formula_artifacts_are_absent():
    for path in LEGACY_FORMULA_ARTIFACTS:
        assert not path.exists()


def test_monolith_does_not_embed_five_tensor_formula_blocks():
    text = Path("christine_final.py").read_text(encoding="utf-8")
    for token in LEGACY_FORMULA_TOKENS:
        assert token not in text


def test_runtime_formula_dependency_audit_is_clean():
    assert audit_formula_runtime_dependencies() == []


def test_formula_audit_targets_runtime_facing_entrypoints():
    assert RUNTIME_FORMULA_AUDIT_TARGETS == (
        Path("boot_christine.py"),
        Path("christine_final.py"),
        Path("brain/brain.py"),
    )
