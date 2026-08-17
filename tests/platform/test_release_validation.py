import pytest

from christine.platform.evidence import collect_native_evidence
from christine.platform.validation import EvidenceValidationError, validate_native_evidence


def test_native_evidence_schema_accepts_only_content_free_contract():
    document = collect_native_evidence(sys_platform="linux").to_dict()

    validate_native_evidence(document)


def test_native_evidence_schema_rejects_unknown_payload_without_echoing_it():
    document = collect_native_evidence(sys_platform="linux").to_dict()
    document["payload"] = "private-user-content"

    with pytest.raises(EvidenceValidationError) as error:
        validate_native_evidence(document)

    assert "private-user-content" not in str(error.value)


@pytest.mark.parametrize("invalid_version", [True, 1.0, "1"])
def test_native_evidence_schema_requires_an_integer_schema_version(invalid_version):
    document = collect_native_evidence(sys_platform="linux").to_dict()
    document["schema_version"] = invalid_version

    with pytest.raises(EvidenceValidationError):
        validate_native_evidence(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("identity", {"name": "plan9"}),
        ("capabilities", {"autostart": True}),
        ("provenance", {"source": "native-capability-registry", "mode": "host-private"}),
    ],
)
def test_native_evidence_schema_rejects_malformed_identity_capabilities_and_provenance(field, value):
    document = collect_native_evidence(sys_platform="linux").to_dict()
    document[field] = value

    with pytest.raises(EvidenceValidationError):
        validate_native_evidence(document)


def test_native_evidence_schema_rejects_non_boolean_capability_value():
    document = collect_native_evidence(sys_platform="linux").to_dict()
    document["capabilities"]["gui"] = 1

    with pytest.raises(EvidenceValidationError):
        validate_native_evidence(document)
