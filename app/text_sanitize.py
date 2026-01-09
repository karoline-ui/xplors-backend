# backend/app/text_sanitize.py
import re

def limpar_para_pdf(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"<JSON>\s*\{.*?\}\s*</JSON>", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"```json\s*\{.*?\}\s*```", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)

    texto = re.sub(r"i[' ]?m unable to.*?(?:\n|$)", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"unable to analyze.*?(?:\n|$)", "", texto, flags=re.IGNORECASE)

    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    return texto
