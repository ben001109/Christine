@echo off
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set CHRISTINE_5D9A_TOKEN_CAPACITY=138000000000
set CHRISTINE_G3_WEB_POLICY=aggressive
set CHRISTINE_G3_SYNTHESIS=narrative-native
set CHRISTINE_G3_SHOW_SOURCES=domains
set CHRISTINE_G3_NOVA_HISTORY=96
set CHRISTINE_G3_NOVA_RETRIES=3
set CHRISTINE_G3_CONTEXT_STATE=data\g3_context_graph.json
title Christine G3 v1.6 Entity Resolution Runtime
color 0B

cd /d "%~dp0"

echo.
echo ====================================================================================================
echo  Christine G3 v1.6 - Entity Resolution + Evidence Consensus + Context Intent + 5D9A 138B
echo  URL/handle/name resolution happens before narration; low-quality entity noise is rejected.
echo  5D9A global address space: 138,000,000,000 tokens
echo ====================================================================================================
echo.

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [G3] Starting v1.6 with uv...
    uv run python -X utf8 "%~dp0christine_g3_v16_runtime.py" %*
    set ERR=%ERRORLEVEL%
) else (
    echo [G3] uv not found. Falling back to python...
    python -X utf8 "%~dp0christine_g3_v16_runtime.py" %*
    set ERR=%ERRORLEVEL%
)

if %ERR% NEQ 0 (
    echo.
    echo [!] Christine G3 v1.6 exited with code %ERR%
    echo [!] Rollback runtimes are still available:
    echo     christine_g3_v15_runtime.py       ^(v1.5^)
    echo     christine_g3_nova.py              ^(v1.4^)
    echo     christine_g3_narrative_patch.py   ^(v1.3^)
    echo     christine_g3_native_context.py    ^(v1.2^)
    echo     christine_g3_web138.py            ^(v1.1^)
    echo     christine_g3_frontier.py          ^(v1.0^)
    pause
)
endlocal
