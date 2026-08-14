@echo off
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Christine G3 Frontier Runtime
color 0B

cd /d "%~dp0"

echo.
echo ===============================================================
echo  Christine G3 Frontier Runtime
echo  Task Contract ^| ORBIT Web ^| 5D9A Memory ^| ARGUS Verify
echo ===============================================================
echo.

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [G3] Starting with uv...
    uv run python -X utf8 "%~dp0christine_g3_frontier.py" %*
    set ERR=%ERRORLEVEL%
) else (
    echo [G3] uv not found. Falling back to python...
    python -X utf8 "%~dp0christine_g3_frontier.py" %*
    set ERR=%ERRORLEVEL%
)

if %ERR% NEQ 0 (
    echo.
    echo [!] Christine G3 exited with code %ERR%
    echo [!] Make sure dependencies are installed and Ollama is running.
    pause
)
endlocal
