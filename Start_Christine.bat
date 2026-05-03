@echo off
REM =============================================================
REM  Start_Christine.bat - V1485 Paper-Aligned Boot Launcher
REM  Auto CPU/GPU budget + Paper Psi self-check + christine_final
REM =============================================================
setlocal
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Christine V1485
color 0D

cd /d "%~dp0"

set "PYEXE=C:\Users\josh1\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo.
echo   [Christine V1485] Waking up... (CPU/GPU budget + Paper self-check)
echo.

"%PYEXE%" -X utf8 "%~dp0boot_christine.py" %*
set ERR=%ERRORLEVEL%

if %ERR% NEQ 0 (
    echo.
    echo   [!] Boot launcher exited with code %ERR%
    pause
)
endlocal
