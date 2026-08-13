import sqlite3
from datetime import datetime
import streamlit as st

from config import STATUS, STATUS_ABERTOS
from utils import clean_and_validate_ticket_data
from database import get_db_connection

# Colunas retornadas por get_tickets(), na ordem esperada por render_ticket_card()
_COLUNAS = "id, titulo, descricao, equipamento, urgencia, status, solicitante, prazo, criado_em, atualizado_em, motivo_espera"


def add_ticket(titulo, descricao, equipamento, urgencia, solicitante, prazo):
    ok, msg, titulo, descricao, equipamento, urgencia, solicitante, prazo_str = \
        clean_and_validate_ticket_data(titulo, descricao, equipamento, urgencia, solicitante, prazo)
    if not ok:
        return False, msg
    try:
        agora = datetime.now().isoformat()
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO chamados "
                "(titulo, descricao, equipamento, urgencia, status, solicitante, prazo, criado_em, atualizado_em) "
                "VALUES (?, ?, ?, ?, 'Aberto', ?, ?, ?, ?)",
                (titulo, descricao, equipamento, urgencia, solicitante, prazo_str, agora, agora),
            )
            conn.commit()
        return True, "Chamado criado com sucesso!"
    except Exception as e:
        return False, f"Erro ao criar chamado: {e}"


def update_status(ticket_id, novo_status, motivo=None):
    if novo_status not in STATUS:
        return False, "Status inválido."
    try:
        agora = datetime.now().isoformat()
        with get_db_connection() as conn:
            if novo_status == "Aguardando resposta":
                conn.execute(
                    "UPDATE chamados SET status=?, motivo_espera=?, atualizado_em=? WHERE id=?",
                    (novo_status, motivo, agora, ticket_id),
                )
            else:
                conn.execute(
                    "UPDATE chamados SET status=?, motivo_espera=NULL, atualizado_em=? WHERE id=?",
                    (novo_status, agora, ticket_id),
                )
            conn.commit()
        return True, "Status atualizado!"
    except Exception as e:
        return False, f"Erro ao atualizar status: {e}"


def update_ticket(ticket_id, titulo, descricao, equipamento, urgencia, solicitante, prazo):
    ok, msg, titulo, descricao, equipamento, urgencia, solicitante, prazo_str = \
        clean_and_validate_ticket_data(titulo, descricao, equipamento, urgencia, solicitante, prazo)
    if not ok:
        return False, msg
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE chamados SET titulo=?, descricao=?, equipamento=?, urgencia=?, "
                "solicitante=?, prazo=?, atualizado_em=? WHERE id=?",
                (titulo, descricao, equipamento, urgencia, solicitante, prazo_str,
                 datetime.now().isoformat(), ticket_id),
            )
            conn.commit()
        return True, "Chamado atualizado!"
    except Exception as e:
        return False, f"Erro ao atualizar chamado: {e}"


def delete_ticket(ticket_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM chamados WHERE id=?", (ticket_id,))
            conn.commit()
        return True, "Chamado excluído!"
    except Exception as e:
        return False, f"Erro ao excluir chamado: {e}"


def get_tickets(status=None, equipamento=None, urgencia=None, busca=None):
    try:
        query = f"SELECT {_COLUNAS} FROM chamados WHERE 1=1"
        params = []
        if status:
            query += " AND status=?"
            params.append(status)
        if equipamento:
            query += " AND equipamento=?"
            params.append(equipamento)
        if urgencia:
            query += " AND urgencia=?"
            params.append(urgencia)
        if busca:
            query += " AND (titulo LIKE ? OR descricao LIKE ? OR solicitante LIKE ?)"
            like = f"%{busca}%"
            params += [like, like, like]

        query += """ ORDER BY
            CASE urgencia WHEN 'Urgente' THEN 0 WHEN 'Alta' THEN 1 WHEN 'Média' THEN 2 ELSE 3 END,
            CASE status WHEN 'Aberto' THEN 0 WHEN 'Em andamento' THEN 1 WHEN 'Aguardando resposta' THEN 2 ELSE 3 END,
            prazo IS NULL, prazo ASC,
            criado_em ASC
        """
        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()
    except Exception as e:
        st.error(f"Erro ao buscar chamados: {e}")
        return []


def get_statistics():
    zero_stats = {"total": 0, "urgentes_abertos": 0, **{s: 0 for s in STATUS}}
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT status, COUNT(*) FROM chamados GROUP BY status").fetchall()
            stats = {s: 0 for s in STATUS}
            for status, count in rows:
                if status in stats:
                    stats[status] = count
            total = sum(stats.values())

            placeholders = ",".join("?" * len(STATUS_ABERTOS))
            urgentes_abertos = conn.execute(
                f"SELECT COUNT(*) FROM chamados WHERE urgencia='Urgente' AND status IN ({placeholders})",
                STATUS_ABERTOS,
            ).fetchone()[0]

        stats["total"] = total
        stats["urgentes_abertos"] = urgentes_abertos
        return stats
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return zero_stats


def get_tickets_dataframe():
    """Retorna todos os chamados como DataFrame, usado para exportação em CSV.
    Uso exclusivo do superadmin."""
    import pandas as pd
    with get_db_connection() as conn:
        return pd.read_sql_query(
            "SELECT id AS 'ID', titulo AS 'Título', descricao AS 'Descrição', equipamento AS 'Equipamento', "
            "urgencia AS 'Urgência', status AS 'Status', solicitante AS 'Solicitante', prazo AS 'Prazo', "
            "criado_em AS 'Criado em', atualizado_em AS 'Atualizado em', motivo_espera AS 'Motivo da espera' "
            "FROM chamados ORDER BY id",
            conn,
        )


def clear_resolved_and_closed():
    """Apaga chamados já finalizados ("Precisa ser enviado" / "Foi enviado/Concluído").
    Uso exclusivo do superadmin."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM chamados WHERE status IN ('Precisa ser enviado', 'Foi enviado/Concluído')"
            )
            conn.commit()
        return True, "Histórico de chamados finalizados foi limpo."
    except Exception as e:
        return False, f"Erro ao limpar histórico: {e}"


def clear_all_tickets():
    """Apaga TODOS os chamados, sem exceção. Uso exclusivo do superadmin."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM chamados")
            conn.commit()
        return True, "Todos os chamados foram apagados."
    except Exception as e:
        return False, f"Erro ao apagar chamados: {e}"


def reset_ticket_counter():
    """Reinicia a contagem de IDs (TI-0001 no próximo chamado criado).
    Só tem efeito real se a tabela estiver vazia — do contrário o SQLite
    continua de onde parou, para nunca duplicar um ID já usado."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM sqlite_sequence WHERE name='chamados'")
            conn.commit()
        return True, "Contador de IDs reiniciado."
    except Exception as e:
        return False, f"Erro ao reiniciar contador: {e}"
