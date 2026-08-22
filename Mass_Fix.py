# -*- coding: utf-8 -*-
"""Conservative syntax-repair utility for ``christine_final.py``.

Analysis is read-only. Persisting a repair requires both ``--apply`` and
``--confirm``, a clean Git worktree, and a candidate that parses successfully.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NoReturn, Sequence


SOURCE_PATH = Path(__file__).resolve().with_name("christine_final.py")
EXIT_DRY_RUN = 3
EXIT_AUTHORIZATION_REQUIRED = 64
EXIT_INVALID_SOURCE = 65
EXIT_WRITE_FAILED = 74
EXIT_GIT_REJECTED = 75

_BLOCK_RE = re.compile(
    r"^(\s*)(try|if|elif|else|for|while|with|def|class|except|finally)\b.*:\s*(#.*)?$"
)
_JUNK_CHARACTERS = ("ㄍ", "ㄅ", "ㄆ", "ㄇ", "ㄈ", "ㄉ", "ㄊ", "ㄋ", "ㄌ")
_MAX_SYNTAX_REPAIRS = 400


@dataclass(frozen=True)
class RepairCandidate:
    text: str
    junk_removed: int
    blocks_filled: int
    syntax_lines_disabled: int


def _fill_empty_blocks(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    output: list[str] = []
    inserted = 0

    for index, line in enumerate(lines):
        output.append(line)
        match = _BLOCK_RE.match(line)
        if match is None:
            continue

        indent = len(match.group(1))
        needs_pass = True
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if not stripped or stripped.startswith("#"):
                continue
            following_indent = len(following) - len(following.lstrip())
            needs_pass = following_indent <= indent
            break

        if needs_pass:
            output.append(" " * (indent + 4) + "pass")
            inserted += 1

    return "\n".join(output), inserted


def build_repair_candidate(original: str) -> RepairCandidate:
    """Return a fully parsed repair candidate without writing anything."""

    text = original
    junk_removed = 0
    for character in _JUNK_CHARACTERS:
        count = text.count(character)
        if count:
            text = text.replace(character, "")
            junk_removed += count

    text = re.sub(r";{4,}", ";", text)
    text, blocks_filled = _fill_empty_blocks(text)
    syntax_lines_disabled = 0

    for _ in range(_MAX_SYNTAX_REPAIRS):
        try:
            ast.parse(text)
            break
        except SyntaxError as error:
            line_number = error.lineno or 0
            lines = text.split("\n")
            if not 0 < line_number <= len(lines):
                raise ValueError("repair candidate did not parse") from None

            bad_line = lines[line_number - 1]
            block_match = _BLOCK_RE.match(bad_line)
            if block_match is not None:
                indent = len(block_match.group(1))
                lines.insert(line_number, " " * (indent + 4) + "pass")
            else:
                lines[line_number - 1] = "# [MASS_FIX_DISABLED] " + bad_line
            text = "\n".join(lines)
            syntax_lines_disabled += 1
    else:
        raise ValueError("repair candidate did not parse")

    # This explicit precondition also protects callers that inject a candidate.
    ast.parse(text)
    return RepairCandidate(
        text=text,
        junk_removed=junk_removed,
        blocks_filled=blocks_filled,
        syntax_lines_disabled=syntax_lines_disabled,
    )


def git_worktree_is_clean(project_root: Path) -> bool:
    """Perform the read-only Git cleanliness check required before apply."""

    try:
        result = subprocess.run(
            (
                "git",
                "-C",
                os.fspath(project_root),
                "status",
                "--porcelain=v1",
                "--untracked-files=normal",
            ),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout == b""


def backup_path_for(source_path: Path, original_bytes: bytes) -> Path:
    digest = hashlib.sha256(original_bytes).hexdigest()[:16]
    return source_path.with_name(f"{source_path.name}.bak.mass-fix-{digest}")


def _write_backup(backup_path: Path, original_bytes: bytes) -> None:
    try:
        with backup_path.open("xb") as backup_file:
            backup_file.write(original_bytes)
            backup_file.flush()
            os.fsync(backup_file.fileno())
    except FileExistsError:
        if backup_path.read_bytes() != original_bytes:
            raise OSError("backup collision") from None


def _replace_source_atomically(source_path: Path, candidate_bytes: bytes) -> None:
    source_mode = stat.S_IMODE(source_path.stat().st_mode)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{source_path.name}.mass-fix-",
            dir=source_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(candidate_bytes)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.chmod(source_mode)
        os.replace(temporary_path, source_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


BackupWriter = Callable[[Path, bytes], None]
SourceReplacer = Callable[[Path, bytes], None]


def persist_candidate(
    source_path: Path,
    original_bytes: bytes,
    candidate_text: str,
    *,
    backup_writer: BackupWriter = _write_backup,
    source_replacer: SourceReplacer = _replace_source_atomically,
) -> Path:
    """Back up then atomically replace a source whose content has not changed."""

    ast.parse(candidate_text)
    candidate_bytes = candidate_text.encode("utf-8")
    if source_path.read_bytes() != original_bytes:
        raise OSError("source changed during repair")

    backup_path = backup_path_for(source_path, original_bytes)
    backup_writer(backup_path, original_bytes)

    # Detect a concurrent change after the backup but before replacement.
    if source_path.read_bytes() != original_bytes:
        raise OSError("source changed during repair")
    source_replacer(source_path, candidate_bytes)
    return backup_path


CleanCheck = Callable[[Path], bool]
CandidateBuilder = Callable[[str], RepairCandidate]
CandidatePersister = Callable[[Path, bytes, str], Path]


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        self.exit(2, "[Mass_Fix] rejected: invalid arguments.\n")


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description="Analyze legacy syntax repairs; applying requires two explicit flags.",
        allow_abbrev=False,
    )
    parser.add_argument("--apply", action="store_true", help="enable persistent repair")
    parser.add_argument("--confirm", action="store_true", help="confirm persistent repair")
    parser.add_argument("--dry-run", action="store_true", help="analyze without writing")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    source_path: Path = SOURCE_PATH,
    clean_check: CleanCheck = git_worktree_is_clean,
    candidate_builder: CandidateBuilder = build_repair_candidate,
    candidate_persister: CandidatePersister = persist_candidate,
) -> int:
    args = _parser().parse_args(argv)
    applying = args.apply and args.confirm and not args.dry_run

    if (args.apply or args.confirm) and not applying:
        print("[Mass_Fix] rejected: both apply flags are required.")
        return EXIT_AUTHORIZATION_REQUIRED

    if not source_path.is_file() or source_path.is_symlink():
        print("[Mass_Fix] rejected: source is unavailable.")
        return EXIT_INVALID_SOURCE

    if applying and not clean_check(source_path.parent):
        print("[Mass_Fix] rejected: Git worktree is not clean.")
        return EXIT_GIT_REJECTED

    try:
        original_bytes = source_path.read_bytes()
        original = original_bytes.decode("utf-8")
        candidate = candidate_builder(original)
        ast.parse(candidate.text)
    except (OSError, UnicodeError, SyntaxError, ValueError):
        print("[Mass_Fix] rejected: no valid repair candidate.")
        return EXIT_INVALID_SOURCE

    if not applying:
        print(
            "[Mass_Fix] dry-run: "
            f"changed={str(candidate.text != original).lower()} "
            f"junk={candidate.junk_removed} blocks={candidate.blocks_filled} "
            f"syntax={candidate.syntax_lines_disabled}"
        )
        return EXIT_DRY_RUN

    if candidate.text == original:
        print("[Mass_Fix] applied: source already parses; no files written.")
        return 0

    try:
        candidate_persister(source_path, original_bytes, candidate.text)
    except (OSError, SyntaxError, ValueError):
        print("[Mass_Fix] rejected: persistent write failed; source was not intentionally changed.")
        return EXIT_WRITE_FAILED

    print("[Mass_Fix] applied: backup created and source replaced.")
    return 0


def _entrypoint() -> int:
    try:
        return main()
    except Exception:
        print("[Mass_Fix] rejected: unexpected internal failure.")
        return EXIT_WRITE_FAILED


if __name__ == "__main__":
    raise SystemExit(_entrypoint())
