import streamlit as st
from database import init_db
from css import load_css, tema_toggle_widget
from render import display_header, display_metrics, display_footer
from views import view_tickets_tab, recebidos_tab, new_ticket_tab, admin_tab
from crud import get_statistics
from auth import login_widget, has_access


def main():
    st.set_page_config(
        page_title="Central de Chamados · TI",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_db()
    load_css()
    tema_toggle_widget()
    login_widget()
    display_header()

    stats = get_statistics()
    display_metrics(stats)
    st.markdown("---")

    tab_labels = ["📋 Visualizar Chamados", "📦 Recebidos de Outros Locais"]
    if has_access("admin"):
        tab_labels.append("➕ Novo Chamado")
    if has_access("superadmin"):
        tab_labels.append("⚙️ Administração")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        view_tickets_tab()
    with tabs[1]:
        recebidos_tab()

    idx = 2
    if has_access("admin"):
        with tabs[idx]:
            new_ticket_tab()
        idx += 1
    if has_access("superadmin"):
        with tabs[idx]:
            admin_tab()

    display_footer(stats["total"])


if __name__ == "__main__":
    main()
