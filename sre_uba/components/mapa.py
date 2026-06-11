"""
components/mapa.py
==================
Constrói o mapa Folium com marcadores e traçado de itinerário.
Usa @st.cache_data para evitar reconstrução a cada rerun.
"""

import folium
import streamlit as st

from data.municipios import MUN_INDEX, MUNICIPIOS

COR_BASE    = "#1e3a5f"   # azul navy — saída / sede
COR_PARADA  = "#d97706"   # âmbar    — municípios do roteiro
COR_RETORNO = "#059669"   # verde    — encerramento
COR_ROTA    = "#2563eb"   # azul     — linha do itinerário
COR_INATIVO = "#94a3b8"   # cinza    — municípios não visitados


@st.cache_data(show_spinner=False)
def build_map(
    saida: str,
    paradas_tuple: tuple[str, ...],   # tuple para ser hashable pelo cache
    retorno: str,
    mostrar_todos: bool = True,
) -> folium.Map:
    """
    Constrói e retorna o mapa Folium.
    Recebe paradas como tupla para compatibilidade com @st.cache_data.
    """
    paradas = list(paradas_tuple)

    # Centro do território
    lat_c = sum(m["lat"] for m in MUNICIPIOS) / len(MUNICIPIOS)
    lon_c = sum(m["lon"] for m in MUNICIPIOS) / len(MUNICIPIOS)

    m = folium.Map(
        location=[lat_c, lon_c],
        zoom_start=9,
        tiles="CartoDB positron",
    )

    # Marcadores cinza de todos os municípios (fundo)
    if mostrar_todos:
        for mun in MUNICIPIOS:
            nome = mun["nome"]
            if nome in ([saida] + paradas + [retorno]):
                continue   # vai receber marcador colorido — pula aqui
            folium.CircleMarker(
                location=[mun["lat"], mun["lon"]],
                radius=5,
                color=COR_INATIVO,
                fill=True,
                fill_color="#cbd5e1",
                fill_opacity=0.6,
                tooltip=f"{nome} — {len(mun['escolas'])} escola(s)",
            ).add_to(m)

    # Linha do itinerário
    seq = [saida] + paradas + [retorno]
    if len(seq) > 1:
        coords = [[MUN_INDEX[n]["lat"], MUN_INDEX[n]["lon"]] for n in seq]
        folium.PolyLine(
            coords,
            color=COR_ROTA,
            weight=3.5,
            opacity=0.85,
            tooltip="Itinerário do dia",
        ).add_to(m)

    # Marcador de saída
    _marcador(m, saida, COR_BASE, "S", "Saída")

    # Paradas numeradas
    for i, p in enumerate(paradas, 1):
        n_esc = len(MUN_INDEX[p]["escolas"])
        _marcador(m, p, COR_PARADA, str(i), f"Parada {i} — {n_esc} escola(s)")

    # Encerramento (só se diferente da saída)
    if retorno != saida:
        _marcador(m, retorno, COR_RETORNO, "R", "Encerramento")
    elif paradas:
        _marcador(m, retorno, COR_BASE, "R", "Retorno à saída")

    return m


def _marcador(m: folium.Map, nome: str, cor: str, label: str, tooltip_extra: str):
    mun = MUN_INDEX[nome]
    popup_html = (
        f'<div style="font-family:sans-serif;min-width:190px">'
        f'<b style="font-size:14px">{nome}</b><br>'
        f'<span style="color:#64748b;font-size:12px">{tooltip_extra}</span><hr style="margin:4px 0">'
        f'<span style="font-size:12px">{len(mun["escolas"])} escola(s) estadual(is)</span>'
        f"</div>"
    )
    folium.Marker(
        location=[mun["lat"], mun["lon"]],
        popup=folium.Popup(popup_html, max_width=230),
        tooltip=f"{nome} ({tooltip_extra})",
        icon=folium.DivIcon(
            html=(
                f'<div style="background:{cor};color:white;'
                f'width:30px;height:30px;border-radius:50%;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:11px;font-weight:700;font-family:sans-serif;'
                f'border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,.3)">'
                f"{label}</div>"
            ),
            icon_size=(30, 30),
            icon_anchor=(15, 15),
        ),
    ).add_to(m)
