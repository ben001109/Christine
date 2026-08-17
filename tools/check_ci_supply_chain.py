"""Fail-closed, dependency-free policy for tracked GitHub Actions workflows."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
MAPPING_RE = re.compile(r"^(?:-\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*:(?:\s+(.*))?$")
BLOCK_SCALAR_RE = re.compile(r"^[|>](?:[1-9][+-]?|[+-][1-9]?)?$")
SIMPLE_FLOW_SEQUENCE_RE = re.compile(
    r"^\[\s*[A-Za-z0-9_./:@-]+(?:\s*,\s*[A-Za-z0-9_./:@-]+)*\s*\]$"
)
GITHUB_EXPRESSION_RE = re.compile(r"\$\{\{.*?\}\}")
MATRIX_EXPRESSION_RE = re.compile(r"^\$\{\{\s*matrix\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$")

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


@dataclass(frozen=True)
class _Entry:
    line: int
    indent: int
    key: str | None
    value: str
    sequence: bool = False


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
        if match and BLOCK_SCALAR_RE.fullmatch(_scalar(match.group(2) or "")):
            block_indent = indent
    return tuple(semantic)


def _parse_entries(text: str) -> tuple[list[_Entry], list[str]]:
    entries: list[_Entry] = []
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
                raw_value = body[2:].strip()
                value = _scalar(raw_value)
                problem = _unsupported_value_construct(raw_value)
                if not value or problem:
                    errors.append(f"line {line_number}: unsupported sequence value" + (f": {problem}" if problem else ""))
                entries.append(_Entry(line_number, indent, None, value, sequence=True))
                continue
            errors.append(f"line {line_number}: unsupported YAML mapping-key construct")
            continue

        key = match.group(1)
        raw_value = match.group(2) or ""
        value = _scalar(raw_value)
        problem = _unsupported_value_construct(raw_value)
        if problem:
            errors.append(f"line {line_number}: {problem}")
        entries.append(_Entry(line_number, indent, key, value, sequence=body.startswith("- ")))
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


def _flow_sequence_values(value: str) -> tuple[str, ...]:
    if not SIMPLE_FLOW_SEQUENCE_RE.fullmatch(value):
        return ()
    return tuple(item.strip() for item in value[1:-1].split(","))


def _job_bounds(entries: list[_Entry], position: int) -> tuple[int, int] | None:
    job_start: int | None = None
    for index in range(position - 1, -1, -1):
        entry = entries[index]
        if entry.indent == 2 and entry.key is not None and not entry.sequence and not entry.value:
            job_start = index
            break
    if job_start is None:
        return None
    for index in range(job_start + 1, len(entries)):
        if entries[index].indent <= 2:
            return job_start, index
    return job_start, len(entries)


def _direct_children(
    entries: list[_Entry], start: int, end: int, parent_indent: int, key: str
) -> list[int]:
    return [
        index
        for index in range(start + 1, end)
        if entries[index].indent == parent_indent + 2
        and entries[index].key == key
        and not entries[index].sequence
    ]


def _section_end(entries: list[_Entry], start: int, limit: int) -> int:
    indent = entries[start].indent
    for index in range(start + 1, limit):
        if entries[index].indent <= indent:
            return index
    return limit


def _include_matrix_values(
    entries: list[_Entry], include_start: int, include_end: int, matrix_key: str
) -> tuple[list[str], str | None]:
    include = entries[include_start]
    if include.value:
        return [], "matrix include must use a literal block sequence"
    rows = [
        index
        for index in range(include_start + 1, include_end)
        if entries[index].indent == include.indent + 2 and entries[index].sequence
    ]
    if not rows:
        return [], "matrix include must contain literal rows"

    values: list[str] = []
    for row_position, row_start in enumerate(rows):
        row_end = rows[row_position + 1] if row_position + 1 < len(rows) else include_end
        row = entries[row_start]
        if row.key is None:
            return [], "matrix include rows must be literal mappings"
        candidates: list[str] = []
        if row.key == matrix_key and row.value:
            candidates.append(row.value)
        candidates.extend(
            entry.value
            for entry in entries[row_start + 1 : row_end]
            if entry.key == matrix_key
            and entry.indent == row.indent + 2
            and entry.value
        )
        if len(candidates) != 1:
            return [], f"every matrix include row must contain one literal {matrix_key} value"
        values.extend(candidates)
    return values, None


def _static_matrix_values(
    entries: list[_Entry], reference_position: int, matrix_key: str
) -> tuple[list[str], str | None]:
    bounds = _job_bounds(entries, reference_position)
    if bounds is None:
        return [], "matrix image expression must be inside a literal job"
    job_start, job_end = bounds
    job = entries[job_start]
    strategies = _direct_children(entries, job_start, job_end, job.indent, "strategy")
    if len(strategies) != 1 or entries[strategies[0]].value:
        return [], "matrix image expression requires one literal strategy mapping"
    strategy_start = strategies[0]
    strategy_end = _section_end(entries, strategy_start, job_end)
    matrices = _direct_children(entries, strategy_start, strategy_end, entries[strategy_start].indent, "matrix")
    if len(matrices) != 1 or entries[matrices[0]].value:
        return [], "matrix image expression requires one literal matrix mapping"
    matrix_start = matrices[0]
    matrix_end = _section_end(entries, matrix_start, strategy_end)
    matrix = entries[matrix_start]

    values: list[str] = []
    axes = _direct_children(entries, matrix_start, matrix_end, matrix.indent, matrix_key)
    if len(axes) > 1:
        return [], f"matrix.{matrix_key} must not be duplicated"
    if axes:
        axis_start = axes[0]
        axis = entries[axis_start]
        axis_end = _section_end(entries, axis_start, matrix_end)
        if axis.value:
            values.extend(_flow_sequence_values(axis.value))
            if not values:
                return [], f"matrix.{matrix_key} must use a literal scalar sequence"
        else:
            sequence_values = [
                entry.value
                for entry in entries[axis_start + 1 : axis_end]
                if entry.sequence and entry.indent == axis.indent + 2 and entry.key is None
            ]
            if not sequence_values:
                return [], f"matrix.{matrix_key} must contain literal scalar values"
            values.extend(sequence_values)

    includes = _direct_children(entries, matrix_start, matrix_end, matrix.indent, "include")
    if len(includes) > 1:
        return [], "matrix.include must not be duplicated"
    if includes:
        include_start = includes[0]
        include_end = _section_end(entries, include_start, matrix_end)
        include_values, problem = _include_matrix_values(entries, include_start, include_end, matrix_key)
        if problem:
            return [], problem
        values.extend(include_values)

    if not values:
        return [], f"matrix.{matrix_key} has no statically auditable values"
    return values, None


def _inside_matrix(entries: list[_Entry], position: int) -> bool:
    threshold = entries[position].indent
    for index in range(position - 1, -1, -1):
        entry = entries[index]
        if entry.indent >= threshold:
            continue
        if entry.key == "matrix" and not entry.value:
            return True
        threshold = entry.indent
        if threshold <= 2:
            return False
    return False


def _validate_image_reference(
    entries: list[_Entry], position: int, reference: str
) -> str | None:
    expression = MATRIX_EXPRESSION_RE.fullmatch(reference)
    if expression is None:
        return _validate_image(reference)
    values, problem = _static_matrix_values(entries, position, expression.group(1))
    if problem:
        return problem
    mutable = [value for value in values if _validate_image(value)]
    if mutable:
        return "all static matrix image values must use full sha256 digests"
    return None


def validate_workflow_text(text: str, *, source: str = "<workflow>") -> tuple[str, ...]:
    """Validate immutable references in the supported, bounded YAML subset."""

    entries, errors = _parse_entries(text)
    for position, entry in enumerate(entries):
        line_number, indent, key, value = entry.line, entry.indent, entry.key, entry.value
        problem: str | None = None
        if key == "uses":
            problem = _validate_action(value)
        elif key == "image":
            if not _inside_matrix(entries, position):
                problem = _validate_image_reference(entries, position, value)
        elif key == "container":
            if value:
                problem = _validate_image_reference(entries, position, value)
            else:
                has_image = False
                for child in entries[position + 1 :]:
                    if child.indent <= indent:
                        break
                    if child.key == "image":
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
