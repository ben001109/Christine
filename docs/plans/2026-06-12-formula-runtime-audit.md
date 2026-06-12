# Formula Runtime Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Codify a repeatable runtime-facing legacy five-tensor formula dependency audit without reintroducing formula implementations.

**Architecture:** Add a pure `christine.runtime.formula_audit` helper that scans explicit runtime-facing files and legacy artifact paths for forbidden five-tensor symbols/imports. Existing formula isolation tests will use this helper instead of only hard-coded assertions, while `christine_final.py`, generated files, runtime state, and persisted data remain untouched.

**Tech Stack:** Python 3.10+, pathlib, dataclasses, uv, pytest, static source scanning.

---

## Requirements Captured

- Keep legacy five-tensor formula implementations out of runtime-facing paths.
- Do not implement replacement formulas.
- Do not move, delete, or rewrite runtime state, logs, generated code, backups, mirrors, or self replicas.
- Do not import `christine_final.py` from tests.
- Keep the audit pure: no filesystem writes, no imports of scanned runtime files, no model/API calls.
- Preserve existing checks for absent legacy artifacts and forbidden monolith formula blocks.
- Make the audit reusable so future runtime-facing files can be added to the target list.
- Update `docs/ROADMAP.md` after the slice lands.

## Non-Goals

- No formula extraction or restoration.
- No replacement math/model implementation.
- No generated `brain/generated/` edits.
- No broader monolith refactor outside the audit guard.
- No persisted data format changes.

---

### Task 1: Add Formula Runtime Audit Helper Tests

**Files:**
- Create: `tests/test_formula_runtime_audit.py`

**Step 1: Write failing tests**

Create `tests/test_formula_runtime_audit.py`:

```python
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
```

**Step 2: Run RED**

Run: `uv run pytest tests/test_formula_runtime_audit.py -q`

Expected: FAIL because `christine.runtime.formula_audit` does not exist.

---

### Task 2: Implement Formula Runtime Audit Helper

**Files:**
- Create: `christine/runtime/formula_audit.py`
- Modify: `christine/runtime/__init__.py`
- Test: `tests/test_formula_runtime_audit.py`

**Step 1: Add minimal helper module**

Create `christine/runtime/formula_audit.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable


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
```

Modify `christine/runtime/__init__.py`:

```python
from .formula_audit import (
    FormulaRuntimeFinding,
    audit_formula_runtime_dependencies,
)
```

Add both names to `__all__`.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_formula_runtime_audit.py -q`

Expected: PASS.

**Step 3: Commit helper slice**

Run: `git add christine/runtime/formula_audit.py christine/runtime/__init__.py tests/test_formula_runtime_audit.py && git commit -m "refactor: add formula runtime audit helper"`

---

### Task 3: Refactor Existing Formula Isolation Guards

**Files:**
- Modify: `tests/test_formula_runtime_isolation.py`

**Step 1: Update test to use audit helper**

Replace `tests/test_formula_runtime_isolation.py` with:

```python
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
```

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_formula_runtime_audit.py tests/test_formula_runtime_isolation.py -q`

Expected: PASS.

**Step 3: Commit test refactor**

Run: `git add tests/test_formula_runtime_isolation.py && git commit -m "test: use formula runtime audit helper"`

---

### Task 4: Update Roadmap

**Files:**
- Modify: `docs/ROADMAP.md`

**Step 1: Update tracking text**

In completed M1 slices, add:

```markdown
- Legacy five-tensor formula runtime dependency audit is codified in
  `christine.runtime.formula_audit`.
```

Remove this remaining M1 slice:

```markdown
- Audit and remove or fully isolate legacy five-tensor formula dependencies from
  runtime-facing paths before relying on broader modular architecture.
```

Adjust `Estimated remaining M1 effort` from `9-15 small slices` to `8-14 small slices`.

In `Immediate Next Slices`, remove:

```markdown
- Start a formula-layer runtime dependency audit.
```

**Step 2: Verify docs diff**

Run: `git diff -- docs/ROADMAP.md`

Expected: only roadmap tracking text changes.

**Step 3: Commit roadmap update**

Run: `git add docs/ROADMAP.md && git commit -m "docs: update roadmap after formula runtime audit"`

---

### Task 5: Final Verification And Review

**Files:**
- No planned edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_formula_runtime_audit.py tests/test_formula_runtime_isolation.py tests/test_boot_contract.py -q`

Expected: PASS.

**Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: PASS.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: reaches `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 3: Review**

Perform this session review or subagent review. Check:

- The audit helper is pure and does not import scanned runtime files.
- The audit does not implement or restore legacy formulas.
- Existing legacy artifact and forbidden token coverage is preserved.
- Runtime state, generated files, backups, mirrors, and self replicas are untouched.

**Step 4: Finish branch**

If verification and review pass, merge to `main`, rerun merged-main verification, remove the worktree, delete the branch, and push.
