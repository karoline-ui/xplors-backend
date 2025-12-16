"""
Backend SIMPLES - Versão que funciona
Sem complicações, só o essencial
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

def analisar_com_openai(dados_excel):
    """Analisa dados com GPT-4o - VERSÃO SIMPLES"""
    try:
        # Pegar só primeiras 100 linhas para não estourar tokens
        if len(dados_excel) > 100:
            dados_amostra = dados_excel.head(100)
            info_adicional = f"\n\nNOTA: Amostra de 100 linhas de um total de {len(dados_excel)} linhas."
        else:
            dados_amostra = dados_excel
            info_adicional = ""
        
        # Converter para texto
        dados_texto = dados_amostra.to_string()
        colunas = ", ".join(dados_excel.columns.tolist())
        
        prompt = f"""
Analise os dados fornecidos e crie um relatório COMPLETO e DETALHADO.

Colunas disponíveis: {colunas}
Total de linhas no arquivo: {len(dados_excel)}

Dados para análise:
{dados_texto}
{info_adicional}

Crie um relatório profissional com:

1. RESUMO EXECUTIVO
- Visão geral dos dados
- Principais insights

2. ANÁLISE DETALHADA
- Analise os dados por categoria/tipo (se houver)
- Identifique padrões e tendências
- Destaque pontos importantes

3. INSIGHTS E DESCOBERTAS
- O que se destaca nos dados
- Oportunidades identificadas
- Pontos de atenção

4. RECOMENDAÇÕES
- Ações sugeridas com base nos dados
- Próximos passos
- Prioridades

Seja direto, claro e profissional.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um analista de dados especializado em criar relatórios profissionais."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Erro ao analisar com OpenAI: {e}")
        raise

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
        
        # Ler Excel
        print(f"📄 Lendo arquivo: {arquivo.filename}")
        df = pd.read_excel(arquivo)
        print(f"✅ Excel lido! {len(df)} linhas")
        
        # Analisar com OpenAI
        print(f"🤖 Analisando com IA...")
        analise_texto = analisar_com_openai(df)
        print("✅ Análise concluída!")
        
        # Gerar PDF
        print("📄 Gerando PDF...")
        nome_arquivo_pdf = f"analise_{uuid.uuid4().hex[:8]}.pdf"
        
        # Usar pasta temporária correta para Windows
        if os.name == 'nt':  # Windows
            pasta_temp = os.path.join(os.getcwd(), 'temp')
            if not os.path.exists(pasta_temp):
                os.makedirs(pasta_temp)
            caminho_pdf = os.path.join(pasta_temp, nome_arquivo_pdf)
        else:  # Linux/Mac
            caminho_pdf = os.path.join('/tmp', nome_arquivo_pdf)
        
        dados_analise = {
            'texto': analise_texto,
            'total_linhas': len(df)
        }
        
        gerar_pdf_xplors(
            arquivo_saida=caminho_pdf,
            tipo_analise='geral',
            dados_analise=dados_analise
        )
        print("✅ PDF gerado!")
        
        # Upload para Supabase
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
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        print("✅ Salvo no banco!")
        
        # Limpar arquivo temporário
        os.remove(caminho_pdf)
        
        return jsonify({
            'success': True,
            'message': 'Análise concluída com sucesso!',
            'analise_id': resultado_db.data[0]['id'],
            'pdf_url': pdf_url,
            'tipo_analise': 'geral',
            'total_linhas': len(df)
        })
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'openai': 'configured' if os.getenv('OPENAI_API_KEY') else 'not configured',
        'supabase': 'connected',
        'versao': 'SIMPLES - Versão que funciona'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Servidor rodando em http://localhost:{port}")
    print(f"✅ Versão SIMPLES - Sem complicações")
    app.run(debug=True, host='0.0.0.0', port=port)