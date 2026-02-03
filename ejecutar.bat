@echo off
title Facebook Scraper
echo ========================================
echo    FACEBOOK SCRAPER - Iniciando...
echo ========================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Por favor instala Python desde https://python.org
    pause
    exit /b 1
)

REM Verificar si existe entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] No se encontro entorno virtual, usando Python global
)

echo [INFO] Iniciando aplicacion...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con errores
    pause
)
