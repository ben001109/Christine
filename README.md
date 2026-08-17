# Christine

Christine is a local AI desktop assistant project focused on a persistent, extensible runtime that can combine local execution, optional model integrations, memory-oriented components, desktop interaction, and modular agent-like subsystems.

> **Project status:** early alpha. The repository is actively being modularized from a large legacy runtime into smaller, testable packages. Expect breaking internal changes before a stable release.

## Why Christine exists

Christine explores what a long-running personal desktop assistant can look like when the assistant is treated as a stateful software system rather than a single chat request. Current work emphasizes:

- a persistent desktop-oriented runtime;
- modular brain and conversation-routing components;
- optional local LLM/GPU integrations;
- explicit version and release governance;
- testable extraction of functionality from the legacy monolith;
- compatibility with existing Windows launch workflows while refactoring proceeds.

## Repository layout

Key areas include:

- `boot_christine.py` — launcher and resource/bootstrap entry point;
- `christine_final.py` — legacy runtime handoff target being decomposed incrementally;
- `brain/` — extracted brain package and a primary target for modular development;
- `tests/` — regression and contract tests for extracted behavior;
- `docs/ROADMAP.md` — current development roadmap;
- `docs/VERSIONING.md` — alpha/beta/rc/release governance;
- `AGENTS.md` — repository-specific engineering and refactor rules.

Generated, persisted, backup, and recovery directories are intentionally treated conservatively during refactors. See `AGENTS.md` before making broad structural changes.

## Requirements

- Python 3.10–3.12
- `uv` for environment and dependency management
- Windows is the primary desktop target for several integration paths; some modules can still be developed and tested on other operating systems.

Optional dependency groups include GPU, local LLM, and distributed-service integrations. See `pyproject.toml` for the current dependency definitions.

## Development setup

Install or update the environment:

```bash
uv sync
```

Run the fast launcher self-check without loading Torch:

```bash
uv run python boot_christine.py --check --notorch --fast
```

Compile the primary extracted modules:

```bash
uv run python -m compileall -q -x "brain/generated" boot_christine.py brain
```

Run tests:

```bash
uv run pytest
```

## Development principles

Christine is undergoing an incremental refactor. Contributions should preserve user-owned state, persisted data, launcher compatibility, and existing behavior unless a migration is explicitly designed.

In particular:

1. prefer small, reviewable changes over broad rewrites;
2. add or preserve focused verification for behavior being moved;
3. do not hand-edit generated brain files unless the generator changes too;
4. do not remove backup, mirror, state, or recovery data as part of cleanup work;
5. keep legacy compatibility wrappers when practical while modules are extracted.

See `AGENTS.md` for the complete repository rules.

## Roadmap

The project roadmap and release stages are documented under `docs/`. The current package version is an alpha release line, and stable release semantics are intentionally not claimed yet.

## Contributing

Contributions, bug reports, architecture discussions, and focused refactor proposals are welcome. Please read `CONTRIBUTING.md` before opening a pull request.

## Security

Do not report suspected security vulnerabilities in a public issue. See `SECURITY.md`.

## License

Christine is licensed under the **Apache License 2.0**. See `LICENSE` for the full license text.
