"""
========================================
PROCESSADOR DE PLANILHAS EXCEL
========================================

Este módulo:
1. Lê arquivos Excel (.xlsx, .xls)
2. Identifica automaticamente o tipo de análise
3. Processa e limpa os dados
4. Retorna DataFrame pronto para análise

Tipos de análise identificados:
- concorrencia: ~65 respostas
- merchandising: ~1357 respostas
- preco: ~2166 respostas
"""

import pandas as pd
from pathlib import Path


def processar_planilha(filepath: str) -> pd.DataFrame:
    """
    Lê e processa planilha Excel
    
    Args:
        filepath: Caminho do arquivo Excel
        
    Returns:
        DataFrame com os dados processados
        
    Exemplo:
        >>> dados = processar_planilha("planilha.xlsx")
        >>> print(dados.head())
    """
    
    try:
        print(f"📖 Lendo planilha: {filepath}")
        
        # Ler Excel - tenta .xlsx primeiro, depois .xls
        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            df = pd.read_excel(filepath, engine='xlrd')
        
        print(f"✅ Planilha lida: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"📊 Colunas: {df.columns.tolist()}")
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Remover espaços em branco das colunas
        df.columns = df.columns.str.strip()
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {str(e)}")
        raise Exception(f"Erro ao processar planilha: {str(e)}")


def identificar_tipo(df: pd.DataFrame) -> str:
    """
    Identifica automaticamente o tipo de análise baseado nos dados
    
    Lógica:
    - Se tem coluna "Tipo" com valor específico -> usa ele
    - Senão, usa quantidade de respostas:
        * ~65 respostas = Ações de Concorrência
        * ~1357 respostas = Execução de Merchandising  
        * ~2166 respostas = Pesquisa de Preço
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Tipo de análise: 'concorrencia', 'merchandising' ou 'preco'
        
    Exemplo:
        >>> tipo = identificar_tipo(df)
        >>> print(tipo)
        'merchandising'
    """
    
    total_respostas = len(df)
    print(f"🔍 Total de respostas: {total_respostas}")
    
    # Estratégia 1: Verificar se tem coluna "Tipo"
    if 'Tipo' in df.columns:
        tipo_coluna = df['Tipo'].iloc[0].lower()
        
        if 'concorrência' in tipo_coluna or 'concorrencia' in tipo_coluna:
            return 'concorrencia'
        elif 'merchandising' in tipo_coluna:
            return 'merchandising'
        elif 'preço' in tipo_coluna or 'preco' in tipo_coluna:
            return 'preco'
    
    
    # Estratégia 2: Identificar por quantidade de respostas
    # Com margem de erro de ±20%
    
    if 50 <= total_respostas <= 80:
        # ~65 respostas = Ações de Concorrência
        return 'concorrencia'
        
    elif 1100 <= total_respostas <= 1600:
        # ~1357 respostas = Execução de Merchandising
        return 'merchandising'
        
    elif 1800 <= total_respostas <= 2500:
        # ~2166 respostas = Pesquisa de Preço
        return 'preco'
    
    
    # Se não identificar, assume como merchandising (mais comum)
    print("⚠️ Não foi possível identificar tipo exato. Usando 'merchandising' como padrão.")
    return 'merchandising'


def extrair_metricas_basicas(df: pd.DataFrame) -> dict:
    """
    Extrai métricas básicas da planilha
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Dicionário com métricas
        
    Exemplo:
        >>> metricas = extrair_metricas_basicas(df)
        >>> print(metricas['total_respostas'])
        1357
    """
    
    metricas = {
        'total_respostas': len(df),
        'total_colunas': len(df.columns),
        'colunas': df.columns.tolist(),
        'primeiras_linhas': df.head(3).to_dict('records')
    }
    
    return metricas


# ========================================
# FUNÇÕES AUXILIARES PARA ANÁLISE
# ========================================

def obter_resumo_dados(df: pd.DataFrame) -> str:
    """
    Cria um resumo textual dos dados para enviar para IA
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        String com resumo formatado
    """
    
    resumo = f"""
RESUMO DOS DADOS:

Total de linhas: {len(df)}
Total de colunas: {len(df.columns)}

Colunas disponíveis:
{', '.join(df.columns.tolist())}

Primeiras 5 linhas:
{df.head(5).to_string()}

Estatísticas:
{df.describe().to_string()}
"""
    
    return resumo


if __name__ == "__main__":
    # Teste rápido
    print("🧪 Testando processador de Excel...")
    
    # Criar DataFrame de exemplo
    df_teste = pd.DataFrame({
        'Linha': [1, 2, 3],
        'Tipo': ['Ações concorrência', 'Execução de Merchandising', 'Pesquisa de Preço'],
        'Respostas': [65, 1357, 2166]
    })
    
    print("\n📊 DataFrame de teste:")
    print(df_teste)
    
    print("\n🔍 Identificando tipos:")
    for i, row in df_teste.iterrows():
        df_temp = pd.DataFrame([row] * int(row['Respostas']))
        tipo = identificar_tipo(df_temp)
        print(f"✅ {row['Tipo']}: {tipo} ({row['Respostas']} respostas)")
