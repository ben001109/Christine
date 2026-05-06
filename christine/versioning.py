from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class VersionStage(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    RELEASE = "release"


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
