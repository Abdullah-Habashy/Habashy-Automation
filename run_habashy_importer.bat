@echo off
REM Runs the Habashy importer in Windows Terminal with UTF-8 support
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM Set UTF-8 code page for Arabic support
chcp 65001 >nul

REM Check if Windows Terminal is installed
where wt >nul 2>&1
if %errorlevel% equ 0 (
    REM Run in Windows Terminal (better Arabic support)
    wt -w 0 python "copy_mp3_auphonic_excel_download.py"
) else (
    REM Fallback to regular console
    echo Windows Terminal not found. Running in regular console...
    echo For better Arabic support, install Windows Terminal from Microsoft Store.
    echo.
    python "copy_mp3_auphonic_excel_download.py" || py -3 "copy_mp3_auphonic_excel_download.py"
)

popd
endlocal
