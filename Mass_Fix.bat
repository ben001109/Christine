@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0" || (
    echo [Mass_Fix] Unable to open the project directory. 1>&2
    endlocal
    exit /b 126
)
set "PYEXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [Mass_Fix] Project Python environment is unavailable. 1>&2
    endlocal
    exit /b 127
)
"%PYEXE%" -B -X utf8 "%~dp0Mass_Fix.py" %*
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
