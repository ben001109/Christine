from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import sys
from types import MappingProxyType


class PlatformFeature(str, Enum):
    AUTOSTART = "autostart"
    GLOBAL_HOTKEYS = "global_hotkeys"
    SYSTEM_AUDIO = "system_audio"
    GUI = "gui"
    TTS = "tts"
    LOCAL_LLM = "local_llm"


@dataclass(frozen=True)
class PlatformCapabilities:
    name: str
    supports_autostart: bool
    supports_global_hotkeys: bool
    supports_system_audio: bool
    supports_gui: bool


@dataclass(frozen=True)
class FeatureSupport:
    supported: bool
    detail: str


def detect_platform() -> PlatformCapabilities:
    if sys.platform.startswith("win"):
        return PlatformCapabilities("windows", True, True, True, True)
    if sys.platform == "darwin":
        return PlatformCapabilities("macos", False, False, False, True)
    if sys.platform.startswith("linux"):
        return PlatformCapabilities("linux", False, False, False, True)
    return PlatformCapabilities("unknown", False, False, False, False)


def _features(**values: FeatureSupport):
    return MappingProxyType({PlatformFeature(key): value for key, value in values.items()})


_CAPABILITY_MATRIX = MappingProxyType(
    {
        "windows": _features(
            autostart=FeatureSupport(True, "Windows Startup folder integration"),
            global_hotkeys=FeatureSupport(True, "Windows keyboard hooks"),
            system_audio=FeatureSupport(True, "pyaudiowpatch loopback audio"),
            gui=FeatureSupport(True, "Tk desktop GUI"),
            tts=FeatureSupport(False, "optional local TTS dependency not guaranteed"),
            local_llm=FeatureSupport(False, "requires external local model service"),
        ),
        "linux": _features(
            autostart=FeatureSupport(False, "Linux autostart integration is not wired yet"),
            global_hotkeys=FeatureSupport(False, "pynput/X11/Wayland support is not wired yet"),
            system_audio=FeatureSupport(False, "Windows loopback audio dependency is unavailable"),
            gui=FeatureSupport(True, "Tk desktop GUI when display is available"),
            tts=FeatureSupport(False, "local TTS dependency is optional and not guaranteed"),
            local_llm=FeatureSupport(False, "requires Ollama or another local model service"),
        ),
        "macos": _features(
            autostart=FeatureSupport(False, "macOS launch agent integration is not wired yet"),
            global_hotkeys=FeatureSupport(False, "macOS accessibility hotkeys are not wired yet"),
            system_audio=FeatureSupport(False, "macOS system audio capture is not wired yet"),
            gui=FeatureSupport(True, "Tk desktop GUI when display is available"),
            tts=FeatureSupport(False, "local TTS dependency is optional and not guaranteed"),
            local_llm=FeatureSupport(False, "requires Ollama or another local model service"),
        ),
        "unknown": _features(
            autostart=FeatureSupport(False, "unknown platform"),
            global_hotkeys=FeatureSupport(False, "unknown platform"),
            system_audio=FeatureSupport(False, "unknown platform"),
            gui=FeatureSupport(False, "unknown platform"),
            tts=FeatureSupport(False, "unknown platform"),
            local_llm=FeatureSupport(False, "unknown platform"),
        ),
    }
)


def capability_matrix():
    return _CAPABILITY_MATRIX


def unsupported_message(platform_name: str, feature: PlatformFeature) -> str:
    platform_features = _CAPABILITY_MATRIX.get(platform_name, _CAPABILITY_MATRIX["unknown"])
    support = platform_features[feature]
    if support.supported:
        return f"{platform_name}:{feature.value} 已支援"
    return f"{platform_name}:{feature.value} 尚未支援 — {support.detail}"
