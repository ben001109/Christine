"""Portable evidence documents and atomic, content-free write receipts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .registry import capability_mapping, platform_identity
from .validation import EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceValidationError, validate_native_evidence


@dataclass(frozen=True)
class EvidenceProvenance:
    """Fixed provenance values; no host-specific or user-supplied metadata."""

    source: str = "native-capability-registry"
    mode: str = "native"

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "mode": self.mode}


@dataclass(frozen=True)
class PlatformEvidence:
    """A serializable native capability declaration with no content payload."""

    identity: str
    capabilities: Mapping[str, bool]
    provenance: EvidenceProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "kind": EVIDENCE_KIND,
            "identity": {"name": self.identity},
            "capabilities": dict(self.capabilities),
            "provenance": self.provenance.to_dict(),
        }

    def to_json(self) -> str:
        document = self.to_dict()
        validate_native_evidence(document)
        return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


@dataclass(frozen=True)
class EvidenceReceipt:
    """The result of one atomic attempt, without paths or exception details."""

    status: str
    digest: str

    def to_dict(self) -> dict[str, str | int]:
        return {"schema_version": 1, "status": self.status, "digest": self.digest}


def collect_native_evidence(sys_platform: str | None = None, *, fixture: bool = False) -> PlatformEvidence:
    """Collect only registry-backed evidence; ``fixture`` avoids host detection."""

    identity = platform_identity("linux" if fixture else sys_platform)
    mode = "fixture" if fixture else "native"
    return PlatformEvidence(
        identity=identity.name,
        capabilities=capability_mapping(identity),
        provenance=EvidenceProvenance(mode=mode),
    )


def evidence_digest(document: Mapping[str, Any]) -> str:
    """Return a deterministic digest after schema validation."""

    try:
        validate_native_evidence(document)
        serialized = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (EvidenceValidationError, TypeError, ValueError):
        raise EvidenceValidationError() from None
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def write_evidence_atomically(destination: str | Path, evidence: PlatformEvidence) -> EvidenceReceipt:
    """Write a complete document or leave the previous destination untouched.

    Storage failures are represented by a generic receipt so exception text and
    user-controlled destination strings never leak through this boundary.
    """

    try:
        content = evidence.to_json()
        digest = evidence_digest(evidence.to_dict())
    except (EvidenceValidationError, TypeError, ValueError):
        return EvidenceReceipt(status="rejected", digest="")

    temporary_name: str | None = None
    try:
        destination_path = Path(destination)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination_path.parent, prefix=".platform-evidence-", delete=False
        ) as temporary_file:
            temporary_name = temporary_file.name
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, destination_path)
    except (OSError, TypeError, ValueError):
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        return EvidenceReceipt(status="failed", digest=digest)
    return EvidenceReceipt(status="written", digest=digest)
