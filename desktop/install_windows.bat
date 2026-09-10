@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo   DSA AI Tutor - Windows Installer
echo ===============================================
echo.

set "PROJECT_ROOT=%~dp0.."
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI"

echo Project folder: %PROJECT_ROOT%
echo.

REM ---------------------------------------------------------------
REM 1. Check Python
REM ---------------------------------------------------------------
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [MISSING] Python was not found on PATH.
        echo Install it from https://www.python.org/downloads/ ^(check
        echo "Add python.exe to PATH" during setup^), then run this
        echo installer again.
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)
echo [OK] Python found: %PYTHON_CMD%

REM ---------------------------------------------------------------
REM 2. Check tkinter (the launcher's GUI toolkit)
REM ---------------------------------------------------------------
%PYTHON_CMD% -c "import tkinter" >nul 2>nul
if %errorlevel% neq 0 (
    echo [MISSING] tkinter is not available in this Python install.
    echo Re-run the Python installer and enable the "tcl/tk and IDLE"
    echo option, then run this installer again.
    pause
    exit /b 1
)
echo [OK] tkinter available

REM ---------------------------------------------------------------
REM 3. Check Docker
REM ---------------------------------------------------------------
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [MISSING] Docker was not found on PATH.
    echo Install Docker Desktop from https://www.docker.com/products/docker-desktop/
    echo then run this installer again.
    pause
    exit /b 1
)
echo [OK] Docker found

docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Docker is installed but doesn't seem to be running.
    echo Start Docker Desktop, then use the launcher's "Re-check" button.
) else (
    echo [OK] Docker daemon is running
)

REM ---------------------------------------------------------------
REM 4. Create .env if missing
REM ---------------------------------------------------------------
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\dot.env" (
        copy "%PROJECT_ROOT%\dot.env" "%PROJECT_ROOT%\.env" >nul
        echo [OK] Created .env from template - edit it and add your GROQ_API key.
    )
) else (
    echo [OK] .env already exists
)

REM ---------------------------------------------------------------
REM 5. Create a desktop shortcut to the launcher
REM ---------------------------------------------------------------
set "LAUNCHER=%PROJECT_ROOT%\desktop\dsa_tutor_launcher.py"
set "ICON=%PROJECT_ROOT%\desktop\assets\icon.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\DSA AI Tutor.lnk"

for /f "delims=" %%P in ('where pythonw 2^>nul') do set "PYTHONW=%%P"
if not defined PYTHONW set "PYTHONW=%PYTHON_CMD%"

powershell -NoProfile -Command ^
    "$s = (New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
    "$s.TargetPath = '%PYTHONW%';" ^
    "$s.Arguments = '\"%LAUNCHER%\"';" ^
    "$s.WorkingDirectory = '%PROJECT_ROOT%';" ^
    "$s.IconLocation = '%ICON%';" ^
    "$s.Save()"

if %errorlevel% equ 0 (
    echo [OK] Desktop shortcut created: %SHORTCUT%
) else (
    echo [WARNING] Could not create the desktop shortcut automatically.
    echo You can still run the launcher directly with:
    echo     %PYTHON_CMD% "%LAUNCHER%"
)

echo.
echo ===============================================
echo   Setup complete!
echo   Double-click "DSA AI Tutor" on your Desktop
echo   to open the launcher.
echo ===============================================
pause
