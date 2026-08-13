import html
from datetime import datetime
from config import EQUIPAMENTOS, URGENCIAS


def clean_and_validate_ticket_data(titulo, descricao, equipamento, urgencia, solicitante, prazo):
    """Normaliza espaços e valida campos obrigatórios, sem remover pontuação válida
    (e-mails, IPs, '/', '@', ':' etc. continuam intactos). A proteção contra HTML/JS
    malicioso acontece na hora de EXIBIR o texto (veja escape_html), não aqui."""
    titulo = " ".join((titulo or "").split())
    descricao = " ".join((descricao or "").split())
    solicitante = " ".join((solicitante or "").split())

    if not titulo or len(titulo) < 2:
        return False, "O título deve ter pelo menos 2 caracteres.", None, None, None, None, None, None

    titulo = titulo[:120]
    descricao = descricao[:2000]

    if equipamento not in EQUIPAMENTOS:
        equipamento = "Outro"
    if urgencia not in URGENCIAS:
        urgencia = "Média"

    prazo_str = prazo.isoformat() if prazo else None

    return True, "Dados validados com sucesso", titulo, descricao, equipamento, urgencia, solicitante, prazo_str


def escape_html(texto):
    """Escapa texto do usuário antes de inserir em blocos markdown com unsafe_allow_html,
    evitando que HTML/tags digitados pela pessoa quebrem o layout."""
    return html.escape(texto or "")


def format_datetime(dt_str):
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return dt_str


def format_date(date_str):
    """Formata uma data simples (sem horário, ex: prazo) como dd/mm/aaaa."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).strftime("%d/%m/%Y")
    except ValueError:
        return date_str


def calculate_time_open(created_at_str):
    if not created_at_str:
        return "—"
    try:
        created = datetime.fromisoformat(created_at_str)
        diff = datetime.now() - created
        if diff.days > 0:
            return f"{diff.days}d {diff.seconds // 3600}h"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h {(diff.seconds % 3600) // 60}m"
        else:
            return f"{diff.seconds // 60}m"
    except ValueError:
        return "—"
