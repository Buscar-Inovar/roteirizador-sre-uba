"""
utils/persistencia.py
=====================
Salva e carrega itinerários em JSON local.
Estrutura do arquivo: lista de itinerários, cada um com metadados e paradas.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path

ARQUIVO_DADOS = Path("data/itinerarios.json")


def _carregar_arquivo() -> list[dict]:
    """Carrega o JSON de itinerários. Retorna lista vazia se não existir."""
    if not ARQUIVO_DADOS.exists():
        return []
    try:
        with open(ARQUIVO_DADOS, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _salvar_arquivo(dados: list[dict]) -> None:
    ARQUIVO_DADOS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def salvar_itinerario(
    nome_consultor: str,
    data_visita: date,
    saida: str,
    retorno: str,
    paradas: list[dict],   # [{"municipio": str, "escolas": [str], "objetivo": str}]
    analise: dict,
    justificativa: str,
) -> str:
    """
    Salva um itinerário completo. Retorna o ID gerado.
    """
    dados = _carregar_arquivo()
    itin_id = datetime.now().strftime("%Y%m%d%H%M%S")
    registro = {
        "id":              itin_id,
        "consultor":       nome_consultor,
        "data_visita":     data_visita.isoformat(),
        "salvo_em":        datetime.now().isoformat(),
        "saida":           saida,
        "retorno":         retorno,
        "paradas":         paradas,
        "km_total":        analise.get("km_total", 0),
        "h_total":         analise.get("h_total", 0),
        "n_escolas":       analise.get("n_escolas", 0),
        "pernoite":        analise.get("pernoite", False),
        "justificativa":   justificativa,
    }
    dados.append(registro)
    _salvar_arquivo(dados)
    return itin_id


def listar_itinerarios() -> list[dict]:
    """Retorna todos os itinerários salvos, do mais recente ao mais antigo."""
    dados = _carregar_arquivo()
    return sorted(dados, key=lambda x: x.get("salvo_em", ""), reverse=True)


def carregar_itinerario(itin_id: str) -> dict | None:
    """Retorna um itinerário pelo ID, ou None se não encontrado."""
    for item in _carregar_arquivo():
        if item.get("id") == itin_id:
            return item
    return None


def excluir_itinerario(itin_id: str) -> bool:
    """Remove um itinerário pelo ID. Retorna True se encontrado e removido."""
    dados = _carregar_arquivo()
    novos = [d for d in dados if d.get("id") != itin_id]
    if len(novos) == len(dados):
        return False
    _salvar_arquivo(novos)
    return True


def resumo_mensal(mes: int, ano: int) -> dict:
    """Retorna estatísticas agregadas de um mês específico."""
    dados = _carregar_arquivo()
    filtrados = [
        d for d in dados
        if d.get("data_visita", "").startswith(f"{ano}-{mes:02d}")
    ]
    return {
        "total_viagens":  len(filtrados),
        "total_km":       sum(d.get("km_total", 0) for d in filtrados),
        "total_escolas":  sum(d.get("n_escolas", 0) for d in filtrados),
        "com_pernoite":   sum(1 for d in filtrados if d.get("pernoite")),
        "itinerarios":    filtrados,
    }
