"""
PDF Generator com Gráficos
Gera PDFs profissionais com matplotlib charts
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import matplotlib
matplotlib.use('Agg')  # Backend sem display
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from datetime import datetime
import os

# Cores Xplors
COR_ROXO = colors.HexColor('#8b5cf6')
COR_CIANO = colors.HexColor('#14b8a6')
COR_ROXO_ESCURO = colors.HexColor('#1e1b4b')


class PDFComGraficos:
    def __init__(self, arquivo_saida, dados_analise, dados_excel=None):
        self.arquivo_saida = arquivo_saida
        self.dados_analise = dados_analise
        self.dados_excel = dados_excel
        
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
        """Estilos personalizados"""
        
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
            fontSize=16,
            textColor=COR_ROXO_ESCURO,
            spaceAfter=12,
            spaceBefore=16,
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
    
    def _gerar_grafico_linhas(self, df: pd.DataFrame, titulo: str) -> BytesIO:
        """Gera gráfico de linhas"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Pegar colunas numéricas
        colunas_numericas = df.select_dtypes(include=['number']).columns[:3]
        
        for col in colunas_numericas:
            ax.plot(df.index[:50], df[col][:50], marker='o', label=col, linewidth=2)
        
        ax.set_title(titulo, fontsize=14, fontweight='bold', color='#1e1b4b')
        ax.set_xlabel('Índice', fontsize=10)
        ax.set_ylabel('Valores', fontsize=10)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Salvar em BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        
        return buffer
    
    def _gerar_grafico_barras(self, df: pd.DataFrame, titulo: str) -> BytesIO:
        """Gera gráfico de barras"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Pegar primeira coluna numérica
        col_numerica = df.select_dtypes(include=['number']).columns[0]
        
        # Top 10 valores
        dados_top = df.nlargest(10, col_numerica)
        
        cores = ['#8b5cf6', '#14b8a6', '#6366f1', '#0ea5e9', '#8b5cf6',
                 '#14b8a6', '#6366f1', '#0ea5e9', '#8b5cf6', '#14b8a6']
        
        ax.barh(range(len(dados_top)), dados_top[col_numerica], color=cores[:len(dados_top)])
        ax.set_yticks(range(len(dados_top)))
        ax.set_yticklabels(dados_top.index)
        ax.set_xlabel(col_numerica, fontsize=10)
        ax.set_title(titulo, fontsize=14, fontweight='bold', color='#1e1b4b')
        ax.grid(True, alpha=0.3, axis='x')
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        
        return buffer
    
    def _gerar_grafico_pizza(self, df: pd.DataFrame, titulo: str) -> BytesIO:
        """Gera gráfico de pizza"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Contar valores da primeira coluna
        col = df.columns[0]
        valores = df[col].value_counts().head(6)
        
        cores = ['#8b5cf6', '#14b8a6', '#6366f1', '#0ea5e9', '#f59e0b', '#10b981']
        
        ax.pie(valores, labels=valores.index, autopct='%1.1f%%',
               colors=cores[:len(valores)], startangle=90)
        ax.set_title(titulo, fontsize=14, fontweight='bold', color='#1e1b4b')
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        
        return buffer
    
    def _adicionar_cabecalho(self):
        """Cabeçalho do PDF"""
        
        # Logo/Título
        self.story.append(Paragraph('Relatório Xplors', self.styles['TituloXplors']))
        self.story.append(Spacer(1, 0.3*cm))
        
        # Informações
        data_formatada = datetime.now().strftime('%d/%m/%Y às %H:%M')
        total_linhas = self.dados_analise.get('total_linhas', 0)
        
        info = f'<b>Data:</b> {data_formatada}<br/>'
        info += f'<b>Total de registros:</b> {total_linhas:,}<br/>'
        
        if self.dados_excel is not None:
            info += f'<b>Colunas:</b> {len(self.dados_excel.columns)}'
        
        self.story.append(Paragraph(info, self.styles['TextoNormal']))
        self.story.append(Spacer(1, 1*cm))
    
    def _adicionar_graficos(self):
        """Adiciona gráficos baseados nos dados"""
        
        if self.dados_excel is None or len(self.dados_excel) == 0:
            return
        
        df = self.dados_excel
        
        try:
            # Título da seção
            self.story.append(Paragraph('📊 Visualizações de Dados', self.styles['SubtituloXplors']))
            self.story.append(Spacer(1, 0.5*cm))
            
            # GRÁFICO 1: Linhas (se houver colunas numéricas)
            colunas_numericas = df.select_dtypes(include=['number']).columns
            if len(colunas_numericas) > 0:
                buffer_linhas = self._gerar_grafico_linhas(df, 'Tendência dos Dados')
                img_linhas = RLImage(buffer_linhas, width=15*cm, height=7.5*cm)
                self.story.append(img_linhas)
                self.story.append(Spacer(1, 0.5*cm))
            
            # GRÁFICO 2: Barras (top 10)
            if len(colunas_numericas) > 0:
                buffer_barras = self._gerar_grafico_barras(df, 'Top 10 Valores')
                img_barras = RLImage(buffer_barras, width=15*cm, height=7.5*cm)
                self.story.append(img_barras)
                self.story.append(Spacer(1, 0.5*cm))
            
            # GRÁFICO 3: Pizza (distribuição)
            if len(df.columns) > 0:
                buffer_pizza = self._gerar_grafico_pizza(df, 'Distribuição de Categorias')
                img_pizza = RLImage(buffer_pizza, width=12*cm, height=12*cm)
                self.story.append(img_pizza)
                self.story.append(Spacer(1, 1*cm))
            
        except Exception as e:
            print(f"⚠️ Erro ao gerar gráficos: {e}")
            # Continua sem gráficos se houver erro
    
    def _adicionar_analise_texto(self):
        """Adiciona análise em texto"""
        
        self.story.append(PageBreak())
        self.story.append(Paragraph('📝 Análise Detalhada', self.styles['SubtituloXplors']))
        self.story.append(Spacer(1, 0.5*cm))
        
        texto = self.dados_analise.get('texto', '')
        
        if not texto:
            self.story.append(Paragraph('Nenhuma análise disponível.', self.styles['TextoNormal']))
            return
        
        # Dividir em parágrafos
        paragrafos = texto.split('\n\n')
        
        for paragrafo in paragrafos:
            if paragrafo.strip():
                # Limpar
                paragrafo_limpo = paragrafo.replace('**', '').replace('##', '').replace('#', '')
                paragrafo_limpo = paragrafo_limpo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Adicionar
                if len(paragrafo_limpo) > 0:
                    if len(paragrafo_limpo) < 100 and paragrafo.strip().isupper():
                        # É subtítulo
                        self.story.append(Paragraph(paragrafo_limpo, self.styles['SubtituloXplors']))
                    else:
                        self.story.append(Paragraph(paragrafo_limpo, self.styles['TextoNormal']))
                    
                    self.story.append(Spacer(1, 0.3*cm))
    
    def _adicionar_rodape(self):
        """Rodapé"""
        self.story.append(Spacer(1, 1*cm))
        rodape = Paragraph(
            f'<b>Relatório gerado por Xplors</b><br/>'
            f'Data: {datetime.now().strftime("%d/%m/%Y às %H:%M")}<br/>'
            f'© {datetime.now().year} Xplors - Análise Inteligente',
            self.styles['TextoNormal']
        )
        self.story.append(rodape)
    
    def gerar(self):
        """Gera o PDF completo"""
        
        try:
            print(f"📄 Gerando PDF profissional com gráficos...")
            
            # Cabeçalho
            self._adicionar_cabecalho()
            
            # Gráficos
            self._adicionar_graficos()
            
            # Análise textual
            self._adicionar_analise_texto()
            
            # Rodapé
            self._adicionar_rodape()
            
            # Construir PDF
            self.doc.build(self.story)
            
            print(f"✅ PDF gerado com sucesso: {self.arquivo_saida}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            raise


def gerar_pdf_xplors(arquivo_saida, tipo_analise, dados_analise, dados_excel=None):
    """
    Função principal - Gera PDF com gráficos
    """
    pdf = PDFComGraficos(arquivo_saida, dados_analise, dados_excel)
    pdf.gerar()
    return arquivo_saida
