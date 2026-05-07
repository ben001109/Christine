import pytest
from pathlib import Path

from christine.versioning import (
    ChristineVersion,
    CURRENT_VERSION,
    LegacyVersionKind,
    LegacyVersionRecord,
    VersionStage,
    current_version,
    legacy_version_by_name,
    legacy_version_records,
    next_prerelease,
    parse_version,
    promote_stage,
)


def test_christine_version_formats_alpha_beta_rc_and_release():
    assert ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1).public == "0.2.0-alpha.1"
    assert ChristineVersion(0, 2, 0, VersionStage.BETA, 1).public == "0.2.0-beta.1"
    assert ChristineVersion(0, 2, 0, VersionStage.RC, 1).public == "0.2.0-rc.1"
    assert ChristineVersion(0, 2, 0, VersionStage.RELEASE).public == "0.2.0"


def test_christine_version_maps_to_pep440_package_metadata():
    assert ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1).package_metadata == "0.2.0a1"
    assert ChristineVersion(0, 2, 0, VersionStage.BETA, 2).package_metadata == "0.2.0b2"
    assert ChristineVersion(0, 2, 0, VersionStage.RC, 3).package_metadata == "0.2.0rc3"
    assert ChristineVersion(0, 2, 0, VersionStage.RELEASE).package_metadata == "0.2.0"


def test_parse_version_accepts_release_stages():
    assert parse_version("0.2.0-alpha.1") == ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1)
    assert parse_version("0.2.0-beta.1") == ChristineVersion(0, 2, 0, VersionStage.BETA, 1)
    assert parse_version("0.2.0-rc.1") == ChristineVersion(0, 2, 0, VersionStage.RC, 1)
    assert parse_version("0.2.0") == ChristineVersion(0, 2, 0, VersionStage.RELEASE)


def test_parse_version_rejects_invalid_stage_names():
    with pytest.raises(ValueError, match="invalid Christine version"):
        parse_version("0.2.0-preview.1")


@pytest.mark.parametrize(
    "text",
    [
        "01.2.3",
        "1.02.3",
        "1.2.03",
        "1.2.3-alpha.01",
        "1.2.3-beta.0",
    ],
)
def test_parse_version_rejects_semver_leading_zeroes(text):
    with pytest.raises(ValueError):
        parse_version(text)


def test_release_versions_cannot_have_prerelease_number():
    with pytest.raises(ValueError, match="release versions must not have prerelease numbers"):
        ChristineVersion(0, 2, 0, VersionStage.RELEASE, 1)


def test_christine_version_rejects_invalid_constructor_stage():
    with pytest.raises(ValueError, match="version stage"):
        ChristineVersion(1, 2, 3, "preview", 1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"major": 1.2, "minor": 2, "patch": 3},
        {"major": True, "minor": 2, "patch": 3},
        {"major": 1, "minor": 2.5, "patch": 3},
        {"major": 1, "minor": 2, "patch": False},
    ],
)
def test_christine_version_rejects_invalid_component_types(kwargs):
    with pytest.raises(ValueError, match="version numbers must be integers"):
        ChristineVersion(**kwargs)  # type: ignore[arg-type]


def test_christine_version_rejects_invalid_prerelease_type():
    with pytest.raises(ValueError, match="prerelease number must be an integer"):
        ChristineVersion(1, 2, 3, VersionStage.ALPHA, 1.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="prerelease number must be an integer"):
        ChristineVersion(1, 2, 3, VersionStage.BETA, True)  # type: ignore[arg-type]


def test_prerelease_versions_require_positive_number():
    with pytest.raises(ValueError, match="prerelease versions require a positive number"):
        ChristineVersion(0, 2, 0, VersionStage.ALPHA)

    with pytest.raises(ValueError, match="prerelease versions require a positive number"):
        ChristineVersion(0, 2, 0, VersionStage.BETA, 0)


def test_next_prerelease_increments_same_stage_number():
    version = ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1)

    assert next_prerelease(version) == ChristineVersion(0, 2, 0, VersionStage.ALPHA, 2)


def test_promote_stage_follows_alpha_beta_rc_release_order():
    assert promote_stage(ChristineVersion(0, 2, 0, VersionStage.ALPHA, 3)) == ChristineVersion(
        0, 2, 0, VersionStage.BETA, 1
    )
    assert promote_stage(ChristineVersion(0, 2, 0, VersionStage.BETA, 2)) == ChristineVersion(
        0, 2, 0, VersionStage.RC, 1
    )
    assert promote_stage(ChristineVersion(0, 2, 0, VersionStage.RC, 1)) == ChristineVersion(
        0, 2, 0, VersionStage.RELEASE
    )


def test_release_versions_do_not_promote_again():
    with pytest.raises(ValueError, match="release versions cannot be promoted"):
        promote_stage(ChristineVersion(0, 2, 0, VersionStage.RELEASE))


def test_current_version_declares_active_alpha_development_line():
    assert CURRENT_VERSION.public == "0.2.0-alpha.1"
    assert CURRENT_VERSION.package_metadata == "0.2.0a1"
    assert CURRENT_VERSION.stage == VersionStage.ALPHA
    assert current_version() == CURRENT_VERSION
    assert current_version().package_metadata == "0.2.0a1"
    assert parse_version(current_version().public) == CURRENT_VERSION


def test_current_version_is_not_a_legacy_label():
    legacy_values = {record.value for record in legacy_version_records()}

    assert current_version().public not in legacy_values


def test_versioning_policy_documents_alpha_beta_rc_release_rules():
    policy = Path("docs/VERSIONING.md").read_text(encoding="utf-8")

    assert "MAJOR.MINOR.PATCH[-alpha.N|-beta.N|-rc.N]" in policy
    assert "alpha -> beta -> rc -> release" in policy
    assert "Alpha" in policy
    assert "Beta" in policy
    assert "RC" in policy
    assert "Release" in policy


def test_agent_guide_requires_version_management_rules():
    guide = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "## Version Management" in guide
    assert "docs/VERSIONING.md" in guide
    assert "alpha" in guide
    assert "beta" in guide
    assert "release" in guide


def test_legacy_version_registry_tracks_primary_monolith_version_label():
    record = legacy_version_by_name("CHRISTINE_VERSION")

    assert isinstance(record, LegacyVersionRecord)
    assert record.value == "600.0-final-agi-opus"
    assert record.kind == LegacyVersionKind.MONOLITH_PUBLIC_LABEL
    assert record.source == "christine_final.py"
    assert record.active is True
    assert record.governs_public_release is False


def test_legacy_version_registry_keeps_package_metadata_separate():
    record = legacy_version_by_name("pyproject.version")

    assert record.value == "0.1.0"
    assert record.kind == LegacyVersionKind.PACKAGE_METADATA
    assert record.governs_public_release is False


def test_legacy_version_registry_includes_known_subsystem_labels():
    records = {record.name: record for record in legacy_version_records(active_only=True)}

    for name in ["V42_VERSION", "V42_HERMES_VERSION", "V58_VERSION", "V60_VERSION", "_V70_VERSION"]:
        assert name in records
        assert records[name].kind == LegacyVersionKind.SUBSYSTEM_LABEL
        assert records[name].governs_public_release is False


def test_legacy_version_registry_includes_cache_and_runtime_labels():
    records = {record.name: record for record in legacy_version_records(active_only=True)}

    assert records["_OMEGA_CACHE_VERSION"].kind == LegacyVersionKind.CACHE_SCHEMA
    assert records["_V42_NEURAL_VERSION"].kind == LegacyVersionKind.RUNTIME_LABEL
    assert records["V2000_SKILL_COMPILER_VERSION"].value == "2000.0-singularity"
    assert records["V2499_SKILL_COMPILER_VERSION"].value == "2499.0-beyond-singularity"


def test_active_monolith_legacy_version_records_still_exist_in_source():
    source = Path("christine_final.py").read_text(encoding="utf-8-sig")
    records = [
        record
        for record in legacy_version_records(active_only=True)
        if record.source == "christine_final.py"
    ]

    assert records
    for record in records:
        assert record.value in source


def test_versioning_policy_documents_legacy_version_labels():
    policy = Path("docs/VERSIONING.md").read_text(encoding="utf-8")

    assert "## Legacy Version Labels" in policy
    assert "LEGACY_VERSION_RECORDS" in policy
    assert "migration plan" in policy


def test_versioning_policy_documents_current_development_version():
    policy = Path("docs/VERSIONING.md").read_text(encoding="utf-8")

    assert "## Current Development Version" in policy
    assert "0.2.0-alpha.1" in policy
    assert "CURRENT_VERSION" in policy
    assert "pyproject.toml" in policy
    assert "package metadata" in policy


def test_agent_guide_requires_legacy_version_registration():
    guide = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "legacy version" in guide.lower()
    assert "LEGACY_VERSION_RECORDS" in guide


def test_legacy_version_inventory_documents_key_legacy_values():
    inventory = Path("docs/versions/LEGACY_VERSIONS.md").read_text(encoding="utf-8")

    for value in [
        "600.0-final-agi-opus",
        "42.8-titan",
        "70.0-sovereign-agi",
        "2499.0-beyond-singularity",
    ]:
        assert value in inventory


def test_legacy_version_inventory_covers_all_registered_values():
    inventory = Path("docs/versions/LEGACY_VERSIONS.md").read_text(encoding="utf-8")

    for record in legacy_version_records():
        assert record.value in inventory
