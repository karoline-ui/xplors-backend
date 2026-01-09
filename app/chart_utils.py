# backend/app/chart_utils.py
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _safe_num(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def gerar_graficos_imagem(payload: dict, out_dir: str) -> list[str]:
    """
    Gera PNGs para inserir no PDF:
    - Radar (sub_notas)
    - Barras uplift min/max

    Retorna lista de paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    charts = []

    sub = (payload or {}).get("sub_notas") or {}
    if isinstance(sub, dict) and len(sub) > 0:
        labels = ["Visibilidade", "Organização", "Planograma", "Zonas", "Preços", "Sortimento"]
        keys = [
            "visibilidade_impacto",
            "organizacao_limpeza",
            "planograma_blocagem",
            "zonas_atencao",
            "precos_comunicacao",
            "sortimento_ruido",
        ]
        values = [_safe_num(sub.get(k), 0.0) for k in keys]

        angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
        values_cycle = values + values[:1]
        angles_cycle = angles + angles[:1]

        plt.figure()
        ax = plt.subplot(111, polar=True)
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_rlabel_position(0)
        plt.xticks(angles, labels)
        ax.set_ylim(0, 10)

        ax.plot(angles_cycle, values_cycle)
        ax.fill(angles_cycle, values_cycle, alpha=0.25)

        plt.title("Score de Execução (0 a 10)")
        path = os.path.join(out_dir, "imagem_radar_scores.png")
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()
        charts.append(path)

    upl_min = _safe_num((payload or {}).get("uplist_percent_min"), 0.0)
    upl_max = _safe_num((payload or {}).get("uplist_percent_max"), 0.0)

    if upl_min > 0 or upl_max > 0:
        plt.figure()
        plt.bar(["Uplift mín", "Uplift máx"], [upl_min, upl_max])
        plt.title("Impacto estimado em vendas (faixa)")
        plt.ylabel("%")
        path = os.path.join(out_dir, "imagem_uplift_min_max.png")
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()
        charts.append(path)

    return charts


def kpis_from_imagem_payload(payload: dict) -> list[dict]:
    nota_geral = _safe_num((payload or {}).get("nota_geral"), 0.0)
    upl_min = _safe_num((payload or {}).get("uplist_percent_min"), 0.0)
    upl_max = _safe_num((payload or {}).get("uplist_percent_max"), 0.0)

    tone = "bad"
    if nota_geral >= 8:
        tone = "good"
    elif nota_geral >= 6:
        tone = "warn"

    kpis = [
        {"label": "Nota geral", "value": f"{nota_geral:.1f}/10", "tone": tone},
    ]

    if upl_min > 0 or upl_max > 0:
        kpis.append({"label": "Uplift estimado", "value": f"{upl_min:.0f}%–{upl_max:.0f}%", "tone": "purple"})

    sub = (payload or {}).get("sub_notas") or {}
    if isinstance(sub, dict) and len(sub) > 0:
        vals = [_safe_num(v, 0.0) for v in sub.values()]
        if vals:
            avg = sum(vals) / len(vals)
            kpis.append({"label": "Média sub-notas", "value": f"{avg:.1f}/10", "tone": "purple"})

    return kpis[:6]
