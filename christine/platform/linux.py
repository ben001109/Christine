from .base import PlatformCapabilities, platform_availability


def _unavailable(feature: str) -> str:
    return platform_availability("linux", feature).as_text()


def setup_autostart(*args, **kwargs) -> str:
    return _unavailable("autostart")


def autostart_status(*args, **kwargs) -> str:
    return _unavailable("autostart")


CAPABILITIES = PlatformCapabilities("linux", False, False, False, True)
