@echo off
rem JuegoIA - Bomber Mind: abre el juego con el Python instalado en Windows.
rem La primera vez instala pygame, numpy y matplotlib (pide confirmacion).
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 JuegoIA_portable.py %*
    goto fin
)
where python >nul 2>nul
if %errorlevel%==0 (
    python JuegoIA_portable.py %*
    goto fin
)
echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
echo (marca la casilla "Add python.exe to PATH" durante la instalacion).
pause
exit /b 1
:fin
if errorlevel 1 pause
