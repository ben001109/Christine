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
from .evidence import EvidenceProvenance, EvidenceReceipt, PlatformEvidence, collect_native_evidence, write_evidence_atomically
from .registry import PlatformIdentity, capability_mapping, platform_identity
from .validation import EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceValidationError, validate_native_evidence

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
    "EVIDENCE_KIND",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceProvenance",
    "EvidenceReceipt",
    "EvidenceValidationError",
    "PlatformEvidence",
    "PlatformIdentity",
    "capability_mapping",
    "collect_native_evidence",
    "platform_identity",
    "validate_native_evidence",
    "write_evidence_atomically",
]
