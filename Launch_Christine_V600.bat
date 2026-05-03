@echo off
REM ============================================================
REM   Christine AI V600 — 啟動腳本 (Launch_Christine_V600.bat)
REM   自動 UTF-8 修正 + venv 偵測 + 錯誤日誌保留視窗
REM ============================================================

setlocal EnableExtensions EnableDelayedExpansion

REM --- 1) 切到此 .bat 所在資料夾 ----------------------------------
cd /d "%~dp0"

REM --- 2) 強制整個環境使用 UTF-8（解 CP950 / 中文亂碼根本問題）--
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONLEGACYWINDOWSSTDIO=0"

REM --- 3) 視窗外觀 -----------------------------------------------
title Christine AI V600  -  Autonomous Agent
color 0D

echo.
echo   ============================================================
echo      Christine AI V600  -  Loading...
echo      Working dir: %CD%
echo   ============================================================
echo.

REM --- 4) 決定要用哪個 Python ------------------------------------
set "PYEXE="

if exist "%~dp0venv\Scripts\python.exe" (
    set "PYEXE=%~dp0venv\Scripts\python.exe"
    echo   [OK] 使用 venv:  !PYEXE!
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYEXE=%~dp0.venv\Scripts\python.exe"
    echo   [OK] 使用 .venv: !PYEXE!
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo.
        echo   [X] 找不到 Python. 請安裝 Python 3.10 或建立 venv.
        echo.
        pause
        exit /b 1
    )
    set "PYEXE=python"
    echo   [OK] 使用系統 Python
)

REM --- 5) 確保 data\ 資料夾存在 ----------------------------------
if not exist "%~dp0data" mkdir "%~dp0data"

REM --- 6) 啟動前語法自檢（快速預檢，<1 秒）---------------------
echo   [*] 語法自檢中...
"%PYEXE%" -X utf8 -m py_compile "%~dp0christine_final.py"
if errorlevel 1 (
    echo.
    echo   [X] 語法錯誤! 請檢查 christine_final.py
    echo.
    pause
    exit /b 2
)
echo   [OK] 語法 OK
echo.

REM --- 7) 執行 Christine ----------------------------------------
"%PYEXE%" -X utf8 "%~dp0christine_final.py" %*
set "EXITCODE=%ERRORLEVEL%"

REM --- 8) 若異常離開 -> 保留視窗 + 寫 log ------------------------
if not "%EXITCODE%"=="0" (
    echo.
    echo   ============================================================
    echo     [!] Christine 離開, exit code = %EXITCODE%
    echo     錯誤已追加到 data\launch_error.log
    echo   ============================================================
    >>"%~dp0data\launch_error.log" echo [%date% %time%] exit code=%EXITCODE%
    echo.
    pause
) else (
    echo.
    echo   [OK] Christine 正常結束.
    timeout /t 3 >nul
)

endlocal
exit /b %EXITCODE%
