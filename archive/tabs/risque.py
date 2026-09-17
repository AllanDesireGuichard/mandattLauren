"""Onglet Risque -- crises nommees, distribution des pertes, temps sous l'eau."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import ips, viz

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent

CRISES = [
    ("Lehman et crise financière", 25.6, 12),
    ("Dette souveraine européenne", 6.8, 3),
    ("Choc COVID", 17.5, 5),
    ("Choc d'inflation 2022", 13.8, 17),
]


@st.cache_data
def _dd() -> pd.DataFrame:
    p = ROOT / "data" / "drawdown_distribution.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def render() -> None:
    st.header("Risque — ce que le client vivrait réellement")

    c = st.columns(4)
    c[0].metric("Perte P90 sur 12 mois", "13,8 %", delta="contrainte 15 %",
                delta_color="off")
    c[1].metric("P(perte > 15 %)", "9,1 %", delta="tolérance 10 %",
                delta_color="off")
    c[2].metric("Pire cas observé", "24,9 %", delta="2008",
                delta_color="off")
    c[3].metric("Temps en perte latente", "84,2 %", delta="du temps",
                delta_color="off")

    st.markdown("## Les crises qui ont eu lieu")
    df = pd.DataFrame(CRISES, columns=["Crise", "Perte max", "Récupération"])

    fig = go.Figure()
    colors = [viz.STATUS["critical"] if v > 15 else viz.CATEGORICAL[0]
              for v in df["Perte max"]]
    fig.add_trace(go.Bar(
        y=df.Crise, x=df["Perte max"], orientation="h",
        marker=dict(color=colors, line=dict(color=viz.SURFACE, width=2)),
        text=[f"{v:.1f} %".replace(".", ",") for v in df["Perte max"]],
        textposition="outside", textfont=dict(color=viz.INK_2, size=11),
        hovertemplate="%{y}<br>perte %{x:.1f} %<extra></extra>"))
    fig.add_vline(x=15, line=dict(color=viz.INK_2, width=1, dash="dash"))
    fig.add_annotation(x=15, y=3.5, text="contrainte 15 %", showarrow=False,
                       xshift=48, font=dict(color=viz.INK_2, size=11))
    fig.update_layout(**viz.layout("Perte maximale par épisode", height=300))
    fig.update_xaxes(ticksuffix=" %", range=[0, 32])
    st.plotly_chart(fig, width='stretch')

    st.warning("**Deux des quatre crises auraient dépassé la contrainte de 15 %.** "
               "C'est à dire au client au moment de la décision, pas le jour où "
               "cela se produit.")

    st.markdown("### Le point le plus contre-intuitif")
    st.markdown("""
Le choc de 2022 est **moins profond** que le COVID — 13,8 % contre 17,5 % —
mais **trois fois plus long à récupérer** : 17 mois contre 5.

Parce qu'en 2020 il y a eu un sauvetage monétaire, et qu'en 2022 la cause de
la baisse était précisément la fin de ce sauvetage.

> **Un client ne vit pas la profondeur d'une perte, il vit sa durée.**
""")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=df.Crise, x=df["Récupération"], orientation="h",
        marker=dict(color=viz.CATEGORICAL[2],
                    line=dict(color=viz.SURFACE, width=2)),
        text=[f"{v} mois" for v in df["Récupération"]], textposition="outside",
        textfont=dict(color=viz.INK_2, size=11),
        hovertemplate="%{y}<br>%{x} mois<extra></extra>"))
    fig2.update_layout(**viz.layout("Temps de retour au point haut", height=290))
    fig2.update_xaxes(ticksuffix=" mois", range=[0, 22])
    st.plotly_chart(fig2, width='stretch')

    st.markdown("## Distribution des pertes sur 12 mois glissants")
    d = _dd()
    if d.empty:
        st.info("Lancer `scripts/stress_tests.py` pour alimenter cette section.")
        return

    x = d["drawdown_12m"] * 100
    fig3 = go.Figure()
    fig3.add_trace(go.Histogram(
        x=x, nbinsx=60,
        marker=dict(color=viz.CATEGORICAL[0],
                    line=dict(color=viz.SURFACE, width=1)),
        hovertemplate="perte %{x:.1f} %<br>%{y} fenêtres<extra></extra>"))
    fig3.add_vline(x=15, line=dict(color=viz.STATUS["critical"], width=2))
    fig3.add_annotation(x=15, y=1, yref="paper", text="contrainte 15 %",
                        showarrow=False, xshift=54, yshift=-6,
                        font=dict(color=viz.STATUS["critical"], size=11))
    fig3.update_layout(**viz.layout(
        "5 438 fenêtres de 12 mois observées sur 21,8 ans", height=340))
    fig3.update_xaxes(ticksuffix=" %", title="Perte maximale sur la fenêtre")
    fig3.update_yaxes(title="Nombre de fenêtres")
    st.plotly_chart(fig3, width='stretch')

    q = pd.DataFrame({
        "Centile": ["50", "75", "90", "95", "99", "pire"],
        "Perte": [x.quantile(.5), x.quantile(.75), x.quantile(.9),
                  x.quantile(.95), x.quantile(.99), x.max()],
    })
    st.dataframe(q.style.format({"Perte": "{:.1f} %"}),
                 width='stretch', hide_index=True)
