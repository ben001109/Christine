# Christine Versioning Policy

Christine uses SemVer-compatible public versions with explicit prerelease
stages:

```text
MAJOR.MINOR.PATCH[-alpha.N|-beta.N|-rc.N]
```

Stable releases have no suffix. The stage flow is:

```text
alpha -> beta -> rc -> release
```

## Version Format

- `MAJOR` changes when compatibility or persisted-data expectations change.
- `MINOR` changes when a new user-visible capability or major internal boundary
  lands without breaking the current release line.
- `PATCH` changes for bug fixes, test hardening, documentation corrections, and
  safe internal refactors.
- `alpha.N`, `beta.N`, and `rc.N` use positive integer counters starting at `1`.
- `Release` versions are stable public builds and must not include a prerelease
  number or suffix.

## Stage Rules

- Alpha builds are for internal experiments and unstable integration. Behavior
  may change, but runtime-state safety rules still apply.
- Beta builds are feature-complete candidates. Prefer bug fixes,
  compatibility fixes, documentation, and verification hardening; add new scope
  only with explicit approval.
- RC builds are release candidates. Only blocker fixes, data-safety fixes, and
  verification updates should land.
- Release builds are tagged stable builds. Do not make direct breaking changes
  on a release without starting a new alpha cycle or an explicit hotfix path.

## Required Workflow

- Any commit, branch, or PR that changes the public target version must state the
  target version and stage.
- Promote stages only in order: `alpha -> beta -> rc -> release`.
- Increment prerelease counters within the same stage with `next_prerelease()`.
- Use `promote_stage()` when moving to the next stage.
- Keep version validation in `christine.versioning`.
- Keep package metadata in `pyproject.toml`; do not treat legacy monolith
  constants such as `CHRISTINE_VERSION` as the source of truth for release
  governance.

## Current Mechanism

- `christine.versioning.ChristineVersion` stores a validated version.
- `christine.versioning.VersionStage` defines `alpha`, `beta`, `rc`, and
  `release`.
- `parse_version()` reads public version strings.
- `next_prerelease()` increments `alpha.N`, `beta.N`, or `rc.N`.
- `promote_stage()` moves `alpha -> beta -> rc -> release`.

## Legacy Version Labels

Older Christine builds contain many monolith, subsystem, cache, and runtime
labels that look like versions but are not release-governance versions. These
labels are tracked in `LEGACY_VERSION_RECORDS` and summarized in
`docs/versions/LEGACY_VERSIONS.md`.

- Legacy labels are historical/runtime identifiers, not public release versions.
- New public versions must use `ChristineVersion` and the stage rules above.
- Do not rewrite active legacy labels unless a migration plan covers user-facing
  display text, cache behavior, persisted state, and boot/runtime semantics.
- Every newly discovered legacy version label must be added to
  `LEGACY_VERSION_RECORDS` and `docs/versions/LEGACY_VERSIONS.md` before it is
  renamed, removed, or reinterpreted.
- Treat commented historical labels as audit records; they may be documented as
  inactive, but should not be used for release decisions.
