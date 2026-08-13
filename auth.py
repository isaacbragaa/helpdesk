import hashlib
import secrets
from datetime import datetime, timedelta

import streamlit as st
from database import get_db_connection
from credentials import USERS

# ---------------------------------------------------------------------------
# As credenciais em si (usuário, salt, hash, papel) ficam em credentials.py —
# esse é o único arquivo que você precisa editar para trocar contas/senhas.
# Aqui só fica a LÓGICA de autenticação.
# ---------------------------------------------------------------------------

SESSION_HORAS = 12
MAX_TENTATIVAS = 5
BLOQUEIO_MINUTOS = 15


def credenciais_configuradas():
    """True somente se nenhuma conta ainda estiver com os valores de exemplo
    (COLE_AQUI...) — evita que o app rode "logável" com placeholder por engano."""
    return all(
        u.get("salt") and u.get("password_hash")
        and "COLE_AQUI" not in u["salt"] and "COLE_AQUI" not in u["password_hash"]
        for u in USERS.values()
    )


def _derive(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()


def _now():
    return datetime.utcnow()


def _iso(dt):
    return dt.isoformat()


def _parse(s):
    return datetime.fromisoformat(s)


# ---------------------------------------------------------------------------
# Login (comparação em tempo constante, sem revelar se o usuário existe)
# ---------------------------------------------------------------------------

def check_login(username, password):
    user = USERS.get(username)
    if not user or not user.get("salt") or not user.get("password_hash"):
        return None
    calculado = _derive(password, user["salt"])
    if secrets.compare_digest(calculado, user["password_hash"]):
        return user["role"]
    return None


# ---------------------------------------------------------------------------
# Bloqueio persistente por tentativas erradas (guardado no banco, não na
# sessão — assim um F5 não reseta o contador de tentativas)
# ---------------------------------------------------------------------------

def is_locked_out(username):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT bloqueado_ate FROM login_attempts WHERE username=?", (username,)
        ).fetchone()
    if row and row[0]:
        ate = _parse(row[0])
        if ate > _now():
            return True, ate
    return False, None


def register_failed_attempt(username):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT tentativas FROM login_attempts WHERE username=?", (username,)
        ).fetchone()
        tentativas = (row[0] if row else 0) + 1
        bloqueado_ate = _iso(_now() + timedelta(minutes=BLOQUEIO_MINUTOS)) if tentativas >= MAX_TENTATIVAS else None
        if row:
            conn.execute(
                "UPDATE login_attempts SET tentativas=?, bloqueado_ate=? WHERE username=?",
                (tentativas, bloqueado_ate, username),
            )
        else:
            conn.execute(
                "INSERT INTO login_attempts (username, tentativas, bloqueado_ate) VALUES (?, ?, ?)",
                (username, tentativas, bloqueado_ate),
            )
        conn.commit()


def reset_attempts(username):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM login_attempts WHERE username=?", (username,))
        conn.commit()


# ---------------------------------------------------------------------------
# Sessão persistente via token (guardado no banco + na URL), sobrevive a F5
# ---------------------------------------------------------------------------

def create_session(username, role):
    token = secrets.token_urlsafe(32)
    expira = _iso(_now() + timedelta(hours=SESSION_HORAS))
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, username, role, criado_em, expira_em) VALUES (?, ?, ?, ?, ?)",
            (token, username, role, _iso(_now()), expira),
        )
        conn.commit()
    return token


def validate_session(token):
    if not token:
        return None
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT username, role, expira_em FROM sessions WHERE token=?", (token,)
        ).fetchone()
        if not row:
            return None
        username, role, expira_em = row
        if _parse(expira_em) < _now():
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
            return None
    return username, role


def delete_session(token):
    if not token:
        return
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()


# ---------------------------------------------------------------------------
# Estado local / widgets
# ---------------------------------------------------------------------------

def is_logged_in():
    return st.session_state.get("auth_role") is not None


def current_role():
    return st.session_state.get("auth_role")


def current_user():
    return st.session_state.get("auth_user")


def has_access(min_role):
    role = current_role()
    if role is None:
        return False
    if min_role == "admin":
        return role in ("admin", "superadmin")
    if min_role == "superadmin":
        return role == "superadmin"
    return False


def _restore_session_from_url():
    """Reaproveita um login válido guardado na URL, se existir, para não
    deslogar a pessoa quando ela dá refresh na página."""
    if is_logged_in():
        return
    token = st.query_params.get("session")
    if not token:
        return
    resultado = validate_session(token)
    if resultado:
        username, role = resultado
        st.session_state["auth_role"] = role
        st.session_state["auth_user"] = username
        st.session_state["session_token"] = token
    else:
        del st.query_params["session"]


def login_widget():
    _restore_session_from_url()

    with st.sidebar:
        if is_logged_in():
            rotulo = "Superadmin" if current_role() == "superadmin" else "Admin"
            st.success(f"👤 **{current_user()}** ({rotulo})")
            if st.button("🚪 Sair", use_container_width=True):
                delete_session(st.session_state.get("session_token"))
                st.session_state.pop("auth_role", None)
                st.session_state.pop("auth_user", None)
                st.session_state.pop("session_token", None)
                if "session" in st.query_params:
                    del st.query_params["session"]
                st.rerun()
            return

        st.markdown("### 🔒 Login")

        if not credenciais_configuradas():
            st.warning(
                "⚠️ Nenhuma conta configurada. Edite o arquivo **credentials.py** "
                "e cole o SALT e o PASSWORD_HASH gerados por `gerar_credenciais.py`."
            )
            return

        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

            if entrar:
                usuario = usuario.strip()
                bloqueado, ate = is_locked_out(usuario)
                if bloqueado:
                    st.error(f"Conta bloqueada por tentativas incorretas. Tente novamente após {ate.strftime('%H:%M:%S')} (UTC).")
                else:
                    role = check_login(usuario, senha)
                    if role:
                        reset_attempts(usuario)
                        token = create_session(usuario, role)
                        st.session_state["auth_role"] = role
                        st.session_state["auth_user"] = usuario
                        st.session_state["session_token"] = token
                        st.query_params["session"] = token
                        st.rerun()
                    else:
                        register_failed_attempt(usuario)
                        st.error("Usuário ou senha inválidos.")

        st.caption("Sem login: apenas visualização dos chamados.")
