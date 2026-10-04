@echo off
REM ===============================================================
REM DSA AI Tutor — one-click entry point (Windows)
REM
REM Double-click this file after extracting/cloning the project.
REM It runs the real installer in desktop\install_windows.bat
REM (which checks Python/Docker, creates .env, and adds a Desktop
REM shortcut) and then opens the launcher GUI immediately, so you
REM don't have to go hunting for it on first run.
REM ===============================================================

setlocal
set "HERE=%~dp0"
set "LAUNCHER=%HERE%desktop\dsa_tutor_launcher.py"

call "%HERE%desktop\install_windows.bat"
if %errorlevel% neq 0 (
    echo.
    echo Setup did not finish - see the messages above.
    pause
    exit /b 1
)

echo.
echo Opening the DSA AI Tutor launcher...
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%LAUNCHER%"
) else (
    start "" python "%LAUNCHER%"
)
