"""
exports/documentos.py
=====================
Gera texto formal de justificativa e exporta PDF institucional.
Dependência: fpdf2  (pip install fpdf2)
"""

from datetime import date
from io import BytesIO

from utils.calculos import fmt_h


# ---------------------------------------------------------------------------
# JUSTIFICATIVA TEXTUAL
# ---------------------------------------------------------------------------

def gerar_justificativa(
    nome_consultor: str,
    data_visita: date | str,
    paradas: list[dict],          # [{"municipio": str, "escolas": [str], "objetivo": str}]
    analise: dict,
    base_retorno: str,
    objetivo_principal: str = "",
    objetivo_livre: str = "",
) -> str:
    """
    Gera parágrafo formal de justificativa para prestação de contas.

    `paradas` é a lista de dicionários com município, escolas selecionadas e objetivo.
    Cada parada pode ter um objetivo diferente; o objetivo_principal cobre o dia inteiro
    quando não há variação por escola.
    """
    data_str = (
        data_visita.strftime("%d/%m/%Y")
        if isinstance(data_visita, date)
        else str(data_visita)
    )

    muns_unicos = list(dict.fromkeys(p["municipio"] for p in paradas))
    todas_esc   = [e for p in paradas for e in p["escolas"]]
    n_esc       = len(todas_esc)

    if len(muns_unicos) == 1:
        mun_str = muns_unicos[0]
    elif len(muns_unicos) == 2:
        mun_str = " e ".join(muns_unicos)
    else:
        mun_str = ", ".join(muns_unicos[:-1]) + " e " + muns_unicos[-1]

    if n_esc <= 4:
        esc_str = "; ".join(todas_esc)
    else:
        esc_str = "; ".join(todas_esc[:3]) + f"; e demais {n_esc - 3} unidade(s) do roteiro"

    obj = objetivo_livre if objetivo_principal == "Outro (especificar abaixo)" and objetivo_livre \
        else objetivo_principal or "acompanhamento pedagógico e suporte técnico às unidades escolares"
    obj = obj[0].lower() + obj[1:] if obj else obj

    logistica = (
        f"Dada a extensão do circuito ({analise['km_total']} km), foi necessária a "
        f"ativação de pernoite em hotel regional no município de {base_retorno}, "
        "visando a otimização logística e o cumprimento integral da agenda pedagógica."
        if analise.get("pernoite")
        else (
            f"O circuito de {analise['km_total']} km foi executado com retorno à base em Ubá "
            "no mesmo dia, dentro dos parâmetros operacionais vigentes."
        )
    )

    h_por_esc = fmt_h(analise.get("horas_por_escola", 2.0))

    return (
        f"JUSTIFICATIVA DE DESLOCAMENTO — SRE UBÁ / INSTITUTO HORTENSE\n\n"
        f"Em {data_str}, o(a) servidor(a) {nome_consultor}, no exercício de suas "
        f"atribuições junto à Superintendência Regional de Ensino de Ubá (SRE Ubá), "
        f"realizou visita técnica de {obj} ao(s) município(s) de {mun_str}, "
        f"percorrendo um total de {analise['km_total']} km em rota otimizada por "
        f"proximidade geográfica.\n\n"
        f"Foram atendidas {n_esc} unidade(s) escolar(es) estadual(is), a saber: "
        f"{esc_str}. Em cada unidade foram realizadas ações com duração estimada de "
        f"{h_por_esc} por escola, totalizando aproximadamente "
        f"{fmt_h(analise['h_total'])} de jornada de trabalho efetivo, incluindo "
        f"deslocamento.\n\n"
        f"{logistica}\n\n"
        f"O itinerário foi organizado de forma a concentrar as visitas por cluster "
        f"geográfico, reduzindo deslocamentos redundantes e assegurando o máximo "
        f"aproveitamento da jornada, em conformidade com as diretrizes de "
        f"racionalização de recursos da SEE/MG."
    )


# ---------------------------------------------------------------------------
# EXPORTAÇÃO PDF
# ---------------------------------------------------------------------------

def gerar_pdf(
    nome_consultor: str,
    data_visita: date | str,
    paradas: list[dict],
    analise: dict,
    segmentos: list[tuple[str, str, int]],
    base_retorno: str,
    justificativa: str,
) -> bytes:
    """
    Gera PDF institucional e retorna como bytes (para st.download_button).
    Layout: cabeçalho, métricas, tabela de segmentos, escolas, justificativa.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("Instale fpdf2: pip install fpdf2")

    data_str = (
        data_visita.strftime("%d/%m/%Y")
        if isinstance(data_visita, date)
        else str(data_visita)
    )

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(30, 58, 95)        # azul navy
            self.rect(0, 0, 210, 22, "F")
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(255, 255, 255)
            self.set_xy(10, 6)
            self.cell(0, 10, "SRE Ubá — Roteirização Logística / Instituto Hortense")
            self.set_text_color(0, 0, 0)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, f"Página {self.page_no()} — Documento gerado automaticamente pelo sistema SRE Ubá",
                      align="C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(14, 28, 14)

    def secao(titulo: str):
        pdf.ln(4)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 7, f"  {titulo.upper()}", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def linha_kv(chave: str, valor: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(52, 6, chave + ":", ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, valor, ln=True)

    # ── Cabeçalho do documento ──────────────────────────────────────
    pdf.ln(4)
    linha_kv("Consultor responsável", nome_consultor or "—")
    linha_kv("Data da visita",        data_str)
    linha_kv("Base de saída",         segmentos[0][0] if segmentos else "—")
    linha_kv("Encerramento em",       base_retorno)

    # ── Métricas ────────────────────────────────────────────────────
    secao("Resumo da jornada")

    metricas = [
        ("Km total percorrido", f"{analise['km_total']} km"),
        ("Tempo de estrada",    fmt_h(analise["h_estrada"])),
        ("Tempo de agenda",     fmt_h(analise["h_agenda"])),
        ("Jornada total",       fmt_h(analise["h_total"])),
        ("Escolas atendidas",   str(analise["n_escolas"])),
        ("Uso da jornada",      f"{analise['pct_jornada']}%"),
        ("Decisão logística",   "Pernoite em hotel regional" if analise["pernoite"] else "Bate-volta"),
    ]
    for chave, valor in metricas:
        linha_kv(chave, valor)

    if analise.get("saturado"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 6, "  ⚠ ATENÇÃO: Jornada acima do limite operacional de 8h.", ln=True)
        pdf.set_text_color(0, 0, 0)

    # ── Segmentos ───────────────────────────────────────────────────
    secao("Itinerário — segmentos")

    col_w = [10, 65, 65, 25, 25]
    headers = ["#", "Origem", "Destino", "Km", "Tempo"]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(226, 232, 240)
    for w, h in zip(col_w, headers):
        pdf.cell(w, 6, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for i, (orig, dest, km) in enumerate(segmentos):
        label = "R" if i == len(segmentos) - 1 else str(i + 1)
        fill = i % 2 == 0
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0],  6, label, border=1, fill=fill, align="C")
        pdf.cell(col_w[1], 6, orig[:35],  border=1, fill=fill)
        pdf.cell(col_w[2], 6, dest[:35],  border=1, fill=fill)
        pdf.cell(col_w[3], 6, f"{km} km", border=1, fill=fill, align="C")
        from utils.calculos import horas_estrada, fmt_h as fh
        pdf.cell(col_w[4], 6, fh(horas_estrada(km)), border=1, fill=fill, align="C")
        pdf.ln()

    # ── Escolas por município ────────────────────────────────────────
    secao("Escolas atendidas por município")

    for parada in paradas:
        pdf.set_font("Helvetica", "B", 9)
        mun_label = f"{parada['municipio']}  ({len(parada['escolas'])} escola(s))"
        if parada.get("objetivo"):
            mun_label += f"  —  {parada['objetivo'][:60]}"
        pdf.cell(0, 6, mun_label, ln=True)
        pdf.set_font("Helvetica", "", 8)
        for escola in parada["escolas"]:
            pdf.cell(6, 5, "")
            pdf.cell(0, 5, f"• {escola}", ln=True)
        pdf.ln(1)

    # ── Justificativa ────────────────────────────────────────────────
    secao("Justificativa para prestação de contas")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 5.5, justificativa)

    buf = BytesIO()
    buf.write(pdf.output())
    return buf.getvalue()
