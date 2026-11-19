@echo off
rem Local AI CAD Kit - one-click setup. Installs programs and downloads the model (about 20 GB).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 (
  echo.
  echo Setup stopped with an error. See install.log in this folder.
  pause
  exit /b 1
)
echo.
echo Setup finished. Next: double-click START-CAD.bat
pause
