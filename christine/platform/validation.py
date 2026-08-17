"""Validation for the content-free native platform-evidence schema."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


EVIDENCE_SCHEMA_VERSION = 1
EVIDENCE_KIND = "christine.platform.native-evidence"
_PLATFORM_NAMES = frozenset({"windows", "macos", "linux", "unknown"})
_CAPABILITY_NAMES = frozenset(
    {"autostart", "global_hotkeys", "system_audio", "gui", "tts", "local_llm"}
)
_PROVENANCE = {"source": "native-capability-registry", "mode": "native"}
_FIXTURE_PROVENANCE = {"source": "native-capability-registry", "mode": "fixture"}


class EvidenceValidationError(ValueError):
    """A generic error which never repeats untrusted evidence content."""

    def __init__(self) -> None:
        super().__init__("invalid platform evidence")


def _invalid() -> None:
    raise EvidenceValidationError()


def validate_native_evidence(document: Mapping[str, Any]) -> None:
    """Ensure *document* has exactly the portable, payload-free v1 schema."""

    if not isinstance(document, Mapping) or set(document) != {
        "schema_version",
        "kind",
        "identity",
        "capabilities",
        "provenance",
    }:
        _invalid()
    if type(document["schema_version"]) is not int or document["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        _invalid()
    if document["kind"] != EVIDENCE_KIND:
        _invalid()

    identity = document["identity"]
    if not isinstance(identity, Mapping) or set(identity) != {"name"} or identity["name"] not in _PLATFORM_NAMES:
        _invalid()

    capabilities = document["capabilities"]
    if not isinstance(capabilities, Mapping) or set(capabilities) != _CAPABILITY_NAMES:
        _invalid()
    if not all(type(value) is bool for value in capabilities.values()):
        _invalid()

    provenance = document["provenance"]
    if not isinstance(provenance, Mapping) or dict(provenance) not in (_PROVENANCE, _FIXTURE_PROVENANCE):
        _invalid()
