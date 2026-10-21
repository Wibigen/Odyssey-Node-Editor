@echo off
setlocal enabledelayedexpansion
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

if exist "OdysseyNodes.exe" del /q "OdysseyNodes.exe"

py -3 -m pip install -r requirements.txt pyinstaller

py -3 -m PyInstaller --noconsole --onefile --name OdysseyNodes --icon "assets\logo.ico" --add-data "assets;assets" --collect-submodules odyssey odyssey_nodes.py

if exist "dist\OdysseyNodes.exe" (
    move /y "dist\OdysseyNodes.exe" "%BASE_DIR%" >nul
)

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "OdysseyNodes.spec" del /q "OdysseyNodes.spec"
for /d /r "%BASE_DIR%" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"

if exist "OdysseyNodes.exe" (echo. & echo OdysseyNodes.exe is ready next to this script.) else (echo. & echo Build failed.)
pause
