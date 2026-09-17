"""
Genere les graphiques du deck, en PNG haute resolution.

Meme palette que l'application (core/viz.py), validee par le script du
referentiel dataviz. Regles suivies : marques fines, grille recessive, pas de
legende pour une serie unique, etiquettes directes plutot qu'un nombre sur
chaque point, texte en jetons de texte et jamais en couleur de serie.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips, viz                # noqa: E402
from core.benchmark import COMPONENTS    # noqa: E402
from core.cma import portfolio_return    # noqa: E402
from core.succession import droits_donation_np  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
DATA = Path(__file__).resolve().parent.parent / "data"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": viz.GRID, "axes.labelcolor": viz.INK_2,
    "text.color": viz.INK, "xtick.color": viz.INK_2, "ytick.color": viz.INK_2,
    "axes.grid": True, "grid.color": viz.GRID, "grid.linewidth": .7,
    "axes.axisbelow": True, "figure.dpi": 200,
    "savefig.transparent": True, "savefig.bbox": "tight",
})
C = viz.CATEGORICAL


def _clean(ax, spines=("top", "right")):
    for s in spines:
        ax.spines[s].set_visible(False)
    return ax


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", pad_inches=0.12)
    plt.close(fig)
    print(f"  {name}.png")


def allocation():
    saa = ips.SAA_INDICATIVE
    order = sorted(saa, key=lambda k: -saa[k])
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = np.arange(len(order))
    cols = [viz.color_of(k) for k in order]
    ax.barh(y, [saa[k] * 100 for k in order], color=cols, height=.68,
            edgecolor="white", linewidth=1.6)
    for i, k in enumerate(order):
        ax.text(saa[k] * 100 + .5, i, f"{saa[k]:.0%}", va="center",
                fontsize=10.5, color=viz.INK_2)
    ax.set_yticks(y, [viz.LABEL[k] for k in order])
    ax.invert_yaxis()
    ax.set_xlim(0, 30)
    ax.set_xlabel("Poids cible (%)")
    ax.grid(axis="y", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in C[:4]]
    ax.legend(handles, list(viz.GROUPS), frameon=False, ncol=4,
              loc="lower right", bbox_to_anchor=(1, -.22), fontsize=10)
    _clean(ax)
    save(fig, "allocation")


def faisabilite():
    xs = np.arange(0, 6.25, .25) / 100
    exp = [portfolio_return(ips.SAA_INDICATIVE, x) * 100 for x in xs]
    req = [(x + ips.TOTAL_FEES + ips.TAX_DRAG_STRUCTURED) * 100 for x in xs]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.plot(xs * 100, exp, color=C[0], lw=2.2, label="Rendement attendu")
    ax.plot(xs * 100, req, color=C[1], lw=2.2, label="Seuil requis")
    ax.axvline(4, color=viz.INK_2, lw=1, ls=":")
    ax.annotate("hypothèse client", (4, max(exp)), xytext=(6, -4),
                textcoords="offset points", fontsize=10, color=viz.INK_2)
    i = int(np.argmin(np.abs(np.array(exp) - np.array(req))))
    ax.plot(xs[i] * 100, exp[i], "o", ms=8, color=viz.INK, zorder=5)
    ax.annotate(f"croisement\n{xs[i]*100:.1f} %".replace(".", ","),
                (xs[i] * 100, exp[i]), xytext=(-70, 10),
                textcoords="offset points", fontsize=10, color=viz.INK)
    ax.set_xlabel("Inflation annuelle (%)")
    ax.set_ylabel("Rendement brut (%)")
    ax.legend(frameon=False, loc="upper left", fontsize=10.5)
    _clean(ax)
    save(fig, "faisabilite")


def crises():
    noms = ["Lehman\n2007-2009", "Dette souveraine\n2011", "COVID\n2020",
            "Inflation\n2022"]
    pertes, recup = [25.6, 6.8, 17.5, 13.8], [12, 3, 5, 17]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1))
    cols = [viz.STATUS["critical"] if p > 15 else C[0] for p in pertes]
    axes[0].bar(noms, pertes, color=cols, width=.6, edgecolor="white", lw=1.6)
    axes[0].axhline(15, color=viz.INK_2, ls="--", lw=1.1)
    axes[0].annotate("contrainte 15 %", (3.4, 15.6), ha="right", fontsize=10,
                     color=viz.INK_2)
    for i, p in enumerate(pertes):
        axes[0].text(i, p + .7, f"{p:.1f}".replace(".", ",") + " %", ha="center",
                     fontsize=10.5, color=viz.INK_2)
    axes[0].set_ylim(0, 31); axes[0].set_ylabel("Perte maximale (%)")
    axes[0].grid(axis="x", visible=False); _clean(axes[0])

    axes[1].bar(noms, recup, color=C[2], width=.6, edgecolor="white", lw=1.6)
    for i, r in enumerate(recup):
        axes[1].text(i, r + .4, f"{r} mois", ha="center", fontsize=10.5,
                     color=viz.INK_2)
    axes[1].set_ylim(0, 20); axes[1].set_ylabel("Retour au point haut (mois)")
    axes[1].grid(axis="x", visible=False); _clean(axes[1])
    save(fig, "crises")


def distribution():
    p = DATA / "drawdown_distribution.csv"
    if not p.exists():
        return
    x = pd.read_csv(p)["drawdown_12m"] * 100
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.hist(x, bins=64, color=C[0], edgecolor="white", linewidth=.5)
    ax.axvline(15, color=viz.STATUS["critical"], lw=2)
    ax.annotate("contrainte 15 %", (15.4, ax.get_ylim()[1] * .92), fontsize=10.5,
                color=viz.STATUS["critical"])
    ax.axvline(x.quantile(.9), color=viz.INK_2, lw=1.2, ls="--")
    ax.annotate(f"P90  {x.quantile(.9):.1f} %".replace(".", ","),
                (x.quantile(.9) - .4, ax.get_ylim()[1] * .92), ha="right",
                fontsize=10.5, color=viz.INK_2)
    ax.set_xlabel("Perte maximale sur 12 mois glissants (%)")
    ax.set_ylabel("Nombre de fenêtres")
    ax.grid(axis="x", visible=False); _clean(ax)
    save(fig, "distribution")


def transmission():
    lab = ["Aucune\nstructuration", "Recommandée", "Maximale"]
    net, imp = [160, 210, 225], [130, 62, 38]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    ax.bar(lab, net, color=C[0], width=.55, edgecolor="white", lw=1.6,
           label="Net aux enfants")
    ax.bar(lab, imp, bottom=net, color=C[1], width=.55, edgecolor="white",
           lw=1.6, label="Impôt")
    for i, (n, m) in enumerate(zip(net, imp)):
        ax.text(i, n / 2, f"{n} M€", ha="center", va="center", color="white",
                fontsize=13, fontweight="bold")
        ax.text(i, n + m / 2, f"{m} M€", ha="center", va="center", color="white",
                fontsize=11.5)
    ax.set_ylabel("Patrimoine dans 25 ans (M€)")
    ax.legend(frameon=False, ncol=2, loc="upper left", fontsize=10.5)
    ax.set_ylim(0, 330); ax.grid(axis="x", visible=False); _clean(ax)
    save(fig, "transmission")


def leviers():
    lab = ["Optimisation\nd'allocation", "Dé-risquage\naprès stress tests",
           "STRUCTURATION\nfiscale"]
    val = [5.5, -7.4, 50]
    cols = [C[0], viz.STATUS["critical"], C[2]]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.bar(lab, val, color=cols, width=.5, edgecolor="white", lw=1.6)
    for i, v in enumerate(val):
        ax.text(i, v + (2 if v > 0 else -4),
                (f"{v:+.0f} M€" if abs(v) >= 20
                 else f"{v:+.1f} M€".replace(".", ",")),
                ha="center", fontsize=12, color=viz.INK,
                fontweight="bold" if abs(v) > 20 else "normal")
    ax.axhline(0, color=viz.INK_2, lw=1)
    ax.set_ylabel("Gain pour les enfants sur 25 ans (M€)")
    ax.set_ylim(-14, 60); ax.grid(axis="x", visible=False); _clean(ax)
    save(fig, "leviers")


def anniversaire():
    montant = 36e6
    ages = list(range(57, 66))
    d = [droits_donation_np(montant, a, 2)[0] / 1e6 for a in ages]
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    cols = [viz.STATUS["critical"] if a > 60 else C[0] for a in ages]
    ax.bar([str(a) for a in ages], d, color=cols, width=.6, edgecolor="white",
           lw=1.6)
    for i, v in enumerate(d):
        ax.text(i, v + .15, f"{v:.1f}".replace(".", ",") + " M€", ha="center",
                fontsize=10, color=viz.INK_2)
    top = max(d) * 1.52
    ax.set_ylim(0, top)
    # Cartouche place AU-DESSUS des barres : l'espace est cree par le ylim,
    # jamais pris sur la zone de trace.
    ax.annotate("", xy=(4, d[4] * 1.09), xytext=(2.2, top * .80),
                arrowprops=dict(arrowstyle="-|>", color=viz.STATUS["critical"],
                                lw=2.2, shrinkA=4, shrinkB=8,
                                connectionstyle="arc3,rad=-.15"))
    ax.text(1.9, top * .89, "+1,6 M€ en franchissant un seul anniversaire",
            ha="center", va="center", fontsize=12.5,
            color=viz.STATUS["critical"], fontweight="bold")
    ax.text(1.9, top * .805, "barème de l'art. 669 CGI : la nue-propriété "
            "taxable passe de 50 % à 60 %", ha="center", va="center",
            fontsize=9.5, color=viz.INK_2)
    ax.set_xlabel("Âge du donateur au jour de la donation")
    ax.set_ylabel("Droits de donation (M€)")
    ax.grid(axis="x", visible=False); _clean(ax)
    save(fig, "anniversaire")


def backtest():
    lab = ["Stratégie Lauren", "60/40 classique"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    for ax, (titre, vals, fmt, lim) in zip(axes, [
            ("Rendement annualisé", [5.75, 6.35], "{:.2f} %", 8),
            ("Perte maximale", [26.3, 32.5], "{:.1f} %", 40),
            ("Calmar", [0.22, 0.20], "{:.2f}", 0.30)]):
        ax.bar(lab, vals, color=[C[0], C[1]], width=.5, edgecolor="white",
               lw=1.6)
        for i, v in enumerate(vals):
            ax.text(i, v + lim * .03, fmt.format(v).replace(".", ","),
                    ha="center", fontsize=11.5, color=viz.INK_2)
        ax.set_title(titre, fontsize=12, color=viz.INK, pad=10)
        ax.set_ylim(0, lim); ax.grid(axis="x", visible=False)
        ax.tick_params(axis="x", labelsize=9.5); _clean(ax)
    save(fig, "backtest")


def benchmark_comp():
    comps = sorted(COMPONENTS, key=lambda c: -c.weight)
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    y = np.arange(len(comps))
    ax.barh(y, [c.weight * 100 for c in comps],
            color=[viz.color_of(c.saa_class) for c in comps], height=.66,
            edgecolor="white", lw=1.6)
    for i, c in enumerate(comps):
        ax.text(c.weight * 100 + .4, i, f"{c.weight:.0%}", va="center",
                fontsize=10, color=viz.INK_2)
    ax.set_yticks(y, [c.index_name[:46] for c in comps], fontsize=9.5)
    ax.invert_yaxis(); ax.set_xlim(0, 28)
    ax.set_xlabel("Poids dans le benchmark (%)")
    ax.grid(axis="y", visible=False); _clean(ax)
    save(fig, "benchmark")


def qualite():
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.9))
    axes[0].bar(["avant filtre", "après filtre"], [28.9, 1.6],
                color=[viz.STATUS["critical"], C[0]], width=.45,
                edgecolor="white", lw=1.6)
    for i, v in enumerate([28.9, 1.6]):
        axes[0].text(i, v + .8, f"{v:.1f}".replace(".", ",") + " %", ha="center",
                     fontsize=12, color=viz.INK_2)
    axes[0].set_title("Volatilité d'un ETF souverain 1-3 ans", fontsize=12,
                      color=viz.INK, pad=10)
    axes[0].set_ylabel("Volatilité annuelle (%)"); axes[0].set_ylim(0, 34)
    axes[0].grid(axis="x", visible=False); _clean(axes[0])

    etapes = ["Candidats", "Séries\nrécupérées", "Séries\nexploitables",
              "Supports\nretenus"]
    vals = [226, 187, 182, 48]
    axes[1].bar(etapes, vals, color=C[0], width=.55, edgecolor="white", lw=1.6)
    for i, v in enumerate(vals):
        axes[1].text(i, v + 5, str(v), ha="center", fontsize=12,
                     color=viz.INK_2)
    axes[1].set_title("Entonnoir de sélection", fontsize=12, color=viz.INK,
                      pad=10)
    axes[1].set_ylim(0, 260); axes[1].grid(axis="x", visible=False)
    axes[1].tick_params(axis="x", labelsize=9.5); _clean(axes[1])
    save(fig, "qualite")


if __name__ == "__main__":
    print("Génération des graphiques :")
    for f in (allocation, faisabilite, crises, distribution, transmission,
              leviers, anniversaire, backtest, benchmark_comp, qualite):
        f()
    print(f"\n-> {OUT}")
