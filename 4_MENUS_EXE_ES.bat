@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul || (echo No encontre Python 3. Instalalo desde python.org marcando "Add Python to PATH". & pause & exit /b 1)
title Paradise Lost - 4 Menus de la ventana en espanol (opcional)
for /f "tokens=1,* delims==" %%a in (config.txt) do if /i "%%a"=="JUEGO" set "JUEGO=%%b"
if "%JUEGO%"=="" (echo Corre primero 1_EXTRAER. & pause & exit /b 1)
%PY% -c "import pefile" 2>nul || (echo Falta el modulo pefile. Instalalo con:  %PY% -m pip install pefile & pause & exit /b 1)
if exist "%JUEGO%\malie_es.exe" (echo Ya existe malie_es.exe en la carpeta del juego; no se sobrescribe. & pause & exit /b 0)
%PY% herramientas\pl_exe_es.py "%JUEGO%\malie.exe" "%JUEGO%\malie_es.exe"
echo Abre el juego con malie_es.exe (malie.exe queda intacto).
pause
