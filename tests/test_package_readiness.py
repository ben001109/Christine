from pathlib import Path

from christine.release_readiness import assess_package_readiness


def _write_project(root: Path, *, version: str = "0.2.0a1", lock_version: str = "0.2.0a1") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        f'''[project]
name = "christine"
version = "{version}"

[project.scripts]
christine-package-readiness = "christine.release_readiness:main"

[build-system]
requires = ["setuptools==81.0.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
include-package-data = false

[tool.setuptools.packages.find]
where = ["."]
include = ["christine", "christine.*"]
namespaces = false
''',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        f'''version = 1

[[package]]
name = "christine"
version = "{lock_version}"
source = {{ virtual = "." }}
''',
        encoding="utf-8",
    )


def test_assess_package_readiness_accepts_restricted_alpha_substrate(tmp_path: Path):
    _write_project(tmp_path)

    result = assess_package_readiness(tmp_path)

    assert result.ready is True
    assert result.metadata_version == "0.2.0a1"
    assert result.lock_version == "0.2.0a1"


def test_assess_package_readiness_rejects_version_mismatch(tmp_path: Path):
    _write_project(tmp_path, lock_version="0.2.0a2")

    result = assess_package_readiness(tmp_path)

    assert result.ready is False
    assert "pyproject.toml package version and uv.lock package version differ" in result.errors


def test_assess_package_readiness_rejects_unbounded_package_discovery(tmp_path: Path):
    _write_project(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('include = ["christine", "christine.*"]', 'include = ["*"]'),
        encoding="utf-8",
    )

    result = assess_package_readiness(tmp_path)

    assert result.ready is False
    assert "setuptools package discovery must include only christine" in result.errors


def test_assess_package_readiness_rejects_unpinned_build_backend(tmp_path: Path):
    _write_project(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('setuptools==81.0.0', 'setuptools>=61'),
        encoding="utf-8",
    )

    result = assess_package_readiness(tmp_path)

    assert result.ready is False
    assert "build requirements must be exactly ['setuptools==81.0.0']" in result.errors
