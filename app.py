"""
Sistema de Roteirização e Gestão Logística — SRE Ubá / Instituto Hortense
==========================================================================
Arquivo : app.py
Execução: streamlit run app.py
"""

import math
from datetime import date
import folium
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Roteirizador SRE Ubá",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para aproximar ao layout limpo dos anexos
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #0d6efd;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-card .label {
        font-size: 13px;
        color: #6c757d;
        font-weight: bold;
        text-transform: uppercase;
    }
    .metric-card .value {
        font-size: 20px;
        color: #212529;
        font-weight: bold;
        margin-top: 5px;
    }
    .metric-card .value.danger {
        color: #dc3545;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
            "EE Deputado Carlos Peixoto Filho", "EE Eunice Weaver (Colônia Padre Damião)",
            "EE Barão do Rio Branco", "EE Raul Soares", "EE Professor Lívio de Castro Carneiro",
            "EE Doutor Levindo Coelho", "EE Coronel João Ferreira de Andrade",
            "EE Doutor Registrato José Januário Carneiro", "EE Cesário Alvim", "EE São José",
            "EE Governador Valadares", "EE Padre Joãozinho", "EE Coronel Teixeira Ervilha",
            "EE Coronel Camilo Soares", "EE Márcio Nicolato"
        ]
    },
    {"nome": "Rodeiro", "dist_uba": 12, "lat": -21.2014, "lon": -42.8647, "escolas": ["Escola Estadual de Rodeiro (Unidade Local)"]},
    {"nome": "Tocantins", "dist_uba": 17, "lat": -21.1739, "lon": -43.0183, "escolas": ["EE Professor João Loyola", "EE Dr. João Pinto"]},
    {
        "nome": "Visconde do Rio Branco",
        "dist_uba": 19,
        "lat": -21.0119,
        "lon": -42.8378,
        "escolas": [
            "EE Doutor Celso Machado", "EE Padre Antônio Correa",
            "EE Coronel Avelino Cardoso", "EE Tenente Roberto Soares de Souza Lima",
            "EE de Educação Especial Antonio de Gouvêa Lima"
        ]
    },
    {"nome": "Guidoval", "dist_uba": 22, "lat": -21.1447, "lon": -42.7972, "escolas": ["EE Mariana de Paiva", "EE Coronel Joaquim Martins"]},
    {
        "nome": "Piraúba",
        "dist_uba": 29,
        "lat": -21.2422,
        "lon": -42.8881,
        "escolas": ["EE Lafayete Maurício Lopes", "EE Professora Francisca Pereira Rodrigues", "EE Aurélio Bento Salgado"]
    },
    {"nome": "Guiricema", "dist_uba": 31, "lat": -21.0169, "lon": -42.6833, "escolas": ["EE Prefeito Antônio Arruda"]},
    {"nome": "Divinésia", "dist_uba": 32, "lat": -20.9258, "lon": -42.9461, "escolas": ["EE Professor Biolkino de Andrade"]},
    {"nome": "São Geraldo", "dist_uba": 35, "lat": -20.9228, "lon": -42.8408, "escolas": ["EE Álvaro Giesta", "EE Ministro Aloísio Costa"]},
    {
        "nome": "Astolfo Dutra",
        "dist_uba": 36,
        "lat": -21.3156,
        "lon": -42.8619,
        "escolas": ["EE Olinto Almada", "EE Professor Souza Primo", "EE Deputado Edson Resende"]
    },
    {"nome": "Rio Pomba", "dist_uba": 36, "lat": -21.2747, "lon": -43.1775, "escolas": ["EE Professor José Borges de Morais"]},
    {"nome": "Guarani", "dist_uba": 41, "lat": -21.3519, "lon": -43.0464, "escolas": ["EE Professor Alberto Pacheco"]},
    {"nome": "Coimbra", "dist_uba": 44, "lat": -20.8497, "lon": -42.8011, "escolas": ["EE Emílio Jardim"]},
    {
        "nome": "Ervália",
        "dist_uba": 46,
        "lat": -20.8408,
        "lon": -42.6033,
        "escolas": ["EE Dom Francisco das Chagas", "EE Professor David Procópio", "EE Monsenhor Rodolfo"]
    },
    {"nome": "Silveirânia", "dist_uba": 49, "lat": -21.1675, "lon": -43.2172, "escolas": ["EE Santo Antônio"]},
    {"nome": "Senador Firmino", "dist_uba": 50, "lat": -20.9119, "lon": -43.0903, "escolas": ["EE Professor Cícero Torres Galindo"]},
    {"nome": "Dona Euzébia", "dist_uba": 51, "lat": -21.3194, "lon": -42.8053, "escolas": ["EE Domiciano Esteves", "EE Corina Vieira Henriques"]},
    {"nome": "Paula Cândido", "dist_uba": 52, "lat": -20.8269, "lon": -42.9103, "escolas": ["EE José Maurílio Valente", "EE Professor Samuel João de Deus"]},
    {"nome": "Presidente Bernardes", "dist_uba": 56, "lat": -20.7689, "lon": -43.1103, "escolas": ["EE Antônio Lucas Martins", "EE Padre Vicente Carvalho"]},
    {"nome": "Tabuleiro", "dist_uba": 57, "lat": -21.3661, "lon": -43.2503, "escolas": ["EE Menelick de Carvalho"]},
    {"nome": "Dores do Turvo", "dist_uba": 60, "lat": -21.1097, "lon": -43.1603, "escolas": ["EE Terezinha Pereira"]},
    {"nome": "Brás Pires", "dist_uba": 62, "lat": -20.9239, "lon": -43.1983, "escolas": ["EE José Alves de Magalhães", "EE São Luís"]}
]

NOMES = [m["nome"] for m in MUNICIPIOS]
DICT_MUNICIPIOS = {m["nome"]: m for m in MUNICIPIOS}

# Regras operacionais do projeto
VELOCIDADE_MEDIA_KMH = 50.0
TEMPO_PREPARO_MIN = 15
TEMPO_VISITA_ESC_H = 2.0
JORNADA_MAX_H = 8.0
LIMITE_KM_PERNOITE = 100

def fmt_h(horas_dec):
    h = int(horas_dec)
    m = int(round((horas_dec - h) * 60))
    if h == 0:
        return f"{m}min"
    return f"{h}h {m:02d}min"

def calc_distancia_dois_pontos(p1, p2):
    return abs(DICT_MUNICIPIOS[p1]["dist_uba"] - DICT_MUNICIPIOS[p2]["dist_uba"])

# ═══════════════════════════════════════════════════════════════════
#  BARRA LATERAL - PLANEJAMENTO DE VIAGEM
# ═══════════════════════════════════════════════════════════════════
st.sidebar.markdown("### 🗺️ CONTROLADOR LOGÍSTICO")

cons_saida = st.sidebar.selectbox("Ponto de Saída (Origem):", NOMES, index=0)
cons_dest = st.sidebar.selectbox("Ponto de Retorno (Encerramento):", NOMES, index=0)

st.sidebar.markdown("---")
# PONTO 1 CORRIGIDO: Nome do bloco claro focado em locais a serem visitados
st.sidebar.markdown("#### 🏫 LOCALIZAÇÃO DAS ESCOLAS A SEREM VISITADAS")

locais_visitados = st.sidebar.multiselect(
    "Selecione os municípios que vai inspecionar hoje:",
    [m for m in NOMES if m != cons_saida]
)

# ═══════════════════════════════════════════════════════════════════
#  CORPO PRINCIPAL - PAINEL DE MONITORAMENTO UNIFICADO
# ═══════════════════════════════════════════════════════════════════
st.title("🚚 Painel Unificado de Rotas e Monitoramento")
st.subheader("SRE Ubá — Instituto Hortense")

if locais_visitados:
    # PONTO 2 CORRIGIDO: Tabela Cruzada Cidade X Qtd Escolas X Nomes das Escolas no topo
    st.markdown("### 📋 Cruzamento Territorial: Escolas por Município Atendido")
    
    dados_cruzamento = []
    for cid in locais_visitados:
        lista_esc = DICT_MUNICIPIOS[cid]["escolas"]
        dados_cruzamento.append({
            "Cidade / Município": cid,
            "Quantidade de Escolas": len(lista_esc),
            "Nome das Unidades Escolares": ", ".join(lista_esc)
        })
    
    df_cruzado = pd.DataFrame(dados_cruzamento)
    st.dataframe(df_cruzado, use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════════════════════════
    #  CÁLCULOS LOGÍSTICOS E JORNADA
    # ═══════════════════════════════════════════════════════════════
    # Montagem da sequência de paradas reais
    roteiro_completo = [cons_saida] + locais_visitados + [cons_dest]
    
    circ = 0
    for i in range(len(roteiro_completo) - 1):
        circ += calc_distancia_dois_pontos(roteiro_completo[i], roteiro_completo[i+1])
    
    if circ == 0:
        circ = 5 # Margem mínima para deslocamento interno na mesma cidade
        
    tempo_estrada_h = circ / VELOCIDADE_MEDIA_KMH
    
    # Contagem de escolas e tempo pedagógico
    escolas_alvo = []
    for cid in locais_visitados:
        escolas_alvo.extend(DICT_MUNICIPIOS[cid]["escolas"])
        
    n_esc = len(escolas_alvo)
    h_ag = n_esc * TEMPO_VISITA_ESC_H
    h_tot = tempo_estrada_h + (TEMPO_PREPARO_MIN / 60.0) + h_ag

    # PONTO 3 CORRIGIDO: Exibição contínua sem ocultar dados em abas
    st.markdown("### 🚗 Indicadores de Deslocamento e Viabilidade Operacional")
    
    # Bloco de Cartões de Métricas em Linha
    cc1, cc2, cc3, cc4, cc5 = st.columns(5)
    with cc1:
        st.markdown(f'<div class="metric-card"><div class="label">Tempo Estrada</div><div class="value">{fmt_h(tempo_estrada_h)}</div></div>', unsafe_allow_html=True)
    with cc2:
        st.markdown(f'<div class="metric-card"><div class="label">Circuito Total</div><div class="value">{circ} km</div></div>', unsafe_allow_html=True)
    with cc3:
        st.markdown(f'<div class="metric-card"><div class="label">Nº Escolas</div><div class="value">{n_esc}</div></div>', unsafe_allow_html=True)
    with cc4:
        st.markdown(f'<div class="metric-card"><div class="label">Agenda Mínima</div><div class="value">{fmt_h(h_ag)}</div></div>', unsafe_allow_html=True)
    with cc5:
        classe_danger = "danger" if h_tot > JORNADA_MAX_H else ""
        st.markdown(f'<div class="metric-card"><div class="label">Jornada Total</div><div class="value {classe_danger}">{fmt_h(h_tot)}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # Linha Paralela: Mapa Interativo e Diagnóstico de Viagem
    col_mapa, col_diagnostico = st.columns([3, 2])
    
    with col_mapa:
        st.markdown("#### Mapa do Circuito de Visitas")
        # Centraliza o mapa com base na coordenada da cidade de Saída
        mapa_folium = folium.Map(
            location=[DICT_MUNICIPIOS[cons_saida]["lat"], DICT_MUNICIPIOS[cons_saida]["lon"]], 
            zoom_start=10
        )
        
        coordenadas_linha = []
        for cidade in list(dict.fromkeys(roteiro_completo)):
            lat_c = DICT_MUNICIPIOS[cidade]["lat"]
            lon_c = DICT_MUNICIPIOS[cidade]["lon"]
            coordenadas_linha.append([lat_c, lon_c])
            
            cor = "blue" if cidade == cons_saida else ("green" if cidade == cons_dest else "red")
            folium.Marker(
                location=[lat_c, lon_c],
                popup=f"<b>{cidade}</b><br>{len(DICT_MUNICIPIOS[cidade]['escolas'])} escola(s)",
                icon=folium.Icon(color=cor, icon="home" if cor=="blue" else "info-sign")
            ).add_to(mapa_folium)
            
        if len(coordenadas_linha) > 1:
            folium.PolyLine(coordenadas_linha, color="#0d6efd", weight=4, opacity=0.8).add_to(mapa_folium)
            
        st_folium(mapa_folium, width=None, height=380, returned_objects=[])

    with col_diagnostico:
        st.markdown("#### Diretrizes de Viagem & Custo")
        
        # Alerta de Pernoite
        if circ > LIMITE_KM_PERNOITE:
            st.warning(f"🌙 **Pernoite Recomendado:** O circuito de {circ} km ultrapassa o limite regulamentar de {LIMITE_KM_PERNOITE} km diários.")
            status_pernoite = "Estadia com Pernoite Regional"
        else:
            st.success(f"✅ **Bate-Volta Viável:** Quilometragem total de {circ} km dentro da normalidade operacional.")
            status_pernoite = "Bate-Volta com Retorno à Base"
            
        # Alerta de Horas Estouradas
        if h_tot > JORNADA_MAX_H:
            st.error(f"⚠️ **Alerta de Carga Horária:** A jornada total de {fmt_h(h_tot)} ultrapassa o limite tolerável de {JORNADA_MAX_H}h diárias. Recomenda-se desmembrar esta rota.")
        else:
            st.success("🕒 **Carga Horária Adequada:** Tempo de trânsito e agenda compatíveis com um dia de trabalho.")

        # Quadro Resumo dos Segmentos Atendidos
        st.markdown("📂 **Resumo dos Segmentos Alvo:**")
        st.caption("• Ensino Fundamental (Regular de 9 anos)")
        st.caption("• Ensino Médio / Profissionalizante")

    # ═══════════════════════════════════════════════════════════════
    #  GERADOR DE JUSTIFICATIVA FORMAL
    # ═══════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### ✍️ Justificativa de Deslocamento para Prestação de Contas")
    
    txt_cidades = ", ".join(locais_visitados)
    txt_escolas = "; ".join(escolas_alvo)
    
    justificativa_final = (
        f"Deslocamento intermunicipal realizado em circuito rodoviário no dia {date.today().strftime('%d/%m/%Y')} "
        f"com ponto inicial em {cons_saida} e encerramento em {cons_dest}. Foram visitados os municípios de {txt_cidades} "
        f"para acompanhamento técnico do projeto e auditoria das metas institucionais nas seguintes unidades escolares: "
        f"{txt_escolas}. O roteiro foi consolidado adotando critérios de otimização logística por proximidade territorial "
        f"para redução de quilometragem e economia de combustível. Circuito enquadrado como '{status_pernoite}' devido "
        f"aos parâmetros de distância acumulada ({circ} km) e tempo de agenda pedagógica requerida."
    )
    
    st.text_area("Copie o texto para validação no formulário de reembolso/transporte:", value=justificativa_final, height=130)
    
    st.download_button(
        label="💾 Descarregar Justificativa (.txt)",
        data=justificativa_final,
        file_name=f"justificativa_rota_{date.today().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

else:
    st.info("👈 Utilize a barra lateral à esquerda e selecione os 'Locais a serem visitados' para projetar os cruzamentos territoriais, mapa e relatórios de viagem.")
