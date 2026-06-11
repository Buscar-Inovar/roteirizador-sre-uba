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

from data.municipios import MUN_INDEX, MUNICIPIOS, NOMES, OBJETIVOS_VISITA
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
    carregar_itinerario,
)
from exports.documentos import gerar_justificativa, gerar_justificativa_formatada, gerar_pdf
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
        padding: 5px 0; font-size: .83rem;
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
    .seg-ret { background: #fefce8 !important; border-color: #fde68a !important; }

    .viz-chip {
        display: inline-block; background: #eff6ff; color: #1d4ed8;
        border: 1px solid #bfdbfe; border-radius: 99px;
        padding: 2px 10px; font-size: .75rem; margin: 2px;
    }

    .parada-card {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: .65rem .9rem; margin-bottom: .4rem;
    }
    .parada-card .p-titulo { font-size: .85rem; font-weight: 600; color: #1e3a5f; }
    .parada-card .p-sub    { font-size: .75rem; color: #64748b; margin-top: 2px; }

    .hist-card {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: .75rem 1rem; margin-bottom: .5rem;
    }

    .alerta-saturado {
        background: #fef2f2; border: 1px solid #fca5a5;
        border-radius: 8px; padding: .75rem 1rem;
        font-size: .85rem; color: #991b1b; margin-bottom: .5rem;
    }
    .alerta-pernoite {
        background: #fffbeb; border: 1px solid #fcd34d;
        border-radius: 8px; padding: .75rem 1rem;
        font-size: .85rem; color: #92400e; margin-bottom: .5rem;
    }
    .alerta-ok {
        background: #f0fdf4; border: 1px solid #86efac;
        border-radius: 8px; padding: .75rem 1rem;
        font-size: .85rem; color: #166534; margin-bottom: .5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════
#  SESSION STATE
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
#  HELPERS DE RENDERIZAÇÃO
# ═══════════════════════════════════════════════════════════════════

def _metric(col, lbl, val, cls=""):
    col.markdown(
        f'<div class="metric-card"><div class="lbl">{lbl}</div>'
        f'<div class="val {cls}">{val}</div></div>',
        unsafe_allow_html=True,
    )

def _barra_jornada(pct: int, jornada_max: float):
    bar_cor = "#dc2626" if pct >= 100 else "#d97706" if pct >= 80 else "#059669"
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:.73rem;color:#64748b;margin:.6rem 0 2px">'
        f'<span>Uso da jornada ({fmt_h(jornada_max)})</span>'
        f'<span><b>{pct}%</b></span></div>'
        f'<div class="jornada-wrap"><div class="jornada-fill" '
        f'style="width:{pct}%;background:{bar_cor}"></div></div>',
        unsafe_allow_html=True,
    )

def _alertas_jornada(analise: dict, retorno: str, params: dict):
    """Exibe alertas de saturação e pernoite/bate-volta."""
    if analise["saturado"]:
        st.error(
            f"⚠️ **Agenda saturada.** Jornada de **{fmt_h(analise['h_total'])}** "
            f"ultrapassa o limite de {fmt_h(params['jornada_max_h'])}. "
            "Divida o roteiro em dois dias ou reduza o número de escolas."
        )
    elif analise["pct_jornada"] >= 80:
        st.warning(
            f"⚡ Jornada em **{analise['pct_jornada']}%** "
            f"({fmt_h(analise['h_total'])} de {fmt_h(params['jornada_max_h'])}). "
            "Sem margem para imprevistos."
        )

    if analise["pernoite"]:
        excluir_viz = list({p["municipio"] for p in st.session_state.paradas})
        vizinhos = vizinhos_proximos(retorno, excluir_viz)
        chips = "".join(f'<span class="viz-chip">{v} ({d} km)</span>' for v, d in vizinhos[:5])
        st.markdown(
            f'<div class="alerta-pernoite">'
            f'🌙 <b>Pernoite recomendado.</b> Circuito de <b>{analise["km_total"]} km</b> '
            f'(limite: {params["limite_km_pernoite"]} km). '
            f'Sugerido: hotel regional em <b>{retorno}</b>.<br>'
            f'<span style="font-size:.78rem;opacity:.85">Próximos para amanhã: {chips}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="alerta-ok">'
            f'✅ <b>Bate-volta viável.</b> Circuito de {analise["km_total"]} km — '
            f'retorno para <b>{retorno}</b> recomendado.'
            f'</div>',
            unsafe_allow_html=True,
        )

def _segmentos_html(segmentos: list) -> str:
    html = ""
    for i, (orig, dest, km) in enumerate(segmentos):
        is_ret = i == len(segmentos) - 1
        cls = "seg-item seg-ret" if is_ret else "seg-item"
        label = "R" if is_ret else str(i + 1)
        h = fmt_h(horas_estrada(km, params["velocidade_kmh"]))
        html += (
            f'<div class="{cls}"><b>{label}</b> &nbsp; {orig} → {dest}'
            f' &nbsp; <span style="color:#64748b">{km} km / {h}</span></div>'
        )
    return html

def _escolas_por_parada(paradas: list, params: dict):
    """Renderiza expanders com escolas e objetivo por parada."""
    for p in paradas:
        n = len(p["escolas"])
        h = fmt_h(n * params["horas_por_escola"])
        with st.expander(f"📍 {p['municipio']} — {n} escola(s) · {h}"):
            if p.get("objetivo"):
                st.caption(f"Objetivo: {p['objetivo']}")
            for e in p["escolas"]:
                st.markdown(f'<div class="escola-item">• {e}</div>', unsafe_allow_html=True)


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

    st.markdown("#### Identificação")
    nome_consultor = st.text_input("Consultor responsável", placeholder="Nome completo")
    data_visita    = st.date_input("Data da visita", value=date.today())

    st.divider()

    st.markdown("#### Configurar o dia")
    saida   = st.selectbox("📍 Saída (onde você está agora)", NOMES, index=0)
    retorno = st.selectbox("🏁 Encerramento / retorno", NOMES, index=0)

    st.divider()

    st.markdown("#### Adicionar ao roteiro")
    add_mun = st.selectbox("Município", NOMES, key="sb_add_mun")

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
                    "escolas":   list(esc_selecionadas),
                    "objetivo":  obj_livre if obj_add == "Outro (especificar abaixo)" else obj_add,
                })
                st.rerun()
    with col_clear:
        if st.button("🗑 Limpar", use_container_width=True):
            st.session_state.paradas = []
            st.rerun()

    # Roteiro atual com remoção e reordenação
    if st.session_state.paradas:
        st.markdown("**Roteiro atual:**")
        for i, p in enumerate(st.session_state.paradas):
            c_txt, c_up, c_dn, c_del = st.columns([5, 1, 1, 1])
            with c_txt:
                st.markdown(
                    f"<small><b>{i+1}.</b> {p['municipio']} "
                    f"<span style='color:#94a3b8'>({len(p['escolas'])} esc.)</span></small>",
                    unsafe_allow_html=True,
                )
            with c_up:
                if i > 0 and st.button("↑", key=f"up_{i}", help="Mover para cima"):
                    lst = st.session_state.paradas
                    lst[i-1], lst[i] = lst[i], lst[i-1]
                    st.rerun()
            with c_dn:
                if i < len(st.session_state.paradas) - 1 and st.button("↓", key=f"dn_{i}", help="Mover para baixo"):
                    lst = st.session_state.paradas
                    lst[i], lst[i+1] = lst[i+1], lst[i]
                    st.rerun()
            with c_del:
                if st.button("✕", key=f"del_{i}", help=f"Remover {p['municipio']}"):
                    st.session_state.paradas.pop(i)
                    st.rerun()

    st.divider()

    with st.expander("⚙️ Parâmetros operacionais", expanded=False):
        st.session_state.velocidade_kmh   = st.number_input("Velocidade média (km/h)", 40, 120, int(st.session_state.velocidade_kmh), 5)
        st.session_state.limite_km        = st.number_input("Limite pernoite (km)",    50, 300, int(st.session_state.limite_km), 10)
        st.session_state.jornada_max_h    = st.number_input("Jornada máxima (h)",      4.0, 14.0, float(st.session_state.jornada_max_h), 0.5)
        st.session_state.horas_por_escola = st.number_input("Horas por visita escolar", 0.5, 6.0, float(st.session_state.horas_por_escola), 0.5)

    params.update({
        "velocidade_kmh":     st.session_state.velocidade_kmh,
        "limite_km_pernoite": st.session_state.limite_km,
        "jornada_max_h":      st.session_state.jornada_max_h,
        "horas_por_escola":   st.session_state.horas_por_escola,
    })


# ═══════════════════════════════════════════════════════════════════
#  CÁLCULOS CENTRAIS
# ═══════════════════════════════════════════════════════════════════

paradas      = st.session_state.paradas
nomes_seq    = [saida] + [p["municipio"] for p in paradas] + [retorno]
segmentos    = calcular_segmentos(nomes_seq)
km_total     = sum(s[2] for s in segmentos)
escolas_flat = [e for p in paradas for e in p["escolas"]]
analise      = analisar_jornada(km_total, escolas_flat, params)
pct          = analise["pct_jornada"]
cor_v        = "danger" if pct >= 100 else "warn" if pct >= 80 else "ok"


# ═══════════════════════════════════════════════════════════════════
#  ABAS
# ═══════════════════════════════════════════════════════════════════

tab_rota, tab_consulta, tab_matriz, tab_historico = st.tabs([
    "📋 Planejador do dia",
    "🔍 Consulta de cidade",
    "📊 Matriz completa",
    "📁 Histórico",
])


# ───────────────────────────────────────────────────────────────────
#  ABA 1 — PLANEJADOR DO DIA
# ───────────────────────────────────────────────────────────────────

with tab_rota:

    # ── Métricas ──────────────────────────────────────────────────
    cols = st.columns(6)
    _metric(cols[0], "Km total",      f"{km_total} km",             "")
    _metric(cols[1], "Tempo estrada", fmt_h(analise["h_estrada"]),   "")
    _metric(cols[2], "Tempo agenda",  fmt_h(analise["h_agenda"]),    "")
    _metric(cols[3], "Jornada total", fmt_h(analise["h_total"]),     cor_v)
    _metric(cols[4], "Escolas",       str(analise["n_escolas"]),     "")
    _metric(cols[5], "Municípios",    str(len(paradas)),             "")

    _barra_jornada(pct, params["jornada_max_h"])
    st.markdown("")

    # ── Alertas ───────────────────────────────────────────────────
    _alertas_jornada(analise, retorno, params)

    st.divider()

    # ── Mapa + segmentos + escolas ────────────────────────────────
    col_map, col_det = st.columns([3, 2])

    with col_map:
        st.markdown("##### Mapa do itinerário")
        if not paradas:
            st.caption("Adicione municípios na barra lateral para traçar o roteiro.")
        mapa = build_map(
            saida,
            tuple(p["municipio"] for p in paradas),
            retorno,
            mostrar_todos=True,
        )
        st_folium(mapa, width=None, height=430, returned_objects=[])

    with col_det:
        st.markdown("##### Sequência de segmentos")
        if not paradas:
            st.caption("Nenhuma parada adicionada.")
        else:
            st.markdown(_segmentos_html(segmentos), unsafe_allow_html=True)

        if paradas:
            st.markdown("##### Escolas por parada")
            _escolas_por_parada(paradas, params)

    st.divider()

    # ── Análise detalhada (equivalente ao _exibir_analise do Python) ──
    if paradas:
        with st.expander("📊 Ver análise detalhada completa", expanded=False):
            st.markdown(
                f"**Rota:** {' → '.join(nomes_seq)}\n\n"
                f"| Componente | Valor |\n|---|---|\n"
                f"| Km total | {km_total} km |\n"
                f"| Tempo de estrada | {fmt_h(analise['h_estrada'])} |\n"
                f"| Escolas selecionadas | {analise['n_escolas']} |\n"
                f"| Tempo de agenda | {fmt_h(analise['h_agenda'])} "
                f"({analise['n_escolas']} esc. × {fmt_h(params['horas_por_escola'])}) |\n"
                f"| **Jornada total** | **{fmt_h(analise['h_total'])}** "
                f"({pct}% de {fmt_h(params['jornada_max_h'])}) |\n"
                f"| Decisão | {'🌙 Pernoite em ' + retorno if analise['pernoite'] else '✅ Bate-volta para ' + retorno} |"
            )
            st.markdown("**Detalhamento por segmento:**")
            for i, (orig, dest, km) in enumerate(segmentos):
                is_ret = i == len(segmentos) - 1
                label = "Retorno" if is_ret else f"Trecho {i+1}"
                st.markdown(
                    f"- **{label}:** {orig} → {dest} — "
                    f"{km} km / {fmt_h(horas_estrada(km, params['velocidade_kmh']))}"
                )
            st.markdown("**Escolas selecionadas por município:**")
            for p in paradas:
                n = len(p["escolas"])
                h = fmt_h(n * params["horas_por_escola"])
                st.markdown(f"**{p['municipio']}** ({n} escola(s) · {h})")
                for e in p["escolas"]:
                    st.markdown(f"  - {e}")

    st.divider()

    # ── Objetivo e Justificativa ──────────────────────────────────
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
        nm   = nome_consultor or "[Nome do consultor]"
        just = gerar_justificativa_formatada(
            nome_consultor=nm,
            data_visita=data_visita,
            paradas=paradas,
            analise=analise,
            base_retorno=retorno,
            objetivo_principal=obj_principal,
            objetivo_livre=obj_livre_final,
        )

        st.markdown(f'<div class="just-box">{just}</div>', unsafe_allow_html=True)

        col_dl1, col_dl2, col_sv = st.columns(3)

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
            except (ImportError, FileNotFoundError) as e:
                st.caption(f"PDF indisponível: {e}")

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
                st.success(f"Salvo com sucesso! (ID: {iid})")


# ───────────────────────────────────────────────────────────────────
#  ABA 2 — CONSULTA DE CIDADE (equivalente ao fn_consulta do Python)
# ───────────────────────────────────────────────────────────────────

with tab_consulta:
    cc1, cc2 = st.columns(2)
    with cc1:
        cons_saida = st.selectbox("Saída", NOMES, key="cons_s")
    with cc2:
        cons_dest = st.selectbox(
            "Município a consultar",
            [n for n in NOMES if n != cons_saida],
            key="cons_d",
        )

    mun_d  = MUN_INDEX[cons_dest]
    d_ida  = dist_km(cons_saida, cons_dest)
    circ   = d_ida + dist_km(cons_dest, cons_saida)
    n_esc  = len(mun_d["escolas"])
    h_ag   = n_esc * params["horas_por_escola"]
    h_est  = horas_estrada(d_ida, params["velocidade_kmh"])
    h_circ = horas_estrada(circ, params["velocidade_kmh"])
    h_tot  = h_circ + h_ag   # jornada se visitar todas as escolas
    saturado_cons = h_tot > params["jornada_max_h"]

    st.markdown(f"#### {cons_dest}")
    st.caption(f"De {cons_saida} → {cons_dest} e retorno")

    # Métricas
    ccols = st.columns(6)
    _metric(ccols[0], "Distância",     f"{d_ida} km",       "")
    _metric(ccols[1], "Tempo viagem",  fmt_h(h_est),        "")
    _metric(ccols[2], "Circuito",      f"{circ} km",        "")
    _metric(ccols[3], "Escolas",       str(n_esc),           "")
    _metric(ccols[4], "Agenda mín.",   fmt_h(h_ag),         "")
    _metric(ccols[5], "Jornada total", fmt_h(h_tot),
            "danger" if saturado_cons else "warn" if h_tot / params["jornada_max_h"] >= 0.8 else "ok")

    st.markdown("")

    cm1, cm2 = st.columns([3, 2])

    with cm1:
        mapa_c = build_map(cons_saida, (cons_dest,), cons_saida, mostrar_todos=True)
        st_folium(mapa_c, width=None, height=400, returned_objects=[])

    with cm2:
        # Decisão bate-volta / pernoite
        if circ > params["limite_km_pernoite"]:
            vizinhos_c = vizinhos_proximos(cons_dest, [cons_saida, cons_dest])
            chips_c = "".join(
                f'<span class="viz-chip">{v} ({d} km)</span>'
                for v, d in vizinhos_c[:5]
            )
            st.markdown(
                f'<div class="alerta-pernoite">🌙 <b>Pernoite recomendado.</b> '
                f'Circuito de {circ} km ultrapassa {params["limite_km_pernoite"]} km.<br>'
                f'<span style="font-size:.78rem">Próximos a {cons_dest}: {chips_c}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="alerta-ok">✅ <b>Bate-volta viável.</b> '
                f'Circuito de {circ} km dentro do limite.</div>',
                unsafe_allow_html=True,
            )

        # Alerta de saturação se visitar todas
        if saturado_cons:
            st.markdown(
                f'<div class="alerta-saturado">⚠️ <b>Atenção:</b> visitar todas as {n_esc} '
                f'escolas resulta em {fmt_h(h_tot)} de jornada '
                f'(limite: {fmt_h(params["jornada_max_h"])}). '
                f'Considere dividir em duas visitas.</div>',
                unsafe_allow_html=True,
            )

        # Lista completa de escolas
        st.markdown(f"**Escolas estaduais em {cons_dest}** ({n_esc})")
        for e in mun_d["escolas"]:
            st.markdown(f'<div class="escola-item">• {e}</div>', unsafe_allow_html=True)

        # Botão de atalho: adicionar ao planejador
        st.markdown("")
        if st.button(f"➕ Adicionar {cons_dest} ao planejador", use_container_width=True, key="cons_add_btn"):
            st.session_state.paradas.append({
                "municipio": cons_dest,
                "escolas":   mun_d["escolas"],
                "objetivo":  "Acompanhamento pedagógico e monitoramento de indicadores educacionais",
            })
            st.success(f"{cons_dest} adicionado ao planejador.")


# ───────────────────────────────────────────────────────────────────
#  ABA 3 — MATRIZ COMPLETA (equivalente ao fn_matriz do Python)
# ───────────────────────────────────────────────────────────────────

with tab_matriz:
    st.markdown("##### Matriz completa — todos os municípios")

    mat_col1, mat_col2, mat_col3 = st.columns([2, 1, 1])
    with mat_col1:
        orig_mat = st.selectbox("Origem para calcular", NOMES, key="mat_orig")
    with mat_col2:
        filtro_decisao = st.selectbox(
            "Filtrar por decisão",
            ["Todos", "✅ Bate-volta", "🌙 Pernoite", "⚠️ Saturado"],
            key="mat_filtro",
        )
    with mat_col3:
        modo_matriz = st.radio(
            "Visualização",
            ["Tabela resumida", "Cards com escolas"],
            key="mat_modo",
            horizontal=True,
        )

    # Montar dados ordenados por distância
    linhas_mat = []
    for mun in MUNICIPIOS:
        nome  = mun["nome"]
        if nome == orig_mat:
            continue
        d_ida = dist_km(orig_mat, nome)
        circ  = d_ida + dist_km(nome, orig_mat)
        n_esc = len(mun["escolas"])
        h_ag  = n_esc * params["horas_por_escola"]
        h_est = horas_estrada(circ, params["velocidade_kmh"])
        h_tot = h_est + h_ag
        lim   = params["limite_km_pernoite"]
        sat   = h_tot > params["jornada_max_h"]
        bv    = circ <= lim

        linhas_mat.append({
            "nome":         nome,
            "escolas_list": mun["escolas"],
            "d_ida":        d_ida,
            "t_viagem":     fmt_h(horas_estrada(d_ida, params["velocidade_kmh"])),
            "circ":         circ,
            "n_esc":        n_esc,
            "h_ag":         h_ag,
            "h_tot":        h_tot,
            "sat":          sat,
            "bv":           bv,
        })

    linhas_mat.sort(key=lambda x: x["d_ida"])

    # Aplicar filtro
    if filtro_decisao == "✅ Bate-volta":
        linhas_mat = [l for l in linhas_mat if l["bv"]]
    elif filtro_decisao == "🌙 Pernoite":
        linhas_mat = [l for l in linhas_mat if not l["bv"]]
    elif filtro_decisao == "⚠️ Saturado":
        linhas_mat = [l for l in linhas_mat if l["sat"]]

    # ── MODO 1: Tabela resumida (igual ao fn_matriz do Python) ───────
    if modo_matriz == "Tabela resumida":
        tabela = []
        for l in linhas_mat:
            dec = "✅ Bate-volta" if l["bv"] else "🌙 Pernoite"
            if l["sat"]:
                dec += " ⚠️"
            tabela.append({
                "Município":     l["nome"],
                "Dist. (km)":    l["d_ida"],
                "Tempo viagem":  l["t_viagem"],
                "Circuito (km)": l["circ"],
                "Escolas":       l["n_esc"],
                "Jornada total": fmt_h(l["h_tot"]),
                "Saturado?":     "⚠️ Sim" if l["sat"] else "—",
                "Decisão":       dec,
            })

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
            height=min(80 + len(tabela) * 35, 680),
        )

    # ── MODO 2: Cards com drill-down de escolas (novo) ───────────────
    else:
        for l in linhas_mat:
            dec_label = "✅ Bate-volta" if l["bv"] else "🌙 Pernoite"
            sat_label = "  ⚠️ Saturado" if l["sat"] else ""
            cor_borda = "#86efac" if l["bv"] else "#fcd34d"
            if l["sat"]:
                cor_borda = "#fca5a5"

            with st.expander(
                f"{l['nome']}  ·  {l['d_ida']} km  ·  "
                f"{l['n_esc']} escola(s)  ·  {dec_label}{sat_label}"
            ):
                # Métricas internas do card
                c1, c2, c3, c4, c5 = st.columns(5)
                _metric(c1, "Distância",    f"{l['d_ida']} km",  "")
                _metric(c2, "Tempo viagem", l["t_viagem"],        "")
                _metric(c3, "Circuito",     f"{l['circ']} km",   "")
                _metric(c4, "Agenda mín.",  fmt_h(l["h_ag"]),    "")
                _metric(c5, "Jornada total",fmt_h(l["h_tot"]),
                        "danger" if l["sat"] else "warn" if l["h_tot"] / params["jornada_max_h"] >= 0.8 else "ok")

                # Alertas do município
                st.markdown("")
                if l["sat"]:
                    st.markdown(
                        f'<div class="alerta-saturado">⚠️ Visitar todas as {l["n_esc"]} escolas '
                        f'resulta em {fmt_h(l["h_tot"])} de jornada '
                        f'(limite: {fmt_h(params["jornada_max_h"])}).</div>',
                        unsafe_allow_html=True,
                    )
                elif not l["bv"]:
                    vizinhos_m = vizinhos_proximos(l["nome"], [orig_mat])
                    chips_m = "".join(
                        f'<span class="viz-chip">{v} ({d} km)</span>'
                        for v, d in vizinhos_m[:4]
                    )
                    st.markdown(
                        f'<div class="alerta-pernoite">🌙 Pernoite recomendado. '
                        f'Próximos a {l["nome"]}: {chips_m}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="alerta-ok">✅ Bate-volta viável a partir de {orig_mat}.</div>',
                        unsafe_allow_html=True,
                    )

                # Lista numerada de escolas (igual ao fn_consulta do Python)
                st.markdown(f"**Escolas estaduais em {l['nome']}** ({l['n_esc']})")
                for i, e in enumerate(l["escolas_list"], 1):
                    st.markdown(
                        f'<div class="escola-item">'
                        f'<span style="color:#94a3b8;font-size:.75rem;margin-right:8px">{i:02d}</span>'
                        f'{e}</div>',
                        unsafe_allow_html=True,
                    )

                # Atalho para adicionar ao planejador
                st.markdown("")
                if st.button(
                    f"➕ Adicionar {l['nome']} ao planejador",
                    key=f"mat_add_{l['nome']}",
                    use_container_width=True,
                ):
                    st.session_state.paradas.append({
                        "municipio": l["nome"],
                        "escolas":   l["escolas_list"],
                        "objetivo":  "Acompanhamento pedagógico e monitoramento de indicadores educacionais",
                    })
                    st.success(f"{l['nome']} adicionado ao planejador.")

    # ── Rodapé com totais do território (igual ao Python original) ───
    total_esc = sum(len(m["escolas"]) for m in MUNICIPIOS)
    tot_bv  = sum(1 for l in linhas_mat if l["bv"])
    tot_pn  = sum(1 for l in linhas_mat if not l["bv"])
    tot_sat = sum(1 for l in linhas_mat if l["sat"])

    st.divider()
    rod1, rod2, rod3, rod4 = st.columns(4)
    _metric(rod1, "Municípios exibidos", str(len(linhas_mat)),  "")
    _metric(rod2, "Bate-volta",          str(tot_bv),            "ok")
    _metric(rod3, "Pernoite",            str(tot_pn),            "warn" if tot_pn else "")
    _metric(rod4, "Saturados",           str(tot_sat),           "danger" if tot_sat else "")

    st.caption(
        f"Território completo: 22 municípios · {total_esc} escolas · "
        f"Origem: {orig_mat} · "
        f"Velocidade: {params['velocidade_kmh']} km/h · "
        f"Limite pernoite: {params['limite_km_pernoite']} km · "
        f"Jornada máx.: {fmt_h(params['jornada_max_h'])} · "
        f"{fmt_h(params['horas_por_escola'])}/escola"
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
        st.markdown("**Resumo do mês:**")
        st.markdown(
            f"- 🗓 **{resumo['total_viagens']}** viagens\n"
            f"- 🚗 **{resumo['total_km']} km** rodados\n"
            f"- 🏫 **{resumo['total_escolas']}** escolas atendidas\n"
            f"- 🌙 **{resumo['com_pernoite']}** pernoites"
        )

    with h_col1:
        itinerarios = listar_itinerarios()

        if not itinerarios:
            st.info(
                "Nenhum itinerário salvo ainda. "
                "Monte um roteiro na aba **Planejador do dia** e clique em 💾 Salvar."
            )
        else:
            for it in itinerarios:
                muns = ", ".join(p["municipio"] for p in it.get("paradas", []))
                label_pernoite = "🌙 Pernoite" if it.get("pernoite") else "✅ Bate-volta"
                with st.expander(
                    f"📅 {it['data_visita']}  —  {it.get('consultor', '—')}  "
                    f"|  {it['km_total']} km · {it['n_escolas']} esc. · {label_pernoite}"
                ):
                    # Detalhes do itinerário salvo
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Municípios:** {muns or '—'}")
                        st.markdown(
                            f"**Saída:** {it.get('saida', '—')}  \n"
                            f"**Retorno:** {it.get('retorno', '—')}"
                        )
                    with col_b:
                        st.markdown(
                            f"**Jornada:** {fmt_h(it.get('h_total', 0))}  \n"
                            f"**Km:** {it.get('km_total', 0)} km  \n"
                            f"**Escolas:** {it.get('n_escolas', 0)}"
                        )

                    # Escolas detalhadas
                    if it.get("paradas"):
                        with st.expander("Ver escolas deste itinerário"):
                            for p in it["paradas"]:
                                st.markdown(f"**{p['municipio']}**")
                                for e in p.get("escolas", []):
                                    st.markdown(f"  - {e}")

                    # Justificativa
                    if it.get("justificativa"):
                        with st.expander("Ver justificativa"):
                            st.markdown(
                                f'<div class="just-box">{it["justificativa"]}</div>',
                                unsafe_allow_html=True,
                            )
                        st.download_button(
                            "⬇️ Baixar justificativa .txt",
                            data=it["justificativa"].encode("utf-8"),
                            file_name=f"just_{it['data_visita']}.txt",
                            mime="text/plain",
                            key=f"dl_{it['id']}",
                        )

                    # Ações
                    bt1, bt2 = st.columns(2)
                    with bt1:
                        if st.button("📋 Recarregar no planejador", key=f"rec_{it['id']}", use_container_width=True):
                            st.session_state.paradas = it.get("paradas", [])
                            st.success(
                                f"Itinerário de {it['data_visita']} carregado no planejador. "
                                "Acesse a aba Planejador do dia."
                            )
                    with bt2:
                        if st.button("🗑 Excluir", key=f"exc_{it['id']}", use_container_width=True):
                            excluir_itinerario(it["id"])
                            st.success("Registro excluído.")
                            st.rerun()
