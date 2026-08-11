# Contributing to Christine

Thank you for contributing to Christine. The project is in an early alpha refactor stage, so the main goal is to improve the codebase without losing existing behavior or user-owned state.

## Start with the repository rules

Read `AGENTS.md` before making a substantial change. It documents the supported commands, current architecture, refactor protocol, generated-code boundaries, persisted-state rules, and release process.

## Development setup

Christine uses `uv` for Python dependency and environment management:

```bash
uv sync
```

Useful verification commands include:

```bash
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain
uv run python boot_christine.py --check --notorch --fast
uv run pytest
```

Run the narrowest relevant check for your change. Some integrations are hardware- or Windows-dependent, so document any checks you cannot run locally.

## Good contribution scope

Prefer contributions that are:

- focused and reviewable;
- backed by a regression test or contract check when behavior changes;
- compatible with existing entry points and persisted data;
- explicit about any optional dependency or platform requirement;
- incremental when extracting code from `christine_final.py`.

Avoid broad cleanup PRs that delete state, backup, mirror, generated, or recovery material.

## Issues and feature proposals

For bugs, provide reproducible steps, expected behavior, actual behavior, platform details, and logs where safe.

For architecture or feature changes, describe the problem being solved and identify the smallest stable seam for implementation. Large monolith rewrites should be split into independently verifiable stages.

## Pull requests

Pull requests should include:

- a concise summary and rationale;
- affected modules and entry points;
- verification commands and results;
- compatibility or migration notes;
- platform/hardware limitations, if any;
- versioning implications when the change affects a public release stage.

## Security

Do not publish suspected vulnerabilities in a public issue. See `SECURITY.md`.

## Licensing

A repository-wide open-source license has not yet been selected. Do not copy third-party code into the repository unless its license and attribution requirements are clearly understood and documented.