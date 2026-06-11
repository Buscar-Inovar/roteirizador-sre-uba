"""
utils/calculos.py
=================
Funções puras de cálculo: distâncias, jornada, análise de rota.
Sem dependências de Streamlit — testáveis isoladamente.
"""

from data.municipios import MUN_INDEX, DISTANCIAS_REAIS


# ---------------------------------------------------------------------------
# PARÂMETROS PADRÃO (sobrescritos via session_state na UI)
# ---------------------------------------------------------------------------

VELOCIDADE_KMH_DEFAULT     = 60
LIMITE_KM_PERNOITE_DEFAULT = 100
JORNADA_MAX_H_DEFAULT      = 8.0
HORAS_POR_ESCOLA_DEFAULT   = 2.0


# ---------------------------------------------------------------------------
# DISTÂNCIA
# ---------------------------------------------------------------------------

def dist_km(a: str, b: str, params: dict | None = None) -> int:
    """
    Retorna a distância rodoviária estimada entre dois municípios.

    Prioridade:
      1. Par cadastrado em DISTANCIAS_REAIS (medição real)
      2. Um dos pontos é Ubá → usa dist_uba diretamente
      3. Aproximação: |dist_uba_a - dist_uba_b| + min(a,b) * 0.25

    O argumento `params` é ignorado aqui mas mantido para assinatura uniforme.
    """
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


def calcular_segmentos(sequencia: list[str]) -> list[tuple[str, str, int]]:
    """Retorna [(origem, destino, km)] para cada trecho da sequência."""
    return [
        (sequencia[i], sequencia[i + 1], dist_km(sequencia[i], sequencia[i + 1]))
        for i in range(len(sequencia) - 1)
    ]


# ---------------------------------------------------------------------------
# TEMPO
# ---------------------------------------------------------------------------

def horas_estrada(km: int, velocidade: float = VELOCIDADE_KMH_DEFAULT) -> float:
    return km / velocidade if velocidade > 0 else 0.0


def fmt_h(h: float) -> str:
    """Formata float de horas em string legível: 1h 30min."""
    if h < 0:
        return "0min"
    hh = int(h)
    mm = round((h - hh) * 60)
    if mm == 60:          # evita "1h 60min"
        hh += 1
        mm = 0
    if hh == 0:
        return f"{mm}min"
    return f"{hh}h {mm}min" if mm else f"{hh}h"


# ---------------------------------------------------------------------------
# ANÁLISE DE JORNADA
# ---------------------------------------------------------------------------

def analisar_jornada(
    km_total: int,
    escolas_selecionadas: list[str],   # lista FLAT de nomes de escolas selecionadas
    params: dict,
) -> dict:
    """
    Analisa a viabilidade da jornada do dia.

    Parâmetros recebidos via `params` (session_state):
        velocidade_kmh, limite_km_pernoite, jornada_max_h, horas_por_escola
    """
    vel    = params.get("velocidade_kmh",     VELOCIDADE_KMH_DEFAULT)
    lim_km = params.get("limite_km_pernoite", LIMITE_KM_PERNOITE_DEFAULT)
    jorn_h = params.get("jornada_max_h",      JORNADA_MAX_H_DEFAULT)
    h_esc  = params.get("horas_por_escola",   HORAS_POR_ESCOLA_DEFAULT)

    n_esc    = len(escolas_selecionadas)
    h_est    = horas_estrada(km_total, vel)
    h_ag     = n_esc * h_esc
    h_tot    = h_est + h_ag
    saturado = h_tot > jorn_h
    pernoite = km_total > lim_km or saturado
    pct      = min(100, round((h_tot / jorn_h) * 100)) if jorn_h > 0 else 0

    return {
        "km_total":           km_total,
        "h_estrada":          h_est,
        "h_agenda":           h_ag,
        "h_total":            h_tot,
        "n_escolas":          n_esc,
        "saturado":           saturado,
        "pernoite":           pernoite,
        "pct_jornada":        pct,
        "limite_km":          lim_km,
        "jornada_max_h":      jorn_h,
        "horas_por_escola":   h_esc,
    }


# ---------------------------------------------------------------------------
# SUGESTÃO DE VIZINHOS (para pernoite)
# ---------------------------------------------------------------------------

def vizinhos_proximos(cidade: str, excluir: list[str], n: int = 5) -> list[tuple[str, int]]:
    """Retorna as N cidades mais próximas de `cidade`, excluindo as já visitadas."""
    from data.municipios import NOMES
    candidatos = [(c, dist_km(cidade, c)) for c in NOMES if c not in excluir and c != cidade]
    return sorted(candidatos, key=lambda x: x[1])[:n]
