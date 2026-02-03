@echo off
title Facebook Scraper - Instalacion
echo ========================================
echo    FACEBOOK SCRAPER - Instalador
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado
    echo Descarga Python desde: https://python.org
    pause
    exit /b 1
)

echo [INFO] Python encontrado:
python --version
echo.

REM Crear entorno virtual
echo [INFO] Creando entorno virtual...
python -m venv venv

if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual
    pause
    exit /b 1
)

REM Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo.
echo [INFO] Instalando dependencias...
echo Esto puede tomar unos minutos...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INSTALACION COMPLETADA
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   1. Haz doble clic en ejecutar.bat
echo   O desde terminal:
echo   2. Activa el entorno: venv\Scripts\activate
echo   3. Ejecuta: python main.py
echo.
pause
