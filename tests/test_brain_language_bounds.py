"""Exercise language capacity boundaries without importing an unavailable NumPy runtime."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run_pure_python(script: str) -> None:
    environment = os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-S", "-c", textwrap.dedent(script)],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr


def test_tokenizer_reserves_one_bounded_unknown_token_for_new_characters():
    _run_pure_python(
        """
        from brain.language import CharTokenizer

        tokenizer = CharTokenizer(vocab_max=4)
        assert tokenizer.encode("abcd") == [0, 1, 2, 3]
        assert tokenizer.vocab() == 3
        assert tokenizer.encode("da") == [3, 0]
        assert tokenizer.vocab() == 3
        """
    )


def test_language_module_ingests_more_unique_characters_than_srn_capacity():
    _run_pure_python(
        """
        import math
        from brain.language import LanguageModule

        module = LanguageModule(hidden=2, seed=0)
        text = "".join(chr(0x1000 + offset) for offset in range(module.srn.vmax + 32))
        assert math.isfinite(module.ingest(text))
        assert module.vocab_size() == module.srn.vmax - 1
        assert all(0 <= token_id < module.srn.vmax for pair in module.bigram for token_id in pair)
        """
    )


def test_srn_learning_uses_the_same_bounded_ids_as_step():
    _run_pure_python(
        """
        import math
        from brain.language import SRN

        srn = SRN(vocab_max=4, hidden=2, seed=0)
        assert math.isfinite(srn.learn(11, 14))
        assert len(srn.step(19)) == 4
        """
    )


def test_tokenizer_and_srn_reject_invalid_fixed_capacities():
    _run_pure_python(
        """
        from brain.language import CharTokenizer, SRN

        for invalid in (0, 1, True, "4"):
            for factory in (CharTokenizer, SRN):
                try:
                    factory(vocab_max=invalid)
                except ValueError:
                    continue
                raise AssertionError(invalid)
        """
    )
