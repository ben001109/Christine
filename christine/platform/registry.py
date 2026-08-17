"""Content-free platform identity and capability registry.

The registry deliberately exposes only the portable platform family and the
capabilities already declared by :mod:`christine.platform.base`.  It does not
collect host names, paths, environment variables, or runtime diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from types import MappingProxyType
from typing import Mapping

from .base import PlatformFeature, is_feature_supported


_SYS_PLATFORM_NAMES = MappingProxyType(
    {
        "win32": "windows",
        "cygwin": "windows",
        "msys": "windows",
        "darwin": "macos",
        "linux": "linux",
    }
)
_KNOWN_PLATFORM_NAMES = frozenset({"windows", "macos", "linux", "unknown"})


@dataclass(frozen=True)
class PlatformIdentity:
    """The safe, normalized identity used in native evidence."""

    name: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name}


def platform_identity(sys_platform: str | None = None) -> PlatformIdentity:
    """Return a normalized family without preserving an unrecognized input."""

    value = sys.platform if sys_platform is None else sys_platform
    return PlatformIdentity(name=_SYS_PLATFORM_NAMES.get(value, "unknown"))


def capability_mapping(identity: PlatformIdentity | str) -> Mapping[str, bool]:
    """Return the declared capability flags for a normalized platform identity."""

    name = identity.name if isinstance(identity, PlatformIdentity) else identity
    normalized_name = name if name in _KNOWN_PLATFORM_NAMES else "unknown"
    return MappingProxyType(
        {
            feature.value: is_feature_supported(normalized_name, feature)
            for feature in PlatformFeature
        }
    )
