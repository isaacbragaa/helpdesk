import streamlit as st

# ---------------------------------------------------------------------------
# Duas paletas (clara/escura). Tudo abaixo é injetado como variáveis CSS
# (:root) e usado tanto pelo CSS fixo quanto pelos estilos inline gerados em
# render.py — assim os dois temas ficam consistentes em qualquer lugar da tela.
# ---------------------------------------------------------------------------
_PALETAS = {
    "claro": {
        "bg": "#F1F3F6",
        "bg_sidebar": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_input": "#FBFBFC",
        "bg_hover": "#EEF1F5",
        "texto": "#151B26",
        "texto_muted": "#5B6472",
        "borda": "#E2E8F0",
        "primaria": "#2A5298",
        "primaria_escura": "#1E3C72",
        "gradiente": "linear-gradient(135deg, #1E3C72 0%, #2A5298 100%)",
        "desc_bg": "#F8F9FA",
        "sombra": "0 2px 8px rgba(0,0,0,0.05)",
    },
    "escuro": {
        "bg": "#0E121B",
        "bg_sidebar": "#151A24",
        "bg_card": "#1A2030",
        "bg_input": "#212838",
        "bg_hover": "#242C3E",
        "texto": "#E8EBF2",
        "texto_muted": "#98A2B3",
        "borda": "#2E3648",
        "primaria": "#5B8DEF",
        "primaria_escura": "#3E6BC4",
        "gradiente": "linear-gradient(135deg, #16213E 0%, #24406E 100%)",
        "desc_bg": "#212838",
        "sombra": "0 2px 8px rgba(0,0,0,0.35)",
    },
}


def get_tema():
    """Lê o tema atual (sessão -> URL -> padrão 'claro'), sem desenhar nada."""
    if "tema" not in st.session_state:
        tema_url = st.query_params.get("tema")
        st.session_state["tema"] = tema_url if tema_url in _PALETAS else "claro"
    return st.session_state["tema"]


def tema_toggle_widget():
    """Botão na barra lateral para trocar entre claro/escuro, persistente
    (guardado na URL, sobrevive a um F5, igual à sessão de login)."""
    with st.sidebar:
        atual = get_tema()
        st.markdown("##### 🎨 Aparência")
        escolha = st.radio(
            "Aparência", ["☀️ Claro", "🌙 Escuro"],
            index=0 if atual == "claro" else 1,
            horizontal=True, label_visibility="collapsed", key="tema_radio",
        )
        novo = "claro" if "Claro" in escolha else "escuro"
        if novo != atual:
            st.session_state["tema"] = novo
            st.query_params["tema"] = novo
            st.rerun()
        st.markdown("---")


def load_css():
    p = _PALETAS[get_tema()]
    st.markdown(f"""
    <style>
        :root {{
            --bg: {p["bg"]};
            --bg-sidebar: {p["bg_sidebar"]};
            --bg-card: {p["bg_card"]};
            --bg-input: {p["bg_input"]};
            --bg-hover: {p["bg_hover"]};
            --texto: {p["texto"]};
            --texto-muted: {p["texto_muted"]};
            --borda: {p["borda"]};
            --primaria: {p["primaria"]};
            --primaria-escura: {p["primaria_escura"]};
            --desc-bg: {p["desc_bg"]};
            --sombra: {p["sombra"]};
        }}

        html, body, .stApp {{ background-color: var(--bg) !important; color: var(--texto) !important; }}
        [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar) !important; border-right: 1px solid var(--borda); }}
        [data-testid="stSidebar"] * {{ color: var(--texto) !important; }}
        [data-testid="stHeader"] {{ background-color: transparent !important; }}

        .stApp, .stApp [data-testid="stMarkdownContainer"] p, .stApp button,
        .stApp input, .stApp select, .stApp textarea {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}
        h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption,
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
        [data-testid="stCaptionContainer"] {{ color: var(--texto) !important; }}

        .main-header {{
            background: {p["gradiente"]};
            padding: 1.8rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.8rem;
            box-shadow: var(--sombra);
        }}
        .main-header h1 {{ color: white !important; margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
        .main-header p {{ color: rgba(255,255,255,0.85) !important; margin: 6px 0 0 0; font-size: 1rem; }}

        .tag {{
            display: inline-block; font-size: 12px; font-weight: 600;
            padding: 4px 14px; border-radius: 14px; margin-right: 8px;
            background: var(--primaria); color: #FFFFFF !important;
        }}
        .status-badge {{
            display: inline-block; font-size: 12px; font-weight: 600;
            padding: 4px 16px; border-radius: 20px; color: white !important; margin-right: 8px;
        }}
        .urg-pill {{
            display: inline-block; font-size: 12px; font-weight: 700;
            padding: 4px 14px; border-radius: 14px; margin-right: 8px; color: white !important;
        }}
        .meta, .meta * {{ color: var(--texto-muted) !important; font-size: 13px; line-height: 1.8; }}
        .meta b {{ color: var(--texto) !important; }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--borda) !important;
            border-radius: 10px !important;
            background: var(--bg-card) !important;
            margin-bottom: 0.7rem;
            box-shadow: var(--sombra);
        }}
        div[data-testid="stExpander"] summary {{
            font-weight: 600 !important;
            color: var(--texto) !important;
            padding: 10px 15px !important;
            background: var(--bg-card) !important;
        }}
        div[data-testid="stExpander"] p, div[data-testid="stExpander"] div {{ color: var(--texto) !important; }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
        .stTabs [data-baseweb="tab"] {{
            height: 46px; padding: 0 20px; border-radius: 8px 8px 0 0;
            font-weight: 600; font-size: 0.9rem;
            background: var(--bg-hover) !important; color: var(--texto-muted) !important;
        }}
        .stTabs [aria-selected="true"] {{
            background: var(--primaria-escura) !important; color: white !important;
        }}

        .stForm {{ background: var(--bg-card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--borda); }}

        /* Campos de texto/número/data e o "invólucro" visível deles (a caixa
           arredondada que aparece na tela é um wrapper do BaseWeb, não o
           <input> em si — por isso miramos nos dois). */
        input, textarea,
        [data-baseweb="input"], [data-baseweb="base-input"],
        [data-baseweb="textarea"],
        [data-baseweb="select"] > div, [data-baseweb="select"] [data-baseweb="input"] {{
            background-color: var(--bg-input) !important; color: var(--texto) !important;
            border-color: var(--borda) !important; border-radius: 8px !important;
        }}
        /* Texto de exemplo dentro do campo (ex: "🔎 título, solicitante...") —
           sem esta regra, ele herda uma cor clara padrão e some no tema escuro. */
        input::placeholder, textarea::placeholder {{
            color: var(--texto-muted) !important;
            opacity: 1 !important;
        }}
        /* Ícones dentro dos campos (lupa da busca, calendário do date_input etc.) */
        [data-baseweb="input"] svg, [data-baseweb="base-input"] svg,
        [data-testid="stDateInput"] svg, [data-testid="stTextInput"] svg {{
            fill: var(--texto-muted) !important;
        }}
        [data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="calendar"],
        ul[role="listbox"], div[data-baseweb="popover"] * {{
            background-color: var(--bg-card) !important; color: var(--texto) !important;
        }}
        [data-baseweb="menu"] li:hover {{ background-color: var(--bg-hover) !important; }}

        .stButton button {{ border-radius: 8px !important; font-weight: 600 !important; }}
        .stButton button[kind="primary"], .stButton button[data-testid="baseButton-primary"] {{
            background: var(--primaria) !important; border: none !important; color: white !important;
        }}
        .stButton button[kind="secondary"], .stButton button[data-testid="baseButton-secondary"] {{
            background: var(--bg-card) !important; color: var(--texto) !important; border: 1px solid var(--borda) !important;
        }}

        [data-testid="stMetric"], .metric-wrapper {{
            background: var(--bg-card); border-radius: 10px; padding: 15px 10px; text-align: center;
            box-shadow: var(--sombra); border: 1px solid var(--borda);
        }}
        .metric-number {{ font-size: 1.9rem; font-weight: 700; line-height: 1.2; }}
        .metric-label {{
            font-size: 0.72rem; color: var(--texto-muted) !important; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px;
        }}

        .desc-box {{
            background: var(--desc-bg); padding: 12px 16px; border-radius: 8px; margin: 8px 0;
            font-size: 0.95rem; line-height: 1.6; color: var(--texto) !important;
            border-left: 3px solid var(--primaria); white-space: pre-wrap;
        }}

        .footer {{
            margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--borda);
            color: var(--texto-muted) !important; font-size: 0.8rem; text-align: center;
        }}
    </style>
    """, unsafe_allow_html=True)
