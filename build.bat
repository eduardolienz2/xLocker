@echo off
setlocal
set "ROOT=%~dp0"
set "STAGING=%TEMP%\xLocker-build-%RANDOM%-%RANDOM%"

echo ================================
echo   BUILD AUTOMATICO INICIADO
echo ================================
echo.

echo Gerando codigo ofuscado...
python -m pyarmor.cli gen -O "%STAGING%\obfuscated" "%ROOT%src\password_generator_gui.py"
if errorlevel 1 goto :error

echo.
echo Gerando executavel protegido...
python -m PyInstaller --onefile --noconsole --icon="%ROOT%assets\xLocker.ico" --name GerenciadorDeSenhas --hidden-import=tkinter --hidden-import=tkinter.ttk --hidden-import=tkinter.messagebox --hidden-import=uuid --hidden-import=hashlib --hidden-import=os --hidden-import=json --hidden-import=base64 --hidden-import=secrets --collect-all cryptography --distpath "%STAGING%\dist" --workpath "%STAGING%\work" --specpath "%STAGING%\spec" "%STAGING%\obfuscated\password_generator_gui.py"
if errorlevel 1 goto :error

if not exist "%ROOT%dist" mkdir "%ROOT%dist"
copy /Y "%STAGING%\dist\GerenciadorDeSenhas.exe" "%ROOT%dist\GerenciadorDeSenhas.exe"
if errorlevel 1 goto :error

rmdir /S /Q "%STAGING%"
echo.
echo ================================
echo BUILD FINALIZADO COM SUCESSO!
echo EXE disponivel em: dist\GerenciadorDeSenhas.exe
echo ================================
pause
exit /b 0

:error
echo.
echo ERRO NA COMPILACAO. Os arquivos existentes em dist nao foram removidos.
echo Arquivos de diagnostico, se gerados, estao em: %STAGING%
pause
exit /b 1
