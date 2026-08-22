import ast
import hashlib
from pathlib import Path

import pytest

import Mass_Fix as mass_fix


def _write_broken_source(root: Path) -> Path:
    source = root / "legacy.py"
    source.write_text("def repaired():\n", encoding="utf-8")
    return source


def _artifacts(root: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in root.iterdir()
        if path.is_file()
    }


def test_default_is_read_only_analysis_and_exits_nonzero(tmp_path, capsys):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)

    result = mass_fix.main([], source_path=source, clean_check=lambda _: pytest.fail())

    assert result == mass_fix.EXIT_DRY_RUN
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert "dry-run" in output.out
    assert output.err == ""


@pytest.mark.parametrize(
    ("arguments", "expected_exit"),
    [
        (["--dry-run"], mass_fix.EXIT_DRY_RUN),
        (
            ["--apply", "--confirm", "--dry-run"],
            mass_fix.EXIT_AUTHORIZATION_REQUIRED,
        ),
    ],
)
def test_explicit_dry_run_combinations_create_no_artifacts(
    tmp_path, capsys, arguments, expected_exit
):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)

    result = mass_fix.main(
        arguments,
        source_path=source,
        clean_check=lambda _: pytest.fail("clean check must not run"),
        candidate_persister=lambda *_: pytest.fail("persister must not run"),
    )

    assert result == expected_exit
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert str(source) not in output.out + output.err
    assert "Traceback" not in output.out + output.err


@pytest.mark.parametrize("flag", ["--apply", "--confirm"])
def test_one_apply_flag_is_rejected_without_read_or_artifacts(tmp_path, flag, capsys):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)

    result = mass_fix.main([flag], source_path=source, clean_check=lambda _: pytest.fail())

    assert result == mass_fix.EXIT_AUTHORIZATION_REQUIRED
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert str(source) not in output.out
    assert "Traceback" not in output.out + output.err


def test_abbreviated_or_unknown_flag_is_rejected_without_echoing_input(tmp_path, capsys):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        mass_fix.main(["--app=private-value"], source_path=source)

    assert exit_info.value.code == 2
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert "private-value" not in output.out + output.err
    assert "Traceback" not in output.out + output.err


def test_dirty_worktree_rejects_before_any_persistent_write(tmp_path, capsys):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)

    result = mass_fix.main(
        ["--apply", "--confirm"],
        source_path=source,
        clean_check=lambda _: False,
        candidate_persister=lambda *_: pytest.fail("persister must not run"),
    )

    assert result == mass_fix.EXIT_GIT_REJECTED
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert str(source) not in output.out
    assert "Traceback" not in output.out + output.err


def test_invalid_candidate_is_rejected_before_persistence(tmp_path, capsys):
    source = _write_broken_source(tmp_path)
    before = _artifacts(tmp_path)
    invalid = mass_fix.RepairCandidate("def still_broken(", 0, 0, 1)

    result = mass_fix.main(
        ["--apply", "--confirm"],
        source_path=source,
        clean_check=lambda _: True,
        candidate_builder=lambda _: invalid,
        candidate_persister=lambda *_: pytest.fail("persister must not run"),
    )

    assert result == mass_fix.EXIT_INVALID_SOURCE
    assert _artifacts(tmp_path) == before
    output = capsys.readouterr()
    assert "Traceback" not in output.out + output.err


def test_double_confirm_persists_backup_before_valid_candidate(tmp_path, capsys):
    source = _write_broken_source(tmp_path)
    original = source.read_bytes()
    candidate = "def repaired():\n    pass\n"
    repair = mass_fix.RepairCandidate(candidate, 0, 1, 0)
    events: list[tuple[str, Path, bytes]] = []

    def write_backup(path: Path, content: bytes) -> None:
        events.append(("backup", path, content))
        path.write_bytes(content)

    def replace_source(path: Path, content: bytes) -> None:
        assert events and events[0][0] == "backup"
        events.append(("source", path, content))
        path.write_bytes(content)

    def persist(path: Path, original_content: bytes, candidate_text: str) -> Path:
        return mass_fix.persist_candidate(
            path,
            original_content,
            candidate_text,
            backup_writer=write_backup,
            source_replacer=replace_source,
        )

    result = mass_fix.main(
        ["--apply", "--confirm"],
        source_path=source,
        clean_check=lambda _: True,
        candidate_builder=lambda _: repair,
        candidate_persister=persist,
    )

    assert result == 0
    assert [event[0] for event in events] == ["backup", "source"]
    backup = events[0][1]
    assert events[0] == ("backup", backup, original)
    assert events[1] == ("source", source, candidate.encode("utf-8"))
    digest = hashlib.sha256(original).hexdigest()[:16]
    assert backup.name == f"legacy.py.bak.mass-fix-{digest}"
    assert backup.read_bytes() == original
    assert source.read_text(encoding="utf-8") == candidate
    ast.parse(source.read_text(encoding="utf-8"))
    output = capsys.readouterr()
    assert "Traceback" not in output.out + output.err


def test_invalid_persist_candidate_never_calls_backup_or_source_writer(tmp_path):
    source = _write_broken_source(tmp_path)

    with pytest.raises(SyntaxError):
        mass_fix.persist_candidate(
            source,
            source.read_bytes(),
            "def invalid(",
            backup_writer=lambda *_: pytest.fail("backup must not run"),
            source_replacer=lambda *_: pytest.fail("source writer must not run"),
        )


def test_backup_failure_preserves_source_and_never_calls_source_writer(tmp_path):
    source = _write_broken_source(tmp_path)
    original = source.read_bytes()

    with pytest.raises(OSError):
        mass_fix.persist_candidate(
            source,
            original,
            "def repaired():\n    pass\n",
            backup_writer=lambda *_: (_ for _ in ()).throw(OSError("injected")),
            source_replacer=lambda *_: pytest.fail("source writer must not run"),
        )

    assert source.read_bytes() == original
    assert _artifacts(tmp_path) == {source.name: original}


def test_post_backup_source_race_preserves_foreign_content_and_skips_replacer(tmp_path):
    source = _write_broken_source(tmp_path)
    original = source.read_bytes()
    foreign_content = b"# independently updated\n"
    replacer_calls: list[tuple[Path, bytes]] = []

    def backup_then_mutate_source(_path: Path, _content: bytes) -> None:
        source.write_bytes(foreign_content)

    with pytest.raises(OSError):
        mass_fix.persist_candidate(
            source,
            original,
            "def repaired():\n    pass\n",
            backup_writer=backup_then_mutate_source,
            source_replacer=lambda path, content: replacer_calls.append((path, content)),
        )

    assert replacer_calls == []
    assert source.read_bytes() == foreign_content


def test_real_backup_is_exclusive_idempotent_and_fsyncs_new_content(
    tmp_path, monkeypatch
):
    original = b"def original():\n    pass\n"
    backup_path = tmp_path / "legacy.py.bak.mass-fix-test"
    fsync_calls: list[int] = []
    monkeypatch.setattr(mass_fix.os, "fsync", fsync_calls.append)

    mass_fix._write_backup(backup_path, original)

    assert backup_path.read_bytes() == original
    assert len(fsync_calls) == 1

    # The same deterministic backup is accepted without truncation or rewrite.
    mass_fix._write_backup(backup_path, original)

    assert backup_path.read_bytes() == original
    assert len(fsync_calls) == 1


def test_atomic_replace_failure_preserves_source_and_removes_temporary_file(
    tmp_path, monkeypatch
):
    source = _write_broken_source(tmp_path)
    original = source.read_bytes()
    monkeypatch.setattr(
        mass_fix.os,
        "replace",
        lambda *_: (_ for _ in ()).throw(OSError("injected")),
    )

    with pytest.raises(OSError):
        mass_fix._replace_source_atomically(source, b"def replaced():\n    pass\n")

    assert source.read_bytes() == original
    assert list(tmp_path.glob(".legacy.py.mass-fix-*")) == []


def test_batch_wrapper_uses_only_project_venv_and_forwards_arguments():
    source = (Path(__file__).resolve().parents[2] / "Mass_Fix.bat").read_text(
        encoding="utf-8-sig"
    )
    lowered = source.lower()

    assert 'set "pyexe=%~dp0.venv\\scripts\\python.exe"' in lowered
    assert 'if not exist "%pyexe%" (' in lowered
    assert '"%pyexe%" -b -x utf8 "%~dp0mass_fix.py" %*' in lowered
    assert 'set "exitcode=%errorlevel%"' in lowered
    assert "endlocal & exit /b %exitcode%" in lowered
    assert "--apply" not in lowered
    assert "--confirm" not in lowered
    assert "pause" not in lowered
    assert "where " not in lowered
    assert "c:\\users\\" not in lowered
    assert "traceback" not in lowered
