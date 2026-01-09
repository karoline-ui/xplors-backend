"""
SUPABASE CLIENT - XPLORS (HARDENED)

- Storage: upload de PDFs
- Retorna SIGNED URL (bucket privado recomendado)
"""

import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # ideal: service role só no backend
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "pdfs")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_KEY são obrigatórios")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf_to_storage(file_path: str, user_id: str, expires_in_seconds: int = 3600) -> dict:
    """
    Upload do PDF no Storage e retorno de URL assinada (expira).

    Returns:
        {"path": "...", "signed_url": "..."}
    """
    storage_path = f"{user_id}/{uuid.uuid4().hex}.pdf"

    with open(file_path, "rb") as f:
        data = f.read()

    supabase.storage.from_(BUCKET_NAME).upload(
        storage_path,
        data,
        file_options={"content-type": "application/pdf"},
    )

    signed = supabase.storage.from_(BUCKET_NAME).create_signed_url(storage_path, expires_in_seconds)

    signed_url = None
    if isinstance(signed, dict):
        signed_url = signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url")

    if not signed_url:
        # fallback (não ideal): URL pública
        signed_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)

    return {"path": storage_path, "signed_url": signed_url}


def verificar_token(token: str):
    """Verifica token JWT do Supabase (sem logar token)."""
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception:
        return None


def salvar_analise(user_id: str, dados: dict) -> dict:
    """Salva análise no banco."""
    resultado = supabase.table("analises").insert({"user_id": user_id, **dados}).execute()
    return resultado.data[0] if getattr(resultado, "data", None) else {}


def listar_analises(user_id: str, limit: int = 20) -> list:
    """Lista análises do usuário."""
    res = (
        supabase.table("analises")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []
