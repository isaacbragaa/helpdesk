from datetime import datetime
import streamlit as st

from database import get_db_connection

_COLUNAS = "id, item, origem, descricao, data_chegada, status, data_saida, o_que_foi_feito, reportado_por, criado_em, atualizado_em"


def add_recebido(item, origem, descricao, data_chegada, reportado_por=None):
    item = " ".join((item or "").split())[:120]
    origem = " ".join((origem or "").split())[:120]
    descricao = " ".join((descricao or "").split())[:2000]
    reportado_por = " ".join((reportado_por or "").split())[:120] or None

    if not item or len(item) < 2:
        return False, "Descreva o que chegou (pelo menos 2 caracteres)."
    if not origem:
        return False, "Informe de onde o item veio."

    try:
        agora = datetime.now().isoformat()
        data_chegada_str = data_chegada.isoformat() if data_chegada else None
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO recebidos (item, origem, descricao, data_chegada, status, reportado_por, criado_em, atualizado_em) "
                "VALUES (?, ?, ?, ?, 'Aguardando envio', ?, ?, ?)",
                (item, origem, descricao, data_chegada_str, reportado_por, agora, agora),
            )
            conn.commit()
        return True, "Item registrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao registrar item: {e}"


def update_recebido(rid, item, origem, descricao, data_chegada):
    item = " ".join((item or "").split())[:120]
    origem = " ".join((origem or "").split())[:120]
    descricao = " ".join((descricao or "").split())[:2000]

    if not item or len(item) < 2:
        return False, "Descreva o que chegou (pelo menos 2 caracteres)."
    if not origem:
        return False, "Informe de onde o item veio."

    try:
        data_chegada_str = data_chegada.isoformat() if data_chegada else None
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE recebidos SET item=?, origem=?, descricao=?, data_chegada=?, atualizado_em=? WHERE id=?",
                (item, origem, descricao, data_chegada_str, datetime.now().isoformat(), rid),
            )
            conn.commit()
        return True, "Item atualizado!"
    except Exception as e:
        return False, f"Erro ao atualizar item: {e}"


def marcar_enviado(rid, data_saida, o_que_foi_feito):
    o_que_foi_feito = " ".join((o_que_foi_feito or "").split())[:2000]
    if not o_que_foi_feito:
        return False, "Descreva o que foi feito/enviado."
    try:
        data_saida_str = data_saida.isoformat() if data_saida else None
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE recebidos SET status='Enviado', data_saida=?, o_que_foi_feito=?, atualizado_em=? WHERE id=?",
                (data_saida_str, o_que_foi_feito, datetime.now().isoformat(), rid),
            )
            conn.commit()
        return True, "Marcado como enviado!"
    except Exception as e:
        return False, f"Erro ao marcar como enviado: {e}"


def reabrir_recebido(rid):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE recebidos SET status='Aguardando envio', data_saida=NULL, o_que_foi_feito=NULL, atualizado_em=? WHERE id=?",
                (datetime.now().isoformat(), rid),
            )
            conn.commit()
        return True, "Reaberto — voltou para 'Aguardando envio'."
    except Exception as e:
        return False, f"Erro ao reabrir: {e}"


def delete_recebido(rid):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM recebidos WHERE id=?", (rid,))
            conn.commit()
        return True, "Item excluído!"
    except Exception as e:
        return False, f"Erro ao excluir: {e}"


def get_recebidos(status=None, busca=None):
    try:
        query = f"SELECT {_COLUNAS} FROM recebidos WHERE 1=1"
        params = []
        if status:
            query += " AND status=?"
            params.append(status)
        if busca:
            query += " AND (item LIKE ? OR origem LIKE ? OR descricao LIKE ?)"
            like = f"%{busca}%"
            params += [like, like, like]
        query += " ORDER BY data_chegada IS NULL, data_chegada DESC, criado_em DESC"
        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()
    except Exception as e:
        st.error(f"Erro ao buscar itens recebidos: {e}")
        return []


def get_recebidos_dataframe():
    """Usado na exportação CSV, exclusiva do superadmin."""
    import pandas as pd
    with get_db_connection() as conn:
        return pd.read_sql_query(
            "SELECT id AS 'ID', item AS 'Item', origem AS 'Origem', descricao AS 'O que precisa ser feito', "
            "data_chegada AS 'Data de chegada', status AS 'Status', data_saida AS 'Data de saída', "
            "o_que_foi_feito AS 'O que foi feito/enviado', reportado_por AS 'Registrado por', "
            "criado_em AS 'Criado em', atualizado_em AS 'Atualizado em' FROM recebidos ORDER BY id",
            conn,
        )


def clear_enviados():
    """Apaga apenas os itens já marcados como 'Enviado'. Uso exclusivo do superadmin."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM recebidos WHERE status='Enviado'")
            conn.commit()
        return True, "Itens já enviados foram limpos do histórico."
    except Exception as e:
        return False, f"Erro ao limpar histórico: {e}"


def clear_all_recebidos():
    """Apaga TODOS os itens de Recebidos, sem exceção. Uso exclusivo do superadmin."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM recebidos")
            conn.commit()
        return True, "Todos os itens de Recebidos foram apagados."
    except Exception as e:
        return False, f"Erro ao apagar itens: {e}"


def reset_recebido_counter():
    """Reinicia a contagem de IDs (REC-0001 no próximo item registrado).
    Só tem efeito real se a tabela estiver vazia."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM sqlite_sequence WHERE name='recebidos'")
            conn.commit()
        return True, "Contador de IDs de Recebidos reiniciado."
    except Exception as e:
        return False, f"Erro ao reiniciar contador: {e}"
