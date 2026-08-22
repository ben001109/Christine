import re
import unittest
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_BATCH_LAUNCHERS = (
    "Launch_Christine_V600.bat",
    "Start_Christine.bat",
    "啟動Christine (2).bat",
    "啟動Christine.bat",
)
SUPPORTED_POWERSHELL_LAUNCHERS = ("啟動Christine.ps1",)
NON_LAUNCHER_WINDOWS_SCRIPTS = {
    "Diagnose_Christine.bat",
    "Fix_Defender_Whitelist.bat",
    "Fix_Torch_Reinstall.bat",
    "Mass_Fix.bat",
    "建立桌面捷徑.ps1",
}


def _read_script(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8-sig")


@dataclass(frozen=True)
class BatchBlock:
    header: str
    body: tuple[str, ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _parse_batch(source: str) -> tuple[str | BatchBlock, ...]:
    lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().lower().startswith("rem ")
    ]
    nodes: list[str | BatchBlock] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        _require(line != ")", "unexpected batch block terminator")
        if line.endswith("("):
            body: list[str] = []
            index += 1
            while index < len(lines) and lines[index] != ")":
                _require(not lines[index].endswith("("), "nested batch block is unsupported")
                body.append(lines[index])
                index += 1
            _require(index < len(lines), f"unterminated batch block: {line}")
            nodes.append(BatchBlock(line, tuple(body)))
        else:
            nodes.append(line)
        index += 1
    return tuple(nodes)


def _validate_batch_flow(source: str) -> None:
    nodes = _parse_batch(source)
    cd_guard = BatchBlock(
        'cd /d "%~dp0" || (',
        (
            "echo [Christine] Unable to open the project directory. 1>&2",
            "endlocal",
            "exit /b 126",
        ),
    )
    interpreter_guard = BatchBlock(
        'if not exist "%PYEXE%" (',
        (
            "echo [Christine] Project Python environment is unavailable. 1>&2",
            "endlocal",
            "exit /b 127",
        ),
    )
    bootstrap_guard = BatchBlock(
        'if not exist "%~dp0boot_christine.py" (',
        (
            "echo [Christine] Project bootstrap is unavailable. 1>&2",
            "endlocal",
            "exit /b 127",
        ),
    )
    expected_tail: tuple[str | BatchBlock, ...] = (
        cd_guard,
        'set "PYEXE=%~dp0.venv\\Scripts\\python.exe"',
        interpreter_guard,
        bootstrap_guard,
        '"%PYEXE%" -X utf8 "%~dp0boot_christine.py" %*',
        'set "EXITCODE=%ERRORLEVEL%"',
        "endlocal & exit /b %EXITCODE%",
    )

    _require(cd_guard in nodes, "project-root guard is missing")
    tail_index = nodes.index(cd_guard)
    _require(nodes[tail_index:] == expected_tail, "batch control-flow tail is not trusted")
    allowed_prelude_prefixes = (
        "@echo off",
        "setlocal EnableExtensions DisableDelayedExpansion",
        "chcp 65001 >nul 2>&1",
        'set "PYTHONUTF8=1"',
        'set "PYTHONIOENCODING=utf-8"',
        'set "PYTHONLEGACYWINDOWSSTDIO=0"',
        "title ",
        "color ",
    )
    for node in nodes[:tail_index]:
        _require(isinstance(node, str), "control flow is forbidden in batch prelude")
        _require(
            node.startswith(allowed_prelude_prefixes),
            f"unexpected executable batch prelude: {node}",
        )


def _powershell_lines(source: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "} catch {":
            lines.extend(("}", "catch {"))
        else:
            lines.append(line)
    return tuple(lines)


def _brace_delta(line: str) -> int:
    in_single_quote = False
    in_double_quote = False
    delta = 0
    for char in line:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == "{":
                delta += 1
            elif char == "}":
                delta -= 1
    _require(not in_single_quote and not in_double_quote, "unterminated PowerShell string")
    return delta


def _powershell_top_level(lines: tuple[str, ...]) -> tuple[str, ...]:
    depth = 0
    top_level: list[str] = []
    for line in lines:
        if line == "}":
            depth -= 1
            _require(depth >= 0, "unexpected PowerShell block terminator")
            continue
        if depth == 0:
            top_level.append(line)
        depth += _brace_delta(line)
        _require(depth >= 0, "invalid PowerShell block depth")
    _require(depth == 0, "unterminated PowerShell block")
    return tuple(top_level)


def _powershell_block(lines: tuple[str, ...], header: str) -> tuple[str, ...]:
    _require(lines.count(header) == 1, f"PowerShell block must be unique: {header}")
    start = lines.index(header)
    depth = _brace_delta(header)
    _require(depth == 1, f"invalid PowerShell block header: {header}")
    body: list[str] = []
    for line in lines[start + 1 :]:
        depth += _brace_delta(line)
        if depth == 0:
            return tuple(body)
        _require(depth > 0, f"invalid PowerShell block: {header}")
        body.append(line)
    raise ValueError(f"unterminated PowerShell block: {header}")


def _validate_powershell_flow(source: str) -> None:
    lines = _powershell_lines(source)
    top_level = _powershell_top_level(lines)
    root_guard = "if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {"
    interpreter_guard = "if (-not (Test-Path -LiteralPath $PyExe -PathType Leaf)) {"
    bootstrap_guard = "if (-not (Test-Path -LiteralPath $BootScript -PathType Leaf)) {"
    expected_tail = (
        "$ProjectRoot = $PSScriptRoot",
        root_guard,
        '$PyExe = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"',
        '$BootScript = Join-Path $ProjectRoot "boot_christine.py"',
        interpreter_guard,
        bootstrap_guard,
        "try {",
        "catch {",
        "$BootArgs = @()",
        'if ($Cpu -gt 0)     { $BootArgs += @("--cpu", "$Cpu") }',
        'if ($Gpu -ne 0.80)  { $BootArgs += @("--gpu", "$Gpu") }',
        'if ($NoGpu)         { $BootArgs += "--nogpu" }',
        'if ($Fast)          { $BootArgs += "--fast" }',
        'if ($Check)         { $BootArgs += "--check" }',
        "if ($Pass)          { $BootArgs += $Pass }",
        'Write-Host "  [Christine V1485] Waking up..." -ForegroundColor Magenta',
        "& $PyExe -X utf8 $BootScript @BootArgs",
        "exit [int]$LASTEXITCODE",
    )

    _require(expected_tail[0] in top_level, "PowerShell project root is missing")
    tail_index = top_level.index(expected_tail[0])
    _require(top_level[tail_index:] == expected_tail, "PowerShell control flow is not trusted")
    _require(
        _powershell_block(lines, root_guard)
        == (
            'Write-Host "[Christine] Unable to resolve the project directory." '
            "-ForegroundColor Red",
            "exit 126",
        ),
        "PowerShell root failure must exit 126",
    )
    _require(
        _powershell_block(lines, interpreter_guard)
        == (
            'Write-Host "[Christine] Project Python environment is unavailable." '
            "-ForegroundColor Red",
            "exit 127",
        ),
        "PowerShell interpreter failure must exit 127",
    )
    _require(
        _powershell_block(lines, bootstrap_guard)
        == (
            'Write-Host "[Christine] Project bootstrap is unavailable." -ForegroundColor Red',
            "exit 127",
        ),
        "PowerShell bootstrap failure must exit 127",
    )
    _require(
        _powershell_block(lines, "try {")
        == ("Set-Location -LiteralPath $ProjectRoot -ErrorAction Stop",),
        "PowerShell project-root transition is not guarded",
    )
    _require(
        _powershell_block(lines, "catch {")
        == (
            'Write-Host "[Christine] Unable to open the project directory." -ForegroundColor Red',
            "exit 126",
        ),
        "PowerShell location failure must exit 126",
    )


def _move_line_before(source: str, moving: str, destination: str) -> str:
    lines = source.splitlines()
    moving_index = next(i for i, line in enumerate(lines) if line.strip() == moving)
    moving_line = lines.pop(moving_index)
    destination_index = next(
        i for i, line in enumerate(lines) if line.strip() == destination
    )
    lines.insert(destination_index, moving_line)
    return "\n".join(lines)


class WindowsLauncherContractTests(unittest.TestCase):
    def test_root_windows_scripts_have_an_explicit_security_classification(self):
        discovered = {
            path.name
            for pattern in ("*.bat", "*.cmd", "*.ps1")
            for path in REPO_ROOT.glob(pattern)
        }
        classified = (
            set(SUPPORTED_BATCH_LAUNCHERS)
            | set(SUPPORTED_POWERSHELL_LAUNCHERS)
            | NON_LAUNCHER_WINDOWS_SCRIPTS
        )

        self.assertEqual(discovered, classified)

    def test_supported_batch_launchers_use_only_project_bootstrap(self):
        for name in SUPPORTED_BATCH_LAUNCHERS:
            with self.subTest(name=name):
                source = _read_script(name)
                lowered = source.lower()

                _validate_batch_flow(source)

                self.assertNotIn("christine_final.py", lowered)
                self.assertEqual(lowered.count("boot_christine.py"), 2)
                self.assertIn('set "pyexe=%~dp0.venv\\scripts\\python.exe"', lowered)
                self.assertIn('cd /d "%~dp0" || (', lowered)
                self.assertIn('if not exist "%pyexe%" (', lowered)
                self.assertIn(
                    '"%pyexe%" -x utf8 "%~dp0boot_christine.py" %*', lowered
                )
                self.assertEqual(
                    lowered.count('"%pyexe%" -x utf8 "%~dp0boot_christine.py" %*'),
                    1,
                )
                self.assertIn('set "exitcode=%errorlevel%"', lowered)
                self.assertIn("endlocal & exit /b %exitcode%", lowered)
                self.assertNotIn("where ", lowered)
                self.assertNotIn('set "pyexe=python"', lowered)
                self.assertNotRegex(
                    lowered,
                    re.compile(r"(?m)^\s*(?:python|python3|py)(?:\.exe)?(?:\s|$)"),
                )
                self.assertNotRegex(
                    lowered,
                    re.compile(r"(?i)[a-z]:\\[^\r\n]*python(?:\.exe)?"),
                )
                self.assertNotIn("--legacy-monolith", lowered)
                self.assertNotIn("--allow-legacy-side-effects", lowered)
                self.assertIn("exit /b 126", lowered)
                self.assertIn("exit /b 127", lowered)

    def test_supported_powershell_launcher_uses_only_project_bootstrap(self):
        source = _read_script(SUPPORTED_POWERSHELL_LAUNCHERS[0])
        lowered = source.lower()

        _validate_powershell_flow(source)

        self.assertNotIn("christine_final.py", lowered)
        self.assertEqual(lowered.count("boot_christine.py"), 1)
        self.assertIn("$projectroot = $psscriptroot", lowered)
        self.assertIn(
            '$pyexe = join-path $projectroot ".venv\\scripts\\python.exe"', lowered
        )
        self.assertIn('$bootscript = join-path $projectroot "boot_christine.py"', lowered)
        self.assertIn("set-location -literalpath $projectroot -erroraction stop", lowered)
        self.assertIn("$bootargs = @()", lowered)
        self.assertIn('$bootargs += @("--cpu", "$cpu")', lowered)
        self.assertIn('$bootargs += @("--gpu", "$gpu")', lowered)
        self.assertIn('$bootargs += "--nogpu"', lowered)
        self.assertIn('$bootargs += "--fast"', lowered)
        self.assertIn('$bootargs += "--check"', lowered)
        self.assertIn("$bootargs += $pass", lowered)
        self.assertIn("[parameter(valuefromremainingarguments = $true)]", lowered)
        self.assertIn("& $pyexe -x utf8 $bootscript @bootargs", lowered)
        self.assertEqual(lowered.count("& $pyexe -x utf8 $bootscript @bootargs"), 1)
        self.assertIn("exit [int]$lastexitcode", lowered)
        self.assertNotIn("get-command", lowered)
        self.assertNotIn('$pyexe = "python"', lowered)
        self.assertNotRegex(
            lowered,
            re.compile(r"(?m)^\s*&\s*(?:python|python3|py)(?:\.exe)?(?:\s|$)"),
        )
        self.assertNotRegex(
            lowered,
            re.compile(r"(?i)[a-z]:\\[^\r\n]*python(?:\.exe)?"),
        )
        self.assertNotIn("--legacy-monolith", lowered)
        self.assertNotIn("--allow-legacy-side-effects", lowered)
        self.assertIn("exit 126", lowered)
        self.assertEqual(lowered.count("exit 127"), 2)

    def test_batch_flow_rejects_invocation_before_bootstrap_guard(self):
        source = _read_script(SUPPORTED_BATCH_LAUNCHERS[0])
        reordered = _move_line_before(
            source,
            '"%PYEXE%" -X utf8 "%~dp0boot_christine.py" %*',
            'if not exist "%~dp0boot_christine.py" (',
        )

        with self.assertRaisesRegex(ValueError, "control-flow tail"):
            _validate_batch_flow(reordered)

    def test_powershell_flow_rejects_invocation_before_interpreter_guard(self):
        source = _read_script(SUPPORTED_POWERSHELL_LAUNCHERS[0])
        reordered = _move_line_before(
            source,
            "& $PyExe -X utf8 $BootScript @BootArgs",
            "if (-not (Test-Path -LiteralPath $PyExe -PathType Leaf)) {",
        )

        with self.assertRaisesRegex(ValueError, "control flow"):
            _validate_powershell_flow(reordered)


if __name__ == "__main__":
    unittest.main()
