"""
Backend COMPLETO - Xplors
ESPECIALIZADO EM ANÁLISE DE MERCHANDISING
Pronto para deploy no Google Cloud Run
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
from supabase import create_client, Client
from app.pdf_generator_com_graficos import gerar_pdf_xplors
from app.cost_tracker import CostTracker, estimar_tokens_texto, estimar_tokens_imagem
from app.image_analyzer import ImageAnalyzer
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
    print("⚠️ AVISO: Variáveis SUPABASE não configuradas")
    supabase = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase conectado!")

# Inicializar trackers
if supabase:
    cost_tracker = CostTracker(supabase)
    image_analyzer = ImageAnalyzer(os.getenv('OPENAI_API_KEY'))
else:
    cost_tracker = None
    image_analyzer = None

# Limite padrão
LIMITE_MENSAL_PADRAO = float(os.getenv('LIMITE_MENSAL', '100.0'))


def analisar_com_openai(dados_excel):
    """Analisa dados com GPT-4o"""
    try:
        if len(dados_excel) > 100:
            dados_amostra = dados_excel.head(100)
            info_adicional = f"\n\nNOTA: Amostra de 100 linhas de um total de {len(dados_excel)} linhas."
        else:
            dados_amostra = dados_excel
            info_adicional = ""
        
        dados_texto = dados_amostra.to_string()
        colunas = ", ".join(dados_excel.columns.tolist())
        
        prompt = f"""
Analise os dados fornecidos e crie um relatório COMPLETO e DETALHADO.

Colunas: {colunas}
Total de linhas: {len(dados_excel)}

Dados:
{dados_texto}
{info_adicional}

Crie um relatório profissional com:

1. RESUMO EXECUTIVO
2. ANÁLISE DETALHADA
3. INSIGHTS E DESCOBERTAS
4. RECOMENDAÇÕES

Seja direto, claro e profissional.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um analista de dados especializado."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analise = response.choices[0].message.content
        tokens_input = response.usage.prompt_tokens
        tokens_output = response.usage.completion_tokens
        
        return analise, tokens_input, tokens_output
        
    except Exception as e:
        print(f"Erro ao analisar com OpenAI: {e}")
        raise


@app.route('/upload', methods=['POST'])
def upload_arquivo():
    """Endpoint de upload e análise de planilhas"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['file']
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # VERIFICAR LIMITE
        if cost_tracker:
            status_limite = cost_tracker.verificar_limite(user_id, LIMITE_MENSAL_PADRAO)
            
            if not status_limite['pode_usar']:
                return jsonify({
                    'error': 'Limite mensal atingido',
                    'limite_info': status_limite
                }), 429
            
            if status_limite['alerta']:
                print(f"⚠️ Usuário {user_id} está em {status_limite['percentual']:.1f}% do limite")
        
        if arquivo.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
        # Ler Excel
        print(f"📄 Lendo arquivo: {arquivo.filename}")
        df = pd.read_excel(arquivo)
        print(f"✅ Excel lido! {len(df)} linhas")
        
        # Analisar
        print(f"🤖 Analisando com IA...")
        analise_texto, tokens_input, tokens_output = analisar_com_openai(df)
        print("✅ Análise concluída!")
        
        # Registrar custo
        custo = 0
        if cost_tracker:
            custo = cost_tracker.registrar_uso(
                user_id=user_id,
                tipo='analise',
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                metadata={'arquivo': arquivo.filename, 'linhas': len(df)}
            )
        
        # Gerar PDF com gráficos
        print("📄 Gerando PDF com gráficos...")
        nome_arquivo_pdf = f"analise_{uuid.uuid4().hex[:8]}.pdf"
        
        # Cloud Run usa /tmp
        caminho_pdf = os.path.join('/tmp', nome_arquivo_pdf)
        
        dados_analise = {
            'texto': analise_texto,
            'total_linhas': len(df)
        }
        
        gerar_pdf_xplors(
            arquivo_saida=caminho_pdf,
            tipo_analise='geral',
            dados_analise=dados_analise,
            dados_excel=df
        )
        print("✅ PDF gerado!")
        
        # Upload para Supabase
        if supabase:
            print("☁️ Salvando no Supabase...")
            with open(caminho_pdf, 'rb') as f:
                pdf_data = f.read()
                
            storage_path = f"analises/{user_id}/{nome_arquivo_pdf}"
            
            supabase.storage.from_('relatorios-pdf').upload(
                storage_path,
                pdf_data,
                file_options={"content-type": "application/pdf"}
            )
            
            pdf_url = supabase.storage.from_('relatorios-pdf').get_public_url(storage_path)
            print("✅ PDF salvo no Supabase!")
            
            # Salvar no banco
            print("💾 Salvando no banco...")
            resultado_db = supabase.table('analises').insert({
                'user_id': user_id,
                'nome_arquivo_original': arquivo.filename,
                'tipo_analise': 'geral',
                'total_linhas': len(df),
                'pdf_filename': nome_arquivo_pdf,
                'pdf_url': pdf_url,
                'custo_usd': custo,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            print("✅ Salvo no banco!")
        else:
            pdf_url = f"/tmp/{nome_arquivo_pdf}"
            resultado_db = None
        
        # Limpar
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
        
        # Status atualizado
        status_limite_atualizado = cost_tracker.verificar_limite(user_id, LIMITE_MENSAL_PADRAO) if cost_tracker else None
        
        return jsonify({
            'success': True,
            'message': 'Análise concluída com sucesso!',
            'analise_id': resultado_db.data[0]['id'] if resultado_db else None,
            'pdf_url': pdf_url,
            'tipo_analise': 'geral',
            'total_linhas': len(df),
            'custo_usd': custo,
            'limite_status': status_limite_atualizado
        })
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/upload-imagem', methods=['POST'])
def upload_imagem():
    """Endpoint de upload e análise de imagens - MERCHANDISING"""
    try:
        if not image_analyzer:
            return jsonify({'error': 'Image analyzer não configurado'}), 500
            
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhuma imagem enviada'}), 400
        
        arquivo = request.files['file']
        user_id = request.form.get('user_id')
        tipo_analise = request.form.get('tipo', 'merchandising')
        contexto = request.form.get('contexto', '')
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # VERIFICAR LIMITE
        if cost_tracker:
            status_limite = cost_tracker.verificar_limite(user_id, LIMITE_MENSAL_PADRAO)
            
            if not status_limite['pode_usar']:
                return jsonify({
                    'error': 'Limite mensal atingido',
                    'limite_info': status_limite
                }), 429
        
        print(f"🖼️ Analisando imagem: {arquivo.filename}")
        
        # Preparar imagem
        imagem_base64, largura, altura = image_analyzer.preparar_imagem(arquivo)
        tokens_imagem = estimar_tokens_imagem(largura, altura)
        
        # Analisar
        resultado = image_analyzer.analisar_automatico(imagem_base64, tipo_analise, contexto)
        
        # Registrar custo
        custo = 0
        if cost_tracker:
            custo = cost_tracker.registrar_uso(
                user_id=user_id,
                tipo='imagem',
                tokens_input=resultado['tokens_input'],
                tokens_output=resultado['tokens_output'],
                tokens_imagem=tokens_imagem,
                metadata={
                    'arquivo': arquivo.filename,
                    'tipo': resultado['tipo'],
                    'contexto': contexto
                }
            )
        
        # Salvar análise no banco
        if supabase:
            resultado_db = supabase.table('analises_imagem').insert({
                'user_id': user_id,
                'nome_arquivo': arquivo.filename,
                'tipo_conteudo': resultado['tipo'],
                'analise': resultado['analise'],
                'custo_usd': custo,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        else:
            resultado_db = None
        
        print("✅ Análise de merchandising concluída!")
        
        # Status atualizado
        status_limite_atualizado = cost_tracker.verificar_limite(user_id, LIMITE_MENSAL_PADRAO) if cost_tracker else None
        
        return jsonify({
            'success': True,
            'analise_id': resultado_db.data[0]['id'] if resultado_db else None,
            'analise': resultado['analise'],
            'tipo_conteudo': resultado['tipo'],
            'custo_usd': custo,
            'limite_status': status_limite_atualizado
        })
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/custos/<user_id>', methods=['GET'])
def obter_custos(user_id):
    """Obtém estatísticas de custos"""
    try:
        if not cost_tracker:
            return jsonify({'error': 'Cost tracker não configurado'}), 500
            
        dias = int(request.args.get('dias', 30))
        
        stats = cost_tracker.obter_estatisticas(user_id, dias)
        uso_diario = cost_tracker.obter_uso_diario(user_id, dias)
        limite_status = cost_tracker.verificar_limite(user_id, LIMITE_MENSAL_PADRAO)
        
        return jsonify({
            'estatisticas': stats,
            'uso_diario': uso_diario,
            'limite_status': limite_status,
            'limite_mensal': LIMITE_MENSAL_PADRAO
        })
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'openai': 'configured' if os.getenv('OPENAI_API_KEY') else 'not configured',
        'supabase': 'connected' if supabase else 'not configured',
        'versao': 'GCP-MERCHANDISING',
        'features': [
            'Análise de planilhas',
            'PDFs com gráficos',
            'Análise de MERCHANDISING',
            'Tracking de custos',
            'Controle de limites'
        ]
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Servidor MERCHANDISING rodando em http://0.0.0.0:{port}")
    print(f"🏪 Especializado em análise de stands/displays")
    print(f"☁️ Pronto para Google Cloud Run")
    app.run(debug=False, host='0.0.0.0', port=port)
