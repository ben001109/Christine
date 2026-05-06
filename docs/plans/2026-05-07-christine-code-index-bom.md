# Code Index BOM Handling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stop the startup `Code index error: invalid non-printable character U+FEFF` by making the monolith code-index source read tolerate UTF-8 BOM.

**Architecture:** Keep the change minimal and local to the existing monolith code-index seam. Do not import `christine_final.py` in tests; use a static regression guard plus an AST smoke check that proves BOM-tolerant decoding parses the current monolith source.

**Tech Stack:** Python 3.10+, pytest, `uv run`, existing `boot_christine.py`/`christine_final.py` entry points.

---

### Task 1: Root Cause Evidence And Plan

**Files:**
- Create: `docs/plans/2026-05-07-christine-code-index-bom.md`

**Evidence gathered:**
- Logged symptom: `level5_logs/full_open_test_20260506_011839.log` line 72 shows `Code index error: invalid non-printable character U+FEFF (<unknown>, line 1)`.
- Error source: `christine_final.py` `_build_code_index(force=False)` reads `SELF_PATH` using `encoding="utf-8"`, then calls `_ast_module.parse(src)`.
- Current file prefix: `xxd -l 16 christine_final.py` shows `ef bb bf`, a UTF-8 BOM.
- Reproduction: `uv run python -c 'import ast; src=open("christine_final.py", "r", encoding="utf-8").read(); ast.parse(src)'` fails with `SyntaxError: invalid non-printable character U+FEFF`.
- Hypothesis test: `uv run python -c 'import ast; src=open("christine_final.py", "r", encoding="utf-8-sig").read(); ast.parse(src); print("parse-ok")'` prints `parse-ok`.

**Step 1: Commit the plan**

Run: `git add docs/plans/2026-05-07-christine-code-index-bom.md && git commit -m "docs: plan code index BOM handling"`

Expected: plan commit succeeds.

---

### Task 2: Add Regression Tests

**Files:**
- Create: `tests/test_code_index_bom.py`

**Step 1: Write failing tests**

Create tests that:
- Assert a UTF-8 BOM byte sequence decoded with `utf-8-sig` parses with `ast.parse` and does not start with `\ufeff`.
- Assert the V42 Optimizer code-index block in `christine_final.py` reads `SELF_PATH` with `encoding="utf-8-sig"` before `_ast_module.parse(src)`.
- Assert the current monolith source parses when read with `encoding="utf-8-sig"`.

**Step 2: Run RED**

Run: `uv run pytest tests/test_code_index_bom.py -q`

Expected: FAIL because `christine_final.py` still uses `encoding="utf-8"` in the code-index block.

---

### Task 3: Apply Minimal Monolith Fix

**Files:**
- Modify: `christine_final.py`
- Test: `tests/test_code_index_bom.py`

**Step 1: Change only the code-index source read**

In the V42 Optimizer `_build_code_index(force=False)` block, change:

```python
with open(SELF_PATH, "r", encoding="utf-8") as f:
    src = f.read()
```

to:

```python
with open(SELF_PATH, "r", encoding="utf-8-sig") as f:
    src = f.read()
```

This fixes the startup printed error without rewriting file contents, changing cache format, or importing new modules.

**Step 2: Run GREEN**

Run: `uv run pytest tests/test_code_index_bom.py -q`

Expected: all tests pass.

**Step 3: Run targeted parse check**

Run: `uv run python -c 'import ast; src=open("christine_final.py", "r", encoding="utf-8-sig").read(); ast.parse(src); print("parse-ok")'`

Expected: `parse-ok`.

**Step 4: Commit**

Run: `git add christine_final.py tests/test_code_index_bom.py && git commit -m "fix: tolerate BOM in code index source"`

Expected: commit succeeds.

---

### Task 4: Final Verification And Merge

**Files:**
- No planned production edits.

**Step 1: Run focused checks**

Run: `uv run pytest tests/test_code_index_bom.py tests/test_startup_platform_imports.py -q`

Expected: all tests pass.

**Step 2: Run full checks**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain christine christine_final.py`

Expected: no output.

Run: `uv run python boot_christine.py --check --notorch --fast --no-banner`

Expected: `[Runtime Health]` output and `自檢完成`.

Run: `git diff --check`

Expected: no output.

**Step 3: Review**

Request blocker-focused review for the branch diff against `main`, covering:
- `christine_final.py`
- `tests/test_code_index_bom.py`
- `docs/plans/2026-05-07-christine-code-index-bom.md`

**Step 4: Merge and push**

If review has no blocking findings:
- Fast-forward merge into local `main`.
- Re-run merged-main verification.
- Remove `.worktrees/code-index-bom`.
- Delete branch `code-index-bom`.
- Push `main` only if explicitly authorized.
