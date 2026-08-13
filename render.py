import streamlit as st
from datetime import date

from config import EQUIPAMENTOS, URGENCIAS, STATUS, STATUS_FINALIZADOS, URG_COLOR, STATUS_COLOR, RECEBIDO_STATUS_COLOR
from utils import format_datetime, format_date, calculate_time_open, escape_html
from crud import update_status, delete_ticket, update_ticket
from crud_recebidos import marcar_enviado, reabrir_recebido, delete_recebido, update_recebido
from database import USE_TURSO


def render_ticket_card(ticket_data, role=None):
    (tid, titulo, descricao, equipamento, urgencia, status,
     solicitante, prazo, criado_em, atualizado_em, motivo_espera) = ticket_data

    pode_editar = role in ("admin", "superadmin")
    pode_excluir = role == "superadmin"

    equipamento = equipamento if equipamento in EQUIPAMENTOS else "Outro"
    urgencia = urgencia if urgencia in URGENCIAS else "Média"
    status = status if status in STATUS else "Aberto"

    cor_urg = URG_COLOR.get(urgencia, "#999")
    cor_status = STATUS_COLOR.get(status, "#95A5A6")

    hoje = date.today().isoformat()
    atrasado = bool(prazo) and prazo < hoje and status not in STATUS_FINALIZADOS
    tempo_aberto = calculate_time_open(criado_em)
    prazo_fmt = format_date(prazo)

    titulo_curto = titulo[:60] + ("..." if len(titulo) > 60 else "")
    header = f"📌 TI-{tid:04d} · {titulo_curto}"
    if atrasado:
        header = f"⚠️ {header}"

    with st.expander(header, expanded=False):
        st.markdown(f"""
        <div style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
            <span class="tag">{escape_html(equipamento)}</span>
            <span class="urg-pill" style="background:{cor_urg};">⚡ {escape_html(urgencia)}</span>
            <span class="status-badge" style="background:{cor_status};">{escape_html(status)}</span>
            {'<span style="color:#D6394A; font-weight:700; margin-left:6px;">⚠️ Atrasado</span>' if atrasado else ''}
        </div>
        """, unsafe_allow_html=True)

        if descricao and descricao.strip():
            st.markdown(f'<div class="desc-box">{escape_html(descricao)}</div>', unsafe_allow_html=True)

        if status == "Aguardando resposta" and motivo_espera:
            st.markdown(
                f'<div class="desc-box" style="border-left-color:#3498DB;">⏳ <b>Motivo da espera:</b> {escape_html(motivo_espera)}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"""
        <div class="meta">
            👤 <b>Solicitante:</b> {escape_html(solicitante) or "—"} &nbsp;|&nbsp;
            📆 <b>Prazo:</b> {"⚠️ " if atrasado else ""}{prazo_fmt or "sem prazo"} &nbsp;|&nbsp;
            ⏱️ <b>Tempo aberto:</b> {tempo_aberto} &nbsp;|&nbsp;
            📅 <b>Criado:</b> {format_datetime(criado_em)}
        </div>
        """, unsafe_allow_html=True)

        if not pode_editar and not pode_excluir:
            st.caption("🔒 Faça login como admin para gerenciar este chamado.")
            return

        st.divider()

        colA, colB, colC = st.columns([1.6, 1, 1])

        with colA:
            if pode_editar:
                novo_status = st.selectbox(
                    "📌 Status", STATUS, index=STATUS.index(status), key=f"status_{tid}"
                )
                if novo_status != status:
                    if novo_status == "Aguardando resposta":
                        motivo_input = st.text_input(
                            "Motivo da espera",
                            value=motivo_espera or "",
                            key=f"motivo_{tid}",
                            placeholder="Ex: aguardando peça de reposição",
                        )
                        if st.button("✅ Confirmar", key=f"confirmar_motivo_{tid}"):
                            if not motivo_input.strip():
                                st.warning("Informe o motivo antes de confirmar.")
                            else:
                                success, msg = update_status(tid, novo_status, motivo_input.strip())
                                if success:
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        success, msg = update_status(tid, novo_status)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)

        with colB:
            if pode_editar and st.button("✏️ Editar", key=f"ed_{tid}", use_container_width=True):
                st.session_state[f"editando_{tid}"] = not st.session_state.get(f"editando_{tid}", False)

        with colC:
            if pode_excluir:
                confirmando = st.session_state.get(f"confirm_del_{tid}", False)
                label = "⚠️ Confirmar exclusão" if confirmando else "🗑️ Excluir"
                if st.button(label, key=f"del_{tid}", use_container_width=True):
                    if confirmando:
                        success, msg = delete_ticket(tid)
                        if success:
                            st.session_state.pop(f"confirm_del_{tid}", None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state[f"confirm_del_{tid}"] = True
                        st.rerun()

        if pode_editar and st.session_state.get(f"editando_{tid}", False):
            st.divider()
            st.markdown("#### ✏️ Editar chamado")
            with st.form(f"form_edit_{tid}"):
                e_titulo = st.text_input("Título", value=titulo)
                e_desc = st.text_area("Descrição", value=descricao or "")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_equip = st.selectbox("Equipamento", EQUIPAMENTOS, index=EQUIPAMENTOS.index(equipamento))
                    e_urg = st.selectbox("Urgência", URGENCIAS, index=URGENCIAS.index(urgencia))
                with col_e2:
                    e_solic = st.text_input("Solicitante", value=solicitante or "")
                e_prazo = st.date_input("Prazo", value=date.fromisoformat(prazo) if prazo else None)

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    salvar = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
                with col_s2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if salvar:
                    success, msg = update_ticket(tid, e_titulo, e_desc, e_equip, e_urg, e_solic, e_prazo)
                    if success:
                        st.session_state[f"editando_{tid}"] = False
                        st.rerun()
                    else:
                        st.error(msg)
                if cancelar:
                    st.session_state[f"editando_{tid}"] = False
                    st.rerun()


def render_recebido_card(recebido_data, role=None):
    """Card do sistema de Recebidos — completamente separado dos chamados
    (tabela própria, IDs próprios, chaves de widget com prefixo 'rec_' para
    nunca colidir com as chaves dos cards de chamado)."""
    (rid, item, origem, descricao, data_chegada, status, data_saida,
     o_que_foi_feito, reportado_por, criado_em, atualizado_em) = recebido_data

    pode_editar = role in ("admin", "superadmin")
    pode_excluir = role == "superadmin"

    cor = RECEBIDO_STATUS_COLOR.get(status, "#999")
    emoji = "🟠" if status == "Aguardando envio" else "🟢"
    item_curto = item[:60] + ("..." if len(item) > 60 else "")
    header = f"{emoji} REC-{rid:04d} · {item_curto}"

    with st.expander(header, expanded=False):
        st.markdown(
            f'<div style="margin-bottom: 12px;"><span class="status-badge" style="background:{cor};">{escape_html(status)}</span></div>',
            unsafe_allow_html=True,
        )

        chegada_txt = f" · chegou em {format_date(data_chegada)}" if data_chegada else ""
        st.markdown(
            f'<div class="desc-box" style="border-left-color:#9B59B6;">📦 <b>De onde veio:</b> {escape_html(origem)}{chegada_txt}</div>',
            unsafe_allow_html=True,
        )

        if descricao and descricao.strip():
            st.markdown(
                f'<div class="desc-box">📝 <b>O que precisa ser feito:</b> {escape_html(descricao)}</div>',
                unsafe_allow_html=True,
            )

        if status == "Enviado":
            st.markdown(
                f'<div class="desc-box" style="border-left-color:#2ECC71;">'
                f'✅ <b>Enviado em:</b> {format_date(data_saida) or "—"}<br>'
                f'<b>O que foi feito/enviado:</b> {escape_html(o_que_foi_feito) or "—"}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"""
        <div class="meta">
            👤 <b>Registrado por:</b> {escape_html(reportado_por) or "—"} &nbsp;|&nbsp;
            📅 <b>Registrado em:</b> {format_datetime(criado_em)}
        </div>
        """, unsafe_allow_html=True)

        if not pode_editar and not pode_excluir:
            st.caption("🔒 Faça login como admin para gerenciar este item.")
            return

        st.divider()

        if status == "Aguardando envio":
            if pode_editar:
                with st.form(f"rec_enviar_{rid}"):
                    st.markdown("**✅ Marcar como enviado**")
                    c1, c2 = st.columns(2)
                    with c1:
                        data_saida_input = st.date_input("Data de saída", value=date.today())
                    with c2:
                        feito_input = st.text_input("O que foi feito/enviado *", placeholder="Ex: peça trocada e devolvida")
                    confirmar = st.form_submit_button("Confirmar envio", type="primary", use_container_width=True)
                    if confirmar:
                        success, msg = marcar_enviado(rid, data_saida_input, feito_input)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            if pode_editar and st.button("↩️ Reabrir (voltar para Aguardando envio)", key=f"rec_reabrir_{rid}"):
                success, msg = reabrir_recebido(rid)
                if success:
                    st.rerun()
                else:
                    st.error(msg)

        col_ed, col_del = st.columns(2)
        with col_ed:
            if pode_editar and st.button("✏️ Editar", key=f"rec_ed_{rid}", use_container_width=True):
                st.session_state[f"rec_editando_{rid}"] = not st.session_state.get(f"rec_editando_{rid}", False)
        with col_del:
            if pode_excluir:
                confirmando = st.session_state.get(f"rec_confirm_del_{rid}", False)
                label = "⚠️ Confirmar exclusão" if confirmando else "🗑️ Excluir"
                if st.button(label, key=f"rec_del_{rid}", use_container_width=True):
                    if confirmando:
                        success, msg = delete_recebido(rid)
                        if success:
                            st.session_state.pop(f"rec_confirm_del_{rid}", None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state[f"rec_confirm_del_{rid}"] = True
                        st.rerun()

        if pode_editar and st.session_state.get(f"rec_editando_{rid}", False):
            st.divider()
            st.markdown("#### ✏️ Editar item recebido")
            with st.form(f"rec_form_edit_{rid}"):
                e_item = st.text_input("O que chegou", value=item)
                e_origem = st.text_input("De onde veio", value=origem)
                e_desc = st.text_area("O que precisa ser feito", value=descricao or "")
                e_chegada = st.date_input("Data de chegada", value=date.fromisoformat(data_chegada) if data_chegada else None)

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    salvar = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
                with col_s2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if salvar:
                    success, msg = update_recebido(rid, e_item, e_origem, e_desc, e_chegada)
                    if success:
                        st.session_state[f"rec_editando_{rid}"] = False
                        st.rerun()
                    else:
                        st.error(msg)
                if cancelar:
                    st.session_state[f"rec_editando_{rid}"] = False
                    st.rerun()


def display_metrics(stats):
    cols = st.columns(7)
    itens = [
        ("📊 Total", stats["total"], "#1E3C72"),
        ("🔴 Abertos", stats["Aberto"], "#E74C3C"),
        ("🟡 Andamento", stats["Em andamento"], "#F39C12"),
        ("🔵 Aguardando", stats["Aguardando resposta"], "#3498DB"),
        ("🟣 A enviar", stats["Precisa ser enviado"], "#9B59B6"),
        ("🟢 Concluídos", stats["Foi enviado/Concluído"], "#2ECC71"),
        ("🚨 Urgentes", stats["urgentes_abertos"], "#D6394A" if stats["urgentes_abertos"] > 0 else "#66707E"),
    ]
    for col, (label, valor, cor) in zip(cols, itens):
        with col:
            st.markdown(f"""
            <div class="metric-wrapper">
                <div class="metric-number" style="color:{cor};">{valor}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def display_header():
    st.markdown("""
    <div class="main-header">
        <h1>🖥️ Central de Chamados · TI</h1>
        <p>Sistema de gerenciamento de chamados técnicos</p>
    </div>
    """, unsafe_allow_html=True)


def display_footer(total_tickets):
    from datetime import datetime
    armazenamento = "☁️ Turso (nuvem, permanente)" if USE_TURSO else "💾 SQLite local"
    st.markdown(f"""
    <div class="footer">
        🖥️ Central de Chamados · TI &nbsp;|&nbsp; {datetime.now().strftime('%d/%m/%Y %H:%M')}
        &nbsp;|&nbsp; 🗃️ {total_tickets} chamados registrados &nbsp;|&nbsp; {armazenamento}
    </div>
    """, unsafe_allow_html=True)
