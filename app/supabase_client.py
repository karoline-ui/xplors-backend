"""
========================================
SUPABASE CLIENT - XPLORS
========================================

Configuração e inicialização do Supabase
- Auth (autenticação)
- Storage (PDFs)
- Database (histórico)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ========================================
# CONFIGURAÇÃO
# ========================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "relatorios-pdf")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Configure SUPABASE_URL e SUPABASE_KEY no .env")

# Criar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ========================================
# FUNÇÕES DE STORAGE
# ========================================

def upload_pdf_to_storage(file_path: str, file_name: str) -> str:
    """
    Faz upload do PDF para Supabase Storage
    
    Args:
        file_path: Caminho local do arquivo
        file_name: Nome do arquivo no storage
        
    Returns:
        URL pública do arquivo
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Upload para Supabase Storage
        res = supabase.storage.from_(BUCKET_NAME).upload(
            file_name,
            data,
            file_options={"content-type": "application/pdf"}
        )
        
        # Obter URL pública
        url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
        
        print(f"✅ PDF salvo no Supabase: {file_name}")
        return url
        
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {str(e)}")
        raise


def get_pdf_from_storage(file_name: str) -> bytes:
    """
    Baixa PDF do Supabase Storage
    
    Args:
        file_name: Nome do arquivo
        
    Returns:
        Conteúdo do arquivo em bytes
    """
    try:
        res = supabase.storage.from_(BUCKET_NAME).download(file_name)
        return res
    except Exception as e:
        print(f"❌ Erro ao baixar PDF: {str(e)}")
        raise


# ========================================
# FUNÇÕES DE DATABASE
# ========================================

def salvar_analise(user_id: str, dados: dict) -> dict:
    """
    Salva análise no banco de dados
    
    Args:
        user_id: ID do usuário
        dados: Dados da análise
        
    Returns:
        Registro criado
    """
    try:
        resultado = supabase.table('analises').insert({
            'user_id': user_id,
            'tipo_analise': dados['tipo_analise'],
            'total_linhas': dados['total_linhas'],
            'pdf_url': dados['pdf_url'],
            'pdf_filename': dados['pdf_filename'],
            'nome_arquivo_original': dados.get('nome_arquivo_original'),
            'created_at': dados.get('created_at')
        }).execute()
        
        print(f"✅ Análise salva no banco: {resultado.data[0]['id']}")
        return resultado.data[0]
        
    except Exception as e:
        print(f"❌ Erro ao salvar análise: {str(e)}")
        raise


def buscar_analises_usuario(user_id: str) -> list:
    """
    Busca todas as análises de um usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Lista de análises
    """
    try:
        resultado = supabase.table('analises').select('*').eq(
            'user_id', user_id
        ).order('created_at', desc=True).execute()
        
        return resultado.data
        
    except Exception as e:
        print(f"❌ Erro ao buscar análises: {str(e)}")
        return []


def buscar_analise_por_id(analise_id: str) -> dict:
    """
    Busca uma análise específica
    
    Args:
        analise_id: ID da análise
        
    Returns:
        Dados da análise
    """
    try:
        resultado = supabase.table('analises').select('*').eq(
            'id', analise_id
        ).execute()
        
        if resultado.data:
            return resultado.data[0]
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar análise: {str(e)}")
        return None


# ========================================
# FUNÇÕES DE AUTH
# ========================================

def verificar_token(token: str) -> dict:
    """
    Verifica se token JWT é válido
    
    Args:
        token: Token JWT
        
    Returns:
        Dados do usuário se válido, None se inválido
    """
    try:
        user = supabase.auth.get_user(token)
        return user.user.__dict__ if user.user else None
    except:
        return None


if __name__ == "__main__":
    print("🧪 Testando conexão com Supabase...")
    print(f"📍 URL: {SUPABASE_URL}")
    print(f"🪣 Bucket: {BUCKET_NAME}")
    print("✅ Supabase configurado!")
