# ═══════════════════════════════════════════════════════════════════
#  啟動Christine.ps1 — V1485 PowerShell 啟動器
#  支援參數：  .\啟動Christine.ps1 -Cpu 4 -Gpu 0.5 -Fast
# ═══════════════════════════════════════════════════════════════════
param(
    [int]$Cpu = 0,
    [double]$Gpu = 0.80,
    [switch]$NoGpu,
    [switch]$Fast,
    [switch]$Check,
    [string[]]$Pass
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 | Out-Null

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Here

$PyExe = "C:\Users\josh1\AppData\Local\Programs\Python\Python313\python.exe"
if (-not (Test-Path $PyExe)) { $PyExe = "python" }

$Args = @("$Here\boot_christine.py")
if ($Cpu -gt 0)     { $Args += @("--cpu", "$Cpu") }
if ($Gpu -ne 0.80)  { $Args += @("--gpu", "$Gpu") }
if ($NoGpu)         { $Args += "--nogpu" }
if ($Fast)          { $Args += "--fast" }
if ($Check)         { $Args += "--check" }
if ($Pass)          { $Args += $Pass }

Write-Host ""
Write-Host "  [Christine V1485]  Waking up…" -ForegroundColor Magenta
Write-Host ""

& $PyExe @Args
$ec = $LASTEXITCODE

if ($ec -ne 0) {
    Write-Host ""
    Write-Host "  [!] Boot launcher exited with code $ec" -ForegroundColor Yellow
    Read-Host "Press Enter to close"
}
exit $ec
