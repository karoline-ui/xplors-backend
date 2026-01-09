"""
Analisador de Imagens - ESPECIALIZADO EM MERCHANDISING
Analisa stands, displays, vitrines e posicionamento de produtos
"""

from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image

class ImageAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def preparar_imagem(self, arquivo_imagem) -> tuple:
        """Prepara imagem para análise (retorna base64 e dimensões)"""
        try:
            # Abrir imagem
            img = Image.open(arquivo_imagem)
            
            # Redimensionar se muito grande (max 2048x2048)
            max_size = 2048
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Converter para base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return img_base64, img.width, img.height
            
        except Exception as e:
            print(f"❌ Erro ao preparar imagem: {e}")
            raise
    
    def analisar_merchandising(self, imagem_base64: str, contexto: str = "") -> dict:
        """
        Análise PROFISSIONAL de Merchandising Visual
        Para stands, displays, vitrines, exposições de produtos
        """
        try:
            prompt = f"""
Você é um especialista em VISUAL MERCHANDISING e TRADE MARKETING.

Analise esta foto de stand/display/vitrine de produtos e forneça uma análise PROFISSIONAL e DETALHADA.

{f"CONTEXTO: {contexto}" if contexto else ""}

Forneça uma análise completa seguindo esta estrutura:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 1. ANÁLISE GERAL DO DISPLAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Primeira Impressão:**
- Avaliação visual geral (0-10)
- Impacto visual inicial
- Atratividade para clientes

**Elementos Identificados:**
- Produtos visíveis
- Materiais de PDV (cartazes, wobblers, displays)
- Iluminação
- Cores predominantes
- Organização geral

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👁️ 2. VISIBILIDADE E DESTAQUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pontos Fortes:**
- O que está funcionando bem
- Produtos em destaque
- Elementos que chamam atenção

**Pontos Fracos:**
- Produtos "escondidos" ou mal posicionados
- Áreas com pouca visibilidade
- Elementos que prejudicam a visualização

**Nível de Visibilidade:** (Baixo / Médio / Alto)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 3. ORGANIZAÇÃO E LAYOUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Avaliação da Organização:**
- Produtos bem alinhados? (Sim/Não)
- Categorização clara? (Sim/Não)
- Aproveitamento do espaço: (Ruim / Médio / Bom)

**Problemas Identificados:**
- Desorganização
- Espaços vazios desperdiçados
- Excesso de informação
- Poluição visual

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 4. SUGESTÕES DE MELHORIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**PRIORIDADE ALTA (Fazer AGORA):**
1. [Ação específica e prática]
2. [Ação específica e prática]
3. [Ação específica e prática]

**PRIORIDADE MÉDIA:**
1. [Ação específica]
2. [Ação específica]

**PRIORIDADE BAIXA:**
1. [Ação específica]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 5. RECOMENDAÇÕES ESTRATÉGICAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Posicionamento de Produtos:**
- Como reorganizar para maximizar vendas
- Produtos que devem estar na altura dos olhos
- Agrupamento por categoria/cor/tamanho

**Iluminação:**
- Onde adicionar/melhorar iluminação
- Produtos que precisam de destaque luminoso

**Materiais de PDV:**
- Cartazes/displays necessários
- Wobblers, stoppers, precificadores
- Onde posicionar cada material

**Cores e Visual:**
- Combinação de cores
- Contraste e harmonia
- Sugestões de alteração

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 6. IMPACTO ESPERADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Se as melhorias forem implementadas:**
- Aumento estimado de visibilidade: X%
- Potencial de atração de clientes: (Baixo/Médio/Alto)
- Provável impacto nas vendas: (Positivo/Muito Positivo)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 7. CHECKLIST DE AÇÃO IMEDIATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ [Ação 1]
□ [Ação 2]
□ [Ação 3]
□ [Ação 4]
□ [Ação 5]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ NOTA FINAL: X/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Justificativa da nota:**
[Explicação breve]

**Próximo passo prioritário:**
[Ação mais importante a fazer]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANTE:
- Seja ESPECÍFICO e PRÁTICO
- Foque em ações EXECUTÁVEIS
- Pense como se fosse treinar um funcionário
- Considere custos baixos e fácil implementação
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em Visual Merchandising, Trade Marketing e execução de PDV (Ponto de Venda). Sua missão é analisar displays e fornecer sugestões práticas e acionáveis para melhorar vendas."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{imagem_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            analise = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens
            
            return {
                'analise': analise,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tipo': 'merchandising'
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar merchandising: {e}")
            raise
    
    def analisar_grafico(self, imagem_base64: str) -> dict:
        """Analisa gráfico em imagem"""
        try:
            prompt = """
Analise este gráfico/chart em detalhes.

Extraia e forneça:

1. TIPO DE GRÁFICO
   - Qual tipo: linha, barra, pizza, dispersão, etc

2. DADOS PRINCIPAIS
   - Valores numéricos visíveis
   - Categorias/labels
   - Título do gráfico

3. INSIGHTS
   - Tendências identificadas
   - Padrões importantes
   - Comparações relevantes

4. CONCLUSÕES
   - Principal mensagem do gráfico
   - Recomendações baseadas nos dados

Seja preciso com os números e detalhado nas análises.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{imagem_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            analise = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens
            
            return {
                'analise': analise,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tipo': 'grafico'
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar gráfico: {e}")
            raise
    
    def analisar_tabela(self, imagem_base64: str) -> dict:
        """Analisa tabela em imagem"""
        try:
            prompt = """
Extraia TODOS os dados desta tabela.

Forneça:

1. ESTRUTURA
   - Cabeçalhos das colunas
   - Número de linhas e colunas

2. DADOS COMPLETOS
   - Todos os valores da tabela
   - Formato CSV se possível

3. ANÁLISE
   - Resumo estatístico (se numérico)
   - Padrões identificados
   - Valores destacados (máximo, mínimo, médias)

4. INSIGHTS
   - Principais descobertas
   - Comparações relevantes

Seja preciso e completo na extração dos dados.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{imagem_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            analise = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens
            
            return {
                'analise': analise,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tipo': 'tabela'
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar tabela: {e}")
            raise
    
    def analisar_automatico(self, imagem_base64: str, tipo_analise: str = 'merchandising', contexto: str = "") -> dict:
        """
        Analisa imagem automaticamente
        tipo_analise: 'merchandising', 'grafico', 'tabela'
        """
        
        # PADRÃO: Merchandising (análise de stands/displays)
        if tipo_analise == 'merchandising':
            return self.analisar_merchandising(imagem_base64, contexto)
        elif tipo_analise == 'grafico':
            return self.analisar_grafico(imagem_base64)
        elif tipo_analise == 'tabela':
            return self.analisar_tabela(imagem_base64)
        else:
            # Default: merchandising
            return self.analisar_merchandising(imagem_base64, contexto)
