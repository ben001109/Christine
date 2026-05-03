@echo off
REM ============================================================
REM  Fix_Torch_Reinstall.bat - 重裝 PyTorch (CPU 版 或 GPU 版)
REM  適用情境: torch 載入 > 30 秒、import torch 吐 DLL 錯誤
REM ============================================================
chcp 65001 >nul 2>&1
title Reinstall PyTorch
color 0E

set "PYEXE=C:\Users\josh1\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo.
echo ============================================
echo   重新安裝 PyTorch
echo ============================================
echo.
echo   [1] GPU 版 (CUDA 12.1) - 需要 NVIDIA 顯卡
echo   [2] CPU 版 - 不用 GPU^, 載入快 ^(~2 秒^)^, 推理慢
echo   [3] 取消
echo.
set /p choice="選擇 (1/2/3): "

if "%choice%"=="1" goto gpu
if "%choice%"=="2" goto cpu
goto end

:gpu
echo.
echo [安裝] GPU 版 torch (CUDA 12.1)...
"%PYEXE%" -m pip uninstall -y torch torchvision torchaudio
"%PYEXE%" -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu121
goto verify

:cpu
echo.
echo [安裝] CPU 版 torch...
"%PYEXE%" -m pip uninstall -y torch torchvision torchaudio
"%PYEXE%" -m pip install --upgrade torch --index-url https://download.pytorch.org/whl/cpu
goto verify

:verify
echo.
echo ============================================
echo   驗證安裝
echo ============================================
"%PYEXE%" -c "import time; t=time.time(); import torch; print(f'torch={torch.__version__}  load={time.time()-t:.2f}s  cuda={torch.cuda.is_available()}')"
echo.

:end
pause
