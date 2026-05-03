# Christine Modelization Design

## Goal

Christine should gain model-assisted capabilities without replacing deterministic
runtime behavior. The model layer must help Christine understand her codebase,
route requests, summarize memory, and preserve personality, while launchers,
tools, GUI actions, file operations, platform integration, and safety gates stay
in explicit Python modules.

## Architecture

Use a hybrid design:

- Deterministic runtime remains the source of truth for side effects.
- Retrieval and small models provide context, ranking, summarization, and routing.
- Larger fine-tuning happens only after corpus filtering, privacy review, and evals
  are in place.
- Every model output that can affect files, tools, GUI, deployment, memory, or
  platform actions must pass through deterministic policy code.

Initial modules live under `christine/modelization/` and expose safe data
selection utilities before any training, embedding, or inference code is added.

## Corpus Sources

Allowed corpus sources:

- Source code for `boot_christine.py`, `brain/`, `christine/`, and selected stable
  legacy seams in `christine_final.py`.
- Documentation in `docs/`, `AGENTS.md`, project plans, launcher notes, and module
  contracts.
- Selected chat and tool transcripts after manual review or automated privacy
  filtering.
- Selected memory summaries, not raw private state files.
- Test files that document behavior contracts.

The first corpus filter is intentionally conservative. It includes source and
docs by default, and excludes paths known to contain runtime state, generated
code, benchmark repos, secrets, caches, and model weights.

## Corpus Exclusions

Always exclude:

- Secrets and local credentials: `.env`, key files, tokens, browser profiles.
- Raw private state: `data/`, `growth.log`, `heartbeat.txt`,
  `nexus_v2_state.json`, and unsummarized memory databases.
- Generated or external bulk data: `brain/generated/`, `ARC-AGI/`, caches,
  benchmark datasets, exports, mirrors, backups, and self replicas.
- Binary or model artifacts: `.safetensors`, `.pt`, `.pkl`, `.npy`, `.pyc`.

Exclusions must be enforced before embedding, training, sync, or upload. If a
future task needs any excluded source, it requires an explicit review and a new
test proving the exception is safe.

## Model Tracks

1. Repository Knowledge Model

Build embeddings or local RAG over source, docs, plans, and tests so Christine
can answer questions about her own architecture and refactor state. This should
be read-only and local-first.

2. Routing/Policy Model

Train a small classifier only after deterministic routing tests exist. The model
may recommend paths such as brain, local LLM, cloud LLM, tools, GUI, or worker,
but deterministic policy makes the final decision.

3. Memory Summarization Model

Summarize long-term memories into safe, queryable records. Raw state remains
untouched unless a migration plan and backup strategy exist.

4. Behavior Distillation Model

LoRA or SFT can preserve Christine's voice and tool-use habits only after a
privacy-reviewed corpus and eval baseline exist. This is later than embeddings
and routing, not the first implementation target.

## Evaluation

Evals must exist before model outputs are trusted:

- Personality preservation: Chinese tone, user-owned identity, emotional
  semantics, and direct helpfulness.
- Tool routing accuracy: choose the right deterministic subsystem without unsafe
  side effects.
- Hallucination rate: avoid false claims about files, memory, tests, formulas, or
  system state.
- Memory recall precision: cite summaries accurately and avoid leaking excluded
  raw state.
- Cross-platform safety: Windows, Linux, and macOS capability boundaries are
  respected.

Each model track needs before/after metrics. A model that cannot beat the
deterministic baseline stays advisory or disabled.

## Deployment

Modelization stays local-first:

- Keep a local registry for corpus versions, embedding indexes, model metadata,
  and eval results.
- Optional distributed inference workers may be added through the deployment
  protocol, but no cloud dependency is required for core Christine behavior.
- Remote workers receive filtered summaries or prompts, never raw excluded state.
- Health checks must expose model availability without blocking launcher startup.

## First Implementation Boundary

The first implementation is only `should_include_in_model_corpus(path)`. It does
not build embeddings, train models, read private state, or modify runtime
behavior. This keeps Task 8 reversible and gives later work a tested safety
boundary.
