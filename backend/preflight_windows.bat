@echo off
setlocal
cd /d "%~dp0"
if exist env\Scripts\python.exe (set "PY=env\Scripts\python.exe") else (set "PY=python")
%PY% -m compileall -q core config
if errorlevel 1 (echo Python compile tekshiruvi xato bilan tugadi.& exit /b 1)
%PY% manage.py check
if errorlevel 1 (echo Django system check xato bilan tugadi. Server ishga tushirilmaydi.& exit /b 1)
echo.
echo PRE-FLIGHT OK - loyiha ishga tushirishga tayyor.
endlocal
