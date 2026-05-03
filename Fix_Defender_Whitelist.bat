@echo off
REM ============================================================
REM  Fix_Defender_Whitelist.bat - 把 torch/christine/python 加入
REM  Windows Defender 白名單，大幅加速首次 torch 載入 (5~15s -> 1~3s)
REM  需要「系統管理員」權限。
REM ============================================================
REM 自動提權
>nul 2>&1 net session || (
    echo [!] 需要系統管理員權限 ^(正在嘗試自動提權...^)
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

chcp 65001 >nul 2>&1
title Fix Defender Whitelist for Christine
color 0A
echo.
echo ============================================
echo   加入 Windows Defender 白名單
echo ============================================
echo.

set "TORCH_DIR=C:\Users\josh1\AppData\Local\Programs\Python\Python313\Lib\site-packages\torch"
set "CHRISTINE_DIR=F:\christine"
set "PYDIR=C:\Users\josh1\AppData\Local\Programs\Python\Python313"

echo [1] 加入 torch 資料夾:  %TORCH_DIR%
powershell -NoProfile -Command "Add-MpPreference -ExclusionPath '%TORCH_DIR%'"
echo.

echo [2] 加入 christine 資料夾:  %CHRISTINE_DIR%
powershell -NoProfile -Command "Add-MpPreference -ExclusionPath '%CHRISTINE_DIR%'"
echo.

echo [3] 加入 Python 安裝資料夾:  %PYDIR%
powershell -NoProfile -Command "Add-MpPreference -ExclusionPath '%PYDIR%'"
echo.

echo [4] 加入 python.exe 處理程序白名單
powershell -NoProfile -Command "Add-MpPreference -ExclusionProcess 'python.exe'"
echo.

echo [5] 目前白名單:
powershell -NoProfile -Command "(Get-MpPreference).ExclusionPath | ForEach-Object { '    - ' + $_ }"
echo.

echo ============================================
echo   完成^^！下次 torch 載入應該快很多
echo   ^(4 GB 的 torch DLL 不再被即時掃描^)
echo ============================================
pause
