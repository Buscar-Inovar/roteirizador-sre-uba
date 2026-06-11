"""
data/municipios.py
==================
Banco de dados oficial SRE Ubá — municípios, escolas e coordenadas.

Coordenadas via IBGE / OpenStreetMap (valores precisos).
Distâncias reais entre pares de cidades frequentes: preencha conforme
você for medindo no campo ou via Google Maps. Qualquer par não cadastrado
usa a aproximação linear como fallback transparente.
"""

# ---------------------------------------------------------------------------
# BANCO DE MUNICÍPIOS
# Cada entrada: nome, dist_uba (km rodoviário), lat/lon (IBGE), escolas
# ---------------------------------------------------------------------------

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
        "lat": -21.1958,
        "lon": -43.0217,
        "escolas": ["Escola Estadual de Rodeiro (Unidade Local)"],
    },
    {
        "nome": "Tocantins",
        "dist_uba": 17,
        "lat": -21.1714,
        "lon": -43.0156,
        "escolas": ["EE Professor João Loyola", "EE Dr. João Pinto"],
    },
    {
        "nome": "Visconde do Rio Branco",
        "dist_uba": 19,
        "lat": -21.0100,
        "lon": -42.8394,
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
        "lat": -21.1553,
        "lon": -42.7900,
        "escolas": ["EE Mariana de Paiva", "EE Coronel Joaquim Martins"],
    },
    {
        "nome": "Piraúba",
        "dist_uba": 29,
        "lat": -21.0044,
        "lon": -43.0000,
        "escolas": [
            "EE Lafayete Maurício Lopes",
            "EE Professora Francisca Pereira Rodrigues",
            "EE Aurélio Bento Salgado (Córrego dos Ferreiras)",
        ],
    },
    {
        "nome": "Guiricema",
        "dist_uba": 31,
        "lat": -21.0131,
        "lon": -42.7872,
        "escolas": ["EE Prefeito Antônio Arruda"],
    },
    {
        "nome": "Divinésia",
        "dist_uba": 32,
        "lat": -21.1444,
        "lon": -43.1556,
        "escolas": ["EE Professor Biolkino de Andrade"],
    },
    {
        "nome": "São Geraldo",
        "dist_uba": 35,
        "lat": -20.9233,
        "lon": -42.8325,
        "escolas": ["EE Álvaro Giesta", "EE Ministro Aloísio Costa"],
    },
    {
        "nome": "Astolfo Dutra",
        "dist_uba": 36,
        "lat": -21.3128,
        "lon": -42.8608,
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
        "lon": -43.1764,
        "escolas": ["EE Professor José Borges de Morais"],
    },
    {
        "nome": "Guarani",
        "dist_uba": 41,
        "lat": -21.3597,
        "lon": -43.0361,
        "escolas": ["EE Professor Alberto Pacheco"],
    },
    {
        "nome": "Coimbra",
        "dist_uba": 44,
        "lat": -20.8567,
        "lon": -42.8033,
        "escolas": ["EE Emílio Jardim"],
    },
    {
        "nome": "Ervália",
        "dist_uba": 46,
        "lat": -20.8375,
        "lon": -42.6594,
        "escolas": [
            "EE Dom Francisco das Chagas",
            "EE Professor David Procópio",
            "EE Monsenhor Rodolfo",
        ],
    },
    {
        "nome": "Silveirânia",
        "dist_uba": 49,
        "lat": -21.0947,
        "lon": -43.2217,
        "escolas": ["EE Santo Antônio"],
    },
    {
        "nome": "Senador Firmino",
        "dist_uba": 50,
        "lat": -20.9144,
        "lon": -43.1206,
        "escolas": ["EE Professor Cícero Torres Galindo"],
    },
    {
        "nome": "Dona Euzébia",
        "dist_uba": 51,
        "lat": -21.3947,
        "lon": -42.7564,
        "escolas": ["EE Domiciano Esteves", "EE Corina Vieira Henriques"],
    },
    {
        "nome": "Paula Cândido",
        "dist_uba": 52,
        "lat": -20.8700,
        "lon": -42.9256,
        "escolas": [
            "EE José Maurílio Valente",
            "EE Professor Samuel João de Deus",
        ],
    },
    {
        "nome": "Presidente Bernardes",
        "dist_uba": 56,
        "lat": -21.4894,
        "lon": -42.9836,
        "escolas": ["EE Antônio Lucas Martins", "EE Padre Vicente Carvalho"],
    },
    {
        "nome": "Tabuleiro",
        "dist_uba": 57,
        "lat": -21.4661,
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
        "lat": -20.8969,
        "lon": -43.0167,
        "escolas": ["EE José Alves de Magalhães", "EE São Luís"],
    },
]

# ---------------------------------------------------------------------------
# DISTÂNCIAS REAIS ENTRE PARES (preencha conforme medição real)
# Chave: tupla em ordem alfabética. Valor: km rodoviário.
# Qualquer par não listado usa a aproximação linear como fallback.
# ---------------------------------------------------------------------------

DISTANCIAS_REAIS: dict[tuple[str, str], int] = {
    ("Astolfo Dutra", "Rio Pomba"):            10,
    ("Astolfo Dutra", "Guarani"):              20,
    ("Guarani", "Rio Pomba"):                  18,
    ("Guarani", "Tabuleiro"):                  14,
    ("Guarani", "Presidente Bernardes"):       24,
    ("Piraúba", "Rio Pomba"):                  12,
    ("Piraúba", "Visconde do Rio Branco"):     20,
    ("Rodeiro", "Tocantins"):                   8,
    ("Rodeiro", "Guidoval"):                   14,
    ("Tocantins", "Visconde do Rio Branco"):   12,
    ("Dona Euzébia", "Presidente Bernardes"):  14,
    ("Dona Euzébia", "Tabuleiro"):             20,
    ("Ervália", "São Geraldo"):                22,
    ("Coimbra", "São Geraldo"):                18,
    ("Divinésia", "Rio Pomba"):                18,
    ("Silveirânia", "Dores do Turvo"):         14,
    ("Senador Firmino", "Dores do Turvo"):     22,
    ("Brás Pires", "Paula Cândido"):           18,
    ("Brás Pires", "Senador Firmino"):         20,
    # Adicione outros pares conforme você for medindo no campo
}

# ---------------------------------------------------------------------------
# OBJETIVOS DE VISITA (alimenta o gerador de justificativa)
# ---------------------------------------------------------------------------

OBJETIVOS_VISITA: list[str] = [
    "Acompanhamento pedagógico e monitoramento de indicadores educacionais",
    "Formação continuada de professores — metodologia socioemocional EAI",
    "Reunião com equipe gestora para alinhamento do Projeto de Vida",
    "Aplicação e devolutiva de instrumentos diagnósticos",
    "Visita de supervisão técnica e orientação administrativa",
    "Acompanhamento da implementação do Programa Aprender Já",
    "Conselho de classe e análise de resultados por turma",
    "Outro (especificar abaixo)",
]

# Índice rápido por nome
MUN_INDEX: dict[str, dict] = {m["nome"]: m for m in MUNICIPIOS}
NOMES: list[str] = [m["nome"] for m in MUNICIPIOS]
