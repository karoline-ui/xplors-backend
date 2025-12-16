"""
PDF Generator SUPER SIMPLES
SEM gráficos, SEM complicações - Só funciona!
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os
from datetime import datetime

# Cores Xplors
COR_ROXO = colors.HexColor('#8b5cf6')
COR_CIANO = colors.HexColor('#14b8a6')
COR_ROXO_ESCURO = colors.HexColor('#1e1b4b')

class PDFSimples:
    def __init__(self, arquivo_saida, tipo_analise, dados_analise):
        self.arquivo_saida = arquivo_saida
        self.tipo_analise = tipo_analise
        self.dados_analise = dados_analise
        
        self.doc = SimpleDocTemplate(
            arquivo_saida,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2*cm
        )
        
        self.story = []
        self.styles = getSampleStyleSheet()
        self._criar_estilos()
    
    def _criar_estilos(self):
        """Estilos simples"""
        
        self.styles.add(ParagraphStyle(
            name='TituloXplors',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=COR_ROXO,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtituloXplors',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=COR_ROXO_ESCURO,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14
        ))
    
    def _limpar_texto(self, texto):
        """Limpar texto de forma segura"""
        if not texto:
            return ""
        
        # Remover markdown
        texto = texto.replace('**', '')
        texto = texto.replace('##', '')
        texto = texto.replace('#', '')
        
        # Escapar XML
        texto = texto.replace('&', '&amp;')
        texto = texto.replace('<', '&lt;')
        texto = texto.replace('>', '&gt;')
        
        return texto.strip()
    
    def _adicionar_cabecalho(self):
        """Cabeçalho simples"""
        
        # Título
        self.story.append(Paragraph('Relatório de Análise', self.styles['TituloXplors']))
        self.story.append(Spacer(1, 0.5*cm))
        
        # Info básica
        data_formatada = datetime.now().strftime('%d/%m/%Y às %H:%M')
        total_linhas = self.dados_analise.get('total_linhas', 0)
        
        info = f'<b>Data:</b> {data_formatada}<br/><b>Total de registros:</b> {total_linhas}'
        
        self.story.append(Paragraph(info, self.styles['TextoNormal']))
        self.story.append(Spacer(1, 1*cm))
    
    def _adicionar_conteudo(self):
        """Adicionar conteúdo da análise"""
        
        texto = self.dados_analise.get('texto', '')
        
        if not texto:
            self.story.append(Paragraph('Nenhuma análise disponível.', self.styles['TextoNormal']))
            return
        
        # Dividir em parágrafos
        paragrafos = texto.split('\n\n')
        
        for paragrafo in paragrafos:
            if paragrafo.strip():
                # Limpar
                paragrafo_limpo = self._limpar_texto(paragrafo)
                
                if len(paragrafo_limpo) > 0:
                    # Se for curto e tudo maiúsculo, é subtítulo
                    if len(paragrafo_limpo) < 100 and paragrafo.strip().isupper():
                        self.story.append(Paragraph(paragrafo_limpo, self.styles['SubtituloXplors']))
                    else:
                        self.story.append(Paragraph(paragrafo_limpo, self.styles['TextoNormal']))
                    
                    self.story.append(Spacer(1, 0.2*cm))
    
    def gerar(self):
        """Gerar PDF"""
        
        try:
            print(f"📄 Gerando PDF em: {self.arquivo_saida}")
            
            # Cabeçalho
            self._adicionar_cabecalho()
            
            # Conteúdo
            self._adicionar_conteudo()
            
            # Rodapé
            self.story.append(Spacer(1, 1*cm))
            rodape = Paragraph(
                f'<b>Relatório gerado por Xplors</b><br/>'
                f'Data: {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
                self.styles['TextoNormal']
            )
            self.story.append(rodape)
            
            # Gerar
            self.doc.build(self.story)
            
            print(f"✅ PDF gerado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            raise


def gerar_pdf_xplors(arquivo_saida, tipo_analise, dados_analise, dados_excel=None):
    """
    Função principal - VERSÃO SIMPLES
    """
    pdf = PDFSimples(arquivo_saida, tipo_analise, dados_analise)
    pdf.gerar()
    return arquivo_saida