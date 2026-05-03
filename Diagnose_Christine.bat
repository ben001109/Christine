@echo off
REM ============================================================
REM  Diagnose_Christine.bat - 一鍵診斷三種 GPU/torch 卡頓原因
REM   [1] NVIDIA 驅動是否裝好
REM   [2] PyTorch + CUDA 能否正常載入（測實際耗時）
REM   [3] Windows Defender 白名單狀態
REM  最後給修復建議。
REM ============================================================
setlocal
chcp 65001 >nul 2>&1
title Christine Diagnose
color 0B

cd /d "%~dp0"
set "PYEXE=C:\Users\josh1\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo.
echo =====================================================
echo   CHRISTINE 啟動卡頓診斷工具
echo =====================================================
echo.

echo [1/4] ---- NVIDIA 驅動 (nvidia-smi) ----
nvidia-smi 2>nul
if errorlevel 1 (
    echo    ^!^! 找不到 nvidia-smi^^。可能原因:
    echo       a^) 沒裝 NVIDIA 驅動  =^> 去 https://www.nvidia.com/drivers 下載
    echo       b^) 沒有 NVIDIA 卡      =^> 跳過 GPU^, 用 --notorch --fast 啟動
) else (
    echo    [OK] 驅動正常
)
echo.

echo [2/4] ---- PyTorch + CUDA 載入測試 ----
echo    (若卡住超過 30 秒^, 請按 Ctrl+C 跳過^, 代表 torch/CUDA 有問題^)
"%PYEXE%" -X utf8 "%~dp0_diag_torch.py"
echo.

echo [3/4] ---- Windows Defender 白名單 ----
powershell -NoProfile -Command "try { $ex=(Get-MpPreference).ExclusionPath; if($ex){ '    目前白名單:'; $ex | ForEach-Object { '      - ' + $_ } } else { '    [無白名單] 建議加入 torch 資料夾' } } catch { '    無法查詢 (需管理員權限)' }"
echo.

echo [4/4] ---- 修復建議 ----
echo.
echo   [A] 要把 torch 資料夾加入 Defender 白名單 (加速首次載入):
echo       1. 以「系統管理員」身份開啟 PowerShell
echo       2. 複製貼上以下指令:
echo.
echo          Add-MpPreference -ExclusionPath "C:\Users\josh1\AppData\Local\Programs\Python\Python313\Lib\site-packages\torch"
echo          Add-MpPreference -ExclusionPath "F:\christine"
echo          Add-MpPreference -ExclusionProcess "python.exe"
echo.
echo   [B] 若 torch 真的載入 ^> 30 秒 且上面 nvidia-smi 正常:
echo          pip install --upgrade --force-reinstall torch --index-url https://download.pytorch.org/whl/cu121
echo       ^(如果你不用 GPU 可以裝 CPU 版更快^):
echo          pip install --upgrade --force-reinstall torch --index-url https://download.pytorch.org/whl/cpu
echo.
echo   [C] 最快繞過 (不管 GPU)：
echo          Start_Christine.bat --notorch
echo       Christine 主程式自己需要 GPU 時仍會載入^, 不影響功能。
echo.
echo =====================================================
pause
endlocal
