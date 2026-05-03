# Christine Agent Guide

This file applies to the whole repository.

## Project Priority

Christine is a high-value personal AI desktop assistant. Treat the project as
stateful, user-owned, and emotionally important. Prefer safe, reversible,
incremental changes over broad rewrites.

## Package Management

- Use `uv` for all Python environment and dependency work.
- Do not use `pip install` directly. Use `uv add <package>` or
  `uv add --dev <package>`.
- Run commands through `uv run` when possible.
- Keep dependency changes in `pyproject.toml` and the `uv.lock` file once a lock
  file is generated.

## Common Commands

- Create or update the environment: `uv sync`
- Add runtime dependency: `uv add <package>`
- Add development dependency: `uv add --dev <package>`
- Fast launcher smoke check: `uv run python boot_christine.py --check --notorch --fast`
- Full launcher self-check without torch loading: `uv run python boot_christine.py --check --notorch`
- Start Christine: `uv run python boot_christine.py`
- Compile focused modules: `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain`
- Run tests when present: `uv run pytest`

## Current Architecture

- `boot_christine.py` is the launcher and hardware/resource budget bootstrapper.
- `christine_final.py` is the large legacy monolith and current runtime handoff
  target.
- `brain/` contains the extracted brain package and should be the first target
  for focused tests and modular improvements.
- `brain/generated/` contains generated MegaCortex area files. Do not hand-edit
  generated files unless the generator is being changed too.
- `data/`, `level5_logs/`, `growth.log`, `heartbeat.txt`, and
  `nexus_v2_state.json` are runtime/state artifacts. Do not delete or rewrite
  them without explicit user approval.
- `.bat` and `.ps1` files are user-facing Windows launchers. Preserve their
  behavior unless the task explicitly changes launch behavior.
- `backups/`, `mirrors/`, and `self_replicas/` may contain recovery copies. Do
  not remove them during refactors.

## Refactor Protocol

- Start every substantial refactor by identifying the behavior that must be
  preserved and adding a focused smoke test or compile check for it.
- Keep changes small and reviewable. Avoid large all-at-once rewrites of
  `christine_final.py`.
- Extract stable pieces from the monolith into modules only when there is a
  clear seam and a verification command.
- Preserve existing entry points: `boot_christine.py`, `christine_final.py`, and
  the Windows launcher scripts.
- Do not change persisted data formats without a migration plan and a backup
  strategy.
- Do not remove Chinese user-facing wording, personality, memory behavior, or
  emotional semantics unless the user explicitly requests it.
- Prefer compatibility wrappers over breaking imports while the monolith is
  being decomposed.

## Coding Standards

- Target Python 3.10+.
- New code should avoid import-time side effects where practical.
- Handle optional dependencies gracefully. Many runtime features are hardware or
  Windows dependent.
- Keep comments short and useful. Explain non-obvious decisions, not obvious
  assignments.
- Use pathlib for new filesystem code unless integrating with existing `os.path`
  code.
- Avoid broad exception swallowing in new code. If existing code swallows
  exceptions, do not expand that pattern without a reason.

## Verification

- Before claiming a change is complete, run the narrowest relevant command.
- For launcher or brain changes, prefer:
  `uv run python -m compileall -q -x "brain/generated" boot_christine.py brain`
- For behavior touching boot flow, run:
  `uv run python boot_christine.py --check --notorch --fast`
- If a command cannot be run on this OS or hardware, state that clearly in the
  final response.

## Documentation

- Put refactor designs and implementation plans in `docs/plans/`.
- Update this file when commands, entry points, or refactor rules change.
