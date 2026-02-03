@echo off
title Generar Dashboard de Candidatos
echo ========================================
echo  GENERADOR DE DASHBOARD
echo ========================================
echo.

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

cd /d "%~dp0"
python -c "from src.dashboard_generator import main; main()"

echo.
echo Dashboard generado en: output\dashboard.html
echo.
pause
