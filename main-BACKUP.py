"""
Backend INTELIGENTE - Sistema Multi-Prompt
Detecta tipos automaticamente e usa prompt específico para cada tipo
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
from supabase import create_client, Client
from app.pdf_generator import gerar_pdf_xplors
import uuid
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuração Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Configure SUPABASE_URL e SUPABASE_KEY no .env")

supabase: Client = create_client(supabase_url, supabase_key)
print("✅ Supabase conectado!")

# MAPEAMENTO: Palavras-chave → Tipo de análise
TIPO_MAPPING = {
    'feedback': ['feedback', 'comentario', 'avaliacao', 'satisfacao', 'comercial', 'promotor'],
    'preco': ['preco', 'price', 'pricing', 'pesquisa de preco', 'pesquisa_preco'],
    'merchandising': ['merchandising', 'execucao', 'gondola', 'exposicao', 'pdv'],
    'concorrencia': ['concorrencia', 'competidor', 'competitor', 'acoes concorrencia']
}

# PROMPTS ESPECÍFICOS - Um para cada tipo!
PROMPTS_ESPECIFICOS = {
    'feedback': """
Analise os FEEDBACKS/COMENTÁRIOS fornecidos e crie um relatório detalhado:

## 1. RESUMO EXECUTIVO
- Quantidade de feedbacks por categoria
- Distribuição por tipo de equipe
- Score geral de satisfação

## 2. ANÁLISE DE SENTIMENTOS
- 😊 Positivos: quantidade e temas principais
- 😐 Neutros: quantidade e temas principais  
- 😞 Negativos: quantidade e temas principais

## 3. PRINCIPAIS PROBLEMAS
- Top 5 problemas mencionados
- Frequência de cada problema
- Urgência (crítico, alto, médio, baixo)

## 4. PROBLEMAS POR CATEGORIA
- Merchandising: problemas específicos
- Comercial: problemas específicos
- Promotor: problemas específicos
- Área Comercial: problemas específicos

## 5. ANÁLISE DO APP/SISTEMA
- Problemas técnicos reportados
- Funcionalidades com mais reclamações
- Sugestões de melhoria

## 6. RECOMENDAÇÕES PRIORITÁRIAS
- **Urgente** (fazer hoje)
- **Curto prazo** (próximos 7 dias)
- **Médio prazo** (próximo mês)

Seja específico, cite exemplos (sem identificar pessoas) e priorize ações.
""",

    'preco': """
Analise os dados de PESQUISA DE PREÇO fornecidos:

## 1. RESUMO EXECUTIVO
- Quantidade de SKUs pesquisados
- Quantidade de clientes/lojas
- Range de preços (min, max, mediana)

## 2. TOP PRODUTOS ANALISADOS
- 10 SKUs com mais dados coletados
- Variação de preço por produto
- Produtos com maior dispersão

## 3. ANÁLISE POR CLIENTE/LOJA
- Clientes mais competitivos (preços mais baixos)
- Clientes menos competitivos (preços mais altos)
- Ranking de competitividade

## 4. OPORTUNIDADES DE PRICING
- SKUs com potencial de ajuste
- Produtos sub-precificados
- Produtos sobre-precificados
- Gaps vs concorrência

## 5. ALERTAS CRÍTICOS
- Produtos com preços muito fora da curva
- Perdas de competitividade
- Oportunidades sendo desperdiçadas

## 6. RECOMENDAÇÕES
- Ajustes de preço prioritários (top 10 SKUs)
- Estratégia por categoria
- Ações imediatas

Use números, percentuais e valores reais. Seja específico e prático.
""",

    'merchandising': """
Analise os dados de EXECUÇÃO DE MERCHANDISING:

## 1. RESUMO EXECUTIVO
- Quantidade de execuções analisadas
- PDVs/lojas visitados
- Score geral de execução

## 2. PERFORMANCE POR PDV
- Lojas com melhor execução
- Lojas com pior execução
- Padrões identificados

## 3. ANÁLISE DE EXPOSIÇÃO
- Share of shelf por produto/categoria
- Visibilidade nos pontos de venda
- Qualidade da execução

## 4. PROBLEMAS IDENTIFICADOS
- Rupturas de estoque
- Problemas de exposição
- Falhas de execução
- Issues recorrentes

## 5. COMPLIANCE
- % de execução conforme planejado
- Desvios mais comuns
- Impacto nas vendas

## 6. OPORTUNIDADES
- Melhorias de exposição
- Otimização de layout
- Ações para aumentar visibilidade

## 7. RECOMENDAÇÕES
- Ações corretivas prioritárias
- Treinamentos necessários
- Follow-up recomendado

Seja específico com lojas, produtos e problemas. Use dados reais.
""",

    'concorrencia': """
Analise os dados de AÇÕES DA CONCORRÊNCIA:

## 1. RESUMO EXECUTIVO
- Quantidade de ações monitoradas
- Principais concorrentes identificados
- Tipos de ações observadas

## 2. ANÁLISE POR CONCORRENTE
- Principais players
- Frequência de ações
- Estratégias identificadas

## 3. TIPOS DE AÇÕES
- Promoções
- Ativações
- Mudanças de preço
- Lançamentos
- Outras ações

## 4. ANÁLISE COMPETITIVA
- Pontos fortes dos concorrentes
- Pontos fracos dos concorrentes
- Oportunidades para nossa marca
- Ameaças identificadas

## 5. IMPACTO NO MERCADO
- Ações mais impactantes
- Respostas necessárias
- Timing crítico

## 6. RECOMENDAÇÕES ESTRATÉGICAS
- Contramedidas sugeridas
- Ações preventivas
- Oportunidades de antecipação

Seja estratégico e prático. Foque em insights acionáveis.
"""
}

def detectar_tipo_por_nome(nome_tipo):
    """Detecta o tipo de análise baseado no nome do tipo"""
    nome_lower = nome_tipo.lower()
    
    for tipo_analise, keywords in TIPO_MAPPING.items():
        for keyword in keywords:
            if keyword in nome_lower:
                return tipo_analise
    
    return 'geral'  # fallback

def analisar_por_tipo(df, tipo_nome, prompt):
    """Analisa um subset de dados com prompt específico"""
    try:
        dados_texto = df.to_string()
        
        prompt_completo = f"""
        {prompt}
        
        Dados para análise ({len(df)} linhas):
        {dados_texto}
        
        Formate sua resposta em markdown com seções claras.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Você é um analista especializado em {tipo_nome}."},
                {"role": "user", "content": prompt_completo}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Erro ao analisar tipo {tipo_nome}: {e}")
        raise

def analisar_planilha_inteligente(df):
    """
    Analisa planilha de forma inteligente:
    1. Detecta se tem coluna 'Tipo'
    2. Separa por tipo
    3. Analisa cada tipo com prompt específico
    4. Combina tudo
    """
    
    # Verificar se tem coluna 'Tipo'
    tem_coluna_tipo = 'Tipo' in df.columns or 'tipo' in df.columns
    
    if tem_coluna_tipo:
        print("📊 Planilha COM coluna 'Tipo' - Analisando por tipo...")
        
        # Normalizar nome da coluna
        coluna_tipo = 'Tipo' if 'Tipo' in df.columns else 'tipo'
        
        # Pegar tipos únicos
        tipos_unicos = df[coluna_tipo].unique()
        print(f"✅ Tipos encontrados: {tipos_unicos}")
        
        # Análises separadas
        analises = []
        
        for tipo_nome in tipos_unicos:
            # Filtrar dados desse tipo
            df_tipo = df[df[coluna_tipo] == tipo_nome]
            
            # Detectar qual tipo de análise usar
            tipo_analise = detectar_tipo_por_nome(tipo_nome)
            prompt = PROMPTS_ESPECIFICOS.get(tipo_analise, PROMPTS_ESPECIFICOS['feedback'])
            
            print(f"🤖 Analisando '{tipo_nome}' como '{tipo_analise}' ({len(df_tipo)} linhas)...")
            
            # Analisar
            analise = analisar_por_tipo(df_tipo, tipo_nome, prompt)
            
            # Adicionar ao resultado
            analises.append({
                'tipo_nome': tipo_nome,
                'tipo_analise': tipo_analise,
                'total_linhas': len(df_tipo),
                'analise': analise
            })
        
        # Combinar todas as análises
        resultado_final = f"# RELATÓRIO COMPLETO - ANÁLISE MULTI-TIPO\n\n"
        resultado_final += f"**Total de registros:** {len(df)}\n"
        resultado_final += f"**Tipos analisados:** {len(analises)}\n\n"
        resultado_final += "---\n\n"
        
        for idx, item in enumerate(analises, 1):
            resultado_final += f"# {idx}. {item['tipo_nome'].upper()}\n\n"
            resultado_final += f"*{item['total_linhas']} registros analisados*\n\n"
            resultado_final += item['analise']
            resultado_final += "\n\n---\n\n"
        
        return resultado_final, 'multi-tipo'
    
    else:
        print("📊 Planilha SEM coluna 'Tipo' - Analisando como geral...")
        
        # Análise geral usando prompt de feedback por padrão
        dados_texto = df.to_string()
        colunas = ", ".join(df.columns.tolist())
        
        prompt = f"""
        Analise os dados fornecidos de forma completa e estruturada.
        
        Colunas: {colunas}
        Total de linhas: {len(df)}
        
        Dados:
        {dados_texto}
        
        Crie um relatório detalhado com insights acionáveis.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um analista de dados especializado em varejo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        return response.choices[0].message.content, 'geral'
@app.route('/upload', methods=['POST'])
def upload_arquivo():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['file']
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        if arquivo.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
        # 📄 Ler Excel
        print(f"📄 Lendo arquivo Excel: {arquivo.filename}")
        df = pd.read_excel(arquivo)
        print(f"✅ Excel lido! {len(df)} linhas")

        # 🤖 Análise inteligente
        print("🤖 Iniciando análise inteligente...")
        analise_texto, tipo_detectado = analisar_planilha_inteligente(df)
        print(f"✅ Análise concluída! Tipo: {tipo_detectado}")

        # ============================
        # 📄 GERAR PDF (CORRIGIDO)
        # ============================
        print("📄 Gerando PDF...")

        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            caminho_pdf = tmp.name

        nome_arquivo_pdf = f"analise_{tipo_detectado}_{uuid.uuid4().hex[:8]}.pdf"

        dados_analise = {
            'texto': analise_texto,
            'total_linhas': len(df)
        }

        dados_excel_dict = df.head(100).to_dict('records')

        gerar_pdf_xplors(
            arquivo_saida=caminho_pdf,
            tipo_analise=tipo_detectado,
            dados_analise=dados_analise,
            dados_excel=dados_excel_dict
        )

        # 🔥 VERIFICAÇÃO CRÍTICA
        if not os.path.exists(caminho_pdf):
            raise Exception("PDF não foi gerado corretamente")

        print("✅ PDF gerado com sucesso!")

        # ============================
        # ☁️ UPLOAD SUPABASE
        # ============================
        print("☁️ Enviando PDF para o Supabase...")

        with open(caminho_pdf, 'rb') as f:
            pdf_data = f.read()

        storage_path = f"analises/{user_id}/{nome_arquivo_pdf}"

        supabase.storage.from_('relatorios-pdf').upload(
            storage_path,
            pdf_data,
            file_options={"content-type": "application/pdf"}
        )

        pdf_url = supabase.storage.from_('relatorios-pdf').get_public_url(storage_path)

        # 🗃️ Salvar no banco
        resultado_db = supabase.table('analises').insert({
            'user_id': user_id,
            'nome_arquivo_original': arquivo.filename,
            'tipo_analise': tipo_detectado,
            'total_linhas': len(df),
            'pdf_filename': nome_arquivo_pdf,
            'pdf_url': pdf_url,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        # 🧹 Limpar arquivo temporário
        os.remove(caminho_pdf)

        # 🚀 Resposta FINAL pro frontend
        return jsonify({
            'success': True,
            'message': 'Análise concluída com sucesso!',
            'analise_id': resultado_db.data[0]['id'],
            'pdf_url': pdf_url,  # 👈 FRONT USA ISSO PRA VISUALIZAR
            'tipo_analise': tipo_detectado,
            'total_linhas': len(df)
        })

    except Exception as e:
        print(f"❌ Erro no upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'openai': 'configured' if os.getenv('OPENAI_API_KEY') else 'not configured',
        'supabase': 'connected',
        'modo': 'INTELIGENTE - Detecta tipos automaticamente',
        'tipos_suportados': list(PROMPTS_ESPECIFICOS.keys())
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Servidor rodando em http://localhost:{port}")
    print(f"🤖 Modo INTELIGENTE:")
    print(f"   - Detecta coluna 'Tipo' automaticamente")
    print(f"   - Separa e analisa cada tipo com prompt específico")
    print(f"   - Combina tudo em um relatório completo")
    print(f"📊 Tipos suportados: {list(PROMPTS_ESPECIFICOS.keys())}")
    app.run(debug=True, host='0.0.0.0', port=port)