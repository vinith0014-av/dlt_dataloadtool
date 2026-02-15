@echo off
REM DLT Ingestion Framework - Easy Runner
REM This batch file sets up the environment and runs the framework

echo ============================================================================
echo DLT Ingestion Framework - ADLS Gen2
echo ============================================================================
echo.

REM Set Python path to include src directory
set PYTHONPATH=%~dp0src

REM Run using the venv with shorter path (avoids Windows long path issues)
C:\venv_dlt\Scripts\python.exe -m main

if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: Framework execution failed
    echo ============================================================================
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Framework execution completed
echo ============================================================================
pause
