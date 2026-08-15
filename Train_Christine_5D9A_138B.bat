@echo off
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set CHRISTINE_5D9A_TOKEN_CAPACITY=138000000000
title Christine ATLAS-138 Trainer
color 0A
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage:
    echo   Train_Christine_5D9A_138B.bat dataset.jsonl
    echo.
    echo JSONL row example:
    echo   {"text":"...","source":"...","source_trust":0.85,"namespace":"world"}
    pause
    exit /b 2
)

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    uv run python -X utf8 -m christine_g3v2.train138_cli "%~1" --show-objectives
) else (
    python -X utf8 -m christine_g3v2.train138_cli "%~1" --show-objectives
)
set ERR=%ERRORLEVEL%
if %ERR% NEQ 0 pause
endlocal
