from pathlib import Path
import zipfile

from tools.verify_package_wheel import main, verify_package_wheel


DIST_INFO = "christine-0.2.0a1.dist-info"


def _write_wheel(
    path: Path,
    *extra_members: str,
    entry_points: str = "[console_scripts]\nchristine-package-readiness = christine.release_readiness:main\n",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    members = {
        "christine/__init__.py": '"""Christine package."""\n',
        "christine/release_readiness.py": "def main(): pass\n",
        f"{DIST_INFO}/METADATA": "Metadata-Version: 2.1\nName: christine\n",
        f"{DIST_INFO}/WHEEL": "Wheel-Version: 1.0\n",
        f"{DIST_INFO}/RECORD": "",
        f"{DIST_INFO}/entry_points.txt": entry_points,
    }
    members.update({member: "blocked" for member in extra_members})
    with zipfile.ZipFile(path, "w") as archive:
        for member, content in members.items():
            archive.writestr(member, content)
    return path


def test_verify_package_wheel_accepts_restricted_package_surface(tmp_path: Path):
    result = verify_package_wheel(_write_wheel(tmp_path / "christine.whl"))

    assert result.valid is True
    assert "christine/release_readiness.py" in result.members


def test_verify_package_wheel_rejects_state_and_legacy_members(tmp_path: Path):
    result = verify_package_wheel(
        _write_wheel(
            tmp_path / "christine.whl",
            "data/session.sqlite",
            "christine_final.py",
            "backups/recovery.zip",
        )
    )

    assert result.valid is False
    assert any(error.startswith("data/session.sqlite:") for error in result.errors)
    assert any(error.startswith("christine_final.py:") for error in result.errors)
    assert any(error.startswith("backups/recovery.zip:") for error in result.errors)


def test_verify_package_wheel_rejects_non_package_surface_member(tmp_path: Path):
    result = verify_package_wheel(_write_wheel(tmp_path / "christine.whl", "tools/inspect_mem.py"))

    assert result.valid is False
    assert any(error.startswith("tools/inspect_mem.py:") for error in result.errors)


def test_verify_package_wheel_rejects_extra_public_entry_point(tmp_path: Path):
    result = verify_package_wheel(
        _write_wheel(
            tmp_path / "christine.whl",
            entry_points=(
                "[console_scripts]\n"
                "christine-package-readiness = christine.release_readiness:main\n"
                "christine = christine.gui.app:main\n"
            ),
        )
    )

    assert result.valid is False
    assert "wheel entry point must expose only the package readiness command" in result.errors


def test_verify_package_wheel_rejects_traversal_and_absolute_directory_members(tmp_path: Path):
    wheel = _write_wheel(tmp_path / "christine.whl")
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("../recovery/", "")
        archive.writestr("/data/", "")

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.members == ()
    assert result.errors == ("wheel contains an unsafe member path", "wheel contains an unsafe member path")


def test_verify_package_wheel_rejects_duplicate_member(tmp_path: Path):
    wheel = _write_wheel(tmp_path / "christine.whl")
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("christine/__init__.py", "duplicate")

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("duplicate wheel member path: christine/__init__.py",)


def test_verify_package_wheel_rejects_windows_style_member(tmp_path: Path):
    wheel = _write_wheel(tmp_path / "christine.whl")
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr(r"C:\state\session.db", "blocked")

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("wheel contains an unsafe member path",)


def test_verify_package_wheel_rejects_windows_drive_and_unc_members(tmp_path: Path):
    wheel = _write_wheel(tmp_path / "christine.whl")
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("C:/state/session.db", "blocked")
        archive.writestr("//server/share/state.db", "blocked")

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("wheel contains an unsafe member path", "wheel contains an unsafe member path")


def test_verify_package_wheel_rejects_non_metadata_dist_info_payloads(tmp_path: Path):
    result = verify_package_wheel(
        _write_wheel(
            tmp_path / "christine.whl",
            f"{DIST_INFO}/state.db",
            f"{DIST_INFO}/archive.zip",
        )
    )

    assert result.valid is False
    assert any(error.startswith(f"{DIST_INFO}/state.db:") for error in result.errors)
    assert any(error.startswith(f"{DIST_INFO}/archive.zip:") for error in result.errors)


def test_verify_package_wheel_rejects_malformed_entry_points_without_echoing_content(tmp_path: Path, capsys):
    wheel = _write_wheel(
        tmp_path / "christine.whl",
        entry_points="[console_scripts\nuntrusted-payload = %(missing)s\n",
    )

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("wheel entry point metadata is invalid",)
    assert "untrusted-payload" not in "\n".join(result.errors)
    assert main([str(wheel)]) == 1
    assert "untrusted-payload" not in capsys.readouterr().out


def test_verify_package_wheel_rejects_invalid_utf8_entry_points_without_echoing_content(tmp_path: Path, capsys):
    wheel = _write_wheel(
        tmp_path / "christine.whl",
        entry_points=b"[console_scripts]\nuntrusted-\xff = blocked\n",
    )

    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("wheel entry point metadata is invalid",)
    assert "untrusted" not in "\n".join(result.errors)
    assert main([str(wheel)]) == 1
    assert "untrusted" not in capsys.readouterr().out


def test_verify_package_wheel_rejects_entry_point_read_error_without_echoing_content(tmp_path: Path, monkeypatch, capsys):
    wheel = _write_wheel(tmp_path / "christine.whl")

    def raise_read_error(*_args, **_kwargs):
        raise OSError("untrusted read failure")

    monkeypatch.setattr(Path, "read_text", raise_read_error)
    result = verify_package_wheel(wheel)

    assert result.valid is False
    assert result.errors == ("wheel entry point metadata is invalid",)
    assert "untrusted" not in "\n".join(result.errors)
    assert main([str(wheel)]) == 1
    assert "untrusted" not in capsys.readouterr().out
