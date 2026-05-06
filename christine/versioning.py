from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class VersionStage(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    RELEASE = "release"


class LegacyVersionKind(str, Enum):
    PACKAGE_METADATA = "package_metadata"
    MONOLITH_PUBLIC_LABEL = "monolith_public_label"
    SUBSYSTEM_LABEL = "subsystem_label"
    CACHE_SCHEMA = "cache_schema"
    RUNTIME_LABEL = "runtime_label"
    COMMENTED_HISTORY = "commented_history"


_NUMERIC_ID = r"(?:0|[1-9]\d*)"
_PRERELEASE_NUMBER = r"(?:[1-9]\d*)"
_VERSION_RE = re.compile(
    rf"^({_NUMERIC_ID})\.({_NUMERIC_ID})\.({_NUMERIC_ID})(?:-(alpha|beta|rc)\.({_PRERELEASE_NUMBER}))?$"
)


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class ChristineVersion:
    major: int
    minor: int
    patch: int
    stage: VersionStage = VersionStage.RELEASE
    prerelease: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage, VersionStage):
            raise ValueError("version stage must be alpha, beta, rc, or release")
        if not all(_is_plain_int(value) for value in (self.major, self.minor, self.patch)):
            raise ValueError("version numbers must be integers")
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("version numbers must be non-negative")
        if self.stage == VersionStage.RELEASE:
            if self.prerelease is not None:
                raise ValueError("release versions must not have prerelease numbers")
            return
        if self.prerelease is None:
            raise ValueError("prerelease versions require a positive number")
        if not _is_plain_int(self.prerelease):
            raise ValueError("prerelease number must be an integer")
        if self.prerelease <= 0:
            raise ValueError("prerelease versions require a positive number")

    @property
    def public(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.stage == VersionStage.RELEASE:
            return base
        return f"{base}-{self.stage.value}.{self.prerelease}"


def parse_version(text: str) -> ChristineVersion:
    match = _VERSION_RE.match(str(text or ""))
    if not match:
        raise ValueError(f"invalid Christine version: {text}")
    major, minor, patch, stage, prerelease = match.groups()
    if stage is None:
        return ChristineVersion(int(major), int(minor), int(patch), VersionStage.RELEASE)
    return ChristineVersion(int(major), int(minor), int(patch), VersionStage(stage), int(prerelease))


def next_prerelease(version: ChristineVersion) -> ChristineVersion:
    if version.stage == VersionStage.RELEASE:
        raise ValueError("release versions cannot have prerelease increments")
    return ChristineVersion(
        version.major,
        version.minor,
        version.patch,
        version.stage,
        (version.prerelease or 0) + 1,
    )


def promote_stage(version: ChristineVersion) -> ChristineVersion:
    if version.stage == VersionStage.ALPHA:
        return ChristineVersion(version.major, version.minor, version.patch, VersionStage.BETA, 1)
    if version.stage == VersionStage.BETA:
        return ChristineVersion(version.major, version.minor, version.patch, VersionStage.RC, 1)
    if version.stage == VersionStage.RC:
        return ChristineVersion(version.major, version.minor, version.patch, VersionStage.RELEASE)
    raise ValueError("release versions cannot be promoted")


@dataclass(frozen=True)
class LegacyVersionRecord:
    name: str
    value: str
    source: str
    kind: LegacyVersionKind
    note: str
    active: bool = True
    governs_public_release: bool = False


LEGACY_VERSION_RECORDS: tuple[LegacyVersionRecord, ...] = (
    LegacyVersionRecord(
        "pyproject.version",
        "0.1.0",
        "pyproject.toml",
        LegacyVersionKind.PACKAGE_METADATA,
        "Package metadata version; not the release-stage governance source.",
    ),
    LegacyVersionRecord(
        "CHRISTINE_VERSION",
        "600.0-final-agi-opus",
        "christine_final.py",
        LegacyVersionKind.MONOLITH_PUBLIC_LABEL,
        "Legacy monolith display/runtime label retained for compatibility.",
    ),
    LegacyVersionRecord("V42_VERSION", "7.2-persistent-brain", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "V42 persistent brain subsystem label."),
    LegacyVersionRecord("V42_NEURAL_VERSION", "42.2-true-intelligence", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "V42 neural brain subsystem label."),
    LegacyVersionRecord("V42_PROMETHEUS_VERSION", "42.3-prometheus", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Prometheus subsystem label."),
    LegacyVersionRecord("V42_ATLAS_VERSION", "42.4-atlas", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Atlas subsystem label."),
    LegacyVersionRecord("V42_CORTEX_VERSION", "42.5-cortex", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Cortex subsystem label."),
    LegacyVersionRecord("V42_AGI_VERSION", "42.6-agi-cognitive", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "AGI cognitive subsystem label."),
    LegacyVersionRecord("V42_AGI2_VERSION", "42.7-agi-phase2", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "AGI phase 2 subsystem label."),
    LegacyVersionRecord("V42_PHASE3_VERSION", "42.8-mega-cortex", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Mega Cortex phase label."),
    LegacyVersionRecord("V42_HERMES_VERSION", "42.8-titan", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Hermes/Titan subsystem label."),
    LegacyVersionRecord("V42_PHASE4_VERSION", "42.9-proto-agi", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "Proto-AGI phase label."),
    LegacyVersionRecord("V58_VERSION", "58.0-sentient-memory-authority", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "V58 memory authority subsystem label."),
    LegacyVersionRecord("V60_VERSION", "60.0-true-agi-core", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "V60 AGI core subsystem label."),
    LegacyVersionRecord("_V70_VERSION", "70.0-sovereign-agi", "christine_final.py", LegacyVersionKind.SUBSYSTEM_LABEL, "V70 sovereign AGI subsystem label."),
    LegacyVersionRecord("_OMEGA_CACHE_VERSION", "v12.3-turbo-full-v2", "christine_final.py", LegacyVersionKind.CACHE_SCHEMA, "Omega cache schema invalidation label."),
    LegacyVersionRecord("_V42_NEURAL_VERSION", "v2.0-GPU-89.07%", "christine_final.py", LegacyVersionKind.RUNTIME_LABEL, "Runtime neural engine label with accuracy note."),
    LegacyVersionRecord("V2000_SKILL_COMPILER_VERSION", "2000.0-singularity", "christine_final.py", LegacyVersionKind.RUNTIME_LABEL, "Inline skill compiler runtime label."),
    LegacyVersionRecord("V2499_SKILL_COMPILER_VERSION", "2499.0-beyond-singularity", "christine_final.py", LegacyVersionKind.RUNTIME_LABEL, "Inline advanced skill compiler runtime label."),
    LegacyVersionRecord("CHRISTINE_VERSION_PROMETHEUS_COMMENT", "4.2-prometheus", "christine_final.py", LegacyVersionKind.COMMENTED_HISTORY, "Commented historical CHRISTINE_VERSION label.", active=False),
    LegacyVersionRecord("CHRISTINE_VERSION_ATLAS_COMMENT", "4.2-atlas", "christine_final.py", LegacyVersionKind.COMMENTED_HISTORY, "Commented historical CHRISTINE_VERSION label.", active=False),
    LegacyVersionRecord("CHRISTINE_VERSION_CONTEXTUAL_COMMENT", "12.9-contextual", "christine_final.py", LegacyVersionKind.COMMENTED_HISTORY, "Commented historical CHRISTINE_VERSION label.", active=False),
)


def legacy_version_records(*, active_only: bool = False) -> tuple[LegacyVersionRecord, ...]:
    if active_only:
        return tuple(record for record in LEGACY_VERSION_RECORDS if record.active)
    return LEGACY_VERSION_RECORDS


def legacy_version_by_name(name: str) -> LegacyVersionRecord:
    for record in LEGACY_VERSION_RECORDS:
        if record.name == name:
            return record
    raise KeyError(name)
