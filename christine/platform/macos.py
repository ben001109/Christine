from .base import PlatformCapabilities, platform_availability


def _unavailable(feature: str) -> str:
    return platform_availability("macos", feature).as_text()


def setup_autostart(*args, **kwargs) -> str:
    return _unavailable("autostart")


def autostart_status(*args, **kwargs) -> str:
    return _unavailable("autostart")


CAPABILITIES = PlatformCapabilities("macos", False, False, False, True)
