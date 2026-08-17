"""Fail closed when a Christine wheel contains paths outside its package surface."""
from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
from tempfile import TemporaryDirectory
import zipfile


PACKAGE_ROOT = "christine"
DIST_INFO_SUFFIX = ".dist-info"
ENTRY_POINT_NAME = "christine-package-readiness"
ENTRY_POINT_TARGET = "christine.release_readiness:main"
FORBIDDEN_PATH_PARTS = frozenset(
    {
        "arc-agi",
        "archive",
        "archives",
        "backup",
        "backups",
        "brain",
        "data",
        "legacy",
        "level5_logs",
        "mirrors",
        "recovery",
        "self_replicas",
        "state",
        "states",
        "v42_export",
    }
)
FORBIDDEN_FILENAMES = frozenset(
    {
        "christine_final.py",
        "growth.log",
        "heartbeat.txt",
        "nexus_v2_state.json",
    }
)
ALLOWED_DIST_INFO_FILES = frozenset({"METADATA", "RECORD", "WHEEL", "entry_points.txt", "top_level.txt"})
REQUIRED_DIST_INFO_FILES = frozenset({"METADATA", "RECORD", "WHEEL", "entry_points.txt"})
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class WheelVerification:
    """Outcome of inspecting an extracted wheel file list."""

    wheel: Path
    members: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def _normal_member_name(name: str, *, is_directory: bool) -> PurePosixPath | None:
    if not name or "\\" in name or name.startswith("/") or WINDOWS_DRIVE_RE.match(name):
        return None
    raw_parts = name.split("/")
    if is_directory:
        if raw_parts.pop() != "":
            return None
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        return None
    return PurePosixPath(*raw_parts)


def _is_dist_info_root(name: str) -> bool:
    normalized = name.casefold()
    return normalized.startswith(f"{PACKAGE_ROOT}-") and normalized.endswith(DIST_INFO_SUFFIX)


def _path_violation(path: PurePosixPath, *, is_directory: bool) -> str | None:
    parts = path.parts
    normalized_parts = tuple(part.casefold() for part in parts)
    if any(part in FORBIDDEN_PATH_PARTS for part in normalized_parts):
        return "contains a forbidden state, legacy, archive, recovery, or backup path component"
    if normalized_parts[-1] in FORBIDDEN_FILENAMES or ".bak." in normalized_parts[-1]:
        return "contains a forbidden runtime-state or legacy filename"
    root = parts[0]
    if root == PACKAGE_ROOT:
        if is_directory:
            return None
        if path.suffix != ".py":
            return "package surface may contain Python source files only"
        return None
    if _is_dist_info_root(root):
        if is_directory:
            return None if len(parts) == 1 else "dist-info metadata must not contain nested directories"
        if len(parts) != 2 or parts[-1] not in ALLOWED_DIST_INFO_FILES:
            return "dist-info metadata file is not in the allowed minimal surface"
        return None
    return "is outside the allowed christine package and dist-info surface"


def _validated_members(archive: zipfile.ZipFile, errors: list[str]) -> tuple[tuple[zipfile.ZipInfo, PurePosixPath], ...]:
    validated: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []
    seen: set[PurePosixPath] = set()
    for info in archive.infolist():
        member = _normal_member_name(info.filename, is_directory=info.is_dir())
        if member is None:
            errors.append("wheel contains an unsafe member path")
            continue
        if member in seen:
            errors.append(f"duplicate wheel member path: {member.as_posix()}")
            continue
        seen.add(member)
        violation = _path_violation(member, is_directory=info.is_dir())
        if violation is not None:
            errors.append(f"{member.as_posix()}: {violation}")
            continue
        validated.append((info, member))
    return tuple(validated)


def _extract_members(wheel: Path, destination: Path, errors: list[str]) -> tuple[str, ...]:
    try:
        archive = zipfile.ZipFile(wheel)
    except (FileNotFoundError, OSError, zipfile.BadZipFile):
        errors.append("cannot read wheel archive")
        return ()

    try:
        with archive:
            validated = _validated_members(archive, errors)
            if errors:
                return ()
            for info, member in validated:
                if info.is_dir():
                    continue
                target = destination.joinpath(*member.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except (OSError, RuntimeError, zipfile.BadZipFile):
        errors.append("cannot extract wheel archive")
        return ()

    return tuple(
        item.relative_to(destination).as_posix()
        for item in sorted(destination.rglob("*"))
        if item.is_file()
    )


def _required_metadata_errors(destination: Path, members: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    if f"{PACKAGE_ROOT}/__init__.py" not in members:
        errors.append("wheel is missing christine/__init__.py")
    dist_info_dirs = {
        PurePosixPath(member).parts[0]
        for member in members
        if _is_dist_info_root(PurePosixPath(member).parts[0])
    }
    if len(dist_info_dirs) != 1:
        return errors + ["wheel must contain exactly one christine dist-info directory"]
    dist_info = next(iter(dist_info_dirs))
    for filename in REQUIRED_DIST_INFO_FILES:
        if f"{dist_info}/{filename}" not in members:
            errors.append(f"wheel is missing required metadata file: {filename}")
    entry_points = destination / dist_info / "entry_points.txt"
    if entry_points.is_file():
        try:
            parser = configparser.ConfigParser()
            parser.read_string(entry_points.read_text(encoding="utf-8"))
            valid_entry_point = (
                parser.sections() == ["console_scripts"]
                and parser.options("console_scripts") == [ENTRY_POINT_NAME]
                and parser.get("console_scripts", ENTRY_POINT_NAME, fallback=None) == ENTRY_POINT_TARGET
            )
        except (OSError, UnicodeError, configparser.Error):
            errors.append("wheel entry point metadata is invalid")
        else:
            if not valid_entry_point:
                errors.append("wheel entry point must expose only the package readiness command")
    return errors


def verify_package_wheel(wheel: str | Path) -> WheelVerification:
    """Extract a wheel into a temporary directory and validate its file surface."""
    wheel_path = Path(wheel).resolve()
    errors: list[str] = []
    with TemporaryDirectory(prefix="christine-wheel-verify-") as temporary:
        destination = Path(temporary)
        members = _extract_members(wheel_path, destination, errors)
        if not errors:
            errors.extend(_required_metadata_errors(destination, members))
    return WheelVerification(wheel_path, members, tuple(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify that a Christine wheel has a restricted artifact surface.")
    parser.add_argument("wheel", type=Path)
    arguments = parser.parse_args(argv)
    result = verify_package_wheel(arguments.wheel)
    if result.valid:
        print(f"wheel surface verified: {result.wheel}")
    else:
        print(f"wheel surface rejected: {result.wheel}")
        for error in result.errors:
            print(f"- {error}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
