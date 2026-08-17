"""Conservative checks for Christine's alpha package metadata.

This module only evaluates the package substrate.  A passing result is not a
release qualification and does not make claims about runtime support.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import tomllib

from christine.versioning import current_version


PACKAGE_NAME = "christine"
ENTRY_POINT_NAME = "christine-package-readiness"
ENTRY_POINT_TARGET = "christine.release_readiness:main"
BUILD_BACKEND = "setuptools.build_meta"
BUILD_REQUIREMENT = "setuptools==81.0.0"
PACKAGE_INCLUDE = ("christine", "christine.*")


@dataclass(frozen=True)
class PackageReadiness:
    """Result of static metadata and lockfile consistency checks."""

    project_root: Path
    metadata_version: str | None
    lock_version: str | None
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.errors


def _load_toml(path: Path, errors: list[str], label: str) -> dict[str, object] | None:
    try:
        with path.open("rb") as file:
            loaded = tomllib.load(file)
    except FileNotFoundError:
        errors.append(f"missing {label}: {path.name}")
        return None
    except tomllib.TOMLDecodeError as error:
        errors.append(f"invalid {label}: {error}")
        return None
    if not isinstance(loaded, dict):
        errors.append(f"invalid {label}: expected a table")
        return None
    return loaded


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _lock_package_version(lock: dict[str, object], errors: list[str]) -> str | None:
    packages = lock.get("package")
    if not isinstance(packages, list):
        errors.append("uv.lock has no package entries")
        return None

    matches = [
        package
        for package in packages
        if isinstance(package, dict)
        and package.get("name") == PACKAGE_NAME
        and _mapping(package.get("source")).get("virtual") == "."
    ]
    if len(matches) != 1:
        errors.append("uv.lock must contain exactly one virtual christine package")
        return None

    version = matches[0].get("version")
    if not isinstance(version, str):
        errors.append("virtual christine package in uv.lock has no version")
        return None
    return version


def assess_package_readiness(project_root: str | Path) -> PackageReadiness:
    """Check that the alpha package metadata and existing lockfile agree."""
    root = Path(project_root).resolve()
    errors: list[str] = []
    pyproject = _load_toml(root / "pyproject.toml", errors, "pyproject.toml")
    lock = _load_toml(root / "uv.lock", errors, "uv.lock")
    metadata_version: str | None = None
    lock_version: str | None = None

    if pyproject is not None:
        project = _mapping(pyproject.get("project"))
        name = project.get("name")
        version = project.get("version")
        metadata_version = version if isinstance(version, str) else None
        expected_version = current_version().package_metadata
        if name != PACKAGE_NAME:
            errors.append(f"project name must be {PACKAGE_NAME!r}")
        if metadata_version != expected_version:
            errors.append(f"project version must match current_version package metadata ({expected_version})")

        scripts = _mapping(project.get("scripts"))
        if scripts != {ENTRY_POINT_NAME: ENTRY_POINT_TARGET}:
            errors.append("project scripts must expose only the package readiness entry point")

        build_system = _mapping(pyproject.get("build-system"))
        if build_system.get("build-backend") != BUILD_BACKEND:
            errors.append(f"build backend must be {BUILD_BACKEND}")
        if build_system.get("requires") != [BUILD_REQUIREMENT]:
            errors.append(f"build requirements must be exactly [{BUILD_REQUIREMENT!r}]")

        setuptools = _mapping(_mapping(pyproject.get("tool")).get("setuptools"))
        if setuptools.get("include-package-data") is not False:
            errors.append("setuptools include-package-data must be false")
        package_find = _mapping(setuptools.get("packages")).get("find")
        package_find = _mapping(package_find)
        if package_find.get("where") != ["."]:
            errors.append("setuptools package discovery must start at the repository root")
        if tuple(package_find.get("include", ())) != PACKAGE_INCLUDE:
            errors.append("setuptools package discovery must include only christine")
        if package_find.get("namespaces") is not False:
            errors.append("setuptools package discovery must disable namespace packages")

    if lock is not None:
        lock_version = _lock_package_version(lock, errors)
    if metadata_version is not None and lock_version is not None and metadata_version != lock_version:
        errors.append("pyproject.toml package version and uv.lock package version differ")

    return PackageReadiness(root, metadata_version, lock_version, tuple(errors))


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Christine alpha package metadata and lock consistency.")
    parser.add_argument("--project-root", type=Path, default=_default_project_root())
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    arguments = parser.parse_args(argv)
    result = assess_package_readiness(arguments.project_root)
    if arguments.json:
        payload = asdict(result)
        payload["project_root"] = str(result.project_root)
        payload["ready"] = result.ready
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif result.ready:
        print(f"package substrate ready: {result.metadata_version} (lock: {result.lock_version})")
    else:
        print("package substrate is not ready:")
        for error in result.errors:
            print(f"- {error}")
    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
