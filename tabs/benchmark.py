"""Onglet Benchmark -- le composite, et ce qu'il mesure reellement."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import viz
from core.benchmark import COMPONENTS, REBALANCING, validity_checks


def render() -> None:
    st.header("Benchmark hybride")
    st.caption("Il ne se choisit pas, il se déduit de l'allocation : mêmes "
               "poids, mêmes indices filtrés, même devise, même politique de "
               "couverture. La seule différence — il est purement passif.")

    df = pd.DataFrame([
        {"Poids": c.weight, "Indice": c.index_name,
         "Couverture": c.hedge, "Filtre ESG": "oui" if c.esg else "—"}
        for c in COMPONENTS]).sort_values("Poids", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df.Indice, x=df.Poids, orientation="h",
        marker=dict(color=viz.CATEGORICAL[0],
                    line=dict(color=viz.SURFACE, width=2)),
        text=[f"{v:.0%}" for v in df.Poids], textposition="outside",
        textfont=dict(color=viz.INK_2, size=11),
        hovertemplate="%{y}<br>%{x:.0%}<extra></extra>"))
    fig.update_layout(**viz.layout("Composition", height=430))
    fig.update_xaxes(tickformat=".0%", range=[0, 0.30])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width='stretch')

    st.dataframe(df.style.format({"Poids": "{:.0%}", "Couverture": "{:.0%}"}),
                 width='stretch', hide_index=True)
    st.caption(f"Rebalancement : {REBALANCING}.")

    st.markdown("## Ce qu'il mesure vraiment")
    st.info("""
Ses poids étant ceux de l'allocation stratégique, **l'écart stratégique est nul
par construction.** Ce n'est pas un défaut de conception, c'est le bon réglage :
le client a validé cette allocation, elle ne doit donc pas être une source de
sur- ou sous-performance mesurée.

Ce qui reste mesuré, c'est notre **exécution** — écarts tactiques dans les
bandes de ± 3 points, écart de suivi des fonds face à leur indice, timing de
rebalancement.
""")

    c = st.columns(3)
    c[0].metric("Écart de suivi médian", "1,04 %", delta="par an",
                delta_color="off")
    c[1].metric("90ᵉ centile", "1,58 %", delta="par an", delta_color="off")
    c[2].metric("Bandes tactiques", "± 3 pts", delta="budget total",
                delta_color="off")

    st.markdown("> *« Même en utilisant tout notre budget tactique, votre "
                "portefeuille reste à moins de 1,6 % d'écart annuel de sa "
                "référence. C'est la mesure honnête de notre marge de "
                "manœuvre — et donc de ce que vous nous payez pour faire. »*")

    st.markdown("## Critères de validité")
    st.dataframe(pd.DataFrame([
        {"Critère": lbl, "Vérifié": "oui" if ok else "non", "Détail": d}
        for lbl, ok, d in validity_checks()]),
        width='stretch', hide_index=True)

    st.markdown("## Double référence")
    st.markdown("""
| Référence | Rôle |
|---|---|
| **Relative** — le composite ci-dessus | Mesure la valeur ajoutée de gestion |
| **Absolue** — inflation constatée + 0 %, nette de frais et d'impôts | Mesure l'atteinte de l'objectif client |

Un benchmark relatif ne dit pas si l'objectif est atteint : **on peut battre
son indice et s'appauvrir.**
""")

    st.warning("""
**Piège d'historique à connaître.** La série « composition complète » démarre
en juin 2020 — inception du tracker crypto — donc **après le krach COVID**.
Elle affiche 7,32 % de rendement et 11,1 % de perte maximale, contre 5,62 % et
18,4 % hors crypto. Ce n'est pas un effet de la crypto, c'est un effet de
fenêtre. **Ligne de référence : hors crypto, 6,9 ans, 5,62 % brut, 4,77 % net.**
""")
