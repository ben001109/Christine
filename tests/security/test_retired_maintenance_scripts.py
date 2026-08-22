import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RETIRED_MAINTENANCE_SCRIPTS = (
    "Diagnose_Christine.bat",
    "Fix_Defender_Whitelist.bat",
    "Fix_Torch_Reinstall.bat",
)

_EXPECTED_STUB_LINES = {
    "Diagnose_Christine.bat": (
        "@echo off",
        "setlocal EnableExtensions DisableDelayedExpansion",
        "echo [Christine] 此舊版診斷入口已停用。",
        "echo [Christine] 本檔僅回報停用狀態，不會執行硬體、套件或系統設定檢查。",
        "echo [Christine] 請由維護者依專案鎖定流程進行診斷。",
        "endlocal",
        "exit /b 78",
    ),
    "Fix_Defender_Whitelist.bat": (
        "@echo off",
        "setlocal EnableExtensions DisableDelayedExpansion",
        "echo [Christine] 此舊版安全設定修復入口已停用。",
        "echo [Christine] 本檔不會修改系統安全設定、Python 環境或專案檔案。",
        "echo [Christine] 維護作業僅能依專案鎖定流程由維護者處理。",
        "endlocal",
        "exit /b 78",
    ),
    "Fix_Torch_Reinstall.bat": (
        "@echo off",
        "setlocal EnableExtensions DisableDelayedExpansion",
        "echo [Christine] 此舊版套件修復入口已停用。",
        "echo [Christine] 本檔不會修改系統安全設定、Python 環境或專案檔案。",
        "echo [Christine] 維護作業僅能依專案鎖定流程由維護者處理。",
        "endlocal",
        "exit /b 78",
    ),
}

_FORBIDDEN_POLICY_PATTERNS = (
    re.compile(r"\b(?:add|remove)\s*-\s*mppreference\b", re.IGNORECASE),
    re.compile(r"\bexclusion\s*(?:path|process)\b", re.IGNORECASE),
    re.compile(
        r"(?:\bdefender\b.{0,80}(?:\bexclu\w*\b|白名單)|"
        r"(?:\bexclu\w*\b|白名單).{0,80}\bdefender\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bstart\s*-\s*process\b[^\r\n]*\bverb\b[^\r\n]*\brun\s*as\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:net\s+session|run\s*as(?:\.exe)?|shell\s*execute)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bpip(?:3|\.exe)?\s+(?:install|uninstall)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:python(?:3|\.exe)?|py(?:\.exe)?)\s+-m\s+pip\s+"
        r"(?:install|uninstall)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:set|setx)\s+(?:\"?path\"?\s*=|path\b)", re.IGNORECASE
    ),
    re.compile(
        r"\bwhere(?:\.exe)?\s+(?:python(?:3|\.exe)?|py(?:\.exe)?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:\bpython\b.{0,40}(?:\badd\b|\bappend\b|加入|新增|修復).{0,20}\bpath\b|"
        r"(?:\badd\b|\bappend\b|加入|新增|修復).{0,40}\bpython\b.{0,20}\bpath\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:curl|wget|bitsadmin|certutil)(?:\.exe)?\b", re.IGNORECASE
    ),
    re.compile(r"\binvoke\s*-\s*webrequest\b|https?://", re.IGNORECASE),
)


def _read_script(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8-sig")


def _normalize_for_policy(source: str) -> str:
    return "\n".join(
        " ".join(line.replace("^", "").replace("`", "").split())
        for line in source.splitlines()
    )


def _forbidden_policy_matches(source: str) -> tuple[str, ...]:
    normalized = _normalize_for_policy(source)
    return tuple(
        pattern.pattern
        for pattern in _FORBIDDEN_POLICY_PATTERNS
        if pattern.search(normalized)
    )


def _executable_lines(source: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().lower().startswith("rem ")
    )


class RetiredMaintenanceScriptContractTests(unittest.TestCase):
    def test_retired_script_scope_is_exact_and_tracked(self):
        discovered = {path.name for path in REPO_ROOT.glob("Fix_*.bat")} | {
            "Diagnose_Christine.bat"
        }

        self.assertEqual(discovered, set(RETIRED_MAINTENANCE_SCRIPTS))
        for name in RETIRED_MAINTENANCE_SCRIPTS:
            with self.subTest(name=name):
                self.assertTrue((REPO_ROOT / name).is_file())

    def test_retired_scripts_are_fixed_nonzero_status_only_stubs(self):
        for name in RETIRED_MAINTENANCE_SCRIPTS:
            with self.subTest(name=name):
                source = _read_script(name)
                lines = _executable_lines(source)

                self.assertEqual(lines, _EXPECTED_STUB_LINES[name])
                self.assertFalse(_forbidden_policy_matches(source))

    def test_all_root_windows_scripts_exclude_forbidden_maintenance_controls(self):
        scripts = tuple(
            sorted(
                {
                    path
                    for pattern in ("*.bat", "*.cmd", "*.ps1")
                    for path in REPO_ROOT.glob(pattern)
                }
            )
        )
        self.assertTrue(scripts)

        for path in scripts:
            with self.subTest(name=path.name):
                source = path.read_text(encoding="utf-8-sig")
                self.assertFalse(
                    _forbidden_policy_matches(source),
                    f"forbidden maintenance control in {path.name}",
                )

    def test_forbidden_policy_rejects_execution_and_instruction_forms(self):
        samples = (
            "REM Add-MpPreference -ExclusionPath C:\\unsafe",
            "REM Add^ -^ MpPreference -ExclusionPath C:\\unsafe",
            "echo Remove - MpPreference -ExclusionProcess python.exe",
            "echo 請將 Defender 加入白名單",
            'powershell -Command "Start-Process tool -Verb RunAs"',
            "REM net session",
            "echo 請執行 pip install torch",
            "echo 請執行 p^i^p install torch",
            "REM python -m pip uninstall torch",
            'setx PATH "%PATH%;C:\\Python"',
            "where.exe python.exe",
            "echo Add Python to PATH before starting Christine",
            "REM 把 Python 加入 PATH 後再啟動",
            "echo https://example.invalid/repair.ps1",
            "Invoke-WebRequest https://example.invalid/tool",
            "Invoke`-WebRequest https://example.invalid/tool",
        )

        for source in samples:
            with self.subTest(source=source):
                self.assertTrue(
                    _forbidden_policy_matches(source),
                    f"forbidden maintenance policy escaped detection: {source}",
                )

    def test_user_facing_text_describes_only_locked_maintenance_process(self):
        diagnose = _read_script("Diagnose_Christine.bat")
        self.assertIn("僅回報停用狀態", diagnose)
        self.assertIn("專案鎖定流程", diagnose)

        for name in RETIRED_MAINTENANCE_SCRIPTS:
            with self.subTest(name=name):
                source = _read_script(name)
                self.assertIn("維護者", source)
                self.assertNotRegex(
                    source,
                    re.compile(r"請.{0,20}(?:執行|輸入|貼上|安裝|解除安裝)"),
                )


if __name__ == "__main__":
    unittest.main()
