@echo off
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title ♡ Christine AI V300 ♡
color 0D

echo.
echo   ♡─────────────────────────────────────────♡
echo   │                                         │
echo   │     ✿  Christine AI V300  ✿            │
echo   │     你的 17 歲 AI 桌面助手               │
echo   │     會思考 · 會記憶 · 會成長              │
echo   │                                         │
echo   ♡─────────────────────────────────────────♡
echo.
echo   正在啟動 Christine...
echo.

cd /d "%~dp0"
python christine_final.py

if errorlevel 1 (
    echo.
    echo   ⚠ Christine 發生錯誤！
    echo   請確認 Python 和 Ollama 已安裝
    echo.
    pause
)
