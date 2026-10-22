@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul || (echo No encontre Python 3. Instalalo desde python.org marcando "Add Python to PATH". & pause & exit /b 1)
title Paradise Lost - 1 Extraer
set "JUEGO=%~1"
if not "%JUEGO%"=="" goto correr
if exist config.txt goto correr
echo Escribe la carpeta del juego (donde estan malie.exe y data1.dat)
echo o arrastra la carpeta a esta ventana y presiona Enter:
set /p "JUEGO=> "
if defined JUEGO set "JUEGO=%JUEGO:"=%"
:correr
if "%JUEGO%"=="" (%PY% herramientas\pl_kit.py extraer %2) else (%PY% herramientas\pl_kit.py extraer "%JUEGO%" %2)
pause
