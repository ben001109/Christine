"""Fail-closed, dependency-free policy for tracked GitHub Actions workflows."""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess


POLICY_WORKFLOW = ".github/workflows/ci-supply-chain-policy.yml"
CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
FULL_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
REMOTE_ACTION_RE = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*@([0-9a-fA-F]{40})$"
)
LOCAL_ACTION_RE = re.compile(r"^\./[A-Za-z0-9._/-]+$")
IMAGE_DIGEST_RE = re.compile(
    r"^[A-Za-z0-9._-]+(?::[0-9]+)?(?:/[A-Za-z0-9._-]+)*"
    r"(?::[A-Za-z0-9][A-Za-z0-9._-]*)?@sha256:[0-9a-fA-F]{64}$"
)
MAPPING_RE = re.compile(r"^(?:-\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*:\s*(.*)$")
BLOCK_SCALAR_RE = re.compile(r"^[|>](?:[1-9][+-]?|[+-][1-9]?)?$")
SIMPLE_FLOW_SEQUENCE_RE = re.compile(
    r"^\[\s*[A-Za-z0-9_.-]+(?:\s*,\s*[A-Za-z0-9_.-]+)*\s*\]$"
)
GITHUB_EXPRESSION_RE = re.compile(r"\$\{\{.*?\}\}")

EXPECTED_POLICY_SHAPE = (
    (0, "name: CI supply-chain policy"),
    (0, "on:"),
    (2, "pull_request:"),
    (2, "push:"),
    (4, "branches: [main]"),
    (2, "workflow_dispatch:"),
    (0, "permissions:"),
    (2, "contents: read"),
    (0, "jobs:"),
    (2, "ci-supply-chain-policy:"),
    (4, "runs-on: ubuntu-24.04"),
    (4, "steps:"),
    (6, f"- uses: actions/checkout@{CHECKOUT_SHA}"),
    (6, "- run: python3 tools/check_ci_supply_chain.py"),
)


def _without_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(value):
        character = value[index]
        if escaped:
            escaped = False
        elif quote == '"' and character == "\\":
            escaped = True
        elif quote == "'" and character == "'" and index + 1 < len(value) and value[index + 1] == "'":
            index += 1
        elif character in {"'", '"'}:
            quote = character if quote is None else None if quote == character else quote
        elif character == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
        index += 1
    return value.rstrip()


def _scalar(value: str) -> str:
    value = _without_comment(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _unquoted_structure(value: str) -> str:
    output: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(value):
        character = value[index]
        if quote is None:
            if character in {"'", '"'}:
                quote = character
            else:
                output.append(character)
        elif escaped:
            escaped = False
        elif quote == '"' and character == "\\":
            escaped = True
        elif quote == "'" and character == "'" and index + 1 < len(value) and value[index + 1] == "'":
            index += 1
        elif character == quote:
            quote = None
        index += 1
    return "".join(output)


def _unsupported_value_construct(value: str) -> str | None:
    structural = GITHUB_EXPRESSION_RE.sub("", _unquoted_structure(value)).strip()
    if not structural:
        return None
    if structural[0] in "&*!?":
        return "YAML node properties, aliases, and explicit values are unsupported"
    if "{" in structural or "}" in structural:
        return "flow mappings are unsupported"
    if structural.startswith("[") and not SIMPLE_FLOW_SEQUENCE_RE.fullmatch(structural):
        return "only simple scalar flow sequences are supported"
    return None


def _semantic_lines(text: str) -> tuple[tuple[int, str], ...]:
    lines = text.splitlines()
    semantic: list[tuple[int, str]] = []
    block_indent: int | None = None
    for raw_line in lines:
        if block_indent is not None:
            if not raw_line.strip():
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if indent > block_indent:
                continue
            block_indent = None

        content = _without_comment(raw_line).rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        body = content.lstrip(" ")
        semantic.append((indent, body))
        match = MAPPING_RE.fullmatch(body)
        if match and BLOCK_SCALAR_RE.fullmatch(_scalar(match.group(2))):
            block_indent = indent
    return tuple(semantic)


def _parse_entries(text: str) -> tuple[list[tuple[int, int, str, str]], list[str]]:
    entries: list[tuple[int, int, str, str]] = []
    errors: list[str] = []
    block_indent: int | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if block_indent is not None:
            if not raw_line.strip():
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if indent > block_indent:
                continue
            block_indent = None

        content = _without_comment(raw_line).rstrip()
        if not content.strip():
            continue
        if "\t" in content:
            errors.append(f"line {line_number}: tabs are unsupported")
            continue
        indent = len(content) - len(content.lstrip(" "))
        if indent % 2:
            errors.append(f"line {line_number}: indentation must use two-space levels")
        body = content.lstrip(" ")
        match = MAPPING_RE.fullmatch(body)
        if match is None:
            if body.startswith("- "):
                value = body[2:].strip()
                problem = _unsupported_value_construct(value)
                if not value or problem:
                    errors.append(f"line {line_number}: unsupported sequence value" + (f": {problem}" if problem else ""))
                continue
            errors.append(f"line {line_number}: unsupported YAML mapping-key construct")
            continue

        key = match.group(1)
        raw_value = match.group(2)
        value = _scalar(raw_value)
        problem = _unsupported_value_construct(raw_value)
        if problem:
            errors.append(f"line {line_number}: {problem}")
        entries.append((line_number, indent, key, value))
        if BLOCK_SCALAR_RE.fullmatch(value):
            block_indent = indent
    return entries, errors


def _validate_action(reference: str) -> str | None:
    if not reference or "${{" in reference:
        return "action reference must be literal"
    if reference.startswith("./"):
        parts = PurePosixPath(reference[2:]).parts
        if (
            not LOCAL_ACTION_RE.fullmatch(reference)
            or not parts
            or any(part in {"", ".", ".."} for part in parts)
        ):
            return "local action path must stay within the repository"
        return None
    if reference.startswith("docker://"):
        image = reference.removeprefix("docker://")
        return None if IMAGE_DIGEST_RE.fullmatch(image) else "docker action must use a full sha256 digest"
    match = REMOTE_ACTION_RE.fullmatch(reference)
    if match and FULL_COMMIT_RE.fullmatch(match.group(1)):
        return None
    return "third-party action must use a full 40-hex commit SHA"


def _validate_image(reference: str) -> str | None:
    if not reference or "${{" in reference:
        return "container image reference must be literal"
    if not IMAGE_DIGEST_RE.fullmatch(reference):
        return "container image must use a full sha256 digest"
    return None


def validate_workflow_text(text: str, *, source: str = "<workflow>") -> tuple[str, ...]:
    """Validate immutable references in the supported, bounded YAML subset."""

    entries, errors = _parse_entries(text)
    for position, (line_number, indent, key, value) in enumerate(entries):
        problem: str | None = None
        if key == "uses":
            problem = _validate_action(value)
        elif key == "image":
            problem = _validate_image(value)
        elif key == "container":
            if value:
                problem = _validate_image(value)
            else:
                has_image = False
                for _, child_indent, child_key, _ in entries[position + 1 :]:
                    if child_indent <= indent:
                        break
                    if child_key == "image":
                        has_image = True
                if not has_image:
                    problem = "container mapping must contain a digest-pinned image"
        elif key == "services" and value:
            problem = "services must use a literal block mapping with digest-pinned image fields"
        if problem:
            errors.append(f"line {line_number}: {problem}: {value}")
    return tuple(f"{source}:{error}" for error in errors)


def validate_policy_workflow(text: str, *, source: str = POLICY_WORKFLOW) -> tuple[str, ...]:
    """Require the literal bootstrap workflow and its default job check context."""

    if _semantic_lines(text) != EXPECTED_POLICY_SHAPE:
        return (
            f"{source}:dedicated policy workflow must match the literal minimal contract; "
            "custom job names and execution-context overrides are forbidden",
        )
    return ()


def tracked_workflow_paths(repository_root: Path) -> tuple[Path, ...]:
    result = subprocess.run(
        (
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            ":(glob).github/workflows/*.yml",
            ":(glob).github/workflows/*.yaml",
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return tuple(repository_root / relative for relative in result.stdout.split("\0") if relative)


def validate_repository(repository_root: Path) -> tuple[str, ...]:
    repository_root = repository_root.resolve()
    try:
        paths = tracked_workflow_paths(repository_root)
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        return (f"workflow discovery failed: {error}",)

    errors: list[str] = []
    policy_documents: list[str] = []
    for path in paths:
        try:
            if path.is_symlink():
                raise OSError("workflow symlinks or path escapes are forbidden")
            resolved_path = path.resolve(strict=True)
            relative = resolved_path.relative_to(repository_root).as_posix()
            text = resolved_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{path}: workflow read failed: {error}")
            continue
        errors.extend(validate_workflow_text(text, source=relative))
        if relative == POLICY_WORKFLOW:
            policy_documents.append(text)

    if len(policy_documents) != 1:
        errors.append(f"{POLICY_WORKFLOW}: exactly one tracked dedicated policy workflow is required")
    else:
        errors.extend(validate_policy_workflow(policy_documents[0]))
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    errors = validate_repository(arguments.repository_root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("CI supply-chain policy passed for all tracked workflow files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
