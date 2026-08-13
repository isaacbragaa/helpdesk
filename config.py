import os

EQUIPAMENTOS = ["PC", "Monitor", "Impressora", "Periférico", "Rede", "Servidor", "Software", "Outro"]
URGENCIAS = ["Baixa", "Média", "Alta", "Urgente"]

# "Resolvido" e "Fechado" viraram "Precisa ser enviado" e "Foi enviado/Concluído"
# (ver migração em database.py, que renomeia os chamados antigos automaticamente).
STATUS = ["Aberto", "Em andamento", "Aguardando resposta", "Precisa ser enviado", "Foi enviado/Concluído"]
STATUS_ABERTOS = ["Aberto", "Em andamento", "Aguardando resposta"]
STATUS_FINALIZADOS = ["Precisa ser enviado", "Foi enviado/Concluído"]

# Nomes antigos -> novos, usado na migração automática do banco.
STATUS_RENOMEADOS = {
    "Resolvido": "Precisa ser enviado",
    "Fechado": "Foi enviado/Concluído",
}

URG_COLOR = {
    "Baixa": "#2C9C6B",
    "Média": "#D99A1F",
    "Alta": "#E0662C",
    "Urgente": "#D6394A",
}

STATUS_COLOR = {
    "Aberto": "#E74C3C",
    "Em andamento": "#F39C12",
    "Aguardando resposta": "#3498DB",
    "Precisa ser enviado": "#9B59B6",
    "Foi enviado/Concluído": "#2ECC71",
}

STATUS_EMOJI = {
    "Aberto": "🔴",
    "Em andamento": "🟡",
    "Aguardando resposta": "🔵",
    "Precisa ser enviado": "🟣",
    "Foi enviado/Concluído": "🟢",
}

# "Recebidos de outros locais" é um sistema separado dos chamados: só dois
# estados (chegou / já saiu), sem o fluxo de status dos chamados.
RECEBIDO_STATUS = ["Aguardando envio", "Enviado"]
RECEBIDO_STATUS_COLOR = {
    "Aguardando envio": "#E67E22",
    "Enviado": "#2ECC71",
}
RECEBIDO_STATUS_EMOJI = {
    "Aguardando envio": "🟠",
    "Enviado": "🟢",
}

# Caminho do banco local (usado quando NÃO há Turso configurado).
# Pode ser sobrescrito com a variável de ambiente DB_PATH (útil com volume persistente, ex: /data/tickets.db)
DB_PATH = os.environ.get("DB_PATH", "tickets.db")

# Se preenchidas, o app usa um banco Turso (nuvem, gratuito) em vez do SQLite local.
# Necessário para hospedar no Streamlit Community Cloud com dados permanentes,
# já que o armazenamento local de lá é apagado quando o app hiberna.
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

# As credenciais de login ficam em credentials.py (SALT + PASSWORD_HASH,
# nunca a senha em texto puro). Veja esse arquivo e gerar_credenciais.py.
