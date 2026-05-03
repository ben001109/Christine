import subprocess
import sys


def test_fast_boot_check_exits_zero():
    result = subprocess.run(
        [sys.executable, "boot_christine.py", "--check", "--notorch", "--fast", "--no-banner"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "自檢完成" in result.stdout
