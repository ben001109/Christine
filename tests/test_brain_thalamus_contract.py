"""Exercise Thalamus gate validation through the pure-Python fallback."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run_pure_python(script: str) -> None:
    result = subprocess.run(
        [sys.executable, "-S", "-c", textwrap.dedent(script)],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr


def test_gate_requires_exact_dimension_and_clamps_only_after_validation():
    _run_pure_python(
        """
        from brain.thalamus import Thalamus

        thalamus = Thalamus(n=3)
        thalamus.set_gate((-1.0, 0.5, 2.0))
        assert thalamus.gate == [0.0, 0.5, 1.0]
        assert thalamus.relay((2.0, 2.0, 2.0)) == [0.0, 1.0, 2.0]

        before = list(thalamus.gate)
        try:
            thalamus.set_gate((0.1, 0.2))
        except ValueError as exc:
            assert str(exc) == "invalid-thalamus-gate"
        else:
            raise AssertionError("wrong gate dimension was accepted")
        assert thalamus.gate == before
        """
    )


def test_gate_rejects_non_finite_or_non_numeric_values_without_mutation():
    _run_pure_python(
        """
        import math
        from brain.thalamus import Thalamus

        thalamus = Thalamus(n=3)
        before = list(thalamus.gate)
        for invalid in (
            (math.nan, 0.0, 1.0),
            (math.inf, 0.0, 1.0),
            (True, 0.0, 1.0),
            ("0", 0.0, 1.0),
            {0: 0.1, 1: 0.2, 2: 0.3},
            {0.0, 0.5, 1.0},
            (value for value in (0.0, 0.5, 1.0)),
            "000",
            None,
        ):
            try:
                thalamus.set_gate(invalid)
            except ValueError as exc:
                assert str(exc) == "invalid-thalamus-gate"
            else:
                raise AssertionError(repr(invalid))
            assert thalamus.gate == before
        """
    )
