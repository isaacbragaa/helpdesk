@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Central de Chamados TI

echo ===============================================
echo   Central de Chamados TI - Iniciando...
echo ===============================================
echo.

REM --- Procura o Python instalado (tenta "python" e depois "py") ---
set PYCMD=
where python >nul 2>nul
if not errorlevel 1 (
    set PYCMD=python
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set PYCMD=py
    )
)

if "%PYCMD%"=="" (
    echo [ERRO] Python nao foi encontrado neste computador.
    echo.
    echo 1. Baixe em: https://www.python.org/downloads/
    echo 2. Durante a instalacao, marque a opcao "Add Python to PATH"
    echo 3. Depois de instalar, execute este arquivo de novo.
    echo.
    pause
    exit /b 1
)

REM --- Cria o ambiente virtual na primeira vez ---
if not exist ".venv" (
    echo Preparando o sistema pela primeira vez, aguarde...
    %PYCMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo Verificando/instalando dependencias (pode demorar um pouco na primeira vez)...
python -c "import sys; print('Versao do Python encontrada:', sys.version.split()[0])"
python -m pip install --upgrade pip -q
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar as dependencias.
    echo.
    echo Causas mais comuns:
    echo  - Sem conexao com a internet no momento da instalacao
    echo  - Python muito antigo instalado ^(recomendado: Python 3.10 ou mais novo^)
    echo    Baixe a versao mais recente em: https://www.python.org/downloads/
    echo.
    echo Veja a mensagem de erro detalhada acima para mais detalhes.
    echo.
    pause
    exit /b 1
)

REM --- Avisa se as credenciais de login ainda nao foram configuradas ---
findstr /C:"COLE_AQUI" credentials.py >nul
if not errorlevel 1 (
    echo.
    echo [AVISO] As credenciais de login ainda nao foram configuradas.
    echo O sistema vai abrir normalmente, mas ninguem consegue entrar (so visualizar)
    echo ate voce editar o arquivo credentials.py.
    echo Para gerar usuario e senha, de dois cliques em: gerar_credenciais.bat
    echo.
    pause
)

echo.
echo Abrindo o sistema no navegador...
echo Para FECHAR o sistema, feche esta janela ou aperte CTRL+C.
echo.

streamlit run main.py --server.headless false

pause
