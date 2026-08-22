# Christine V1485 Windows 10+ PowerShell launcher.
[CmdletBinding()]
param(
    [int]$Cpu = 0,
    [double]$Gpu = 0.80,
    [switch]$NoGpu,
    [switch]$Fast,
    [switch]$Check,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Pass
)

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$ProjectRoot = $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    Write-Host "[Christine] Unable to resolve the project directory." -ForegroundColor Red
    exit 126
}

$PyExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BootScript = Join-Path $ProjectRoot "boot_christine.py"

if (-not (Test-Path -LiteralPath $PyExe -PathType Leaf)) {
    Write-Host "[Christine] Project Python environment is unavailable." -ForegroundColor Red
    exit 127
}
if (-not (Test-Path -LiteralPath $BootScript -PathType Leaf)) {
    Write-Host "[Christine] Project bootstrap is unavailable." -ForegroundColor Red
    exit 127
}

try {
    Set-Location -LiteralPath $ProjectRoot -ErrorAction Stop
} catch {
    Write-Host "[Christine] Unable to open the project directory." -ForegroundColor Red
    exit 126
}

$BootArgs = @()
if ($Cpu -gt 0)     { $BootArgs += @("--cpu", "$Cpu") }
if ($Gpu -ne 0.80)  { $BootArgs += @("--gpu", "$Gpu") }
if ($NoGpu)         { $BootArgs += "--nogpu" }
if ($Fast)          { $BootArgs += "--fast" }
if ($Check)         { $BootArgs += "--check" }
if ($Pass)          { $BootArgs += $Pass }

Write-Host "  [Christine V1485] Waking up..." -ForegroundColor Magenta
& $PyExe -X utf8 $BootScript @BootArgs
exit [int]$LASTEXITCODE
