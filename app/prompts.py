"""
========================================
PROMPTS DE IA - 3 TIPOS DE ANÁLISE
========================================

Este módulo contém:
1. 3 prompts especializados (Concorrência, Merchandising, Preço)
2. Função para análise com OpenAI diretamente (SEM LangChain)
3. Configuração do modelo de IA

Cada prompt é otimizado para gerar insights específicos
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

# Carregar variáveis de ambiente (.env)
load_dotenv()


# ========================================
# CONFIGURAÇÃO DA IA
# ========================================

def criar_cliente_openai():
    """
    Cria e configura o cliente OpenAI
    VERSÃO CORRIGIDA para Python 3.13+
    
    Returns:
        Cliente OpenAI configurado
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY não encontrada! Configure o arquivo .env")
    
    print(f"🔑 API Key encontrada: {api_key[:20]}...")
    
    # CORREÇÃO: Criar cliente SEM parâmetro proxies
    # Compatível com Python 3.13+ e openai>=1.0.0
    try:
        cliente = OpenAI(
            api_key=api_key,
            timeout=120.0,  # 2 minutos de timeout
            max_retries=3   # 3 tentativas em caso de erro
        )
        print("✅ Cliente OpenAI criado com sucesso!")
        return cliente
    except Exception as e:
        print(f"❌ Erro ao criar cliente OpenAI: {str(e)}")
        raise


# ========================================
# PROMPT 1: AÇÕES DE CONCORRÊNCIA (~65 respostas)
# ========================================

PROMPT_CONCORRENCIA = """
Você é um Analista Sênior de Inteligência Competitiva e Trade Marketing.

Analise os dados de AÇÕES DE CONCORRÊNCIA abaixo e gere um relatório executivo completo.

DADOS RECEBIDOS:
{dados}

TOTAL DE RESPOSTAS: {total}

ESTRUTURA DO RELATÓRIO:

1. RESUMO EXECUTIVO
- Visão geral das ações da concorrência
- Principais ameaças identificadas
- Nível de agressividade competitiva (Alto/Médio/Baixo)

2. ANÁLISE DAS AÇÕES
- Listar as 5 principais ações da concorrência por frequência
- Para cada ação: impacto no mercado, gravidade, resposta recomendada
- Identificar padrões: promoções, lançamentos, expansão territorial

3. MATRIZ DE RISCO COMPETITIVO
- Ações que exigem resposta imediata (0-7 dias)
- Ações para monitorar (curto prazo)
- Oportunidades identificadas nas ações dos concorrentes

4. RECOMENDAÇÕES ESTRATÉGICAS
- 3 ações de contra-ataque prioritárias
- Como neutralizar ameaças principais
- Oportunidades para ganhar mercado

5. KPIs PARA MONITORAR
- Métricas específicas para acompanhar concorrentes
- Frequência de monitoramento recomendada

REGRAS:
- Seja ESPECÍFICO e QUANTITATIVO
- Use exemplos reais dos dados
- Classifique riscos como Alto/Médio/Baixo
- Linguagem executiva e direta
- Mínimo 1500 palavras
"""


# ========================================
# PROMPT 2: EXECUÇÃO DE MERCHANDISING (~1357 respostas)
# ========================================

PROMPT_MERCHANDISING = """
Você é um Analista Sênior de Trade Marketing e Visual Merchandising.

Analise os dados de EXECUÇÃO DE MERCHANDISING abaixo e gere um relatório executivo completo.

DADOS RECEBIDOS:
{dados}

TOTAL DE RESPOSTAS: {total}

ESTRUTURA DO RELATÓRIO:

1. RESUMO EXECUTIVO
- Nível geral de execução (Excelente/Bom/Regular/Crítico)
- Taxa de conformidade com padrões
- Principais problemas de execução

2. ANÁLISE DE CONFORMIDADE
- % de lojas com execução correta
- Top 5 itens com melhor execução
- Top 5 itens com pior execução
- Análise por região/ponto de venda (se houver dados)

3. PROBLEMAS CRÍTICOS IDENTIFICADOS
- Rupturas de estoque detectadas
- Problemas de visibilidade dos produtos
- Falhas de precificação
- Questões de organização e limpeza
- Cada problema com: frequência, impacto em vendas, custo estimado

4. IMPACTO EM VENDAS
- Estimativa de perda de vendas por má execução
- Oportunidades de ganho com melhorias
- ROI esperado das correções

5. PLANO DE AÇÃO CORRETIVO
- Ações urgentes (0-7 dias) com responsável
- Melhorias curto prazo (1-4 semanas)
- Investimentos necessários
- Treinamentos recomendados

6. KPIs DE MERCHANDISING
- Métricas para acompanhamento semanal
- Metas recomendadas para cada KPI

REGRAS:
- Seja MUITO ESPECÍFICO com números e %
- Cite exemplos reais dos dados
- Calcule impactos financeiros quando possível
- Classifique tudo como Crítico/Alto/Médio/Baixo
- Linguagem executiva e acionável
- Mínimo 2000 palavras
"""


# ========================================
# PROMPT 3: PESQUISA DE PREÇO (~2166 respostas)
# ========================================

PROMPT_PRECO = """
Você é um Analista Sênior de Pricing e Competitividade de Mercado.

Analise os dados de PESQUISA DE PREÇOS abaixo e gere um relatório executivo completo.

DADOS RECEBIDOS:
{dados}

TOTAL DE RESPOSTAS: {total}

ESTRUTURA DO RELATÓRIO:

1. RESUMO EXECUTIVO
- Posicionamento de preço vs concorrência (Acima/Igual/Abaixo)
- Índice de competitividade de preços
- Principais gaps identificados

2. ANÁLISE COMPARATIVA DE PREÇOS
- Produtos mais caros vs concorrência (Top 10)
- Produtos mais baratos vs concorrência (Top 10)
- Diferença % média por categoria
- Análise de spread de preços (mínimo, máximo, médio)

3. OPORTUNIDADES DE PRECIFICAÇÃO
- Produtos onde podemos aumentar preço sem perder competitividade
- Produtos onde devemos reduzir preço urgentemente
- Estratégias de preço psicológico identificadas

4. ANÁLISE DE ELASTICIDADE
- Produtos sensíveis a preço (alta elasticidade)
- Produtos com baixa sensibilidade a preço
- Recomendações de ajuste por produto

5. ESTRATÉGIA DE PRICING
- Ajustes recomendados por produto/categoria
- Impacto estimado em margem e volume
- Análise de break-even dos ajustes
- Calendário de implementação (urgente/curto/médio prazo)

6. MONITORAMENTO COMPETITIVO
- Produtos para monitorar semanalmente
- Alertas de preço a configurar
- KPIs de competitividade

7. SIMULAÇÕES FINANCEIRAS
- Cenário 1: Manter preços atuais
- Cenário 2: Igualar principais concorrentes
- Cenário 3: Estratégia híbrida (ajustes seletivos)
- Recomendação final com justificativa

REGRAS:
- Use MUITOS NÚMEROS, % e comparações
- Calcule impactos financeiros reais
- Cite produtos e preços específicos dos dados
- Seja ACIONÁVEL - cada recomendação deve ter: produto, ajuste, impacto
- Classifique urgência como Imediato/Curto/Médio prazo
- Linguagem executiva e estratégica
- Mínimo 2500 palavras
"""


# ========================================
# FUNÇÃO PRINCIPAL DE ANÁLISE
# ========================================

def obter_prompt_por_tipo(tipo: str) -> str:
    """
    Retorna o prompt correto baseado no tipo de análise
    
    Args:
        tipo: 'concorrencia', 'merchandising' ou 'preco'
        
    Returns:
        Template do prompt
    """
    
    prompts = {
        'concorrencia': PROMPT_CONCORRENCIA,
        'merchandising': PROMPT_MERCHANDISING,
        'preco': PROMPT_PRECO
    }
    
    return prompts.get(tipo, PROMPT_MERCHANDISING)


def analisar_com_ia(df: pd.DataFrame, prompt_template: str, tipo: str) -> str:
    """
    Analisa os dados usando IA com o prompt específico
    VERSÃO CORRIGIDA - Compatível com Python 3.13+
    
    Fluxo:
    1. Prepara os dados em formato legível
    2. Cria o prompt com os dados
    3. Chama o modelo OpenAI diretamente
    4. Retorna a análise completa
    
    Args:
        df: DataFrame com os dados
        prompt_template: Template do prompt a usar
        tipo: Tipo de análise
        
    Returns:
        String com análise completa da IA
    """
    
    try:
        print(f"🤖 Iniciando análise de {tipo}...")
        
        # ========================================
        # PREPARAR DADOS PARA IA
        # ========================================
        
        # Converter DataFrame para formato legível
        # Pega primeiras 30 linhas
        amostra = df.head(30) if len(df) > 30 else df
        
        dados_texto = f"""
INFORMAÇÕES GERAIS:
- Total de registros: {len(df)}
- Colunas: {', '.join(df.columns.tolist())}

AMOSTRA DOS DADOS (primeiras linhas):
{amostra.to_string(index=False)}

ESTATÍSTICAS:
{df.describe(include='all').to_string()}
"""
        
        print(f"📊 Dados preparados: {len(dados_texto)} caracteres")
        
        
        # ========================================
        # CRIAR CLIENTE E EXECUTAR ANÁLISE
        # ========================================
        
        # Criar cliente OpenAI (COM CORREÇÃO!)
        cliente = criar_cliente_openai()
        
        # Substituir placeholders no prompt
        prompt_final = prompt_template.replace("{dados}", dados_texto)
        prompt_final = prompt_final.replace("{total}", str(len(df)))
        
        print("🔄 Chamando OpenAI GPT-4o...")
        
        # Executar análise com OpenAI diretamente
        resposta = cliente.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {
                    "role": "system",
                    "content": "Você é um analista especializado em trade marketing e inteligência competitiva. Gere relatórios executivos completos e acionáveis."
                },
                {
                    "role": "user",
                    "content": prompt_final
                }
            ],
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4000"))
        )
        
        resultado = resposta.choices[0].message.content
        
        print(f"✅ Análise concluída: {len(resultado)} caracteres")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro na análise com IA: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Erro ao analisar com IA: {str(e)}")


# ========================================
# TESTE RÁPIDO
# ========================================

if __name__ == "__main__":
    print("🧪 Testando prompts...")
    
    # Criar DataFrame de teste
    df_teste = pd.DataFrame({
        'Produto': ['Produto A', 'Produto B', 'Produto C'],
        'Preço': [10.50, 25.90, 15.00],
        'Concorrente': ['Loja X', 'Loja Y', 'Loja Z'],
        'Diferença': ['-5%', '+10%', '0%']
    })
    
    print("\n📊 Dados de teste:")
    print(df_teste)
    
    print("\n✅ Prompts disponíveis:")
    print("- Concorrência")
    print("- Merchandising")
    print("- Preço")
    
    print("\n⚠️ Para testar análise real, configure OPENAI_API_KEY no .env")
