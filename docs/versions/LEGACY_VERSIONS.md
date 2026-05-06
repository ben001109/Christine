# Legacy Version Labels

This inventory keeps old Christine version-like labels visible while the project
moves to `christine.versioning` and `docs/VERSIONING.md`.

These labels are not public release governance. They are historical/runtime
identifiers that must stay stable until a focused migration proves the related
display, cache, persisted-state, or subsystem behavior is preserved.

## Active Labels

| Name | Value | Kind | Source | Notes |
| --- | --- | --- | --- | --- |
| `pyproject.version` | `0.1.0` | package metadata | `pyproject.toml` | Package metadata, not release-stage governance. |
| `CHRISTINE_VERSION` | `600.0-final-agi-opus` | monolith public label | `christine_final.py` | Legacy monolith display/runtime label. |
| `V42_VERSION` | `7.2-persistent-brain` | subsystem label | `christine_final.py` | V42 persistent brain label. |
| `V42_NEURAL_VERSION` | `42.2-true-intelligence` | subsystem label | `christine_final.py` | V42 neural brain label. |
| `V42_PROMETHEUS_VERSION` | `42.3-prometheus` | subsystem label | `christine_final.py` | Prometheus subsystem label. |
| `V42_ATLAS_VERSION` | `42.4-atlas` | subsystem label | `christine_final.py` | Atlas subsystem label. |
| `V42_CORTEX_VERSION` | `42.5-cortex` | subsystem label | `christine_final.py` | Cortex subsystem label. |
| `V42_AGI_VERSION` | `42.6-agi-cognitive` | subsystem label | `christine_final.py` | AGI cognitive label. |
| `V42_AGI2_VERSION` | `42.7-agi-phase2` | subsystem label | `christine_final.py` | AGI phase 2 label. |
| `V42_PHASE3_VERSION` | `42.8-mega-cortex` | subsystem label | `christine_final.py` | Mega Cortex phase label. |
| `V42_HERMES_VERSION` | `42.8-titan` | subsystem label | `christine_final.py` | Hermes/Titan label. |
| `V42_PHASE4_VERSION` | `42.9-proto-agi` | subsystem label | `christine_final.py` | Proto-AGI phase label. |
| `V58_VERSION` | `58.0-sentient-memory-authority` | subsystem label | `christine_final.py` | V58 memory authority label. |
| `V60_VERSION` | `60.0-true-agi-core` | subsystem label | `christine_final.py` | V60 AGI core label. |
| `_V70_VERSION` | `70.0-sovereign-agi` | subsystem label | `christine_final.py` | V70 sovereign AGI label. |
| `_OMEGA_CACHE_VERSION` | `v12.3-turbo-full-v2` | cache schema | `christine_final.py` | Cache invalidation label. |
| `_V42_NEURAL_VERSION` | `v2.0-GPU-89.07%` | runtime label | `christine_final.py` | Runtime neural engine label. |
| `V2000_SKILL_COMPILER_VERSION` | `2000.0-singularity` | runtime label | `christine_final.py` | Inline skill compiler label. |
| `V2499_SKILL_COMPILER_VERSION` | `2499.0-beyond-singularity` | runtime label | `christine_final.py` | Inline advanced skill compiler label. |

## Inactive Historical Labels

| Name | Value | Kind | Source | Notes |
| --- | --- | --- | --- | --- |
| `CHRISTINE_VERSION_PROMETHEUS_COMMENT` | `4.2-prometheus` | commented history | `christine_final.py` | Historical commented label. |
| `CHRISTINE_VERSION_ATLAS_COMMENT` | `4.2-atlas` | commented history | `christine_final.py` | Historical commented label. |
| `CHRISTINE_VERSION_CONTEXTUAL_COMMENT` | `12.9-contextual` | commented history | `christine_final.py` | Historical commented label. |

## Migration Rule

Do not rewrite these values in place just to make them look like modern
versions. First add or update a `LegacyVersionRecord`, document the migration,
then change one subsystem at a time with tests covering the old behavior.
