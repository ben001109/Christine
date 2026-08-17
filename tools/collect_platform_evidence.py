"""Collect the minimal native platform-evidence substrate.

This tool does not inspect application state.  It emits only the v1 portable
schema and may run the five approved focused test targets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from christine.platform.evidence import collect_native_evidence, write_evidence_atomically


FOCUSED_TEST_TARGETS = (
    "tests/platform",
    "tests/test_platform_capabilities.py",
    "tests/test_platform_runtime_gates.py",
    "tests/test_startup_platform_imports.py",
    "tests/test_boot_contract.py",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--run-suite", action="store_true")
    parser.add_argument("--help", action="help")
    return parser


def run_focused_suite(runner=subprocess.run) -> bool:
    """Run exactly the approved native-evidence test slice."""

    result = runner([sys.executable, "-m", "pytest", *FOCUSED_TEST_TARGETS], check=False)
    return result.returncode == 0


def main(argv: Sequence[str] | None = None, *, runner=subprocess.run) -> int:
    parser = build_parser()
    try:
        arguments = parser.parse_args(argv)
    except (argparse.ArgumentError, SystemExit):
        return 2

    if arguments.run_suite and not run_focused_suite(runner):
        print('{"status":"focused-suite-failed"}')
        return 1

    evidence = collect_native_evidence(fixture=arguments.fixture)
    if arguments.output and not arguments.dry_run:
        receipt = write_evidence_atomically(Path(arguments.output), evidence)
        print(json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":")))
        return 0 if receipt.status == "written" else 1

    print(evidence.to_json(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
