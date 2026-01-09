"""
PROCESSADOR DE PLANILHAS EXCEL (Xplors) - versão turbinada (KPIs + Gráficos inteligentes)

- Lê Excel
- Identifica tipo (concorrência / merchandising / preço)
- Extrai KPIs úteis
- Gera gráficos (PNG) contextualizados para o PDF:
  - Merchandising: conformidade por item/loja/região/promotor
  - Preço: distribuição, top outliers, média por categoria, dif % vs concorrência (se existir)
  - Concorrência: top ações/concorrentes e recortes por região (se existir)
"""

import os
import re
from pathlib import Path
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


# =========================
# LEITURA / TIPO
# =========================
def processar_planilha(filepath: str) -> pd.DataFrame:
    try:
        print(f"📖 Lendo planilha: {filepath}")

        if filepath.endswith(".xlsx"):
            df = pd.read_excel(filepath, engine="openpyxl")
        else:
            df = pd.read_excel(filepath, engine="xlrd")

        print(f"✅ Planilha lida: {len(df)} linhas, {len(df.columns)} colunas")
        df = df.dropna(how="all")
        df.columns = df.columns.astype(str).str.strip()
        return df

    except Exception as e:
        print(f"❌ Erro ao ler planilha: {str(e)}")
        raise Exception(f"Erro ao processar planilha: {str(e)}")


def identificar_tipo(df: pd.DataFrame) -> str:
    total_respostas = len(df)
    print(f"🔍 Total de respostas: {total_respostas}")

    if "Tipo" in df.columns and len(df) > 0:
        tipo_coluna = str(df["Tipo"].iloc[0]).lower()
        if "concorrência" in tipo_coluna or "concorrencia" in tipo_coluna:
            return "concorrencia"
        elif "merchandising" in tipo_coluna:
            return "merchandising"
        elif "preço" in tipo_coluna or "preco" in tipo_coluna:
            return "preco"

    # fallback por volume (seu padrão)
    if 50 <= total_respostas <= 80:
        return "concorrencia"
    elif 1100 <= total_respostas <= 1600:
        return "merchandising"
    elif 1800 <= total_respostas <= 2500:
        return "preco"

    print("⚠️ Não foi possível identificar tipo exato. Usando 'merchandising' como padrão.")
    return "merchandising"


def extrair_metricas_basicas(df: pd.DataFrame) -> dict:
    return {
        "total_respostas": len(df),
        "total_colunas": len(df.columns),
        "colunas": df.columns.tolist(),
        "primeiras_linhas": df.head(3).to_dict("records")
    }


# =========================
# HELPERS (detecção inteligente)
# =========================
def _norm(s: str) -> str:
    s = str(s or "")
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _find_col_by_keywords(df: pd.DataFrame, keywords: list[str]) -> str | None:
    """
    Procura a melhor coluna cujo nome contenha algum keyword.
    """
    cols = df.columns.tolist()
    scored = []
    for c in cols:
        name = _norm(c)
        score = 0
        for kw in keywords:
            if kw in name:
                score += 1
        if score > 0:
            scored.append((score, c))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _pick_best_categorical(df: pd.DataFrame, exclude: set[str] | None = None) -> str | None:
    exclude = exclude or set()
    candidates = []
    for c in df.columns:
        if c in exclude:
            continue
        s = df[c]
        nunique = s.nunique(dropna=True)
        if 2 <= nunique <= 30:
            candidates.append((c, nunique))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _pick_best_numeric(df: pd.DataFrame, keywords: list[str]) -> str | None:
    """
    Tenta achar uma coluna numérica por keywords no nome.
    """
    cols = [c for c in df.columns if any(k in _norm(c) for k in keywords)]
    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) >= 10:
            return c
    # fallback: qualquer numérica com variância
    for c in df.columns:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) >= 10 and s.nunique() > 5:
            return c
    return None


def _save_fig(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _safe_filename(s: str) -> str:
    s = str(s or "chart")
    s = re.sub(r"[^\w\-\.]+", "_", s, flags=re.UNICODE)
    return s[:120]


def _tone_pct(p: float) -> str:
    if p >= 80:
        return "good"
    if p >= 60:
        return "warn"
    return "bad"


# =========================
# DETECÇÃO DE DIMENSÕES
# =========================
def _detectar_dimensoes(df: pd.DataFrame) -> dict:
    """
    Retorna um dict com possíveis colunas de dimensão.
    """
    dim = {
        "loja": _find_col_by_keywords(df, ["loja", "pdv", "ponto de venda", "filial", "store"]),
        "regiao": _find_col_by_keywords(df, ["regiao", "região", "uf", "estado", "cidade", "bairro", "zona"]),
        "promotor": _find_col_by_keywords(df, ["promotor", "auditor", "pesquisador", "responsavel", "responsável", "equipe"]),
        "categoria": _find_col_by_keywords(df, ["categoria", "linha", "family", "familia", "segmento"]),
        "marca": _find_col_by_keywords(df, ["marca", "brand"]),
        "produto": _find_col_by_keywords(df, ["produto", "sku", "item", "descricao", "descrição", "ean", "codigo", "código"]),
        "concorrente": _find_col_by_keywords(df, ["concorrente", "competidor", "competitor", "rede"]),
        "acao": _find_col_by_keywords(df, ["acao", "ação", "atividade", "execucao", "execução", "observacao", "observação"])
    }
    return dim


# =========================
# CONFORMIDADE (SIM/NÃO/OK)
# =========================
def _detectar_colunas_yn(df: pd.DataFrame) -> list[str]:
    yn_cols = []
    for c in df.columns:
        s = df[c].astype(str).str.lower().str.strip()
        ratio = s.isin(["sim", "não", "nao", "yes", "no", "ok", "nok"]).mean()
        if ratio > 0.6:
            yn_cols.append(c)
    return yn_cols


def _row_conformidade(df: pd.DataFrame, yn_cols: list[str]) -> pd.Series:
    """
    Score por linha: % de itens OK (sim/yes/ok) dentre yn_cols.
    """
    if not yn_cols:
        return pd.Series([None] * len(df), index=df.index)

    ok_vals = {"sim", "yes", "ok"}
    mat = []
    for c in yn_cols:
        s = df[c].astype(str).str.lower().str.strip()
        mat.append(s.isin(ok_vals).astype(float))
    m = pd.concat(mat, axis=1)
    return m.mean(axis=1) * 100.0


# =========================
# PRINCIPAL: KPIs + GRÁFICOS
# =========================
def gerar_insumos_pdf_excel(df: pd.DataFrame, tipo: str, out_dir: str = "tmp_charts") -> dict:
    """
    Retorna dict p/ PDF:
      {
        "total_linhas": int,
        "kpis": [{"label","value","tone"}, ...],
        "charts": ["path1.png", ...]
      }
    """
    tipo = (tipo or "merchandising").lower()
    out_dir = str(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    total = len(df)
    dims = _detectar_dimensoes(df)

    kpis = [{"label": "Registros", "value": str(total), "tone": "purple"}]
    charts: list[str] = []

    # =========================
    # GRÁFICO BASE: Top 10 de uma dimensão “boa”
    # =========================
    prefer_order = [dims.get("loja"), dims.get("regiao"), dims.get("categoria"), dims.get("marca"), dims.get("produto")]
    col_top = next((c for c in prefer_order if c), None) or _pick_best_categorical(df)

    if col_top:
        vc = df[col_top].astype(str).value_counts().head(10)
        plt.figure()
        vc.sort_values().plot(kind="barh")
        plt.title(f"Top 10 - {col_top}")
        plt.xlabel("Ocorrências")
        path = os.path.join(out_dir, f"{tipo}_top10_{_safe_filename(col_top)}.png")
        _save_fig(path)
        charts.append(path)

        kpis.append({"label": f"Variedade ({col_top})", "value": str(df[col_top].nunique(dropna=True)), "tone": "purple"})

    # =========================
    # MERCHANDISING: conformidade inteligente
    # =========================
    if tipo == "merchandising":
        yn_cols = _detectar_colunas_yn(df)

        if yn_cols:
            # conformidade por item (pior -> melhor)
            scores = []
            for c in yn_cols[:30]:
                s = df[c].astype(str).str.lower().str.strip()
                ok = s.isin(["sim", "yes", "ok"]).mean() * 100.0
                scores.append((c, ok))

            avg_ok = sum(v for _, v in scores) / max(len(scores), 1)
            kpis.append({"label": "Conformidade média", "value": f"{avg_ok:.0f}%", "tone": _tone_pct(avg_ok)})

            # % lojas críticas (se houver loja)
            row_score = _row_conformidade(df, yn_cols)
            crit = (row_score < 60).mean() * 100.0
            if pd.notna(crit):
                kpis.append({"label": "Execução crítica", "value": f"{crit:.0f}%", "tone": "bad" if crit >= 25 else "warn"})

            # gráfico: conformidade por item (10 piores)
            scores.sort(key=lambda x: x[1])
            labels = [a for a, _ in scores[:12]]
            vals = [b for _, b in scores[:12]]

            plt.figure()
            plt.barh(labels, vals)
            plt.title("Itens com pior conformidade (SIM/OK)")
            plt.xlabel("% OK")
            path = os.path.join(out_dir, f"{tipo}_pior_conformidade_itens.png")
            _save_fig(path)
            charts.append(path)

            # por loja / região / promotor (se existir)
            for dim_name in ["loja", "regiao", "promotor"]:
                col = dims.get(dim_name)
                if col:
                    tmp = df.copy()
                    tmp["_score"] = row_score
                    g = tmp.groupby(col, dropna=True)["_score"].mean().dropna()
                    if len(g) >= 3:
                        g = g.sort_values().head(12)  # mostra os piores (mais útil)
                        plt.figure()
                        g.sort_values().plot(kind="barh")
                        plt.title(f"Conformidade média (pior) - por {col}")
                        plt.xlabel("% OK")
                        path = os.path.join(out_dir, f"{tipo}_conformidade_por_{_safe_filename(col)}.png")
                        _save_fig(path)
                        charts.append(path)

        else:
            kpis.append({"label": "Conformidade", "value": "Não detectada", "tone": "warn"})

    # =========================
    # PREÇO: gráficos mais úteis
    # =========================
    if tipo == "preco":
        col_preco = _pick_best_numeric(df, ["preço", "preco", "price", "valor", "vlr", "rs", "r$"])
        if col_preco:
            s = pd.to_numeric(df[col_preco], errors="coerce").dropna()
            if len(s) >= 10:
                kpis.append({"label": "Preço médio", "value": f"{s.mean():.2f}", "tone": "purple"})
                kpis.append({"label": "Preço min", "value": f"{s.min():.2f}", "tone": "purple"})
                kpis.append({"label": "Preço max", "value": f"{s.max():.2f}", "tone": "purple"})

                # histograma
                plt.figure()
                plt.hist(s, bins=20)
                plt.title(f"Distribuição de preços ({col_preco})")
                plt.xlabel("Preço")
                plt.ylabel("Frequência")
                path = os.path.join(out_dir, f"{tipo}_hist_{_safe_filename(col_preco)}.png")
                _save_fig(path)
                charts.append(path)

                # top 10 maiores preços (outliers)
                top = s.sort_values(ascending=False).head(10)
                plt.figure()
                top.sort_values().plot(kind="barh")
                plt.title(f"Top 10 maiores preços ({col_preco})")
                plt.xlabel("Preço")
                path = os.path.join(out_dir, f"{tipo}_top10_maiores_precos.png")
                _save_fig(path)
                charts.append(path)

                # média por categoria (se existir)
                col_cat = dims.get("categoria") or dims.get("marca") or None
                if col_cat:
                    tmp = df.copy()
                    tmp["_preco"] = pd.to_numeric(tmp[col_preco], errors="coerce")
                    g = tmp.groupby(col_cat)["_preco"].mean().dropna()
                    if len(g) >= 3:
                        g = g.sort_values(ascending=False).head(12)
                        plt.figure()
                        g.sort_values().plot(kind="barh")
                        plt.title(f"Preço médio por {col_cat} (Top 12)")
                        plt.xlabel("Preço médio")
                        path = os.path.join(out_dir, f"{tipo}_preco_medio_por_{_safe_filename(col_cat)}.png")
                        _save_fig(path)
                        charts.append(path)

        # se existir coluna “concorrente” de preço (muito comum)
        # heurística: procura duas colunas numéricas com "preco" no nome
        price_like = [c for c in df.columns if any(k in _norm(c) for k in ["preço", "preco", "price"])]
        num_candidates = []
        for c in price_like:
            s = pd.to_numeric(df[c], errors="coerce").dropna()
            if len(s) >= 10:
                num_candidates.append(c)

        if len(num_candidates) >= 2:
            # tenta escolher "nosso" e "concorrente"
            nosso = next((c for c in num_candidates if any(k in _norm(c) for k in ["nosso", "xplors", "empresa", "interno"])), num_candidates[0])
            conc = next((c for c in num_candidates if any(k in _norm(c) for k in ["concorr", "compet", "rival"])), None)
            if conc is None:
                # pega outra diferente
                conc = next((c for c in num_candidates if c != nosso), None)

            if conc and conc != nosso:
                a = pd.to_numeric(df[nosso], errors="coerce")
                b = pd.to_numeric(df[conc], errors="coerce")
                dif = (a - b) / b.replace(0, pd.NA) * 100.0
                dif = dif.dropna()
                if len(dif) >= 10:
                    # KPI: índice médio
                    idx = (a / b.replace(0, pd.NA)).dropna()
                    if len(idx) >= 10:
                        idx_medio = idx.mean()
                        kpis.append({"label": "Índice vs conc.", "value": f"{idx_medio:.2f}x", "tone": "purple"})

                    # gráfico: top 10 maiores diferenças %
                    topdif = dif.sort_values(ascending=False).head(10)
                    plt.figure()
                    topdif.sort_values().plot(kind="barh")
                    plt.title(f"Top 10: % acima do concorrente ({nosso} vs {conc})")
                    plt.xlabel("Diferença %")
                    path = os.path.join(out_dir, f"{tipo}_top10_dif_vs_conc.png")
                    _save_fig(path)
                    charts.append(path)

    # =========================
    # CONCORRÊNCIA: top ações / top concorrentes / por região
    # =========================
    if tipo == "concorrencia":
        col_acao = dims.get("acao") or _find_col_by_keywords(df, ["acao", "ação", "atividade", "observacao", "observação", "descricao", "descrição"])
        col_conc = dims.get("concorrente")

        if col_acao:
            vc = df[col_acao].astype(str).value_counts().head(10)
            plt.figure()
            vc.sort_values().plot(kind="barh")
            plt.title(f"Top 10 ações ({col_acao})")
            plt.xlabel("Ocorrências")
            path = os.path.join(out_dir, f"{tipo}_top10_acoes.png")
            _save_fig(path)
            charts.append(path)
            kpis.append({"label": "Ações únicas", "value": str(df[col_acao].nunique(dropna=True)), "tone": "purple"})

        if col_conc:
            vc = df[col_conc].astype(str).value_counts().head(10)
            plt.figure()
            vc.sort_values().plot(kind="barh")
            plt.title(f"Top 10 concorrentes ({col_conc})")
            plt.xlabel("Ocorrências")
            path = os.path.join(out_dir, f"{tipo}_top10_concorrentes.png")
            _save_fig(path)
            charts.append(path)
            kpis.append({"label": "Concorrentes", "value": str(df[col_conc].nunique(dropna=True)), "tone": "purple"})

        # por região
        col_reg = dims.get("regiao")
        if col_reg and col_acao:
            tmp = df.copy()
            tmp["_one"] = 1
            g = tmp.groupby(col_reg)["_one"].sum().sort_values(ascending=False).head(12)
            if len(g) >= 3:
                plt.figure()
                g.sort_values().plot(kind="barh")
                plt.title(f"Volume de ações por {col_reg} (Top 12)")
                plt.xlabel("Ocorrências")
                path = os.path.join(out_dir, f"{tipo}_acoes_por_{_safe_filename(col_reg)}.png")
                _save_fig(path)
                charts.append(path)

    # limita para não estourar PDF
    return {
        "total_linhas": total,
        "kpis": kpis[:6],
        "charts": charts[:8]
    }
