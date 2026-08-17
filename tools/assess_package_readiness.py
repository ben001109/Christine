"""CLI wrapper for the bounded Christine package-substrate readiness check."""
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from christine.release_readiness import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
