@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul || (echo No encontre Python 3. Instalalo desde python.org marcando "Add Python to PATH". & pause & exit /b 1)
title Paradise Lost - 2 Revisar y corregir un CSV
set "ARCH=%~1"
if not "%ARCH%"=="" goto correr
echo Arrastra a esta ventana tu CSV (puede llamarse como quieras) y presiona Enter.
echo Si solo presionas Enter, se revisa trabajo\CSV_MAESTRO.csv
set /p "ARCH=> "
if defined ARCH set "ARCH=%ARCH:"=%"
:correr
if "%ARCH%"=="" (%PY% herramientas\pl_kit.py revisar) else (%PY% herramientas\pl_kit.py revisar "%ARCH%")
pause
