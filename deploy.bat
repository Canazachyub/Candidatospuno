@echo off
title Desplegar Dashboard a GitHub Pages
echo ========================================
echo  DESPLIEGUE A GITHUB PAGES
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

cd /d "%~dp0"

echo [1/4] Preparando archivos para docs/...
python src/deploy_preparer.py --clean
if errorlevel 1 (
    echo [ERROR] Error preparando archivos
    pause
    exit /b 1
)

echo.
echo [2/4] Agregando archivos a Git...
git add docs/ .github/
if errorlevel 1 (
    echo [ERROR] Error en git add
    pause
    exit /b 1
)

echo.
echo [3/4] Creando commit...
set /p MENSAJE="Mensaje del commit (Enter para default): "
if "%MENSAJE%"=="" set MENSAJE=Actualizar dashboard y fichas de candidatos

git commit -m "%MENSAJE%"
if errorlevel 1 (
    echo [AVISO] No hay cambios para commit o error
)

echo.
echo [4/4] Subiendo a GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] Error en git push
    echo Verifica tu conexion y credenciales de GitHub
    pause
    exit /b 1
)

echo.
echo ========================================
echo  DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo El sitio se desplegara automaticamente via GitHub Actions.
echo Revisa el progreso en: https://github.com/TU_USUARIO/TU_REPO/actions
echo.
echo Tu sitio estara disponible en:
echo https://TU_USUARIO.github.io/TU_REPO/
echo.
pause
