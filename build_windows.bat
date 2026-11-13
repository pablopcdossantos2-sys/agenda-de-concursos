@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Instalando dependencias...
py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Instalando PyInstaller...
py -m pip install pyinstaller
if errorlevel 1 goto :error

echo [3/3] Gerando distribuicao portatil...
pyinstaller --noconfirm --clean --windowed --name "Agenda de Concursos" --onedir main.py
if errorlevel 1 goto :error

echo.
echo Compilacao concluida.
echo Copie a pasta dist\Agenda de Concursos para o local desejado.
echo Mantenha a pasta data criada pelo aplicativo junto do executavel.
pause
exit /b 0

:error
echo.
echo Ocorreu um erro durante a compilacao. Confira a mensagem acima.
pause
exit /b 1
