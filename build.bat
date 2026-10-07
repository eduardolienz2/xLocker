@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1

REM Step 1: build the app folder with PyInstaller (onedir = faster start, fewer antivirus false positives)
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :error

python -m PyInstaller --noconfirm --clean xLocker.spec
if errorlevel 1 goto :error

REM Step 2: build the installer (needs Inno Setup 6 installed)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo Inno Setup 6 compiler not found: "%ISCC%"
    goto :error
)

"%ISCC%" "%~dp0installer\installer.iss"
if errorlevel 1 goto :error

popd
exit /b 0

:error
set "BUILD_ERROR=%errorlevel%"
if "%BUILD_ERROR%"=="0" set "BUILD_ERROR=1"
popd
exit /b %BUILD_ERROR%
