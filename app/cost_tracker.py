"""
Sistema de Tracking de Custos - OpenAI API
Rastreia uso, calcula custos e controla limites
"""

from datetime import datetime
from supabase import Client

# Preços GPT-4o (por 1M tokens)
PRECO_INPUT_GPT4O = 2.50  # $2.50 por 1M tokens
PRECO_OUTPUT_GPT4O = 10.00  # $10.00 por 1M tokens
PRECO_IMAGEM_GPT4O = 2.50  # ~$2.50 por 1M tokens de imagem (aproximado)

class CostTracker:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def calcular_custo(self, tokens_input: int, tokens_output: int, tokens_imagem: int = 0) -> float:
        """Calcula custo total em dólares"""
        custo_input = (tokens_input / 1_000_000) * PRECO_INPUT_GPT4O
        custo_output = (tokens_output / 1_000_000) * PRECO_OUTPUT_GPT4O
        custo_imagem = (tokens_imagem / 1_000_000) * PRECO_IMAGEM_GPT4O
        
        return custo_input + custo_output + custo_imagem
    
    def registrar_uso(self, user_id: str, tipo: str, tokens_input: int, 
                     tokens_output: int, tokens_imagem: int = 0, metadata: dict = None):
        """Registra uso da API no banco"""
        try:
            custo = self.calcular_custo(tokens_input, tokens_output, tokens_imagem)
            
            registro = {
                'user_id': user_id,
                'tipo': tipo,  # 'analise', 'imagem', 'pdf'
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tokens_imagem': tokens_imagem,
                'custo_usd': custo,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('api_usage').insert(registro).execute()
            
            print(f"💰 Custo registrado: ${custo:.4f} ({tokens_input + tokens_output + tokens_imagem} tokens)")
            
            return custo
            
        except Exception as e:
            print(f"❌ Erro ao registrar uso: {e}")
            return 0
    
    def verificar_limite(self, user_id: str, limite_mensal: float = 100.0) -> dict:
        """Verifica se usuário atingiu limite mensal"""
        try:
            # Pegar mês atual
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Buscar uso do mês
            response = self.supabase.table('api_usage')\
                .select('custo_usd')\
                .eq('user_id', user_id)\
                .gte('created_at', inicio_mes.isoformat())\
                .execute()
            
            total_gasto = sum(item['custo_usd'] for item in response.data)
            percentual = (total_gasto / limite_mensal) * 100
            
            return {
                'total_gasto': total_gasto,
                'limite': limite_mensal,
                'percentual': percentual,
                'pode_usar': total_gasto < limite_mensal,
                'alerta': percentual >= 80  # Alertar a partir de 80%
            }
            
        except Exception as e:
            print(f"❌ Erro ao verificar limite: {e}")
            return {
                'total_gasto': 0,
                'limite': limite_mensal,
                'percentual': 0,
                'pode_usar': True,
                'alerta': False
            }
    
    def obter_estatisticas(self, user_id: str, dias: int = 30) -> dict:
        """Obtém estatísticas de uso"""
        try:
            from datetime import timedelta
            inicio = datetime.now() - timedelta(days=dias)
            
            response = self.supabase.table('api_usage')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('created_at', inicio.isoformat())\
                .execute()
            
            dados = response.data
            
            total_analises = len([d for d in dados if d['tipo'] == 'analise'])
            total_imagens = len([d for d in dados if d['tipo'] == 'imagem'])
            total_custo = sum(d['custo_usd'] for d in dados)
            total_tokens = sum(d['tokens_input'] + d['tokens_output'] + d.get('tokens_imagem', 0) for d in dados)
            
            # Custo médio por análise
            custo_medio = total_custo / len(dados) if dados else 0
            
            return {
                'total_analises': total_analises,
                'total_imagens': total_imagens,
                'total_custo': total_custo,
                'total_tokens': total_tokens,
                'custo_medio': custo_medio,
                'periodo_dias': dias
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def obter_uso_diario(self, user_id: str, dias: int = 30) -> list:
        """Obtém uso diário para gráficos"""
        try:
            from datetime import timedelta
            from collections import defaultdict
            
            inicio = datetime.now() - timedelta(days=dias)
            
            response = self.supabase.table('api_usage')\
                .select('created_at, custo_usd')\
                .eq('user_id', user_id)\
                .gte('created_at', inicio.isoformat())\
                .order('created_at', desc=False)\
                .execute()
            
            # Agrupar por dia
            uso_por_dia = defaultdict(float)
            
            for item in response.data:
                data = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                dia = data.strftime('%Y-%m-%d')
                uso_por_dia[dia] += item['custo_usd']
            
            # Converter para lista
            resultado = [
                {'data': dia, 'custo': custo}
                for dia, custo in sorted(uso_por_dia.items())
            ]
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao obter uso diário: {e}")
            return []


def estimar_tokens_texto(texto: str) -> int:
    """Estimativa simples de tokens (1 token ≈ 4 caracteres)"""
    return len(texto) // 4


def estimar_tokens_imagem(largura: int = 1024, altura: int = 1024) -> int:
    """Estimativa de tokens para imagem"""
    # GPT-4o Vision: ~765 tokens por imagem 1024x1024
    # Escala baseado no tamanho
    tokens_base = 765
    pixels_base = 1024 * 1024
    pixels_atual = largura * altura
    
    return int((pixels_atual / pixels_base) * tokens_base)
