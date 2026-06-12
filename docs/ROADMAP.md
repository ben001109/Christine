# Christine Roadmap

Current development line: `0.2.0-alpha.1`

This roadmap turns the existing `docs/plans/` implementation notes into a
single status tracker. It is intentionally conservative: old plans do not carry
machine-readable status, so this document tracks only what is visible in the
current codebase, tests, and recently completed slices.

## Status Legend

- Done: implemented, merged, pushed, and covered by current verification.
- Active: next work expected in the current alpha line.
- Planned: accepted direction, not yet implemented as a live runtime feature.
- Blocked: requires explicit approval, external input, hardware, legal review,
  privacy review, or a migration/backup plan.

## Refactor Rules

- Keep `boot_christine.py`, `christine_final.py`, and Windows launchers working.
- Use strangler-style extraction: add tested modules around stable seams first,
  then route legacy code through them.
- Preserve Chinese user-facing wording, personality, memory behavior, emotional
  semantics, and existing launch behavior.
- Do not change persisted data formats without a migration plan and backup
  strategy.
- Keep live routing/tool/GUI/worker side effects disabled or permission-gated
  until tests and policies prove the path safe.
- Use `uv` for Python environment and verification commands.

## Progress Snapshot

- Tracked implementation plan documents: 40.
- Active stage: alpha hardening.
- Completed foundation slices: version governance, package metadata alignment,
  runtime health/version display, platform gates, model factory safety gates,
  disabled runtime route observation, observed ask routing helper, and V10 tool
  result formatting boundary.
- Remaining estimate: 7 major milestones and roughly 30-45 small slices.

## Milestone M0: Alpha Foundation Governance

Status: Done.

Completed scope:
- Public version governance is centered on `christine.versioning`.
- Package metadata is aligned to `0.2.0a1` for the active `0.2.0-alpha.1` line.
- Runtime Health shows version information and optional dependency degradation.
- Legacy version labels are tracked separately from public release governance.
- Platform capability and unavailable-result boundaries exist.
- Linux/macOS autostart paths return structured unavailable responses while
  Windows behavior remains preserved.
- Model Factory safety boundaries exist for source policy, dataset records,
  evaluation gates, provider records, and artifact path safety.

Verification references:
- `docs/VERSIONING.md`
- `docs/versions/LEGACY_VERSIONS.md`
- `docs/model_factory/README.md`
- `tests/test_boot_contract.py`
- `tests/test_platform_runtime_gates.py`
- `tests/test_modelization_*.py`

## Milestone M1: Monolith Seam Hardening

Status: Active.

Goal: keep the monolith running while moving stable, testable behavior into
small modules.

Completed M1 slices:
- V10 tool schema dedupe delegates to `christine.conversation.router`.
- V1484 ask observation remains disabled and best-effort only.
- V1484 observe -> voice -> hint -> fallback orchestration delegates to
  `route_observed_voice_then_fallback()`.
- V10 tool return formatting delegates to
  `christine.tools.dispatch.format_tool_result_message()`.
- V10 tool execution lookup, fallback aliases, and error shaping delegate to
  `christine.tools.dispatch.execute_tool_handler()`.
- V10 prompt and recent-message context assembly delegates to
  `christine.conversation.context`.
- V10 tool-use loop block processing delegates to a runtime-tested helper.
- GUI command listener loops delegate to `christine.gui.commands`.
- Legacy five-tensor formula runtime dependency audit is codified in
  `christine.runtime.formula_audit`.
- V10 session turn recording delegates to `christine.conversation.session`.

Remaining M1 slices:
- Continue migrating remaining historical ask wrappers and memory tool writes to
  session/memory boundaries without changing persisted formats.
- Extract audio/voice availability and fallback boundaries for non-Windows
  environments.

Estimated remaining M1 effort: 7-13 small slices.

Exit criteria:
- V10/V1484 ask paths still answer through the same wrapper chain.
- Tool execution, prompt construction, memory updates, GUI queue handling, and
  audio fallbacks each have focused tests that do not import `christine_final.py`.
- Boot smoke and full tests pass on merged `main`.

## Milestone M2: Tool, Agent, And Routing Safety

Status: Planned.

Goal: make side-effectful capabilities explicit, auditable, and permission-gated
before any autonomous or policy-driven dispatch is enabled.

Planned slices:
- Add a permission decision object for tools, GUI, worker, file, network, and OS
  actions.
- Add side-effect classification for existing tool schemas and handlers.
- Keep policy routing eval-only until route metrics and permission gates pass.
- Add local, ephemeral runtime routing diagnostics without writing persistent
  state by default.
- Add mocked runtime tests for tool loops and routing decisions instead of only
  static guards.
- Define an agent plan -> execute -> verify loop that can run in dry-run mode
  before touching side-effect targets.

Estimated effort: 5-8 small slices.

Exit criteria:
- No live tool/GUI/worker route can run without an explicit policy decision.
- Route policy remains disabled by default unless a later milestone explicitly
  promotes it.
- Tests prove rejected, dry-run, and allowed paths.

## Milestone M3: Local-First Intelligence

Status: Planned.

Goal: make Christine useful without depending on a cloud model while preserving
Claude/API fallback as an optional route.

Planned slices:
- Formalize a local LLM provider interface for Ollama or compatible runtimes.
- Define fallback order: local-first where appropriate, cloud fallback only when
  configured and safe.
- Extract retrieval and context assembly into tested modules.
- Add repository/document retrieval eval fixtures.
- Add memory quality tests before expanding long-term memory usage.
- Keep Model Factory training disabled until legal source, privacy, and eval
  gates are satisfied.

Estimated effort: 5-8 small slices.

Blocked items:
- Real LoRA/QLoRA training requires explicit approval, legal dataset review,
  privacy review, hardware/runtime decision, and eval gates.
- No model artifacts, datasets, checkpoints, eval outputs, or weights should be
  committed.

## Milestone M4: GUI And Productization

Status: Planned.

Goal: turn the current runtime into a reliable desktop product without breaking
current launchers or user-facing behavior.

Planned slices:
- Extract remaining GUI app/theme/window seams.
- Add GUI command loop tests around queue processing.
- Preserve and test Windows launcher behavior.
- Add install/start/check documentation for Windows, Linux, and macOS.
- Add backup/recovery UX for user-owned state.

Estimated effort: 4-7 small slices.

Exit criteria:
- Launchers still work as entry points.
- Non-Windows platforms fail gracefully for unavailable desktop features.
- User-owned state has documented backup and recovery paths.

## Milestone M5: Reliability, Security, And State Safety

Status: Planned.

Goal: make release candidates safe to run on real user machines.

Planned slices:
- Add persisted-state inventory and backup policy.
- Add migration policy before any state format change.
- Audit tool/network/file/OS side effects.
- Add optional dependency and platform matrix checks.
- Add release validation checklist.

Estimated effort: 4-6 small slices.

Exit criteria:
- Every state-changing feature has a rollback or backup story.
- Privacy-sensitive sources are excluded from training and diagnostics unless
  explicitly reviewed.
- Full test, compile, and boot smoke checks are required before release-stage
  promotion.

## Milestone M6: Beta Readiness

Status: Planned.

Goal: freeze the feature set for `0.2.0-beta.1` and focus on correctness.

Promotion requirements:
- M1 monolith seam hardening has no known critical runtime seams left without a
  safe boundary.
- M2 side-effect permission gates are in place.
- M3 local-first provider and retrieval seams exist, even if advanced training
  remains disabled.
- M4 launcher/product docs exist.
- M5 state and privacy policies exist.

Allowed beta work:
- Bug fixes.
- Compatibility fixes.
- Documentation.
- Verification hardening.

Estimated effort from current state: about 30-45 small slices total across M1-M5.

## Milestone M7: RC And Stable Release

Status: Planned.

Goal: ship a stable `0.2.0` release after beta validation.

RC requirements:
- Only blocker fixes, data-safety fixes, and verification updates land.
- Release notes list known degraded optional capabilities.
- Tags and version promotion follow `docs/VERSIONING.md`.
- Boot smoke, compile check, full tests, and launcher checks pass on the release
  branch.

Stable release requirements:
- `CURRENT_VERSION` promotes through `alpha -> beta -> rc -> release` without
  skipping stages unless explicitly approved.
- Public docs describe install, launch, recovery, limitations, and optional
  dependencies.

## Immediate Next Slices

Recommended order:

## Tracking Notes

- This file is the roadmap tracker.
- Detailed task plans still live under `docs/plans/`.
- When a slice is merged, update the relevant milestone status and the remaining
  slice estimate.
