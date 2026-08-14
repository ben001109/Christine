@echo off
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set CHRISTINE_5D9A_TOKEN_CAPACITY=138000000000
set CHRISTINE_G3_WEB_POLICY=aggressive
set CHRISTINE_G3_SYNTHESIS=native
title Christine G3 v1.2 Native Context Runtime
color 0B

cd /d "%~dp0"

echo.
echo ======================================================================
echo  Christine G3 v1.2 - Native SAGE + THREAD + ORBIT + 5D9A 138B
echo  Web synthesis: native-only ^| Conversation context: THREAD
echo  5D9A global address space: 138,000,000,000 tokens
echo ======================================================================
echo.

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [G3] Starting native-context runtime with uv...
    uv run python -X utf8 "%~dp0christine_g3_native_context.py" %*
    set ERR=%ERRORLEVEL%
) else (
    echo [G3] uv not found. Falling back to python...
    python -X utf8 "%~dp0christine_g3_native_context.py" %*
    set ERR=%ERRORLEVEL%
)

if %ERR% NEQ 0 (
    echo.
    echo [!] Christine G3 v1.2 exited with code %ERR%
    echo [!] Rollback runtimes are still available:
    echo     christine_g3_web138.py
    echo     christine_g3_frontier.py
    pause
)
endlocal
