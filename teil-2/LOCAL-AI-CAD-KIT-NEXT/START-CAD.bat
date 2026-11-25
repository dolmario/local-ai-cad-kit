@echo off
rem Local AI CAD Kit - starts the local model, FreeCAD with the MCP bridge and opencode.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-cad.ps1" %*
if errorlevel 1 pause
