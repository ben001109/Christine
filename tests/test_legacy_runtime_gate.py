from __future__ import annotations

import ast
import builtins
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

import boot_christine
from christine.legacy.runtime_gate import require_legacy_runtime_authorization


class _ForgedAuthorization:
    def __eq__(self, other: object) -> bool:
        raise AssertionError("authorization must use identity, not equality")


@pytest.mark.parametrize("token", [None, object(), _ForgedAuthorization()])
def test_require_rejects_missing_fake_and_forged_tokens_without_output(token, capsys):
    with pytest.raises(SystemExit) as exc_info:
        require_legacy_runtime_authorization(token)

    assert exc_info.value.code == 86
    assert capsys.readouterr() == ("", "")


def test_require_rejects_an_omitted_argument_with_the_same_exit_code(capsys):
    with pytest.raises(SystemExit) as exc_info:
        require_legacy_runtime_authorization()

    assert exc_info.value.code == 86
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["--legacy-monolith"],
        ["--allow-legacy-side-effects"],
    ],
)
def test_boot_denies_incomplete_legacy_authorization_before_side_effects(monkeypatch, capsys, flags):
    argv = ["boot_christine.py", *flags]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        boot_christine,
        "_issue_legacy_runtime_authorization",
        lambda: pytest.fail("authorization was issued"),
    )
    monkeypatch.setattr(
        boot_christine,
        "detect_hardware",
        lambda: pytest.fail("hardware detection ran"),
    )
    monkeypatch.setattr(runpy, "run_path", lambda *args, **kwargs: pytest.fail("runpy ran"))
    env_before = dict(os.environ)
    argv_before = list(sys.argv)

    with pytest.raises(SystemExit) as exc_info:
        boot_christine.main()

    assert exc_info.value.code == 86
    assert dict(os.environ) == env_before
    assert sys.argv == argv_before
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["--legacy-monolith"],
        ["--allow-legacy-side-effects"],
    ],
)
def test_boot_cli_silently_denies_incomplete_legacy_authorization(flags):
    result = subprocess.run(
        [sys.executable, "-B", "boot_christine.py", *flags],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 86
    assert result.stdout == ""
    assert result.stderr == ""


def test_check_path_preserves_self_check_without_legacy_handoff(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["boot_christine.py", "--check", "--notorch", "--no-banner"],
    )
    monkeypatch.setattr(boot_christine.platform, "system", lambda: "TestOS")
    monkeypatch.setattr(boot_christine.platform, "release", lambda: "1")
    monkeypatch.setattr(boot_christine.platform, "python_version", lambda: "3.11")
    monkeypatch.setattr(boot_christine.platform, "processor", lambda: "Test CPU")
    monkeypatch.setattr(boot_christine.multiprocessing, "cpu_count", lambda: 8)
    monkeypatch.setattr(
        boot_christine,
        "_issue_legacy_runtime_authorization",
        lambda: pytest.fail("authorization was issued"),
    )
    monkeypatch.setattr(
        boot_christine,
        "detect_hardware",
        lambda: pytest.fail("hardware detection ran"),
    )
    monkeypatch.setattr(
        boot_christine,
        "print_boot_banner",
        lambda *args, **kwargs: pytest.fail("banner rendered despite --no-banner"),
    )
    calls = []

    def fake_build_basic_hardware_info(**kwargs):
        calls.append(("hardware", kwargs))
        return {"cpu_count": 8, "gpu": None}

    def fake_apply_compute_budget(*args, **kwargs):
        calls.append(("budget", args, kwargs))
        return {}, 4, False

    fake_psutil = SimpleNamespace(
        virtual_memory=lambda: SimpleNamespace(total=16 * 1024**3)
    )
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "runpy":
            pytest.fail("runpy was imported")
        if name == "psutil":
            return fake_psutil
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(boot_christine, "build_basic_hardware_info", fake_build_basic_hardware_info)
    monkeypatch.setattr(boot_christine, "apply_compute_budget", fake_apply_compute_budget)
    monkeypatch.setattr(
        boot_christine,
        "print_runtime_health_summary",
        lambda: pytest.fail("provider health probe ran during --check"),
    )
    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert boot_christine.main() == 0
    assert [call[0] for call in calls] == ["hardware", "budget"]
    assert "自檢完成，不啟動主程式" in capsys.readouterr().out


def test_boot_issues_and_injects_authorization_only_for_explicit_legacy_handoff(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "boot_christine.py",
            "--legacy-monolith",
            "--allow-legacy-side-effects",
            "--notorch",
            "--no-banner",
            "forwarded-argument",
        ],
    )
    monkeypatch.setattr(
        boot_christine,
        "build_basic_hardware_info",
        lambda **kwargs: {"cpu_count": 8, "gpu": None},
    )
    monkeypatch.setattr(
        boot_christine,
        "apply_compute_budget",
        lambda *args, **kwargs: ({}, 4, False),
    )
    monkeypatch.setattr(boot_christine, "print_runtime_health_summary", lambda: None)
    handoff = {}

    def fake_run_path(target, *, run_name, init_globals):
        require_legacy_runtime_authorization(
            init_globals["_CHRISTINE_LEGACY_RUNTIME_AUTHORIZATION"]
        )
        handoff.update(target=target, run_name=run_name, init_globals=init_globals)

    monkeypatch.setattr(runpy, "run_path", fake_run_path)

    assert boot_christine.main() == 0
    assert handoff["target"].endswith("christine_final.py")
    assert handoff["run_name"] == "__main__"
    assert set(handoff["init_globals"]) == {"_CHRISTINE_LEGACY_RUNTIME_AUTHORIZATION"}
    assert sys.argv == [handoff["target"], "forwarded-argument"]


def test_monolith_first_two_statements_are_the_legacy_runtime_gate():
    source = Path("christine_final.py").read_text(encoding="utf-8-sig")
    module = ast.parse(source)

    first, second = module.body[:2]
    assert isinstance(first, ast.ImportFrom)
    assert first.module == "christine.legacy.runtime_gate"
    assert [alias.name for alias in first.names] == ["require_legacy_runtime_authorization"]
    assert isinstance(second, ast.Expr)
    assert isinstance(second.value, ast.Call)
    assert isinstance(second.value.func, ast.Name)
    assert second.value.func.id == "require_legacy_runtime_authorization"


def test_direct_monolith_execution_is_silently_denied():
    result = subprocess.run(
        [sys.executable, "-B", "christine_final.py"],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 86
    assert result.stdout == ""
    assert result.stderr == ""
