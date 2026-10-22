@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul || (echo No encontre Python 3. Instalalo desde python.org marcando "Add Python to PATH". & pause & exit /b 1)
title Paradise Lost - 3 Generar data3.dat
set "ARCH=%~1"
if not "%ARCH%"=="" goto correr
echo Arrastra a esta ventana tu CSV traducido (con el nombre que sea) y presiona Enter.
echo Si solo presionas Enter, se usa trabajo\CSV_MAESTRO.csv
set /p "ARCH=> "
if defined ARCH set "ARCH=%ARCH:"=%"
:correr
if "%ARCH%"=="" (%PY% herramientas\pl_kit.py generar) else (%PY% herramientas\pl_kit.py generar "%ARCH%")
pause
