import streamlit as st
from datetime import datetime, date

from config import EQUIPAMENTOS, URGENCIAS, STATUS, STATUS_EMOJI, RECEBIDO_STATUS_EMOJI
from crud import (
    get_tickets, add_ticket, get_tickets_dataframe,
    clear_resolved_and_closed, clear_all_tickets, reset_ticket_counter,
)
from crud_recebidos import (
    add_recebido, get_recebidos, get_recebidos_dataframe,
    clear_enviados, clear_all_recebidos, reset_recebido_counter,
)
from render import render_ticket_card, render_recebido_card
from auth import current_role


def _sub_tabs_por_status(tickets, role):
    """Monta as sub-abas Aberto/Em andamento/.../Concluído para uma lista de chamados
    já filtrada."""
    counts = {s: len([t for t in tickets if t[5] == s]) for s in STATUS}
    tab_names = [f"{STATUS_EMOJI.get(s, '📌')} {s} ({counts.get(s, 0)})" for s in STATUS]
    sub_tabs = st.tabs(tab_names)

    for i, status in enumerate(STATUS):
        with sub_tabs[i]:
            status_tickets = [t for t in tickets if t[5] == status]
            if not status_tickets:
                st.info("📭 Nenhum chamado com este status.")
            else:
                for ticket in status_tickets:
                    render_ticket_card(ticket, role=role)


def view_tickets_tab():
    role = current_role()
    st.markdown("### 🔍 Filtros")

    filtro_col1, filtro_col2, filtro_col3 = st.columns([3, 1.2, 1.2])

    with filtro_col1:
        busca = st.text_input("Buscar", placeholder="🔎 título, solicitante, descrição...")
    with filtro_col2:
        f_equip = st.selectbox("Equipamento", ["Todos"] + EQUIPAMENTOS)
        f_equip = None if f_equip == "Todos" else f_equip
    with filtro_col3:
        f_urg = st.selectbox("Urgência", ["Todas"] + URGENCIAS)
        f_urg = None if f_urg == "Todas" else f_urg

    tickets = get_tickets(equipamento=f_equip, urgencia=f_urg, busca=busca or None)

    # Exportar CSV: só para o superadmin.
    if role == "superadmin":
        col_exp, _ = st.columns([1, 4])
        with col_exp:
            df = get_tickets_dataframe()
            if not df.empty:
                st.download_button(
                    "⬇️ Exportar CSV",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"chamados_ti_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

    if not tickets:
        st.info("📭 Nenhum chamado encontrado com os filtros aplicados.")
        return

    _sub_tabs_por_status(tickets, role)


def recebidos_tab():
    """Aba separada dos chamados: só registra o que chegou de outro local e,
    depois, o que saiu (com data e o que foi feito). Sem o fluxo de status
    dos chamados — só 'Aguardando envio' e 'Enviado'."""
    role = current_role()
    st.markdown("### 📦 Recebidos de outros locais")
    st.caption("O que chegou de outro setor/unidade — e, depois, o que foi feito e quando saiu.")

    with st.expander("➕ Registrar item recebido (não precisa de login)", expanded=False):
        with st.form("form_recebido", clear_on_submit=True):
            item = st.text_input(
                "O que chegou *",
                placeholder='Ex: "PC de Mossoró estação, tombamento 8978"',
                max_chars=120,
            )
            origem = st.text_input(
                "De onde veio *",
                placeholder='Ex: "Mossoró estação", "Ribeira"',
                max_chars=120,
            )
            descricao = st.text_area(
                "O que precisa ser feito",
                placeholder='Ex: "Fonte queimada, precisa trocar a fonte"',
                height=100,
            )
            col_a, col_b = st.columns(2)
            with col_a:
                data_chegada = st.date_input("Chegou no dia", value=date.today())
            with col_b:
                reportado_por = st.text_input("Quem está registrando (opcional)")

            st.caption("* Campo obrigatório")
            enviado = st.form_submit_button("📦 Registrar item recebido", type="primary", use_container_width=True)

            if enviado:
                success, msg = add_recebido(item, origem, descricao, data_chegada, reportado_por)
                if success:
                    st.toast("✅ Item registrado!", icon="📦")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    busca = st.text_input("Buscar", placeholder="🔎 item, origem, descrição...", key="busca_recebidos")
    recebidos = get_recebidos(busca=busca or None)

    if role == "superadmin":
        df = get_recebidos_dataframe()
        if not df.empty:
            st.download_button(
                "⬇️ Exportar CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"recebidos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

    if not recebidos:
        st.info("📭 Nada recebido de outros locais no momento.")
        return

    aguardando = [r for r in recebidos if r[5] == "Aguardando envio"]
    enviados = [r for r in recebidos if r[5] == "Enviado"]

    tab1, tab2 = st.tabs([
        f"{RECEBIDO_STATUS_EMOJI['Aguardando envio']} Aguardando envio ({len(aguardando)})",
        f"{RECEBIDO_STATUS_EMOJI['Enviado']} Enviado ({len(enviados)})",
    ])
    with tab1:
        if not aguardando:
            st.info("📭 Nada aguardando envio.")
        for r in aguardando:
            render_recebido_card(r, role=role)
    with tab2:
        if not enviados:
            st.info("📭 Nada enviado ainda.")
        for r in enviados:
            render_recebido_card(r, role=role)


def new_ticket_tab():
    st.markdown("### 📝 Abrir novo chamado")
    st.markdown("---")

    with st.form("form_novo_chamado", clear_on_submit=True):
        titulo = st.text_input("📌 Título do chamado *", placeholder="Ex: Computador não liga", max_chars=120)
        descricao = st.text_area("📝 Descrição detalhada",
                                  placeholder="Descreva o problema com o máximo de detalhes possível...",
                                  height=150)

        st.markdown("---")
        st.markdown("#### 📋 Informações adicionais")

        col_a, col_b = st.columns(2)
        with col_a:
            equipamento = st.selectbox("🖥️ Equipamento", EQUIPAMENTOS)
            urgencia = st.selectbox(
                "⚡ Urgência", URGENCIAS, index=1,
                help="Baixa: pode esperar | Média: em até 24h | Alta: em até 4h | Urgente: imediato",
            )
        with col_b:
            solicitante = st.text_input("👤 Solicitante", placeholder="Nome de quem está pedindo")

        prazo = st.date_input("📆 Prazo desejado", value=None, help="Data limite para resolução do chamado")

        st.caption("* Campo obrigatório")

        enviado = st.form_submit_button("📨 Criar chamado", type="primary", use_container_width=True)

        if enviado:
            success, msg = add_ticket(titulo, descricao, equipamento, urgencia, solicitante, prazo)
            if success:
                st.toast(f"✅ {msg}", icon="📨")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


def admin_tab():
    st.markdown("### ⚙️ Administração")
    st.caption("Ações visíveis apenas para a conta superadmin.")
    st.markdown("---")

    st.markdown("#### 📊 Exportar tudo (CSV) — exclusivo do superadmin")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        df = get_tickets_dataframe()
        if not df.empty:
            st.download_button(
                "⬇️ Backup de chamados (CSV)",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"backup_chamados_ti_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("Nenhum chamado registrado no momento.")
    with col_c2:
        df_rec = get_recebidos_dataframe()
        if not df_rec.empty:
            st.download_button(
                "⬇️ Backup de recebidos (CSV)",
                data=df_rec.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"backup_recebidos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("Nenhum item recebido no momento.")

    st.markdown("---")
    st.markdown("#### 🧹 Limpar histórico de chamados")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Apagar finalizados**")
        st.caption("Remove chamados com status \"Precisa ser enviado\" ou \"Foi enviado/Concluído\". Os demais continuam.")
        confirmando_parcial = st.session_state.get("confirm_clear_parcial", False)
        label = "⚠️ Confirmar limpeza" if confirmando_parcial else "Limpar finalizados"
        if st.button(label, use_container_width=True, key="btn_clear_parcial"):
            if confirmando_parcial:
                success, msg = clear_resolved_and_closed()
                st.session_state["confirm_clear_parcial"] = False
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.session_state["confirm_clear_parcial"] = True
                st.rerun()

    with col2:
        st.markdown("**Apagar TODOS os chamados**")
        st.caption("⚠️ Remove absolutamente todos os registros. Ação irreversível. (Não afeta os itens de Recebidos.)")
        reiniciar_contador = st.checkbox("Também reiniciar contador (próximo chamado volta a ser TI-0001)", value=True)
        confirmando_total = st.session_state.get("confirm_clear_total", False)
        label = "⚠️⚠️ Confirmar apagar tudo" if confirmando_total else "Apagar todos os chamados"
        if st.button(label, use_container_width=True, key="btn_clear_total"):
            if confirmando_total:
                success, msg = clear_all_tickets()
                st.session_state["confirm_clear_total"] = False
                if success and reiniciar_contador:
                    ok2, msg2 = reset_ticket_counter()
                    msg = msg + " " + msg2
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.session_state["confirm_clear_total"] = True
                st.rerun()

    st.markdown("---")
    st.markdown("#### 🔢 Reiniciar contador de chamados")
    st.caption(
        "Só tem efeito de verdade se a tabela estiver vazia (o SQLite/Turso nunca reaproveita "
        "um ID já usado enquanto existir algum chamado na base, para evitar duplicidade)."
    )
    if st.button("Reiniciar contador (TI-0001 no próximo chamado)", key="btn_reset_counter"):
        success, msg = reset_ticket_counter()
        if success:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("---")
    st.markdown("#### 📦 Limpar histórico de Recebidos de Outros Locais")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Apagar itens já enviados**")
        st.caption("Remove só os itens com status \"Enviado\". Os que estão \"Aguardando envio\" continuam.")
        confirmando_rec_parcial = st.session_state.get("confirm_clear_rec_parcial", False)
        label = "⚠️ Confirmar limpeza" if confirmando_rec_parcial else "Limpar itens enviados"
        if st.button(label, use_container_width=True, key="btn_clear_rec_parcial"):
            if confirmando_rec_parcial:
                success, msg = clear_enviados()
                st.session_state["confirm_clear_rec_parcial"] = False
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.session_state["confirm_clear_rec_parcial"] = True
                st.rerun()

    with col4:
        st.markdown("**Apagar TODOS os itens de Recebidos**")
        st.caption("⚠️ Remove absolutamente todos os registros (enviados e aguardando). Ação irreversível.")
        reiniciar_contador_rec = st.checkbox("Também reiniciar contador (próximo item volta a ser REC-0001)", value=True)
        confirmando_rec_total = st.session_state.get("confirm_clear_rec_total", False)
        label = "⚠️⚠️ Confirmar apagar tudo" if confirmando_rec_total else "Apagar todos os recebidos"
        if st.button(label, use_container_width=True, key="btn_clear_rec_total"):
            if confirmando_rec_total:
                success, msg = clear_all_recebidos()
                st.session_state["confirm_clear_rec_total"] = False
                if success and reiniciar_contador_rec:
                    ok2, msg2 = reset_recebido_counter()
                    msg = msg + " " + msg2
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.session_state["confirm_clear_rec_total"] = True
                st.rerun()
