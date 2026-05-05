"""Platform capability boundaries for Christine."""

from .base import (
    FeatureSupport,
    PlatformCapabilities,
    PlatformFeature,
    capability_matrix,
    detect_platform,
    feature_support,
    is_feature_supported,
    unsupported_message,
)

__all__ = [
    "FeatureSupport",
    "PlatformCapabilities",
    "PlatformFeature",
    "capability_matrix",
    "detect_platform",
    "feature_support",
    "is_feature_supported",
    "unsupported_message",
]
