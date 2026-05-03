# Paper Audit

This document records a first-pass audit of `A Five-Tensor Formalism for Intersubjective Cognition`, the paper behind the formula subsystem currently embedded in Christine. Its purpose is extraction context, not replacement implementation.

## Source

- File: `/home/ben001109/Downloads/A_Five_Tensor_Formalism_for_Intersubjective_Cognition.pdf`
- SHA-256: `17d53f3889b89345622227ad561912f8b3605627d6f43ba49289fd040163e1b1`
- Read date: 2026-05-03
- Scope read: full PDF text, pages 1-41.

## Audit Position

The PDF explains the formula subsystem to extract. The paper text, Appendix D reference implementation, Appendix E verification suite, and current repository implementation disagree on key numeric results. Therefore the subsystem should be quarantined from core runtime rather than expanded or reimplemented during the main refactor.

## First-Pass Red Flags

### R001: Toy perspective count contradiction

Paper locations:

- Abstract says the toy has `D = J = L = M+1 = 2`.
- Section 14.1 repeats `D = J = L = M+1 = 2`.
- Section 14.3 defines `P0 = id`, `P1 = adversary`, `P2 = observer` and raw weights `(1, 0.7, 0.5)`, which means three perspectives.

Impact:

The model dimension `M+1` is ambiguous. Any formula depending on `M`, `phi_m`, or `beta*(M, Delta_max)` cannot be validated from the toy example until this is resolved.

### R002: Appendix D does not reproduce the stated toy numbers

Claimed paper values:

- `Psi ≈ 6.00`
- `Psi_hat ≈ 7.56`
- `Psi_tilde ≈ 12.4`
- `WI ≈ 1.26`
- `EI ≈ 1.64`

Direct sanity check using the PDF Appendix D algorithm and the Section 14 toy data produced:

```text
Psi_tilde appendix-D-style: 8759.505910897855
Psi_hat proxy M=0: 18422.813628555767
EI proxy: 0.4754705816119438
canonical phis: [0.45454545454545453, 0.3181818181818181, 0.22727272727272727]
sum phi2: 0.35950413223140487
```

Impact:

Appendix D cannot be treated as a validated reference implementation. Either the toy numbers use a different normalization/complexity table than Appendix D, or the appendix is inconsistent with the text.

### R003: Repository legacy self-test fails paper targets

Command:

```bash
uv run --no-sync python brain/intersubjective.py
```

Observed output:

```text
Psi        = 35945.802     target ≈ 6.00
PsiHat     = 8506.665      target ≈ 7.56
PsiTilde   = 710.030       target ≈ 12.4
WI         = 0.237         target ≈ 1.26
EI         = 0.083         target ≈ 1.64
bounds_ok  = {'Thm5.7': False, 'Thm6.7': True, 'Thm9.1': True}
```

Impact:

The existing `brain/intersubjective.py` implementation is not numerically aligned with the paper targets and must be quarantined.

### R004: Monolith documents an incorrect beta formula

Legacy source:

- `christine_final.py:118507`

Monolith note says:

```text
beta*(M, Delta_max) <= 1 + log2(M+1)/(M+1) * Delta^2_max
```

Paper Theorem 9.10 says:

```text
beta*(M, Delta_max) <= 1 + log2(M+1)/(M+1) * max(1 - Delta_max / ((ln 2) log2(M+1)), 0)
```

Impact:

At least one formula in the monolith is transcription-level wrong.

### R005: Continuous formulas and discrete appendix use incompatible scaling unless specified

Paper definitions use limits and integrals over `Delta_T`, while Appendix D uses finite sums over integer `t1`, `t2`, `t3` and divides by `T**5`.

Impact:

The implementation needs an explicit discrete approximation spec before any theorem or numeric target can be tested.

### R006: Appendix E includes tests that do not validate theorems

Examples:

- E10 generates artificial data from `a_star * n + b_star * log2(1+n) + c_star + noise`, then tests the same predictor shape.
- Several tests assert monotonicity or bounds without comparing to independent reference fixtures.

Impact:

Appendix E is useful as a list of desired properties, but it is not a sufficient verification suite.

## Formula: `beta*(M, Delta_max)`

**Paper Reference:** Theorem 9.10, Table 9.1.

**Original Statement:**

`beta*(M, Delta_max) <= 1 + (log2(M+1)/(M+1)) * max(1 - Delta_max / ((ln 2) * log2(M+1)), 0)`.

**Symbols:**

- `M`: number of non-base perspective slots where the paper uses `M+1` total perspectives.
- `Delta_max`: maximum distortion bound, non-negative scalar.
- `beta*`: empathy threshold upper bound, dimensionless.

**Current Finding:**

This formula is recorded because it appears in both the PDF and the legacy code. It is not scheduled for implementation in the core refactor, and it still depends on resolving how the paper defines `M` in the toy example.

**Runtime Decision:**

`research-only`; not runtime-ready.

## Formula: `Psi`, `Psi_hat`, `Psi_tilde`

**Paper References:** Def 5.4, Def 6.5, Def 7.11.

**Current Finding:**

These are not runtime-ready. The paper text, Appendix D, Section 14 table, and repository self-test disagree. If a separate future research project ever revisits them, it would first need a written discrete approximation contract covering:

- Whether `T` includes endpoints `0..T` or `0..T-1`.
- Whether discrete sums approximate integrals by raw sums, normalized averages, or weighted quadrature.
- Whether `K(x)` is theoretical, table-driven, gzip length in bytes, or gzip length in bits.
- Whether `K(M_t)` means memory at one time or memory history `M_[0,t]`; the paper text mixes both in labels.
- Whether embedding factors `T^2` and `T` should exist in finite toy computations.
- Whether `M+1` is 2 or 3 in the toy.

**Runtime Decision:**

`legacy/untrusted`; extract from core runtime and preserve as research material.

## Next Extraction Steps

1. Keep this audit with the formula inventory as research documentation.
2. Add a runtime isolation test proving boot and brain core no longer import the legacy formula engine.
3. Move formula-specific code and paper notes into `research/five_tensor/`.
4. Replace normal runtime formula output with neutral quarantine diagnostics.
5. Do not implement replacement formulas in the core refactor.
