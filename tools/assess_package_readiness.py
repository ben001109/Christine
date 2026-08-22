"""CLI wrapper for the bounded Christine package-substrate readiness check."""
from pathlib import Path
import sys


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from christine.release_readiness import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
