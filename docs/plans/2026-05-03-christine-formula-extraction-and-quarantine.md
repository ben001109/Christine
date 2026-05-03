# Christine Formula Extraction And Quarantine Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fully extract the legacy Five-Tensor formula system from Christine's core runtime and preserve it as isolated research material.

**Architecture:** Treat the PDF and all formula code as a separate research track. Core runtime, boot flow, GUI, and brain ticks must not depend on formula outputs or theorem claims. Old code is inventoried, quarantined, and moved behind opt-in research tooling only.

**Tech Stack:** Python 3.10+, uv, pytest for isolation checks, Markdown audit documents.

---

## Scope Correction

This plan is not a formula reimplementation plan. The PDF is the source paper for the formula implementation currently embedded in the project. The task is to extract that subsystem completely from the main application so the full project refactor is not coupled to untrusted or disputed formulas.

## Non-Negotiable Rules

- Do not implement replacement formulas in the core refactor.
- Do not copy old formulas into new runtime modules.
- Do not use old formulas for boot self-checks, brain status, GUI labels, or user-facing theorem claims.
- Preserve the paper, inventory, contradictions, and old code as research artifacts.
- Any future formula work requires a separate explicit approval after extraction.

---

### Task 1: Inventory Formula Sources

**Files:**
- Create/modify: `docs/theory/formula-inventory.md`

**Step 1: Record all known formula sources**

Include at minimum:

- PDF: `/home/ben001109/Downloads/A_Five_Tensor_Formalism_for_Intersubjective_Cognition.pdf`
- `brain/intersubjective.py`
- `brain/intersubjective_v6_backup.py`
- `brain/philosophy.py`
- formula blocks in `christine_final.py`, especially around `118500-119060`

**Step 2: Mark every row as research/legacy**

No row should be marked `validated` or `runtime-ready`.

**Step 3: Verify**

Run: `git diff -- docs/theory/formula-inventory.md`
Expected: inventory lists sources and extraction decisions.

---

### Task 2: Paper Audit For Extraction Context

**Files:**
- Create/modify: `docs/theory/paper-audit.md`

**Step 1: Record PDF metadata**

Include path, title, version, page count, and SHA-256.

**Step 2: Record contradictions relevant to extraction**

The audit should explain why the formulas must not remain in core runtime. It does not need to solve the formulas.

**Step 3: Verify**

Run: `git diff -- docs/theory/paper-audit.md`
Expected: audit records evidence and no replacement implementation tasks.

---

### Task 3: Add Runtime Isolation Test

**Files:**
- Create: `tests/test_formula_runtime_isolation.py`

**Step 1: Write failing test**

```python
from pathlib import Path


def test_core_runtime_does_not_import_legacy_formula_engine():
    forbidden = "brain.intersubjective"
    for path in [Path("boot_christine.py"), Path("brain/brain.py")]:
        assert forbidden not in path.read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails before extraction**

Run: `uv run pytest tests/test_formula_runtime_isolation.py -q`
Expected: fail while core runtime still imports the legacy formula engine.

---

### Task 4: Create Research Quarantine Area

**Files:**
- Create: `research/five_tensor/README.md`
- Create: `research/five_tensor/legacy/`
- Create: `research/five_tensor/audit/`

**Step 1: Add README**

The README must state that this area is research-only and not part of Christine core runtime.

**Step 2: Move legacy formula code only after inventory is complete**

Move or copy old formula-specific code into `research/five_tensor/legacy/` as historical material. Preserve source references in the inventory.

**Step 3: Verify no runtime imports research code**

Run: `uv run pytest tests/test_formula_runtime_isolation.py -q`
Expected: pass after core runtime no longer imports legacy formula engine.

---

### Task 5: Replace Runtime Formula Claims With Neutral Diagnostics

**Files:**
- Modify later: `boot_christine.py`
- Modify later: `brain/brain.py`
- Modify later: relevant GUI/status code in `christine_final.py` after modularization

**Step 1: Remove formula-derived boot claims**

Boot may report that the Five-Tensor research module is quarantined, but must not claim `Psi`, `PsiHat`, `PsiTilde`, `WI`, `EI`, MCAP theorem status, or bounds.

**Step 2: Remove formula-derived brain tick claims**

Brain status may include neutral `formula_subsystem="quarantined"` diagnostics. It must not compute or display old formula metrics in normal runtime.

**Step 3: Verify launch still works**

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`
Expected: exit 0 without formula claims.

---

## Completion Criteria

- Formula sources are inventoried.
- PDF audit is recorded.
- Core runtime has no direct dependency on the legacy formula engine.
- Formula claims are removed from normal boot/status paths.
- Research artifacts are preserved under `research/five_tensor/`.
- No replacement formula implementation was added.
