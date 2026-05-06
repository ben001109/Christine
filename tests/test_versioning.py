import pytest
from pathlib import Path

from christine.versioning import ChristineVersion, VersionStage, next_prerelease, parse_version, promote_stage


def test_christine_version_formats_alpha_beta_rc_and_release():
    assert ChristineVersion(0, 2, 0, VersionStage.ALPHA, 1).public == "0.2.0-alpha.1"
    assert ChristineVersion(0, 2, 0, VersionStage.BETA, 1).public == "0.2.0-beta.1"
    assert ChristineVersion(0, 2, 0, VersionStage.RC, 1).public == "0.2.0-rc.1"
    assert ChristineVersion(0, 2, 0, VersionStage.RELEASE).public == "0.2.0"


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
