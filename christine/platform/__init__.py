"""Platform capability boundaries for Christine."""

from .base import (
    FeatureSupport,
    PlatformCapabilities,
    PlatformFeature,
    capability_matrix,
    detect_platform,
    unsupported_message,
)

__all__ = [
    "FeatureSupport",
    "PlatformCapabilities",
    "PlatformFeature",
    "capability_matrix",
    "detect_platform",
    "unsupported_message",
]
