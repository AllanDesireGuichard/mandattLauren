"""Onglet Transmission -- le levier qui pese neuf fois l'optimisation."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import ips, viz
from core.viz import fr
from core.succession import Poche, droits_donation_np, taux_effectif

GROSS = 0.0579
FRAIS_AV = 0.0025


def _scenario(av_pct: float, np_pct: float, assiette: float, age: int,
              horizon: int, n_enf: int) -> dict:
    av, np_don = av_pct * assiette, np_pct * assiette
    cto = assiette - av - np_don
    droits_don, _ = droits_donation_np(np_don, age, n_enf) if np_don > 0 else (0.0, 0.0)
    r_cto = GROSS - ips.TOTAL_FEES - ips.TAX_DRAG_CTO_COMPETENT
    r_av = GROSS - ips.TOTAL_FEES - ips.TAX_DRAG_STRUCTURED - FRAIS_AV
    poches = [Poche("Assurance-vie", av, "av_990i"),
              Poche("Nue-propriété donnée", np_don, "deja_transmis"),
              Poche("Compte-titres", max(cto - droits_don, 0.0), "succession")]
    for p in poches:
        p.croitre(r_av if p.regime == "av_990i" else r_cto, horizon)
    brut = sum(p.montant for p in poches)
    dd = sum(p.droits_au_deces(n_enf) for p in poches)
    return {"brut": brut, "droits_donation": droits_don, "droits_deces": dd,
            "net": brut - dd, "impot": droits_don + dd,
            "taux": taux_effectif(droits_don + dd, brut + droits_don),
            "poches": poches}


def render() -> None:
    st.header("Transmission")
    st.caption("L'indicateur n'est jamais le patrimoine brut : c'est ce qui "
               "arrive effectivement aux enfants.")

    with st.sidebar:
        st.subheader("Transmission")
        age = st.slider("Âge du donateur", 51, 75, ips.CLIENT_AGE)
        horizon = st.slider("Horizon (ans)", 10, 35, 25)
        av_pct = st.slider("Part en assurance-vie", 0, 80, 30, 5) / 100
        np_pct = st.slider("Part donnée en nue-propriété", 0, 80, 40, 5) / 100
        if av_pct + np_pct > 1.0:
            st.error("La somme dépasse 100 %.")

    assiette = ips.TOTAL_ASSETS - ips.LIQUIDITY_NEED
    if av_pct + np_pct > 1.0:
        return

    ref = _scenario(0.0, 0.0, assiette, age, horizon, ips.N_CHILDREN)
    cur = _scenario(av_pct, np_pct, assiette, age, horizon, ips.N_CHILDREN)
    gain = cur["net"] - ref["net"]

    c = st.columns(4)
    c[0].metric("Sans structuration", fr(ref["net"]/1e6, "M€", 0))
    c[1].metric("Avec votre paramétrage", fr(cur["net"]/1e6, "M€", 0))
    c[2].metric("Gain pour les enfants", ("+" if gain>=0 else "") + fr(gain/1e6, "M€", 0),
                delta=f"{gain/ref['net']:+.0%}")
    c[3].metric("Taux effectif", f"{cur['taux']:.1%}",
                delta=f"contre {ref['taux']:.1%} sans", delta_color="off")

    lab = ["Sans structuration", "Votre paramétrage"]
    nets = [ref["net"] / 1e6, cur["net"] / 1e6]
    imps = [ref["impot"] / 1e6, cur["impot"] / 1e6]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=lab, y=nets, name="Net aux enfants",
                         marker=dict(color=viz.CATEGORICAL[0],
                                     line=dict(color=viz.SURFACE, width=2)),
                         text=[fr(v, "M€", 0) for v in nets],
                         textposition="inside",
                         textfont=dict(color="#fff", size=13),
                         hovertemplate="%{x}<br>net %{y:,.0f} M€<extra></extra>"))
    fig.add_trace(go.Bar(x=lab, y=imps, name="Impôt",
                         marker=dict(color=viz.CATEGORICAL[1],
                                     line=dict(color=viz.SURFACE, width=2)),
                         text=[fr(v, "M€", 0) for v in imps],
                         textposition="inside",
                         textfont=dict(color="#fff", size=13),
                         hovertemplate="%{x}<br>impôt %{y:,.0f} M€<extra></extra>"))
    fig.update_layout(**viz.layout(
        f"Patrimoine transmis dans {horizon} ans", height=380, barmode="stack"))
    fig.update_yaxes(ticksuffix=" M€")
    st.plotly_chart(fig, width='stretch')

    st.info(f"Le patrimoine **brut** du scénario structuré "
            f"({cur['brut']/1e6:,.0f} M€) est ".replace(",", " ") +
            ("**plus faible**" if cur["brut"] < ref["brut"] else "plus élevé") +
            f" que celui du scénario sans structuration "
            f"({ref['brut']/1e6:,.0f} M€), les droits de donation étant payés "
            "dès le départ. C'est la démonstration que le brut est le mauvais "
            "indicateur.".replace(",", " "))

    st.markdown("## Le calendrier — ce que coûte un anniversaire")
    montant = np_pct * assiette
    if montant > 0:
        rows = []
        for a in range(max(age - 1, 51), min(age + 3, 76)):
            d, base = droits_donation_np(montant, a, ips.N_CHILDREN)
            rows.append({"Âge": a, "Nue-propriété taxable": base / montant,
                         "Droits": d / 1e6})
        df = pd.DataFrame(rows)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df["Âge"], y=df["Droits"],
            marker=dict(color=[viz.STATUS["critical"] if a > age
                               else viz.CATEGORICAL[0] for a in df["Âge"]],
                        line=dict(color=viz.SURFACE, width=2)),
            text=[fr(v, "M€") for v in df["Droits"]],
            textposition="outside", textfont=dict(color=viz.INK_2, size=11),
            hovertemplate="%{x} ans<br>%{y:,.1f} M€ de droits<extra></extra>"))
        fig2.update_layout(**viz.layout(
            "Droits sur une donation de " + fr(montant/1e6, "M€", 0) + " selon l'âge", height=320))
        fig2.update_yaxes(ticksuffix=" M€")
        fig2.update_xaxes(title="Âge du donateur au jour de la donation",
                          dtick=1)
        st.plotly_chart(fig2, width='stretch')

        d_now, _ = droits_donation_np(montant, age, ips.N_CHILDREN)
        d_next, _ = droits_donation_np(montant, age + 1, ips.N_CHILDREN)
        if d_next > d_now:
            st.error("**Franchir le prochain anniversaire coûte " + fr((d_next-d_now)/1e6, "M€") + ".** " +
                     "Le barème de l'article 669 CGI évolue par tranches d'âge : "
                     "la valeur taxable de la nue-propriété augmente d'un palier. "
                     "C'est la raison pour laquelle ce dossier a une date limite.")

    with st.expander("Vue tableau — détail par enveloppe"):
        st.dataframe(pd.DataFrame([
            {"Poche": p.nom, "Valeur à terme (M€)": p.montant / 1e6,
             "Droits (M€)": p.droits_au_deces(ips.N_CHILDREN) / 1e6,
             "Net (M€)": (p.montant - p.droits_au_deces(ips.N_CHILDREN)) / 1e6}
            for p in cur["poches"]]).style.format(
                {c: "{:,.1f}" for c in ["Valeur à terme (M€)", "Droits (M€)",
                                        "Net (M€)"]}),
            width='stretch', hide_index=True)

    st.caption("Réserve : ce module applique des règles fiscales exactes à ma "
               "connaissance, mais ne modélise ni le régime matrimonial, ni les "
               "droits du conjoint survivant, ni la réserve héréditaire. "
               "Validation par un notaire indispensable avant mise en œuvre.")
