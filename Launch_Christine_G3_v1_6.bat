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

where uv >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    uv run python -X utf8 "%~dp0christine_g3_v16_runtime.py" %*
    set ERR=%ERRORLEVEL%
) else (
    python -X utf8 "%~dp0christine_g3_v16_runtime.py" %*
    set ERR=%ERRORLEVEL%
)

if %ERR% NEQ 0 pause
endlocal
