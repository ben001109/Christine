@echo off
REM Christine V1485 Windows 10+ launcher.
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title Christine V1485
color 0D

cd /d "%~dp0" || (
    echo [Christine] Unable to open the project directory. 1>&2
    endlocal
    exit /b 126
)

set "PYEXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [Christine] Project Python environment is unavailable. 1>&2
    endlocal
    exit /b 127
)
if not exist "%~dp0boot_christine.py" (
    echo [Christine] Project bootstrap is unavailable. 1>&2
    endlocal
    exit /b 127
)

"%PYEXE%" -X utf8 "%~dp0boot_christine.py" %*
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
