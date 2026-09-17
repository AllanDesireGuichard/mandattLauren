"""Onglet Fiscalite -- friction annuelle derivee et localisation des actifs."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import ips, viz
from core.tax import (LOCATION_CONSTRAINTS, RECOMMENDED_LOCATION,
                      portfolio_drag)


def render() -> None:
    st.header("Fiscalité annuelle et localisation des actifs")

    modes = [("Assurance-vie luxembourgeoise", "av"),
             ("Compte-titres, supports capitalisants", "cto_acc"),
             ("Compte-titres, supports distribuants", "cto_dist")]
    rows = []
    for lbl, m in modes:
        d = portfolio_drag(m)
        rows.append({"Régime": lbl, "Friction annuelle": d,
                     "Rendement brut requis":
                         ips.INFLATION_TARGET + ips.TOTAL_FEES + d})
    df = pd.DataFrame(rows)

    c = st.columns(3)
    for i, r in df.iterrows():
        c[i].metric(r["Régime"].split(",")[0],
                    f"{r['Friction annuelle']:.2f} %".replace(".", ","))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Régime"], x=df["Friction annuelle"], orientation="h",
        marker=dict(color=[viz.CATEGORICAL[0], viz.CATEGORICAL[1],
                           viz.STATUS["critical"]],
                    line=dict(color=viz.SURFACE, width=2)),
        text=[f"{v:.2%}" for v in df["Friction annuelle"]],
        textposition="outside", textfont=dict(color=viz.INK_2, size=11),
        hovertemplate="%{y}<br>friction %{x:.2%}<extra></extra>"))
    fig.update_layout(**viz.layout(
        "Friction fiscale annuelle du portefeuille", height=280))
    fig.update_xaxes(tickformat=".2%", range=[0, 0.016])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width='stretch')

    st.dataframe(df.style.format({"Friction annuelle": "{:.2%}",
                                  "Rendement brut requis": "{:.2%}"}),
                 width='stretch', hide_index=True)

    st.markdown("## Où se trouve vraiment l'argent")
    st.info("""
Entre une structure optimisée et un compte-titres **correctement géré**,
l'écart est de **38 points de base** par an. C'est réel, ce n'est pas décisif.

Entre un compte-titres correctement géré et un compte-titres **négligent** —
des fonds qui distribuent des dividendes taxés chaque année au lieu de les
réinvestir — l'écart est de **60 points de base**. Là c'est considérable, et
c'est **gratuit à corriger** : une question de soin, pas d'ingénierie.

Mais le vrai sujet fiscal n'est pas annuel, il est **successoral** : 50 M€ de
plus pour les enfants, soit neuf fois le gain de toute l'optimisation
d'allocation. Voir l'onglet Transmission.
""")

    st.markdown("## Localisation des actifs")
    st.warning("""
**Appliqué brut, le calcul conclut « tout en assurance-vie »** — ses 0,25 % de
frais battent les 0,63 % du compte-titres sur chaque classe. C'est le même type
de sortie dégénérée que l'optimiseur d'allocation : correcte au regard des
données, fausse au regard du mandat.
""")

    st.dataframe(pd.DataFrame([
        {"Contrainte": k.capitalize(), "Ce qu'elle impose": v}
        for k, v in LOCATION_CONSTRAINTS.items()]),
        width='stretch', hide_index=True)

    st.markdown("### Répartition retenue")
    lab = list(RECOMMENDED_LOCATION)
    val = list(RECOMMENDED_LOCATION.values())
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=lab, y=val,
        marker=dict(color=viz.CATEGORICAL[:2],
                    line=dict(color=viz.SURFACE, width=2)),
        text=[f"{v:.0%}" for v in val], textposition="inside",
        textfont=dict(color="#fff", size=15),
        hovertemplate="%{x}<br>%{y:.0%}<extra></extra>"))
    fig2.update_layout(**viz.layout(height=280))
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, width='stretch')
