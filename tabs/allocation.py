"""Onglet Allocation -- la SAA, et ce que l'optimiseur voulait faire."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import ips, viz

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@st.cache_data
def _opt() -> pd.DataFrame:
    p = ROOT / "data" / "saa_optimized.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def render() -> None:
    st.header("Allocation stratégique")

    saa = ips.SAA_INDICATIVE
    df = pd.DataFrame({
        "Classe": [viz.LABEL[k] for k in saa],
        "Famille": [viz.group_of(k) for k in saa],
        "Poids": list(saa.values()),
    }).sort_values("Poids", ascending=True)

    fig = go.Figure()
    for fam in viz.GROUPS:
        sub = df[df.Famille == fam]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(
            y=sub.Classe, x=sub.Poids, name=fam, orientation="h",
            marker=dict(color=viz.GROUP_COLOR[fam],
                        line=dict(color=viz.SURFACE, width=2)),
            text=[f"{v:.0%}" for v in sub.Poids], textposition="outside",
            textfont=dict(color=viz.INK_2, size=11),
            hovertemplate="%{y}<br>%{x:.0%}<extra></extra>"))
    fig.update_layout(**viz.layout("Poids cibles par classe d'actifs",
                                   height=430, barmode="stack"))
    fig.update_xaxes(tickformat=".0%", range=[0, 0.30])
    st.plotly_chart(fig, width='stretch')

    cols = st.columns(4)
    for i, (fam, members) in enumerate(viz.GROUPS.items()):
        w = sum(saa[m] for m in members)
        cols[i].metric(fam, f"{w:.0%}")

    st.markdown("## Ce que l'optimiseur voulait faire, et pourquoi nous ne l'avons pas suivi")
    o = _opt()
    if o.empty:
        st.info("Lancer `scripts/optimize_saa.py` pour alimenter cette section.")
        return

    o = o.copy()
    o["Classe"] = o["classe"].map(viz.LABEL)
    o = o.sort_values("libre", ascending=False)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=o.Classe, y=o["libre"], name="Optimisation libre",
        marker=dict(color=viz.CATEGORICAL[1],
                    line=dict(color=viz.SURFACE, width=2)),
        hovertemplate="%{x}<br>libre %{y:.1%}<extra></extra>"))
    fig2.add_trace(go.Bar(
        x=o.Classe, y=o["retenu"], name="Retenu (sous contraintes)",
        marker=dict(color=viz.CATEGORICAL[0],
                    line=dict(color=viz.SURFACE, width=2)),
        hovertemplate="%{x}<br>retenu %{y:.1%}<extra></extra>"))
    fig2.update_layout(**viz.layout(height=400, barmode="group",
                                    bargap=0.25, bargroupgap=0.08))
    fig2.update_yaxes(tickformat=".0%")
    fig2.update_xaxes(tickangle=-30)
    st.plotly_chart(fig2, width='stretch')

    st.markdown("""
L'optimisation libre donne une allocation **mathématiquement optimale et
pratiquement inutilisable** : 28 % d'infrastructure — un seul secteur —,
0,8 % d'or, et zéro obligation d'État. Chacune de ces décisions est correcte
au regard des données fournies, et fausse au regard du mandat.

Les contraintes de second niveau encodent des risques que la matrice de
covariance ne peut pas voir.
""")

    st.dataframe(pd.DataFrame([
        {"Contrainte": "Infrastructure ≤ 10 %",
         "Ce qu'elle achète": "Un seul secteur ; le support filtré ESG a 3,1 ans "
                              "et une capacité limitée. Risque de concentration "
                              "et risque d'exécution."},
        {"Contrainte": "Or ≥ 6 %",
         "Ce qu'elle achète": "Seule brique dont la corrélation aux actions baisse "
                              "sous stress (0,07 → −0,07 en 2022). Une covariance "
                              "pleine période efface ce comportement."},
        {"Contrainte": "Souverain EUR ≥ 8 %",
         "Ce qu'elle achète": "Nos hypothèses sont calées sur un seul régime. Elles "
                              "ne tarifient pas la récession — seul scénario où le "
                              "souverain protège."},
        {"Contrainte": "Actions développées ≥ 20 %",
         "Ce qu'elle achète": "Liquidité et capacité pour un mandat de 100 M€."},
        {"Contrainte": "Crypto = 2 %",
         "Ce qu'elle achète": "Décision de gouvernance client, pas une sortie "
                              "d'optimisation."},
    ]), width='stretch', hide_index=True)

    st.caption("Effet mesuré : l'instabilité moyenne des poids entre tirages "
               "passe de 3,8 % à 2,3 %. Le portefeuille contraint est plus "
               "prudent **et** plus reproductible.")
