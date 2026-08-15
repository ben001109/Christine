@echo off
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set CHRISTINE_5D9A_TOKEN_CAPACITY=138000000000
title Christine G3 v2.2 Semantic Router + Memory Hygiene
color 0B
cd /d "%~dp0"
echo.
echo ====================================================================================================
echo  Christine G3 v2.2 - Semantic Router + Memory Hygiene + PRISM
echo  Intent ^> Context ^> 138B/LongDoc/ORBIT ^> Hygiene ^> FactGraph ^> PRISM ^> Verify ^> NOVA
echo  5D9A global address space: 138,000,000,000 tokens
echo ====================================================================================================
echo.
where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    uv run python -X utf8 -m christine_g3v2.cli %*
    set ERR=%ERRORLEVEL%
) else (
    python -X utf8 -m christine_g3v2.cli %*
    set ERR=%ERRORLEVEL%
)
if %ERR% NEQ 0 (
    echo.
    echo [!] Christine G3 v2.2 exited with code %ERR%
    echo [!] v1.x rollback launchers remain available on the feature branch.
    pause
)
endlocal
