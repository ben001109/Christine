"""Platform capability boundaries for Christine."""

from .base import (
    FeatureSupport,
    PlatformAvailability,
    PlatformCapabilities,
    PlatformFeatureRequirement,
    PlatformFeature,
    capability_matrix,
    detect_platform,
    feature_support,
    is_feature_supported,
    platform_availability,
    require_platform_feature,
    unsupported_message,
)

__all__ = [
    "FeatureSupport",
    "PlatformAvailability",
    "PlatformCapabilities",
    "PlatformFeatureRequirement",
    "PlatformFeature",
    "capability_matrix",
    "detect_platform",
    "feature_support",
    "is_feature_supported",
    "platform_availability",
    "require_platform_feature",
    "unsupported_message",
]
