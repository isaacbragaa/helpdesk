#!/bin/bash
cd "$(dirname "$0")"

echo "==============================================="
echo "  Central de Chamados TI - Iniciando..."
echo "==============================================="
echo

if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 nao foi encontrado neste computador."
    echo
    echo "Baixe em: https://www.python.org/downloads/"
    echo "Depois de instalar, execute este arquivo de novo."
    echo
    read -p "Pressione ENTER para fechar..."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Preparando o sistema pela primeira vez, aguarde..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Verificando/instalando dependencias (pode demorar um pouco na primeira vez)..."
python3 -c "import sys; print('Versao do Python encontrada:', sys.version.split()[0])"
pip install --upgrade pip -q
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "[ERRO] Falha ao instalar as dependencias."
    echo
    echo "Causas mais comuns:"
    echo " - Sem conexao com a internet no momento da instalacao"
    echo " - Python muito antigo instalado (recomendado: Python 3.10 ou mais novo)"
    echo "   Baixe a versao mais recente em: https://www.python.org/downloads/"
    echo
    echo "Veja a mensagem de erro detalhada acima para mais detalhes."
    echo
    read -p "Pressione ENTER para fechar..."
    exit 1
fi

if grep -q "COLE_AQUI" credentials.py; then
    echo
    echo "[AVISO] As credenciais de login ainda nao foram configuradas."
    echo "O sistema vai abrir normalmente, mas ninguem consegue entrar (so visualizar)"
    echo "ate voce editar o arquivo credentials.py."
    echo "Para gerar usuario e senha, de dois cliques em: gerar_credenciais.command"
    echo
    read -p "Pressione ENTER para continuar mesmo assim..."
fi

echo
echo "Abrindo o sistema no navegador..."
echo "Para FECHAR o sistema, feche esta janela ou aperte CTRL+C."
echo

streamlit run main.py --server.headless false

read -p "Pressione ENTER para fechar..."
