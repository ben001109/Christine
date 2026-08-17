# Native platform-evidence substrate (PR-2)

## Scope

This slice adds a small, local-only evidence contract built from the existing
platform capability matrix.  It is deliberately not a GUI probe, release gate,
package check, workflow, parity check, or model/state inspection feature.

The schema is versioned and content-free.  It records only a normalized platform
family, declared boolean capability flags, and fixed collector provenance.  It
must not record host names, account names, paths, environment variables,
diagnostics, application state, or user content.

## Contract

- `PlatformIdentity` normalizes a runtime platform value to `windows`, `macos`,
  `linux`, or `unknown`; unknown input is not preserved.
- `PlatformEvidence` serializes to the exact v1 schema and is validated before
  serialization or digesting.
- `write_evidence_atomically` stages a complete document beside its destination
  and replaces it atomically.  A failed write returns a generic receipt and
  leaves an existing destination untouched.
- `tools/collect_platform_evidence.py --dry-run --fixture` emits a deterministic
  fixture without observing the host.  `--run-suite` runs only the approved
  platform slice targets.

## Verification boundary

The evidence proves only what the declared native capability registry says for
one normalized platform family.  It does not prove native GUI behavior,
five-platform execution, release qualification, CI status, or model quality.
