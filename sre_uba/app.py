"""
app.py — SRE Ubá / Instituto Hortense
======================================
Sistema de roteirização logística com mapa interativo.

Execução:
    streamlit run app.py

Dependências:
    pip install streamlit folium streamlit-folium fpdf2
"""

import os
import sys
from datetime import date

# ═══════════════════════════════════════════════════════════════════
#  INJEÇÃO DO DIRETÓRIO RAIZ (Resolve o erro ModuleNotFoundError)
# ═══════════════════════════════════════════════════════════════════
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    "velocidade_kmh":      st.session_state.velocidade_kmh,
    "limite_km_pernoite": st.session_state.limite_km,
    "jornada_max_h":      st.session_state.jornada_max_h,
    "horas_por_escola":   st.session_state.horas_por_escola,
}


# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        """<div style="background:#1e3a5f;color:white;padding:.85rem 1rem;border-radius:10px;margin-bottom:1rem"><div style="font-size:1.1rem;font-weight:700">🗺️ SRE Ubá</div><div style="font-size:.75rem;opacity:.75">Roteirização logística — Instituto Hortense</div></div>""",
        unsafe_allow_html=True,
    )

    # ── Identificação ────────────────────────────────────────────
    st.markdown("#### Identificação")
    nome_consultor = st.text_input("Consultor responsible", placeholder="Nome completo")
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
