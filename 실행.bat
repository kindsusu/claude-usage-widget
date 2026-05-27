@echo off
REM Find pythonw.exe even when not on PATH (some Python installs skip
REM the App Paths registry entry that "start" uses for lookups).

set "PYTHONW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do (
    if not defined PYTHONW set "PYTHONW=%%i"
)
if not defined PYTHONW (
    if exist "%LocalAppData%\Programs\Python\Python314\pythonw.exe" set "PYTHONW=%LocalAppData%\Programs\Python\Python314\pythonw.exe"
)
if not defined PYTHONW (
    for /f "delims=" %%i in ('dir /b /s "%LocalAppData%\Programs\Python\pythonw.exe" 2^>nul') do (
        if not defined PYTHONW set "PYTHONW=%%i"
    )
)
if not defined PYTHONW (
    echo [ERROR] pythonw.exe not found. Install Python 3 from https://www.python.org/
    pause
    exit /b 1
)

start "" "%PYTHONW%" "%~dp0widget.pyw"
