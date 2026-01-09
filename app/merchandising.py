"""
Analisador de Imagem - Merchandising (Xplors)
- Texto 100% PT-BR (sem inglês)
- JSON NUNCA vai para o PDF (apenas para gerar gráficos)
- Relatório claro, objetivo e didático
"""

import base64
from PIL import Image
import io
import json
import re
from openai import OpenAI


def _extract_json(text: str) -> dict | None:
    if not text:
        return None

    m = re.search(r"<JSON>\s*(\{.*?\})\s*</JSON>", text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    return None


def _remove_json_from_text(text: str) -> str:
    """
    Remove blocos de JSON do texto para não aparecer no PDF.
    """
    if not text:
        return ""

    # remove bloco <JSON>...</JSON>
    text = re.sub(r"<JSON>\s*\{.*?\}\s*</JSON>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # remove bloco ```json ... ```
    text = re.sub(r"```json\s*\{.*?\}\s*```", "", text, flags=re.DOTALL | re.IGNORECASE)

    # remove "JSON" solto e lixo extra no fim
    text = re.sub(r"\n\s*JSON\s*\n", "\n", text, flags=re.IGNORECASE)

    return text.strip()


class ImageAnalyzer:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        self.client = OpenAI(api_key=api_key)

    def preparar_imagem(self, arquivo):
        image = Image.open(arquivo.stream).convert("RGB")
        width, height = image.size

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return img_base64, width, height

    def analisar_automatico(self, imagem_base64: str, tipo_analise='merchandising', contexto: str = ''):
        """
        Retorna:
        {
          "total_linhas": 1,
          "analise": "<texto PT-BR limpo e pronto p/ PDF>",
          "json_graficos": {...}
        }
        """

        prompt = f"""
Você é um(a) ESPECIALISTA SÊNIOR em VISUAL MERCHANDISING e TRADE MARKETING.

REGRAS (obrigatórias):
- Escreva 100% em PORTUGUÊS do Brasil (PT-BR). Não use inglês.
- Você TEM acesso à imagem e DEVE analisá-la. Nunca diga “não consigo analisar”.
- Seja claro, direto e didático (cliente final precisa entender).
- Não invente detalhes que não aparecem; quando algo não estiver visível, diga “não é possível confirmar pela foto”.

FORMATO DO RELATÓRIO (obrigatório e nesta ordem):

1) RESUMO EXECUTIVO (3 a 6 linhas)
- O que está bom + o que está travando vendas + maior oportunidade imediata.

2) NOTAS (0 a 10)
- Nota geral
- Sub-notas: Visibilidade, Organização, Planograma, Zonas, Preço/Comunicação, Sortimento

3) DIAGNÓSTICO COM EVIDÊNCIAS
- Pontos fortes (com “por quê”)
- Pontos críticos (com “por quê”)

4) O QUE FAZER AGORA (0–7 dias) — 5 ações
Para cada ação: (a) o que fazer, (b) como fazer em passos, (c) resultado esperado.

5) O QUE FAZER EM 30 DIAS — melhorias estruturais
- Materiais, comunicação, reposição, padronização.

6) PLANOGRAMA TEXTUAL (onde cada tipo de produto deve ficar)
- ZONAS:
  • Centro/altura dos olhos (zona quente)
  • Laterais (zona média)
  • Base (zona fria)
  • Topo (exposição/impacto)
- Diga onde colocar: best sellers, lançamentos, premium, promoções, itens volumosos, itens de impulso.
- Se houver linhas/categorias visíveis, proponha a árvore: Categoria → Subcategoria → Marca → Tamanho.

7) CHECKLIST DE AUDITORIA (10 itens)
- Escrito para promotor usar em campo.

8) IMPACTO ESTIMADO EM VENDAS (faixa)
- Estime uplift mínimo e máximo total (ex.: 5% a 10%)
- Explique as hipóteses em 3 bullets.

IMPORTANTE:
- NÃO coloque JSON no meio do texto.
- No FINAL, retorne APENAS um bloco <JSON>...</JSON> com este formato:

<JSON>
{{
  "nota_geral": 0,
  "sub_notas": {{
    "visibilidade_impacto": 0,
    "organizacao_limpeza": 0,
    "planograma_blocagem": 0,
    "zonas_atencao": 0,
    "precos_comunicacao": 0,
    "sortimento_ruido": 0
  }},
  "uplist_percent_min": 0,
  "uplist_percent_max": 0
}}
</JSON>

Contexto adicional (se houver):
{contexto}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagem_base64}"}}
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=1600
        )

        raw_text = response.choices[0].message.content or ""
        payload = _extract_json(raw_text)

        texto_limpo = _remove_json_from_text(raw_text)

        return {
            "total_linhas": 1,
            "analise": texto_limpo,      # ✅ SEM JSON, SEM inglês (pelo prompt)
            "json_graficos": payload     # ✅ só pra gerar gráficos
        }
