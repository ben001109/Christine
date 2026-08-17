# Christine G3 v2.5 — REASONING FABRIC

v2.5 keeps the v2.4 5D9A-OMEGA control plane and adds three execution-grade cognitive capabilities.

## LOGOS-M9

Formal mathematics path:

`Natural language → MathIR → exact operator → proof steps → deterministic verifier`

Current exact coverage includes arithmetic, modular exponentiation, modular inverse, gcd/lcm, primality, combinations, determinants, quadratics, and Fermat's little theorem proof structure. Unsupported mathematics falls through rather than pretending to be verified.

## CEDAR

Code path:

`Prompt → TaskSpec → architecture/invariants → Christine NativeGenerator → AST/interface verification → bounded repair → NOVA`

The SPEC-GATE uses task specificity rather than a list of benchmark answers. A concrete object such as an explicitly named data structure can be sufficient specification; genuinely vague requests still trigger clarification.

CEDAR intentionally does not auto-execute arbitrary generated code. Runtime execution should be added only through a sandboxed capability.

## MOSAIC-Q

Scientific/research path:

`Long question → entities/concepts/relations → subquestions → multiple ORBIT queries → evidence merge/coverage → normal Hygiene/OMEGA/FactGraph/PRISM/TruthGate`

This prevents long questions from being treated as one giant search entity.

## Relationship to 5D9A-OMEGA

OMEGA remains the central controller. LOGOS corresponds to `symbolic_reason`; CEDAR supplies `generate_code`; MOSAIC supplies `decompose_question`. Successful paths feed OMEGA Adapt so skill success statistics can improve future planning.

## Verification

Local package regression before push: 54 tests passed and `python -m compileall -q christine_g3v2` passed.
