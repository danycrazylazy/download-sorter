@echo off
setlocal
set "SCRIPT=%~dp0classifierscript.py"

where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 (
        py -3 "%SCRIPT%"
        goto :finish
    )
)

where python >nul 2>&1
if errorlevel 1 (
    echo Python 3 was not found.
    echo Install Python 3 and enable the "Add Python to PATH" option,
    echo or install the Python Launcher for Windows.
    set "EXIT_CODE=1"
    goto :end
)

python "%SCRIPT%"

:finish
set "EXIT_CODE=%ERRORLEVEL%"

goto :end

:end
if not "%EXIT_CODE%"=="0" (
    echo.
    echo The program finished with an error. Exit code: %EXIT_CODE%
)

echo.
pause
exit /b %EXIT_CODE%
