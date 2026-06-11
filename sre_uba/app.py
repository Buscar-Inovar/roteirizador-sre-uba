"""
app.py — SRE Ubá / Instituto Hortense
======================================
Sistema de roteirização logística com mapa interativo.

Execução:
    streamlit run app.py

Dependências:
    pip install streamlit folium streamlit-folium fpdf2
"""

from datetime import date

import streamlit as st
from streamlit_folium import st_folium

# Módulos internos
from data.municipios import MUN_INDEX, NOMES, OBJETIVOS_VISITA
from utils.calculos import (
    analisar_jornada,
    calcular_segmentos,
    dist_km,
    fmt_h,
    horas_estrada,
    vizinhos_proximos,
)
from utils.persistencia import (
    excluir_itinerario,
    listar_itinerarios,
    resumo_mensal,
    salvar_itinerario,
)
from exports.documentos import gerar_justificativa, gerar_pdf
from components.mapa import build_map


# ═══════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SRE Ubá — Roteirização",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem !important; }

    .metric-card {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: .65rem 1rem; text-align: center;
    }
    .metric-card .lbl {
        font-size: .68rem; color: #64748b;
        text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px;
    }
    .metric-card .val { font-size: 1.2rem; font-weight: 700; color: #1e3a5f; }
    .metric-card .val.warn   { color: #d97706; }
    .metric-card .val.danger { color: #dc2626; }
    .metric-card .val.ok     { color: #059669; }

    .jornada-wrap {
        background: #e2e8f0; border-radius: 6px;
        height: 10px; overflow: hidden; margin: 5px 0 2px;
    }
    .jornada-fill { height: 100%; border-radius: 6px; }

    .escola-item {
        padding: 4px 0; font-size: .82rem;
        border-bottom: 1px solid #f1f5f9; color: #334155;
    }
    .escola-item:last-child { border-bottom: none; }

    .just-box {
        background: #f8fafc; border: 1px solid #cbd5e1;
        border-radius: 8px; padding: 1rem 1.25rem;
        font-size: .82rem; line-height: 1.8;
        white-space: pre-wrap; color: #1e293b;
        font-family: Georgia, serif;
    }

    .seg-item {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 6px; padding: 6px 10px; margin-bottom: 5px;
        font-size: .82rem;
    }
    .seg-ret { background: #fefce8; }

    .hist-card {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: .75rem 1rem; margin-bottom: .5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════
#  SESSION STATE — inicialização segura
# ═══════════════════════════════════════════════════════════════════

_defaults = {
    "paradas":          [],   # [{"municipio": str, "escolas": [str], "objetivo": str}]
    "velocidade_kmh":   60,
    "limite_km":        100,
    "jornada_max_h":    8.0,
    "horas_por_escola": 2.0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

params = {
    "velocidade_kmh":     st.session_state.velocidade_kmh,
    "limite_km_pernoite": st.session_state.limite_km,
    "jornada_max_h":      st.session_state.jornada_max_h,
    "horas_por_escola":   st.session_state.horas_por_escola,
}


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div style="background:#1e3a5f;color:white;padding:.85rem 1rem;'
        'border-radius:10px;margin-bottom:1rem">'
        '<div style="font-size:1.1rem;font-weight:700">🗺️ SRE Ubá</div>'
        '<div style="font-size:.75rem;opacity:.75">Roteirização logística — Instituto Hortense</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Identificação ────────────────────────────────────────────
    st.markdown("#### Identificação")
    nome_consultor = st.text_input("Consultor responsável", placeholder="Nome completo")
    data_visita    = st.date_input("Data da visita", value=date.today())

    st.divider()

    # ── Configurar o dia ─────────────────────────────────────────
    st.markdown("#### Configurar o dia")
    saida   = st.selectbox("📍 Saída (onde você está agora)", NOMES, index=0)
    retorno = st.selectbox("🏁 Encerramento / retorno", NOMES, index=0)

    st.divider()

    # ── Adicionar município ──────────────────────────────────────
    st.markdown("#### Adicionar ao roteiro")
    add_mun = st.selectbox("Município", NOMES, key="sb_add_mun")

    # Multiselect de escolas do município selecionado
    todas_esc_add = MUN_INDEX[add_mun]["escolas"]
    esc_selecionadas = st.multiselect(
        "Escolas a visitar",
        todas_esc_add,
        default=todas_esc_add,
        key="ms_escolas_add",
        help="Desmarque escolas que não serão visitadas nesta passagem.",
    )

    obj_add = st.selectbox("Objetivo da visita", OBJETIVOS_VISITA, key="sb_obj_add")
    obj_livre = ""
    if obj_add == "Outro (especificar abaixo)":
        obj_livre = st.text_input("Descreva o objetivo", key="ti_obj_livre")

    col_add, col_clear = st.columns(2)
    with col_add:
        if st.button("➕ Adicionar", use_container_width=True):
            if not esc_selecionadas:
                st.warning("Selecione ao menos uma escola.")
            else:
                st.session_state.paradas.append({
                    "municipio": add_mun,
                    "escolas":   esc_selecionadas,
                    "objetivo":  obj_livre if obj_add == "Outro (especificar abaixo)" else obj_add,
                })
                st.rerun()

    with col_clear:
        if st.button("🗑 Limpar", use_container_width=True):
            st.session_state.paradas = []
            st.rerun()

    # Lista do roteiro com remoção individual
    if st.session_state.paradas:
        st.markdown("**Roteiro atual:**")
        for i, p in enumerate(st.session_state.paradas):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f"<small><b>{i+1}.</b> {p['municipio']} "
                    f"<span style='color:#94a3b8'>({len(p['escolas'])} esc.)</span></small>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("✕", key=f"del_{i}", help=f"Remover {p['municipio']}"):
                    st.session_state.paradas.pop(i)
                    st.rerun()

    st.divider()

    # ── Parâmetros ───────────────────────────────────────────────
    with st.expander("⚙️ Parâmetros operacionais", expanded=False):
        st.session_state.velocidade_kmh   = st.number_input("Velocidade média (km/h)", 40, 120, 60, 5)
        st.session_state.limite_km        = st.number_input("Limite pernoite (km)",    50, 300, 100, 10)
        st.session_state.jornada_max_h    = st.number_input("Jornada máxima (h)",      4.0, 14.0, 8.0, 0.5)
        st.session_state.horas_por_escola = st.number_input("Horas por visita escolar", 0.5, 6.0, 2.0, 0.5)

    # Atualizar params com valores possivelmente alterados
    params.update({
        "velocidade_kmh":     st.session_state.velocidade_kmh,
        "limite_km_pernoite": st.session_state.limite_km,
        "jornada_max_h":      st.session_state.jornada_max_h,
        "horas_por_escola":   st.session_state.horas_por_escola,
    })


# ═══════════════════════════════════════════════════════════════════
#  CÁLCULOS CENTRAIS
# ═══════════════════════════════════════════════════════════════════

paradas   = st.session_state.paradas
nomes_seq = [saida] + [p["municipio"] for p in paradas] + [retorno]
segmentos = calcular_segmentos(nomes_seq)
km_total  = sum(s[2] for s in segmentos)

# Escolas efetivamente selecionadas (lista flat)
escolas_flat = [e for p in paradas for e in p["escolas"]]
analise      = analisar_jornada(km_total, escolas_flat, params)


# ═══════════════════════════════════════════════════════════════════
#  ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════

tab_rota, tab_matriz, tab_consulta, tab_historico = st.tabs([
    "📋 Planejador do dia",
    "📊 Matriz completa",
    "🔍 Consulta de cidade",
    "📁 Histórico",
])


# ───────────────────────────────────────────────────────────────────
#  ABA 1 — PLANEJADOR DO DIA
# ───────────────────────────────────────────────────────────────────

with tab_rota:

    # Métricas
    pct = analise["pct_jornada"]
    cor_v = "danger" if pct >= 100 else "warn" if pct >= 80 else "ok"

    cols = st.columns(6)
    for col, lbl, val, cls in [
        (cols[0], "Km total",       f"{km_total} km",                   ""),
        (cols[1], "Tempo estrada",  fmt_h(analise["h_estrada"]),         ""),
        (cols[2], "Tempo agenda",   fmt_h(analise["h_agenda"]),          ""),
        (cols[3], "Jornada total",  fmt_h(analise["h_total"]),           cor_v),
        (cols[4], "Escolas",        str(analise["n_escolas"]),            ""),
        (cols[5], "Municípios",     str(len(paradas)),                   ""),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="lbl">{lbl}</div>'
            f'<div class="val {cls}">{val}</div></div>',
            unsafe_allow_html=True,
        )

    # Barra de jornada
    bar_cor = "#dc2626" if pct >= 100 else "#d97706" if pct >= 80 else "#059669"
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:.73rem;color:#64748b;margin:.6rem 0 2px">'
        f'<span>Uso da jornada ({fmt_h(params["jornada_max_h"])})</span>'
        f'<span><b>{pct}%</b></span></div>'
        f'<div class="jornada-wrap"><div class="jornada-fill" '
        f'style="width:{pct}%;background:{bar_cor}"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Alertas
    if analise["saturado"]:
        st.error(
            f"⚠️ **Agenda saturada.** Jornada estimada de **{fmt_h(analise['h_total'])}** "
            f"ultrapassa o limite de {fmt_h(params['jornada_max_h'])}. "
            "Divida o roteiro em dois dias ou reduza o número de escolas visitadas."
        )
    elif pct >= 80:
        st.warning(
            f"⚡ Jornada em **{pct}%** ({fmt_h(analise['h_total'])} "
            f"de {fmt_h(params['jornada_max_h'])}). Sem margem para imprevistos."
        )

    if analise["pernoite"]:
        vizinhos = vizinhos_proximos(retorno, [p["municipio"] for p in paradas] + [saida])
        viz_str  = " · ".join(f"{v} ({d} km)" for v, d in vizinhos[:4])
        st.warning(
            f"🌙 **Pernoite recomendado.** Circuito de **{km_total} km** "
            f"(limite: {params['limite_km_pernoite']} km). "
            f"Sugerido: hotel regional em **{retorno}**.\n\n"
            f"Próximos para amanhã: {viz_str}"
        )
    else:
        st.success(
            f"✅ **Bate-volta viável.** Circuito de {km_total} km — "
            f"retorno para **{retorno}** recomendado."
        )

    st.divider()

    # Mapa + detalhes
    col_map, col_det = st.columns([3, 2])

    with col_map:
        st.markdown("##### Mapa do itinerário")
        if not paradas:
            st.caption("Adicione municípios na barra lateral para traçar o roteiro.")
            mapa = build_map(saida, tuple(), retorno, mostrar_todos=True)
        else:
            mapa = build_map(
                saida,
                tuple(p["municipio"] for p in paradas),
                retorno,
                mostrar_todos=True,
            )
        st_folium(mapa, width=None, height=430, returned_objects=[])

    with col_det:
        st.markdown("##### Segmentos")
        if not paradas:
            st.caption("Nenhuma parada adicionada.")
        else:
            for i, (orig, dest, km) in enumerate(segmentos):
                is_ret = i == len(segmentos) - 1
                cls    = "seg-item seg-ret" if is_ret else "seg-item"
                st.markdown(
                    f'<div class="{cls}"><b>{"R" if is_ret else i+1}</b> &nbsp; '
                    f'{orig} → {dest} &nbsp; '
                    f'<span style="color:#64748b">{km} km / '
                    f'{fmt_h(horas_estrada(km, params["velocidade_kmh"]))}</span></div>',
                    unsafe_allow_html=True,
                )

        if paradas:
            st.markdown("##### Escolas por município")
            for p in paradas:
                n = len(p["escolas"])
                h = fmt_h(n * params["horas_por_escola"])
                with st.expander(f"📍 {p['municipio']} — {n} escola(s) · {h}"):
                    if p.get("objetivo"):
                        st.caption(f"Objetivo: {p['objetivo']}")
                    for e in p["escolas"]:
                        st.markdown(
                            f'<div class="escola-item">• {e}</div>',
                            unsafe_allow_html=True,
                        )

    st.divider()

    # Objetivo principal e justificativa
    st.markdown("##### Objetivo principal da visita")
    obj_principal = st.selectbox(
        "Objetivo",
        OBJETIVOS_VISITA,
        key="sb_obj_principal",
        label_visibility="collapsed",
    )
    obj_livre_final = ""
    if obj_principal == "Outro (especificar abaixo)":
        obj_livre_final = st.text_area(
            "Descreva o objetivo", key="ta_obj_livre_final", height=70
        )

    st.markdown("##### Justificativa para prestação de contas")

    if not paradas:
        st.caption("Monte um roteiro para gerar a justificativa.")
    else:
        nm  = nome_consultor or "[Nome do consultor]"
        just = gerar_justificativa(
            nome_consultor=nm,
            data_visita=data_visita,
            paradas=paradas,
            analise=analise,
            base_retorno=retorno,
            objetivo_principal=obj_principal,
            objetivo_livre=obj_livre_final,
        )

        st.markdown(
            f'<div class="just-box">{just}</div>',
            unsafe_allow_html=True,
        )

        col_dl1, col_dl2, col_sv = st.columns([2, 2, 2])

        with col_dl1:
            st.download_button(
                "⬇️ Baixar .txt",
                data=just.encode("utf-8"),
                file_name=f"justificativa_{data_visita.strftime('%d-%m-%Y')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_dl2:
            try:
                pdf_bytes = gerar_pdf(
                    nome_consultor=nm,
                    data_visita=data_visita,
                    paradas=paradas,
                    analise=analise,
                    segmentos=segmentos,
                    base_retorno=retorno,
                    justificativa=just,
                )
                st.download_button(
                    "⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_{data_visita.strftime('%d-%m-%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except ImportError:
                st.caption("fpdf2 não instalado — PDF indisponível.")

        with col_sv:
            if st.button("💾 Salvar itinerário", use_container_width=True):
                iid = salvar_itinerario(
                    nome_consultor=nm,
                    data_visita=data_visita,
                    saida=saida,
                    retorno=retorno,
                    paradas=paradas,
                    analise=analise,
                    justificativa=just,
                )
                st.success(f"Itinerário salvo (ID: {iid})")


# ───────────────────────────────────────────────────────────────────
#  ABA 2 — MATRIZ COMPLETA
# ───────────────────────────────────────────────────────────────────

with tab_matriz:
    st.markdown("##### Matriz de distâncias e capacidade")
    orig_mat = st.selectbox("Origem para calcular", NOMES, key="mat_orig")

    linhas = []
    for mun in [m for m in __import__("data.municipios", fromlist=["MUNICIPIOS"]).MUNICIPIOS
                if m["nome"] != orig_mat]:
        nome   = mun["nome"]
        d_ida  = dist_km(orig_mat, nome)
        circ   = d_ida + dist_km(nome, orig_mat)
        n_esc  = len(mun["escolas"])
        h_ag   = n_esc * params["horas_por_escola"]
        h_est  = horas_estrada(circ, params["velocidade_kmh"])
        h_tot  = h_est + h_ag
        lim    = params["limite_km_pernoite"]

        linhas.append({
            "Município":       nome,
            "Dist. (km)":      d_ida,
            "Tempo viagem":    fmt_h(horas_estrada(d_ida, params["velocidade_kmh"])),
            "Circuito (km)":   circ,
            "Escolas":         n_esc,
            "Agenda mín.":     fmt_h(h_ag),
            "Jornada total":   fmt_h(h_tot),
            "Saturado?":       "⚠️ Sim" if h_tot > params["jornada_max_h"] else "—",
            "Decisão":         "🌙 Pernoite" if circ > lim else "✅ Bate-volta",
            "_ord":            d_ida,
        })

    linhas.sort(key=lambda x: x["_ord"])
    for l in linhas:
        del l["_ord"]

    st.dataframe(
        linhas,
        use_container_width=True,
        hide_index=True,
        height=min(80 + len(linhas) * 35, 640),
    )
    from data.municipios import MUNICIPIOS as _MUNS
    total_esc = sum(len(m["escolas"]) for m in _MUNS)
    st.caption(
        f"22 municípios · {total_esc} escolas · "
        f"Velocidade: {params['velocidade_kmh']} km/h · "
        f"Limite pernoite: {params['limite_km_pernoite']} km · "
        f"Jornada máx.: {fmt_h(params['jornada_max_h'])} · "
        f"{fmt_h(params['horas_por_escola'])}/escola"
    )


# ───────────────────────────────────────────────────────────────────
#  ABA 3 — CONSULTA DE CIDADE
# ───────────────────────────────────────────────────────────────────

with tab_consulta:
    cc1, cc2 = st.columns(2)
    with cc1:
        cons_saida = st.selectbox("Saída", NOMES, key="cons_s")
    with cc2:
        cons_dest  = st.selectbox(
            "Município a consultar",
            [n for n in NOMES if n != cons_saida],
            key="cons_d",
        )

    mun_d  = MUN_INDEX[cons_dest]
    d_ida  = dist_km(cons_saida, cons_dest)
    circ   = d_ida + dist_km(cons_dest, cons_saida)
    n_esc  = len(mun_d["escolas"])
    h_ag   = n_esc * params["horas_por_escola"]
    h_est  = horas_estrada(circ, params["velocidade_kmh"])
    h_tot  = h_est + h_ag

    st.markdown(f"#### {cons_dest}")

    ccols = st.columns(6)
    for col, lb, vl, cl in [
        (ccols[0], "Distância",     f"{d_ida} km",     ""),
        (ccols[1], "Tempo viagem",  fmt_h(horas_estrada(d_ida, params["velocidade_kmh"])), ""),
        (ccols[2], "Circuito",      f"{circ} km",      ""),
        (ccols[3], "Escolas",       str(n_esc),         ""),
        (ccols[4], "Agenda mín.",   fmt_h(h_ag),        ""),
        (ccols[5], "Jornada total", fmt_h(h_tot),
             "danger" if h_tot > params["jornada_max_h"] else ""),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="lbl">{lb}</div>'
            f'<div class="val {cl}">{vl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    cm1, cm2 = st.columns([3, 2])
    with cm1:
        mapa_c = build_map(cons_saida, (cons_dest,), cons_saida, mostrar_todos=True)
        st_folium(mapa_c, width=None, height=380, returned_objects=[])

    with cm2:
        if circ > params["limite_km_pernoite"]:
            st.warning(f"🌙 Pernoite recomendado. Circuito de {circ} km.")
        else:
            st.success(f"✅ Bate-volta viável. Circuito de {circ} km.")

        if h_tot > params["jornada_max_h"]:
            st.error(
                f"⚠️ Visitar todas as {n_esc} escolas resulta em "
                f"{fmt_h(h_tot)} de jornada (limite: {fmt_h(params['jornada_max_h'])})."
            )

        st.markdown(f"**Escolas em {cons_dest}** ({n_esc})")
        for e in mun_d["escolas"]:
            st.markdown(
                f'<div class="escola-item">• {e}</div>',
                unsafe_allow_html=True,
            )


# ───────────────────────────────────────────────────────────────────
#  ABA 4 — HISTÓRICO
# ───────────────────────────────────────────────────────────────────

with tab_historico:
    st.markdown("##### Histórico de itinerários salvos")

    h_col1, h_col2 = st.columns([3, 1])
    with h_col2:
        hoje = date.today()
        mes  = st.number_input("Mês", 1, 12, hoje.month, key="hist_mes")
        ano  = st.number_input("Ano", 2024, 2030, hoje.year, key="hist_ano")
        resumo = resumo_mensal(int(mes), int(ano))
        st.markdown(
            f"**{resumo['total_viagens']}** viagens · "
            f"**{resumo['total_km']} km** · "
            f"**{resumo['total_escolas']}** escolas · "
            f"**{resumo['com_pernoite']}** pernoites"
        )

    with h_col1:
        itinerarios = listar_itinerarios()

        if not itinerarios:
            st.info("Nenhum itinerário salvo ainda. Finalize um roteiro na aba **Planejador do dia** e clique em 💾 Salvar.")
        else:
            for it in itinerarios:
                muns = ", ".join(p["municipio"] for p in it.get("paradas", []))
                with st.expander(
                    f"📅 {it['data_visita']}  —  {it.get('consultor','—')}  "
                    f"|  {it['km_total']} km  ·  {it['n_escolas']} esc."
                ):
                    st.markdown(f"**Municípios:** {muns or '—'}")
                    st.markdown(
                        f"**Jornada:** {fmt_h(it.get('h_total', 0))}  "
                        f"| **Pernoite:** {'Sim' if it.get('pernoite') else 'Não'}  "
                        f"| **Saída:** {it.get('saida','—')}  "
                        f"| **Retorno:** {it.get('retorno','—')}"
                    )

                    if it.get("justificativa"):
                        st.markdown(
                            f'<div class="just-box">{it["justificativa"]}</div>',
                            unsafe_allow_html=True,
                        )
                        st.download_button(
                            "⬇️ Baixar justificativa",
                            data=it["justificativa"].encode("utf-8"),
                            file_name=f"just_{it['data_visita']}.txt",
                            mime="text/plain",
                            key=f"dl_{it['id']}",
                        )

                    if st.button("🗑 Excluir este registro", key=f"exc_{it['id']}"):
                        excluir_itinerario(it["id"])
                        st.success("Registro excluído.")
                        st.rerun()
