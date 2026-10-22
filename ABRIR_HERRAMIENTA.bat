@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul && (start "" pythonw herramientas\pl_gui.py & exit /b 0)
where pyw >nul 2>nul && (start "" pyw herramientas\pl_gui.py & exit /b 0)
where python >nul 2>nul && (python herramientas\pl_gui.py & exit /b 0)
echo No encontre Python 3. Instalalo desde python.org marcando "Add Python to PATH".
pause
