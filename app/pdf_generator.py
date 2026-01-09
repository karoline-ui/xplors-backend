from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from datetime import datetime
import os

COR_ROXO = colors.HexColor('#8b5cf6')
COR_ROXO_ESCURO = colors.HexColor('#1e1b4b')
COR_CINZA_TEXTO = colors.HexColor('#111827')
COR_VERDE = colors.HexColor('#10b981')
COR_AMARELO = colors.HexColor('#f59e0b')
COR_VERMELHO = colors.HexColor('#ef4444')


def _fmt_val(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


class PDFXplors:
    def __init__(self, arquivo_saida: str, tipo_analise: str, dados_analise: dict, dados_excel: dict | None = None):
        self.arquivo_saida = arquivo_saida
        self.tipo_analise = (tipo_analise or "merchandising").lower()
        self.dados_analise = dados_analise or {}
        self.dados_excel = dados_excel or {}

        self.doc = SimpleDocTemplate(
            arquivo_saida,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.2 * cm,
            bottomMargin=2 * cm
        )

        self.story = []
        self.styles = getSampleStyleSheet()
        self._criar_estilos()

    def _criar_estilos(self):
        self.styles.add(ParagraphStyle(
            name='TituloXplors',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=COR_ROXO,
            spaceAfter=14,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='SecaoXplors',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=COR_ROXO_ESCURO,
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10.5,
            textColor=COR_CINZA_TEXTO,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='TextoPequeno',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor("#374151"),
            alignment=TA_LEFT,
            spaceAfter=6,
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name='KPI',
            parent=self.styles['Normal'],
            fontSize=10.5,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

    def _limpar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        texto = texto.replace('**', '').replace('##', '').replace('#', '')
        texto = texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return texto.strip()

    def _kpi_table(self, kpis: list[dict]):
        if not kpis:
            return

        cells = []
        for k in kpis[:6]:
            label = _fmt_val(k.get("label"))
            value = _fmt_val(k.get("value"))
            tone = (k.get("tone") or "purple").lower()

            bg = COR_ROXO
            if tone == "good":
                bg = COR_VERDE
            elif tone == "warn":
                bg = COR_AMARELO
            elif tone == "bad":
                bg = COR_VERMELHO

            cell = Table(
                [[Paragraph(label, self.styles['TextoPequeno'])],
                 [Paragraph(value, ParagraphStyle(
                     name="KPIValue",
                     parent=self.styles["KPI"],
                     backColor=bg
                 ))]],
                colWidths=[6.0 * cm]
            )
            cell.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            cells.append(cell)

        grid = []
        for i in range(0, len(cells), 3):
            row = cells[i:i+3]
            if len(row) < 3:
                row += [""] * (3 - len(row))
            grid.append(row)

        t = Table(grid, colWidths=[6.2*cm, 6.2*cm, 6.2*cm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 0.35 * cm))

    def _explicacao_graficos(self) -> str:
        t = self.tipo_analise

        if t == "preco":
            return """
<b>Como ler os gráficos:</b><br/>
• A distribuição mostra onde está a maior parte dos preços (concentração).<br/>
• Valores isolados podem indicar outliers (preço muito fora do padrão) ou inconsistência de cadastro.<br/>
• Use as recomendações para padronizar e reduzir ruído no ponto de venda.
"""
        if t == "concorrencia":
            return """
<b>Como ler os gráficos:</b><br/>
• O “Top 10” mostra quais ações/marcas/itens aparecem mais (frequência).<br/>
• Diferenças grandes indicam desequilíbrio de presença: oportunidade de contra-ataque.
"""
        # merchandising (planilha) OU imagem
        return """
<b>Como ler os gráficos:</b><br/>
• Eles resumem rapidamente onde a execução está forte e onde está falhando.<br/>
• “Conformidade por item” evidencia os pontos de maior perda de venda por execução.<br/>
• Em imagem, o radar (0–10) resume a qualidade por pilar e o gráfico de impacto mostra a faixa de ganho estimado.
"""

    def _add_chart_images(self, chart_paths: list[str]):
        valid = [p for p in (chart_paths or []) if p and os.path.exists(p)]
        if not valid:
            return

        self.story.append(Paragraph("Gráficos do Diagnóstico", self.styles["SecaoXplors"]))
        self.story.append(Paragraph(self._explicacao_graficos(), self.styles["TextoNormal"]))
        self.story.append(Spacer(1, 0.2 * cm))

        for p in valid[:10]:
            try:
                img = RLImage(p)
                img.drawHeight = 8.0 * cm
                img.drawWidth = 16.5 * cm
                self.story.append(img)
                self.story.append(Spacer(1, 0.35 * cm))
            except Exception:
                continue

    def _cabecalho(self):
        self.story.append(Paragraph("Relatório de Análise", self.styles["TituloXplors"]))
        self.story.append(Spacer(1, 0.15 * cm))

        data_formatada = datetime.now().strftime('%d/%m/%Y às %H:%M')

        total_registros = (
            self.dados_analise.get("total_linhas")
            or self.dados_excel.get("total_linhas")
            or self.dados_excel.get("total_respostas")
            or 0
        )

        info = f"""
<b>Tipo:</b> {self.tipo_analise.capitalize()}<br/>
<b>Data:</b> {data_formatada}<br/>
<b>Total de registros:</b> {total_registros}
"""
        self.story.append(Paragraph(info, self.styles["TextoNormal"]))
        self.story.append(Spacer(1, 0.25 * cm))

        kpis = self.dados_excel.get("kpis") or self.dados_analise.get("kpis") or []
        self._kpi_table(kpis)

    def _conteudo_texto(self):
        texto = self.dados_analise.get("texto") or self.dados_analise.get("analise") or ""
        texto = texto.strip() if isinstance(texto, str) else ""

        self.story.append(Paragraph("Insights e Recomendações", self.styles["SecaoXplors"]))

        if not texto:
            self.story.append(Paragraph("Nenhuma análise disponível.", self.styles["TextoNormal"]))
            return

        for bloco in texto.split("\n\n"):
            b = self._limpar_texto(bloco)
            if not b:
                continue

            if len(b) <= 90 and (b.endswith(":") or b.isupper()):
                self.story.append(Paragraph(b.replace(":", ""), self.styles["SecaoXplors"]))
            else:
                self.story.append(Paragraph(b, self.styles["TextoNormal"]))

    def _rodape(self):
        self.story.append(Spacer(1, 0.35 * cm))
        rodape = Paragraph(
            f'<b>Relatório gerado por Xplors</b><br/>'
            f'Data: {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
            self.styles['TextoPequeno']
        )
        self.story.append(rodape)

    def gerar(self):
        self._cabecalho()

        charts = self.dados_excel.get("charts") or self.dados_analise.get("charts") or []
        self._add_chart_images(charts)

        self._conteudo_texto()
        self._rodape()

        self.doc.build(self.story)


def gerar_pdf_xplors(arquivo_saida, tipo_analise, dados_analise, dados_excel=None):
    pdf = PDFXplors(arquivo_saida, tipo_analise, dados_analise, dados_excel=dados_excel)
    pdf.gerar()
    return arquivo_saida
