# Christine G3 v2.3 — TRUTH-GATE + REAL-138 ACCOUNTING + SELF-MAP

## TRUTH-GATE

High-certainty factual wording is rejected when claim support is below the grounding threshold. In particular, `evidence=0` and `facts=0` can no longer produce claims such as `已驗證` or `嚴謹無誤` unless an explicit verifier proves the derived result.

The trace exposes `truth:<reason>:gr=<grounding-ratio>:src=<independent-source-count>`.

## REAL-138 ACCOUNTING

The runtime now separates:

- `capacity_tokens`: virtual 5D9A address capacity.
- `indexed_tokens` / `indexed_leaves`: confirmed from the latest ATLAS manifest.
- `resident_sparse_tokens_estimate` / `loaded_records`: locally resident sparse memory.
- `active_memory_tokens_estimate` / `active_memory_leaves`: memory actually activated on the current turn.
- `global_field_coverage`: only reported when an ATLAS manifest explicitly contains `global_field_leaves`; otherwise it is `null`.

Capacity is never interpreted as `fully loaded`.

## SELF-MAP

`SelfMap` parses the current `christine_g3v2/*.py` source tree using Python AST. It records modules, classes, top-level functions and import edges, then returns self-code evidence for questions about Christine, 5D9A, PRISM, ATLAS, NOVA, ORBIT, Memory Hygiene, Truth Gate and related architecture.

This makes self-knowledge track the code actually running instead of a hand-written FAQ.

## Local verification before push

The v2.3 package was tested together with the existing v2.2 suite:

- `33 passed`
- `python -m compileall -q christine_g3v2` passed.
