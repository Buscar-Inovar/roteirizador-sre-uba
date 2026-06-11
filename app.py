"""
Sistema de Roteirização e Gestão Logística — SRE Ubá / Instituto Hortense
==========================================================================
Arquivo : app.py
Execução: streamlit run app.py

Dependências:
    pip install streamlit folium streamlit-folium

Funcionalidades:
    1. Mapa interativo com Folium — marcadores e traçado do itinerário
    2. Matriz de distâncias dinâmica (origem livre)
    3. Planejador do dia com trava de capacidade de agenda
    4. Regra automática de Pernoite / Bate-Volta
    5. Gerador de justificativa formal para prestação de contas
"""

import math
from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium

# ═══════════════════════════════════════════════════════════════════
#  BANCO DE DADOS OFICIAL
# ═══════════════════════════════════════════════════════════════════

MUNICIPIOS: list[dict] = [
    {
        "nome": "Ubá",
        "dist_uba": 0,
        "lat": -21.1197,
        "lon": -42.9436,
        "escolas": [
            "EE Deputado Carlos Peixoto Filho",
            "EE Eunice Weaver (Colônia Padre Damião)",
            "EE Barão do Rio Branco",
            "EE Raul Soares",
            "EE Professor Lívio de Castro Carneiro",
            "EE Doutor Levindo Coelho",
            "EE Coronel João Ferreira de Andrade",
            "EE Doutor Registrato José Januário Carneiro",
            "EE Cesário Alvim",
            "EE São José",
            "EE Governador Valadares",
            "EE Padre Joãozinho",
            "EE Coronel Teixeira Ervilha",
            "EE Coronel Camilo Soares",
            "EE Márcio Nicolato",
        ],
    },
    {
        "nome": "Rodeiro",
        "dist_uba": 12,
        "lat": -21.1953,
        "lon": -43.0231,
        "escolas": ["Escola Estadual de Rodeiro (Unidade Local)"],
    },
    {
        "nome": "Tocantins",
        "dist_uba": 17,
        "lat": -21.1703,
        "lon": -43.0167,
        "escolas": ["EE Professor João Loyola", "EE Dr. João Pinto"],
    },
    {
        "nome": "Visconde do Rio Branco",
        "dist_uba": 19,
        "lat": -21.0089,
        "lon": -42.8408,
        "escolas": [
            "EE Doutor Celso Machado",
            "EE Padre Antônio Correa",
            "EE Coronel Avelino Cardoso",
            "EE Tenente Roberto Soares de Souza Lima",
            "EE de Educação Especial Antonio de Gouvêa Lima",
        ],
    },
    {
        "nome": "Guidoval",
        "dist_uba": 22,
        "lat": -21.1561,
        "lon": -42.7886,
        "escolas": ["EE Mariana de Paiva", "EE Coronel Joaquim Martins"],
    },
    {
        "nome": "Piraúba",
        "dist_uba": 29,
        "lat": -21.0047,
        "lon": -43.0008,
        "escolas": [
            "EE Lafayete Maurício Lopes",
            "EE Professora Francisca Pereira Rodrigues",
            "EE Aurélio Bento Salgado (Córrego dos Ferreiras)",
        ],
    },
    {
        "nome": "Guiricema",
        "dist_uba": 31,
        "lat": -21.0125,
        "lon": -42.7858,
        "escolas": ["EE Prefeito Antônio Arruda"],
    },
    {
        "nome": "Divinésia",
        "dist_uba": 32,
        "lat": -21.1439,
        "lon": -43.1547,
        "escolas": ["EE Professor Biolkino de Andrade"],
    },
    {
        "nome": "São Geraldo",
        "dist_uba": 35,
        "lat": -20.9222,
        "lon": -42.8336,
        "escolas": ["EE Álvaro Giesta", "EE Ministro Aloísio Costa"],
    },
    {
        "nome": "Astolfo Dutra",
        "dist_uba": 36,
        "lat": -21.3136,
        "lon": -42.8592,
        "escolas": [
            "EE Olinto Almada",
            "EE Professor Souza Primo",
            "EE Deputado Edson Resende",
        ],
    },
    {
        "nome": "Rio Pomba",
        "dist_uba": 36,
        "lat": -21.2728,
        "lon": -43.1767,
        "escolas": ["EE Professor José Borges de Morais"],
    },
    {
        "nome": "Guarani",
        "dist_uba": 41,
        "lat": -21.3592,
        "lon": -43.0367,
        "escolas": ["EE Professor Alberto Pacheco"],
    },
    {
        "nome": "Coimbra",
        "dist_uba": 44,
        "lat": -20.8567,
        "lon": -42.8031,
        "escolas": ["EE Emílio Jardim"],
    },
    {
        "nome": "Ervália",
        "dist_uba": 46,
        "lat": -20.8378,
        "lon": -42.6592,
        "escolas": [
            "EE Dom Francisco das Chagas",
            "EE Professor David Procópio",
            "EE Monsenhor Rodolfo",
        ],
    },
    {
        "nome": "Silveirânia",
        "dist_uba": 49,
        "lat": -21.0950,
        "lon": -43.2219,
        "escolas": ["EE Santo Antônio"],
    },
    {
        "nome": "Senador Firmino",
        "dist_uba": 50,
        "lat": -20.9139,
        "lon": -43.1211,
        "escolas": ["EE Professor Cícero Torres Galindo"],
    },
    {
        "nome": "Dona Euzébia",
        "dist_uba": 51,
        "lat": -21.3947,
        "lon": -42.7561,
        "escolas": ["EE Domiciano Esteves", "EE Corina Vieira Henriques"],
    },
    {
        "nome": "Paula Cândido",
        "dist_uba": 52,
        "lat": -20.8700,
        "lon": -42.9258,
        "escolas": ["EE José Maurílio Valente", "EE Professor Samuel João de Deus"],
    },
    {
        "nome": "Presidente Bernardes",
        "dist_uba": 56,
        "lat": -21.4889,
        "lon": -42.9839,
        "escolas": ["EE Antônio Lucas Martins", "EE Padre Vicente Carvalho"],
    },
    {
        "nome": "Tabuleiro",
        "dist_uba": 57,
        "lat": -21.4664,
        "lon": -43.0736,
        "escolas": ["EE Menelick de Carvalho"],
    },
    {
        "nome": "Dores do Turvo",
        "dist_uba": 60,
        "lat": -20.9703,
        "lon": -43.2864,
        "escolas": ["EE Terezinha Pereira"],
    },
    {
        "nome": "Brás Pires",
        "dist_uba": 62,
        "lat": -20.8972,
        "lon": -43.0164,
        "escolas": ["EE José Alves de Magalhães", "EE São Luís"],
    },
]

# Índice por nome para acesso rápido
MUN_INDEX: dict[str, dict] = {m["nome"]: m for m in MUNICIPIOS}
NOMES: list[str] = [m["nome"] for m in MUNICIPIOS]

# ═══════════════════════════════════════════════════════════════════
#  PARÂMETROS OPERACIONAIS
# ═══════════════════════════════════════════════════════════════════

VELOCIDADE_KMH     = 60
LIMITE_KM_PERNOITE = 100
JORNADA_MAX_H      = 8.0
HORAS_POR_ESCOLA   = 2.0

# Distâncias reais entre cidades (preencha conforme necessário)
DISTANCIAS_REAIS: dict[tuple[str, str], int] = {
    # ("Astolfo Dutra", "Rio Pomba"): 10,
    # ("Piraúba", "Rio Pomba"):       12,
}

# ═══════════════════════════════════════════════════════════════════
#  FUNÇÕES DE CÁLCULO
# ═══════════════════════════════════════════════════════════════════


def dist_km(a: str, b: str) -> int:
    """Distância estimada entre dois municípios em km."""
    if a == b:
        return 0
    par = tuple(sorted([a, b]))
    if par in DISTANCIAS_REAIS:
        return DISTANCIAS_REAIS[par]
    da = MUN_INDEX[a]["dist_uba"]
    db = MUN_INDEX[b]["dist_uba"]
    if a == "Ubá":
        return db
    if b == "Ubá":
        return da
    return max(1, round(abs(da - db) + min(da, db) * 0.25))


def horas_estrada(km: int) -> float:
    return km / VELOCIDADE_KMH


def fmt_h(h: float) -> str:
    hh = int(h)
    mm = round((h - hh) * 60)
    if hh == 0:
        return f"{mm}min"
    return f"{hh}h {mm}min" if mm else f"{hh}h"


def calcular_rota(sequencia: list[str]) -> list[tuple[str, str, int]]:
    """Retorna lista de (origem, destino, km) para cada segmento."""
    return [
        (sequencia[i], sequencia[i + 1], dist_km(sequencia[i], sequencia[i + 1]))
        for i in range(len(sequencia) - 1)
    ]


def analisar_jornada(km_total: int, paradas: list[str]) -> dict:
    total_esc = sum(len(MUN_INDEX[p]["escolas"]) for p in paradas)
    h_est = horas_estrada(km_total)
    h_ag  = total_esc * HORAS_POR_ESCOLA
    h_tot = h_est + h_ag
    return {
        "km_total":    km_total,
        "h_estrada":   h_est,
        "h_agenda":    h_ag,
        "h_total":     h_tot,
        "total_esc":   total_esc,
        "saturado":    h_tot > JORNADA_MAX_H,
        "pernoite":    km_total > LIMITE_KM_PERNOITE or h_tot > JORNADA_MAX_H,
        "pct_jornada": min(100, round((h_tot / JORNADA_MAX_H) * 100)),
    }


# ═══════════════════════════════════════════════════════════════════
#  MAPA FOLIUM
# ═══════════════════════════════════════════════════════════════════

COR_BASE    = "#1e3a5f"   # azul navy — sede Ubá
COR_PARADA  = "#d97706"   # âmbar — municípios do roteiro
COR_RETORNO = "#059669"   # verde — ponto de encerramento
COR_ROTA    = "#2563eb"   # azul — linha do itinerário


def build_map(
    saida: str,
    paradas: list[str],
    retorno: str,
    todos: bool = False,
) -> folium.Map:
    """Constrói o mapa folium com marcadores e traçado da rota."""
    centro_lat = sum(m["lat"] for m in MUNICIPIOS) / len(MUNICIPIOS)
    centro_lon = sum(m["lon"] for m in MUNICIPIOS) / len(MUNICIPIOS)
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=9,
        tiles="CartoDB positron",
    )

    # Todos os municípios como marcadores cinza discretos
    if todos:
        for mun in MUNICIPIOS:
            folium.CircleMarker(
                location=[mun["lat"], mun["lon"]],
                radius=5,
                color="#94a3b8",
                fill=True,
                fill_color="#cbd5e1",
                fill_opacity=0.7,
                tooltip=f"{mun['nome']} — {len(mun['escolas'])} escola(s)",
            ).add_to(m)

    # Linha do itinerário
    sequencia_nomes = [saida] + paradas + ([retorno] if retorno != saida or not paradas else [])
    if len(sequencia_nomes) > 1:
        coords = [
            [MUN_INDEX[n]["lat"], MUN_INDEX[n]["lon"]]
            for n in sequencia_nomes
        ]
        folium.PolyLine(
            coords,
            color=COR_ROTA,
            weight=3,
            opacity=0.85,
            dash_array=None,
            tooltip="Itinerário do dia",
        ).add_to(m)

    # Marcador de saída
    _marcador(m, saida, COR_BASE, "🏠", numero=None, label="Saída")

    # Marcadores das paradas
    for i, p in enumerate(paradas, 1):
        n_esc = len(MUN_INDEX[p]["escolas"])
        _marcador(m, p, COR_PARADA, str(i), numero=i,
                  label=f"Parada {i} — {n_esc} escola(s)")

    # Marcador de retorno (só se diferente da saída)
    if retorno != saida or paradas:
        cor_ret = COR_RETORNO if retorno != saida else COR_BASE
        _marcador(m, retorno, cor_ret, "R", numero=None, label="Encerramento")

    return m


def _marcador(m: folium.Map, nome: str, cor: str, icone_texto: str,
              numero, label: str):
    mun = MUN_INDEX[nome]
    popup_html = f"""
    <div style="font-family:sans-serif;min-width:180px">
        <b style="font-size:14px">{nome}</b><br>
        <span style="color:#64748b;font-size:12px">{label}</span><br>
        <hr style="margin:4px 0">
        <span style="font-size:12px">{len(mun['escolas'])} escola(s) estadual(is)</span>
    </div>
    """
    folium.Marker(
        location=[mun["lat"], mun["lon"]],
        popup=folium.Popup(popup_html, max_width=220),
        tooltip=f"{nome} ({label})",
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:{cor};color:white;
                width:28px;height:28px;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-size:11px;font-weight:700;font-family:sans-serif;
                border:2px solid white;
                box-shadow:0 1px 4px rgba(0,0,0,.35);
            ">{icone_texto}</div>""",
            icon_size=(28, 28),
            icon_anchor=(14, 14),
        ),
    ).add_to(m)


# ═══════════════════════════════════════════════════════════════════
#  GERADOR DE JUSTIFICATIVA
# ═══════════════════════════════════════════════════════════════════


def gerar_justificativa(
    nome_consultor: str,
    data_str: str,
    paradas: list[str],
    analise: dict,
    base_retorno: str,
) -> str:
    muns_unicos = list(dict.fromkeys(paradas))
    todas_esc   = [e for p in paradas for e in MUN_INDEX[p]["escolas"]]

    if len(muns_unicos) == 1:
        mun_str = muns_unicos[0]
    else:
        mun_str = ", ".join(muns_unicos[:-1]) + " e " + muns_unicos[-1]

    if len(todas_esc) <= 4:
        esc_str = "; ".join(todas_esc)
    else:
        esc_str = (
            "; ".join(todas_esc[:3])
            + f"; e demais {len(todas_esc) - 3} unidade(s) do roteiro"
        )

    logistica = (
        f"Dada a extensão do circuito ({analise['km_total']} km), foi necessária "
        f"a ativação de pernoite em hotel regional no município de {base_retorno}, "
        "visando a otimização logística e o cumprimento integral da agenda pedagógica."
        if analise["pernoite"]
        else (
            f"O circuito de {analise['km_total']} km foi planejado com retorno à base "
            "em Ubá no mesmo dia, dentro dos parâmetros operacionais vigentes."
        )
    )

    return f"""JUSTIFICATIVA DE DESLOCAMENTO — SRE UBÁ / INSTITUTO HORTENSE

Em {data_str}, o(a) servidor(a) {nome_consultor}, no exercício de suas atribuições junto à Superintendência Regional de Ensino de Ubá (SRE Ubá), realizou visita técnica de acompanhamento pedagógico ao(s) município(s) de {mun_str}, percorrendo um total de {analise['km_total']} km em rota otimizada por proximidade geográfica.

Foram atendidas {analise['total_esc']} unidade(s) escolar(es) estadual(is), a saber: {esc_str}. Em cada unidade, foram realizadas ações de suporte técnico-pedagógico com duração estimada de {fmt_h(HORAS_POR_ESCOLA)} por escola, totalizando aproximadamente {fmt_h(analise['h_total'])} de jornada de trabalho efetivo, incluindo deslocamento.

{logistica}

O itinerário foi organizado de forma a concentrar as visitas por cluster geográfico, reduzindo deslocamentos redundantes e assegurando o máximo aproveitamento da jornada, em conformidade com as diretrizes de racionalização de recursos da SEE/MG."""


# ═══════════════════════════════════════════════════════════════════
#  STREAMLIT — CONFIGURAÇÃO GLOBAL
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
    /* Cabeçalho principal */
    .bloco-header {
        background: #1e3a5f;
        color: white;
        padding: 1rem 1.5rem 0.85rem;
        border-radius: 10px;
        margin-bottom: 1.25rem;
    }
    .bloco-header h1 {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 0 0 2px;
        color: white;
    }
    .bloco-header p {
        font-size: 0.8rem;
        opacity: 0.75;
        margin: 0;
        color: white;
    }
    /* Cartões de métricas */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        text-align: center;
    }
    .metric-card .label {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: .05em;
        margin-bottom: 2px;
    }
    .metric-card .value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .metric-card .value.warn  { color: #d97706; }
    .metric-card .value.danger { color: #dc2626; }
    .metric-card .value.ok    { color: #059669; }
    /* Barra de jornada */
    .jornada-bar-wrap {
        background: #e2e8f0;
        border-radius: 6px;
        height: 10px;
        overflow: hidden;
        margin: 4px 0 2px;
    }
    .jornada-bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width .4s;
    }
    /* Escola lista */
    .escola-item {
        padding: 4px 0;
        font-size: 0.82rem;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
    }
    .escola-item:last-child { border-bottom: none; }
    /* Justificativa */
    .just-box {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        font-size: 0.82rem;
        line-height: 1.75;
        white-space: pre-wrap;
        color: #1e293b;
        font-family: 'Georgia', serif;
    }
    /* Remove padding extra do Streamlit */
    .block-container { padding-top: 1rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════

if "paradas" not in st.session_state:
    st.session_state.paradas: list[str] = []


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR — CONFIGURAÇÃO DO DIA
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div class="bloco-header"><h1>🗺️ SRE Ubá</h1>'
        "<p>Roteirização e gestão logística</p></div>",
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

    st.markdown("#### Adicionar município ao roteiro")
    add_mun = st.selectbox("Município", NOMES, key="add_mun_sel")

    col_add, col_clear = st.columns(2)
    with col_add:
        if st.button("➕ Adicionar", use_container_width=True):
            st.session_state.paradas.append(add_mun)
    with col_clear:
        if st.button("🗑 Limpar", use_container_width=True):
            st.session_state.paradas = []

    # Lista de paradas com botões de remoção
    if st.session_state.paradas:
        st.markdown("**Roteiro atual:**")
        for i, p in enumerate(st.session_state.paradas):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(
                    f"<small><b>{i+1}.</b> {p} "
                    f"<span style='color:#94a3b8'>({len(MUN_INDEX[p]['escolas'])} esc.)</span></small>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("✕", key=f"del_{i}", help=f"Remover {p}"):
                    st.session_state.paradas.pop(i)
                    st.rerun()

    st.divider()
    st.markdown("#### Parâmetros operacionais")
    vel_kmh    = st.number_input("Velocidade média (km/h)", 40, 100, 60, 5)
    lim_km     = st.number_input("Limite pernoite (km)", 50, 200, 100, 10)
    jornada_h  = st.number_input("Jornada máxima (h)", 4.0, 12.0, 8.0, 0.5)
    h_escola   = st.number_input("Horas por visita escolar", 1.0, 4.0, 2.0, 0.5)

    VELOCIDADE_KMH     = vel_kmh
    LIMITE_KM_PERNOITE = lim_km
    JORNADA_MAX_H      = jornada_h
    HORAS_POR_ESCOLA   = h_escola


# ═══════════════════════════════════════════════════════════════════
#  CÁLCULOS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════

paradas = st.session_state.paradas
sequencia = [saida] + paradas + [retorno]

segmentos = calcular_rota(sequencia)
km_total  = sum(s[2] for s in segmentos)
analise   = analisar_jornada(km_total, paradas)


# ═══════════════════════════════════════════════════════════════════
#  LAYOUT PRINCIPAL — 3 ABAS
# ═══════════════════════════════════════════════════════════════════

tab_rota, tab_matriz, tab_consulta = st.tabs(
    ["📋 Planejador do dia", "📊 Matriz completa", "🔍 Consulta de cidade"]
)


# ───────────────────────────────────────────────────────────────────
#  ABA 1 — PLANEJADOR DO DIA
# ───────────────────────────────────────────────────────────────────

with tab_rota:

    # Métricas do topo
    pct = analise["pct_jornada"]
    cor_jornada = "danger" if pct >= 100 else "warn" if pct >= 80 else "ok"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, label, valor, cls in [
        (c1, "Km total", f"{km_total} km", ""),
        (c2, "Tempo estrada", fmt_h(analise["h_estrada"]), ""),
        (c3, "Tempo agenda", fmt_h(analise["h_agenda"]), ""),
        (c4, "Jornada total", fmt_h(analise["h_total"]), cor_jornada),
        (c5, "Escolas", str(analise["total_esc"]), ""),
        (c6, "Municípios", str(len(paradas)), ""),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="label">{label}</div>'
            f'<div class="value {cls}">{valor}</div></div>',
            unsafe_allow_html=True,
        )

    # Barra de uso da jornada
    bar_cor = "#dc2626" if pct >= 100 else "#d97706" if pct >= 80 else "#059669"
    st.markdown(
        f"""
        <div style="margin:.75rem 0 0;font-size:.75rem;color:#64748b;
                    display:flex;justify-content:space-between">
            <span>Uso da jornada ({fmt_h(JORNADA_MAX_H)})</span>
            <span><b>{pct}%</b></span>
        </div>
        <div class="jornada-bar-wrap">
            <div class="jornada-bar-fill"
                 style="width:{pct}%;background:{bar_cor}"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Alertas
    if analise["saturado"]:
        st.error(
            f"⚠️ **Agenda saturada.** Jornada estimada de {fmt_h(analise['h_total'])} "
            f"ultrapassa o limite de {fmt_h(JORNADA_MAX_H)}. "
            "Divida o roteiro em dois dias ou reduza o número de escolas."
        )
    elif pct >= 80:
        st.warning(
            f"⚡ Jornada em **{pct}%** ({fmt_h(analise['h_total'])} de {fmt_h(JORNADA_MAX_H)}). "
            "Sem margem para imprevistos."
        )

    if analise["pernoite"]:
        st.warning(
            f"🌙 **Pernoite recomendado.** Circuito de {km_total} km ultrapassa "
            f"{LIMITE_KM_PERNOITE} km. Sugerido: ativar pernoite em hotel regional "
            f"em **{retorno}**."
        )
    else:
        st.success(
            f"✅ **Bate-volta viável.** Circuito de {km_total} km — retorno para "
            f"**{retorno}** recomendado."
        )

    st.divider()

    # Mapa + detalhes lado a lado
    col_map, col_det = st.columns([3, 2])

    with col_map:
        st.markdown("##### Mapa do itinerário")
        mapa = build_map(saida, paradas, retorno, todos=True)
        st_folium(mapa, width=None, height=440, returned_objects=[])

    with col_det:
        st.markdown("##### Segmentos da rota")
        if not paradas:
            st.caption("Adicione municípios no painel lateral para montar o roteiro.")
        else:
            for i, (orig, dest, km) in enumerate(segmentos):
                is_ret = i == len(segmentos) - 1
                bg = "#fefce8" if is_ret else "#f8fafc"
                st.markdown(
                    f'<div style="background:{bg};border:1px solid #e2e8f0;'
                    f'border-radius:6px;padding:6px 10px;margin-bottom:5px;font-size:.82rem">'
                    f'<b>{"R" if is_ret else i+1}</b> &nbsp;'
                    f'{orig} → {dest}&nbsp;&nbsp;'
                    f'<span style="color:#64748b">{km} km / {fmt_h(horas_estrada(km))}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if paradas:
            st.markdown("##### Escolas por município")
            for p in paradas:
                with st.expander(
                    f"📍 {p} — {len(MUN_INDEX[p]['escolas'])} escola(s) · "
                    f"{fmt_h(len(MUN_INDEX[p]['escolas']) * HORAS_POR_ESCOLA)}"
                ):
                    for e in MUN_INDEX[p]["escolas"]:
                        st.markdown(
                            f'<div class="escola-item">• {e}</div>',
                            unsafe_allow_html=True,
                        )

    st.divider()

    # Gerador de justificativa
    st.markdown("##### Justificativa para prestação de contas")

    if not paradas:
        st.caption("Monte um roteiro para gerar a justificativa.")
    else:
        nm  = nome_consultor or "[Nome do consultor]"
        dat = data_visita.strftime("%d/%m/%Y")
        just_texto = gerar_justificativa(nm, dat, paradas, analise, retorno)

        st.markdown(
            f'<div class="just-box">{just_texto}</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            label="⬇️ Baixar justificativa (.txt)",
            data=just_texto.encode("utf-8"),
            file_name=f"justificativa_{dat.replace('/', '-')}.txt",
            mime="text/plain",
        )


# ───────────────────────────────────────────────────────────────────
#  ABA 2 — MATRIZ COMPLETA
# ───────────────────────────────────────────────────────────────────

with tab_matriz:
    st.markdown("##### Matriz de distâncias e capacidade")
    orig_mat = st.selectbox(
        "Origem para calcular", NOMES, key="mat_orig",
        help="Selecione o ponto de partida para ver todas as distâncias."
    )

    linhas = []
    for m in MUNICIPIOS:
        if m["nome"] == orig_mat:
            continue
        d_ida   = dist_km(orig_mat, m["nome"])
        circ    = d_ida + dist_km(m["nome"], orig_mat)
        n_esc   = len(m["escolas"])
        h_ag    = n_esc * HORAS_POR_ESCOLA
        h_tot   = horas_estrada(circ) + h_ag
        saturado = "⚠️ Saturado" if h_tot > JORNADA_MAX_H else "—"
        decisao  = "🌙 Pernoite" if circ > LIMITE_KM_PERNOITE else "✅ Bate-volta"
        linhas.append({
            "Município":     m["nome"],
            "Distância":     f"{d_ida} km",
            "Tempo viagem":  fmt_h(horas_estrada(d_ida)),
            "Circuito":      f"{circ} km",
            "Escolas":       n_esc,
            "Agenda mín.":   fmt_h(h_ag),
            "Jornada total": fmt_h(h_tot),
            "Saturação":     saturado,
            "Decisão":       decisao,
            "_d_ord":        d_ida,
        })

    linhas.sort(key=lambda x: x["_d_ord"])
    for l in linhas:
        del l["_d_ord"]

    st.dataframe(
        linhas,
        use_container_width=True,
        hide_index=True,
        height=min(60 + len(linhas) * 35, 600),
    )

    total_esc_terr = sum(len(m["escolas"]) for m in MUNICIPIOS)
    st.caption(
        f"Território: {len(MUNICIPIOS)} municípios · {total_esc_terr} escolas estaduais · "
        f"Velocidade: {VELOCIDADE_KMH} km/h · Limite pernoite: {LIMITE_KM_PERNOITE} km"
    )


# ───────────────────────────────────────────────────────────────────
#  ABA 3 — CONSULTA DE CIDADE
# ───────────────────────────────────────────────────────────────────

with tab_consulta:
    c_saida, c_dest = st.columns(2)
    with c_saida:
        cons_saida = st.selectbox("Saída", NOMES, key="cons_saida")
    with c_dest:
        cons_dest  = st.selectbox(
            "Município a consultar",
            [n for n in NOMES if n != cons_saida],
            key="cons_dest",
        )

    d_ida   = dist_km(cons_saida, cons_dest)
    circ    = d_ida + dist_km(cons_dest, cons_saida)
    mun_d   = MUN_INDEX[cons_dest]
    n_esc   = len(mun_d["escolas"])
    h_ag    = n_esc * HORAS_POR_ESCOLA
    h_tot   = horas_estrada(circ) + h_ag

    st.markdown(f"#### {cons_dest}")

    cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
    for col, lb, vl, cl in [
        (cc1, "Distância",      f"{d_ida} km",      ""),
        (cc2, "Tempo viagem",   fmt_h(horas_estrada(d_ida)), ""),
        (cc3, "Circuito",       f"{circ} km",       ""),
        (cc4, "Escolas",        str(n_esc),          ""),
        (cc5, "Agenda mínima",  fmt_h(h_ag),         ""),
        (cc6, "Jornada total",  fmt_h(h_tot),
             "danger" if h_tot > JORNADA_MAX_H else ""),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="label">{lb}</div>'
            f'<div class="value {cl}">{vl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    col_mapa_c, col_esc_c = st.columns([3, 2])

    with col_mapa_c:
        mapa_c = build_map(cons_saida, [cons_dest], cons_saida, todos=True)
        st_folium(mapa_c, width=None, height=380, returned_objects=[])

    with col_esc_c:
        if circ > LIMITE_KM_PERNOITE:
            st.warning(
                f"🌙 Pernoite recomendado. Circuito de {circ} km ultrapassa {LIMITE_KM_PERNOITE} km."
            )
        else:
            st.success(f"✅ Bate-volta viável. Circuito de {circ} km.")

        if h_tot > JORNADA_MAX_H:
            st.error(
                f"⚠️ Agenda saturada se visitar todas as {n_esc} escolas. "
                f"Jornada seria {fmt_h(h_tot)} (limite: {fmt_h(JORNADA_MAX_H)})."
            )

        st.markdown(f"**Escolas estaduais em {cons_dest}** ({n_esc})")
        for e in mun_d["escolas"]:
            st.markdown(
                f'<div class="escola-item">• {e}</div>',
                unsafe_allow_html=True,
            )
