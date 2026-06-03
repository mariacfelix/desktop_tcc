import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Optional
from models.constants import CORES_CATEGORIA, COR_TEXTO, COR_SUBTEXTO, COR_PRIMARIA


def gerar_grafico_pizza(gastos: list) -> Optional[str]:
    if not gastos:
        return None

    totais = {}
    for g in gastos:
        cat = g.get("categoria") or "Outros"
        totais[cat] = totais.get(cat, 0) + (g.get("custo") or 0)

    if not totais or sum(totais.values()) == 0:
        return None

    labels, sizes, cores = [], [], []
    for cat, val in sorted(totais.items(), key=lambda x: -x[1]):
        labels.append(cat)
        sizes.append(val)
        cores.append(CORES_CATEGORIA.get(cat, "#696969"))

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    ax.pie(
        sizes, labels=None,
        autopct=lambda pct: f"{pct:.1f}%",
        colors=cores, startangle=140,
        wedgeprops=dict(width=0.6, edgecolor="none", linewidth=0),
        pctdistance=0.78,
        textprops={"color": COR_TEXTO, "fontsize": 8},
    )

    handles = [
        mpatches.Patch(color=cores[i], label=f"{labels[i]}  R${sizes[i]:,.2f}")
        for i in range(len(labels))
    ]
    ax.legend(
        handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5),
        fontsize=8, framealpha=0, labelcolor=COR_SUBTEXTO,
    )
    ax.set_title(
        f"Total: R${sum(sizes):,.2f}", color=COR_PRIMARIA,
        fontsize=11, fontweight="bold", pad=10,
    )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()