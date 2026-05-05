"""Platform capability boundaries for Christine."""

from .base import (
    FeatureSupport,
    PlatformCapabilities,
    PlatformFeatureRequirement,
    PlatformFeature,
    capability_matrix,
    detect_platform,
    feature_support,
    is_feature_supported,
    require_platform_feature,
    unsupported_message,
)

__all__ = [
    "FeatureSupport",
    "PlatformCapabilities",
    "PlatformFeatureRequirement",
    "PlatformFeature",
    "capability_matrix",
    "detect_platform",
    "feature_support",
    "is_feature_supported",
    "require_platform_feature",
    "unsupported_message",
]
