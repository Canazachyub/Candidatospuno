@echo off
title Procesador de Candidatos - DeepSeek
echo ========================================
echo  PROCESADOR DE CANDIDATOS - DeepSeek
echo ========================================
echo.

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [AVISO] Entorno virtual no encontrado
    echo Usando Python del sistema...
)

echo.
echo Iniciando procesador...
echo.

cd /d "%~dp0"
python procesar.py

if errorlevel 1 (
    echo.
    echo [ERROR] Error al ejecutar el procesador
    echo Verifica que las dependencias esten instaladas
    pause
)
