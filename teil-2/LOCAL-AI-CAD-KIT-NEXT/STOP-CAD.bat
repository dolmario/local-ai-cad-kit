@echo off
rem Local AI CAD Kit - closes only the llama-server and FreeCAD that START-CAD.bat started (frees GPU memory and RAM).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-cad.ps1"
pause
