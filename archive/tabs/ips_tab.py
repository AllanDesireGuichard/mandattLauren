"""Onglet Faisabilite -- l'IPS, et la sensibilite de l'objectif aux hypotheses."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from core import ips, viz
from core.cma import INFLATION_BASE, expected_returns, portfolio_return


def render() -> None:
    st.header("L'objectif est-il atteignable ?")

    with st.sidebar:
        st.subheader("Hypothèses")
        infl = st.slider("Inflation annuelle", 0.0, 6.0,
                         ips.INFLATION_TARGET * 100, 0.25, format="%.2f %%") / 100
        fee = st.slider("Frais de mandat", 0.0, 1.0,
                        ips.MANDATE_FEE * 100, 0.05, format="%.2f %%") / 100
        drag = st.selectbox("Enveloppe",
                            ["Assurance-vie LUX", "Compte-titres capitalisant",
                             "Compte-titres distribuant"])
        st.caption("Les curseurs ne modifient que cet onglet et celui de "
                   "transmission. L'allocation reste celle de l'IPS.")

    drag_v = {"Assurance-vie LUX": ips.TAX_DRAG_STRUCTURED,
              "Compte-titres capitalisant": ips.TAX_DRAG_CTO_COMPETENT,
              "Compte-titres distribuant": ips.TAX_DRAG_CTO_NAIF}[drag]

    exp = portfolio_return(ips.SAA_INDICATIVE, infl)
    req = infl + fee + ips.INSTRUMENT_TER + drag_v
    marge = exp - req

    c = st.columns(4)
    c[0].metric("Rendement brut attendu", f"{exp:.2f} %".replace(".", ","))
    c[1].metric("Seuil requis", f"{req:.2f} %".replace(".", ","))
    c[2].metric("Marge", f"{marge:+.2f} %".replace(".", ","),
                delta=f"{'atteint' if marge >= 0 else 'non atteint'}",
                delta_color="normal" if marge >= 0 else "inverse")
    c[3].metric("Perte P90 mesurée", "13,8 %",
                delta="contrainte 15 %", delta_color="off")

    if marge < 0:
        st.error(f"**Objectif non atteint** : il manque {abs(marge):.2%} par an. "
                 "Leviers disponibles — négocier les frais, ou accepter un "
                 "budget de risque supérieur.")
    else:
        st.success(f"**Objectif atteint** avec {marge:.2%} de marge annuelle.")

    st.markdown("## Le seuil et le rendement attendu dépendent tous deux de l'inflation")
    st.caption("C'est le point qui a fait basculer le diagnostic : comparer un "
               "seuil bâti sur 4 % d'inflation à des rendements bâtis sur 2 % "
               "revient à juger un portefeuille dans un monde et à l'évaluer "
               "dans un autre.")

    xs = [i / 100 for i in range(0, 625, 25)]
    exps = [portfolio_return(ips.SAA_INDICATIVE, x) for x in xs]
    reqs = [x + fee + ips.INSTRUMENT_TER + drag_v for x in xs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=exps, name="Rendement attendu",
                             line=dict(color=viz.CATEGORICAL[0], width=2),
                             hovertemplate="inflation %{x:.1%}<br>"
                                           "attendu %{y:.2%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=reqs, name="Seuil requis",
                             line=dict(color=viz.CATEGORICAL[1], width=2),
                             hovertemplate="inflation %{x:.1%}<br>"
                                           "requis %{y:.2%}<extra></extra>"))
    fig.add_vline(x=infl, line=dict(color=viz.INK_2, width=1, dash="dot"))
    fig.add_annotation(x=infl, y=max(exps), text="hypothèse retenue",
                       showarrow=False, yshift=12,
                       font=dict(color=viz.INK_2, size=11))
    fig.update_layout(**viz.layout(height=360, hovermode="x unified"))
    fig.update_xaxes(tickformat=".0%", title="Inflation annuelle")
    fig.update_yaxes(tickformat=".1%", title="Rendement brut")
    st.plotly_chart(fig, width='stretch')

    st.caption("Les deux droites se croisent vers 5,4 % d'inflation : au-delà, "
               "l'objectif cesse d'être atteignable avec cette allocation. "
               "L'hypothèse du client (4 %) laisse donc une marge réelle.")

    with st.expander("Vue tableau — hypothèses de marché par classe d'actifs"):
        er = expected_returns(infl)
        base = expected_returns(INFLATION_BASE)
        import pandas as pd
        df = pd.DataFrame({
            "Classe": [viz.LABEL[k] for k in ips.SAA_INDICATIVE],
            "Poids": [ips.SAA_INDICATIVE[k] for k in ips.SAA_INDICATIVE],
            "Attendu (inflation 2 %)": [base[k] for k in ips.SAA_INDICATIVE],
            f"Attendu (inflation {infl:.1%})": [er[k] for k in ips.SAA_INDICATIVE],
        })
        st.dataframe(df.style.format({
            "Poids": "{:.0%}", "Attendu (inflation 2 %)": "{:.2%}",
            f"Attendu (inflation {infl:.1%})": "{:.2%}"}),
            width='stretch', hide_index=True)
