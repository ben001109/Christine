from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


RUNTIME_FORMULA_AUDIT_TARGETS = (
    Path("boot_christine.py"),
    Path("christine_final.py"),
    Path("brain/brain.py"),
)

LEGACY_FORMULA_IMPORTS = (
    "brain.intersubjective",
    "from .intersubjective",
    "from .philosophy",
)

LEGACY_FORMULA_TOKENS = (
    "V1450FiveTensorEmpathyEngine",
    "V1455Paper4Engine",
    "Five-Tensor Empathy Engine",
    "PAPER-4 FULL EQUATIONS",
)

LEGACY_FORMULA_ARTIFACTS = (
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
)


@dataclass(frozen=True)
class FormulaRuntimeFinding:
    kind: str
    path: Path
    token: str
    line_number: int | None = None


def _iter_token_findings(path: Path, relative_path: Path, tokens: Iterable[str]) -> list[FormulaRuntimeFinding]:
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    findings = []
    for token in tokens:
        if token not in text:
            continue
        line_number = text[: text.index(token)].count("\n") + 1
        findings.append(FormulaRuntimeFinding("forbidden_token", relative_path, token, line_number))
    return findings


def audit_formula_runtime_dependencies(
    *,
    root: Path | str = Path("."),
    runtime_targets: Iterable[Path] = RUNTIME_FORMULA_AUDIT_TARGETS,
    legacy_imports: Iterable[str] = LEGACY_FORMULA_IMPORTS,
    legacy_tokens: Iterable[str] = LEGACY_FORMULA_TOKENS,
    legacy_artifacts: Iterable[Path] = LEGACY_FORMULA_ARTIFACTS,
) -> list[FormulaRuntimeFinding]:
    root_path = Path(root)
    findings: list[FormulaRuntimeFinding] = []
    for artifact in legacy_artifacts:
        if (root_path / artifact).exists():
            findings.append(FormulaRuntimeFinding("legacy_artifact", artifact, "exists"))
    forbidden_tokens = tuple(legacy_imports) + tuple(legacy_tokens)
    for target in runtime_targets:
        path = root_path / target
        if path.exists():
            findings.extend(_iter_token_findings(path, target, forbidden_tokens))
    return findings
