@echo off
setlocal
cd /d "%~dp0"
echo This recovers Zeeshan only when your Windows account has SQL Server sysadmin rights.
echo Existing user accounts are preserved.
set /p REPLY=Type RECOVER to reset Zeeshan to temporary credentials: 
if /I not "%REPLY%"=="RECOVER" exit /b 1
if not exist ".venv\Scripts\python.exe" (
 echo Install dependencies first via INSTALL_AND_START.bat
 pause
 exit /b 1
)
".venv\Scripts\python.exe" "SourceCode\bootstrap_sql.py" --repair-admin
pause
