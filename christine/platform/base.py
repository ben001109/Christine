from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class PlatformCapabilities:
    name: str
    supports_autostart: bool
    supports_global_hotkeys: bool
    supports_system_audio: bool
    supports_gui: bool


def detect_platform() -> PlatformCapabilities:
    if sys.platform.startswith("win"):
        return PlatformCapabilities("windows", True, True, True, True)
    if sys.platform == "darwin":
        return PlatformCapabilities("macos", False, False, False, True)
    if sys.platform.startswith("linux"):
        return PlatformCapabilities("linux", False, False, False, True)
    return PlatformCapabilities("unknown", False, False, False, False)
