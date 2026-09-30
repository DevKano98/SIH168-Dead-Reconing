@echo off
rem Continuum IDR — Windows CMD Wrapper for Device Validation Automation
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0device_validate.ps1" %*
exit /b %ERRORLEVEL%
