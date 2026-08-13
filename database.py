import os
from contextlib import contextmanager
from config import DB_PATH, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, STATUS_RENOMEADOS, STATUS_FINALIZADOS

USE_TURSO = bool(TURSO_DATABASE_URL)


@contextmanager
def get_db_connection():
    """Abre uma conexão (Turso na nuvem, se configurado, ou SQLite local) e garante
    que ela é fechada ao final, mesmo em erro."""
    if USE_TURSO:
        import libsql
        conn = libsql.connect(database=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN)
    else:
        import sqlite3
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def _column_exists(conn, table, column):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT,
                equipamento TEXT,
                urgencia TEXT,
                status TEXT,
                solicitante TEXT,
                setor TEXT,
                prazo TEXT,
                criado_em TEXT,
                atualizado_em TEXT
            )
        """)
        # Migração leve: adiciona colunas que possam faltar em bancos já existentes.
        # (a coluna "setor" continua existindo por compatibilidade, só não é mais usada)
        for coluna, tipo in [
            ("solicitante", "TEXT"),
            ("atualizado_em", "TEXT"),
            ("motivo_espera", "TEXT"),
            ("origem", "TEXT"),
            ("data_chegada", "TEXT"),
        ]:
            if not _column_exists(conn, "chamados", coluna):
                conn.execute(f"ALTER TABLE chamados ADD COLUMN {coluna} {tipo}")

        # Renomeia chamados antigos que ainda usam os status "Resolvido"/"Fechado"
        # para os novos nomes ("Precisa ser enviado"/"Foi enviado/Concluído").
        for nome_antigo, nome_novo in STATUS_RENOMEADOS.items():
            conn.execute(
                "UPDATE chamados SET status=? WHERE status=?", (nome_novo, nome_antigo)
            )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON chamados(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_urgencia ON chamados(urgencia)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_equipamento ON chamados(equipamento)")

        # Sessões de login (permite continuar logado após atualizar a página)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                criado_em TEXT,
                expira_em TEXT NOT NULL
            )
        """)

        # Controle de tentativas de login (bloqueio persistente, não reseta com F5)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT PRIMARY KEY,
                tentativas INTEGER NOT NULL DEFAULT 0,
                bloqueado_ate TEXT
            )
        """)

        # "Recebidos de outros locais": tabela própria, separada de chamados
        # (só dois estados — Aguardando envio / Enviado — sem o fluxo de
        # status dos chamados normais).
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recebidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                origem TEXT NOT NULL,
                descricao TEXT,
                data_chegada TEXT,
                status TEXT NOT NULL DEFAULT 'Aguardando envio',
                data_saida TEXT,
                o_que_foi_feito TEXT,
                reportado_por TEXT,
                criado_em TEXT,
                atualizado_em TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recebidos_status ON recebidos(status)")

        # Migração única: chamados criados na versão anterior (quando
        # "Recebidos" ainda usava a tabela de chamados, com o campo "origem")
        # são movidos para a tabela nova e removidos de chamados.
        antigos = conn.execute(
            "SELECT id, titulo, origem, descricao, data_chegada, solicitante, status, atualizado_em "
            "FROM chamados WHERE origem IS NOT NULL AND origem != ''"
        ).fetchall()
        for (cid, titulo, origem, descricao, data_chegada, solicitante, status, atualizado_em) in antigos:
            novo_status = "Enviado" if status in STATUS_FINALIZADOS else "Aguardando envio"
            data_saida = atualizado_em[:10] if (novo_status == "Enviado" and atualizado_em) else None
            conn.execute(
                "INSERT INTO recebidos (item, origem, descricao, data_chegada, status, data_saida, "
                "o_que_foi_feito, reportado_por, criado_em, atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (titulo, origem, descricao, data_chegada, novo_status, data_saida,
                 descricao if novo_status == "Enviado" else None, solicitante,
                 atualizado_em, atualizado_em),
            )
            conn.execute("DELETE FROM chamados WHERE id=?", (cid,))

        conn.commit()
