"""
Étape 5 — Backtests.

Périmètre fixé par Allan le 2026-09-18 : deux blocs.
  1. le parcours 2006-2026 du portefeuille retenu, et la DURÉE de ses
     baisses — ce que l'étape 4, qui ne regardait que leur profondeur, n'a
     pas mesuré ;
  2. VaR et CVaR historiques sur un an, à titre DESCRIPTIF (la règle reste
     la pire baisse depuis le plus haut, étape 4).
Écartés : crises retirées du calcul, crises antérieures à 2006, GARCH,
fenêtres glissantes de dix ans, test du pilier « dynamique ».

Limite dite d'emblée dans l'onglet : ces données sont celles qui ont servi
à construire le portefeuille. Le rejeu ne prouve pas que la limite tient.
"""
from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import allocation, backtests, ips, pedago, viz


def _pct(v: float, dec: int = 1) -> str:
    return viz.fr(v, "%", dec)


def _mois(v: float) -> str:
    return viz.fr(v, "mois", 0)


@st.cache_data(show_spinner="Rejeu du portefeuille sur 2006-2026…")
def _donnees() -> dict:
    v = backtests.valeur()
    return {"v": v, "ep": backtests.episodes(v), "t": backtests.temps_sous(v),
            "r": backtests.un_an(v), "infl": _inflation()}


@st.cache_data(show_spinner=False)
def _inflation() -> dict:
    """Inflation zone euro RÉELLEMENT constatée sur la fenêtre du rejeu."""
    return json.loads((allocation.DATA / "inflation_realisee.json").read_text(
        encoding="utf-8"))


def render() -> None:
    pedago.chaine(5)
    pedago.etape(
        5, "Backtests",
        "Le portefeuille de l'étape 4 rejoué jour après jour d'octobre 2006 "
        "à aujourd'hui. Deux questions : combien de temps met-il à se "
        "remettre de ses baisses, et à quoi ressemble une mauvaise année ?",
    )
    st.warning(
        "**Ce que ce rejeu ne peut pas prouver.** Les vingt années de "
        "données sont celles qui ont servi à construire le portefeuille : "
        "l'étape 4 a cherché une répartition qui ne perde jamais plus de "
        "14 % sur cette période. Qu'il n'y perde pas plus de 14 % est donc "
        "acquis d'avance, et ne dit rien de la prochaine crise. Le rejeu "
        "sert à mesurer ce que le calcul n'a pas regardé : la durée des "
        "baisses et la fréquence des mauvaises années."
    )
    d = _donnees()
    _bloc_parcours(d)
    _bloc_var(d)


# ----------------------------------------------------------------------
def _bloc_parcours(d: dict) -> None:
    v, ep, t = d["v"], d["ep"], d["t"]
    ans = (v.index[-1] - v.index[0]).days / 365.25
    cagr = ((v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1) * 100

    st.markdown("#### Le parcours, et la durée des baisses")
    c = st.columns(4)
    c[0].metric("100 M€ investis en octobre 2006",
                viz.fr(v.iloc[-1] / 1e6, "M€", 0) + " aujourd'hui")
    c[1].metric("Soit par an", _pct(cagr, 2))
    c[2].metric("Pire baisse depuis le plus haut", _pct(t["pire"]))
    c[3].metric("Plus longue période sous le plus haut",
                _mois(max(backtests.mois(a, r) for a, r in
                          zip(ep["sommet"], ep["retour"]) if pd.notna(r))))

    _bloc_seuil(d, cagr)
    _graphique_parcours(v)

    lignes = []
    for x in ep.itertuples():
        retour = x.retour if pd.notna(x.retour) else None
        lignes.append((
            x.sommet.strftime("%m/%Y"), x.creux.strftime("%m/%Y"),
            _pct(x.perte * 100), _mois(backtests.mois(x.sommet, x.creux)),
            retour.strftime("%m/%Y") if retour else "pas encore",
            _mois(backtests.mois(x.sommet, retour)) if retour else "—"))
    st.markdown("**Chaque baisse de plus de 5 %**")
    st.table(pd.DataFrame(lignes, columns=[
        "Plus haut", "Point bas", "Baisse", "Durée de la baisse",
        "Retour au plus haut", "Temps total sous le plus haut"])
        .set_index("Plus haut"))

    e22 = ep[ep["sommet"].dt.year == 2021].iloc[0]
    e08 = ep[ep["sommet"].dt.year == 2007].iloc[0]
    e20 = ep[ep["sommet"].dt.year == 2020].iloc[0]
    st.caption(
        f"2008 et 2020 sont de même profondeur ({_pct(e08.perte * 100)} et "
        f"{_pct(e20.perte * 100)}) mais pas de même durée : "
        f"{_mois(backtests.mois(e20.sommet, e20.retour))} contre "
        f"{_mois(backtests.mois(e08.sommet, e08.retour))} pour revenir au "
        f"plus haut. La plus longue est 2022 : "
        f"{_mois(backtests.mois(e22.sommet, e22.retour))}."
    )
    st.table(pd.DataFrame([
        ("À plus de 1 % sous son plus haut", _pct(t["sous"], 0)),
        ("À plus de 5 % sous son plus haut", _pct(t["5"], 0)),
        ("À plus de 10 % sous son plus haut", _pct(t["10"], 0)),
    ], columns=["Le portefeuille a passé…", "…du temps"])
        .set_index("Le portefeuille a passé…"))
    st.caption(
        "Pour le client, cela veut dire : la plupart du temps, son "
        "patrimoine est un peu en dessous de son meilleur niveau ; une fois "
        "sur six environ, il en est à plus de 5 % ; les pertes proches de "
        "la limite sont rares et brèves."
    )

# ----------------------------------------------------------------------
def _bloc_seuil(d: dict, cagr: float) -> None:
    """
    Le rejeu jugé contre la BONNE inflation.

    CORRECTION DU 2026-09-21. Le rendement réalisé était comparé au seuil de
    4 % de l'énoncé. Or ce 4 % décrit un monde à 4 % d'inflation, tandis que
    la période rejouée en a vécu une autre. Juger un résultat d'un régime
    avec l'exigence d'un autre est exactement le piège que la première
    version du dossier avait identifié comme sa correction la plus
    importante (archive/docs/02_ips.md, § 4.4) — et ici il jouait EN
    DÉFAVEUR du portefeuille.
    """
    inf = d["infl"]
    bt = inf["backtest"]
    reel = cagr - bt["annuel"]
    enonce = ips.INFLATION_TARGET * 100

    st.markdown("**Le rendement réalisé, jugé contre la bonne inflation**")
    st.table(pd.DataFrame([
        ("Rendement du portefeuille", _pct(cagr, 2),
         "Rejeu, rééquilibré chaque mois"),
        ("Inflation zone euro constatée", _pct(bt["annuel"], 2),
         f"{_pct(bt['cumul'], 1)} cumulés sur {bt['annees']:.0f} ans"),
        ("**Rendement réel obtenu**", "**" + _pct(reel, 2) + "**",
         "**Ce que le pouvoir d'achat a réellement gagné**"),
    ], columns=["", "Par an", "D'où il vient"]).set_index(""))

    st.success(
        f"**L'objectif du client a été tenu, et largement.** Sur ces vingt "
        f"années, le portefeuille a rapporté {_pct(reel, 2)} par an "
        f"**au-delà de l'inflation**. Comparer ses {_pct(cagr, 2)} au seuil "
        f"de {_pct(enonce, 0)} de l'énoncé n'aurait aucun sens : ce seuil "
        f"décrit un monde à {_pct(enonce, 0)} d'inflation, la période en a "
        f"vécu {_pct(bt['annuel'], 2)}. Le bon seuil pour juger le passé est "
        f"l'inflation du passé.",
        icon=":material/check_circle:",
    )

    c5 = inf["fenetres"]["5 ans"]["annuel"]
    st.caption(
        f"L'hypothèse du client n'est pas absurde : {_pct(bt['annuel'], 2)} "
        f"par an depuis 2006, mais {_pct(c5, 2)} sur les cinq dernières "
        f"années. Il extrapole ce qu'il vient de vivre."
    )
    st.caption(f"Source : {inf['source']}, dernier point "
               f"{pd.Timestamp(inf['dernier_point']).strftime('%m/%Y')}. "
               f"Taux composé entre les deux bornes, pas une moyenne de "
               f"glissements annuels.")


def _graphique_parcours(v: pd.Series) -> None:
    dd = (v / v.cummax() - 1) * 100
    h = dd.resample("W-FRI").min()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=h.index, y=h.values, mode="lines", fill="tozeroy",
        line={"color": viz.CATEGORICAL[0], "width": 2},
        fillcolor="rgba(42,120,214,.15)",
        hovertemplate="%{x|%d/%m/%Y} : %{y:.1f} %<extra></extra>"))
    for c, (a, b, _) in allocation.CRISES.items():
        fig.add_vrect(x0=a, x1=b, fillcolor=viz.GRID, opacity=.45,
                      line_width=0, annotation_text=c,
                      annotation_position="top left",
                      annotation_font={"color": viz.INK_2, "size": 11})
    fig.add_hline(y=-15, line={"color": viz.INK_2, "width": 1, "dash": "dot"},
                  annotation={"text": "Limite du mandat : −15 %",
                              "font": {"color": viz.INK_2, "size": 11}},
                  annotation_position="bottom left")
    fig.update_layout(**viz.layout(
        "Portefeuille retenu : écart à son plus haut, 2006-2026", height=380,
        showlegend=False,
        yaxis={"title": "Écart au plus haut (%)", "gridcolor": viz.GRID,
               "ticksuffix": " %", "range": [-17, 1]}))
    st.plotly_chart(fig, width="stretch")
    st.caption("À 0, le portefeuille est à son plus haut. Zones grises : les "
               "quatre crises de l'étape 4.")


# ----------------------------------------------------------------------
def _bloc_var(d: dict) -> None:
    r = d["r"]
    v95, c95 = backtests.var_cvar(r, .95)
    v99, c99 = backtests.var_cvar(r, .99)

    st.markdown("#### Une mauvaise année : VaR et CVaR")
    st.markdown(
        "Le résultat sur douze mois glissants, à chaque fin de mois depuis "
        "2006."
    )
    c = st.columns(4)
    c[0].metric("VaR 95 % à un an", _pct(v95))
    c[1].metric("CVaR 95 % à un an", _pct(c95))
    c[2].metric("Pire année", _pct(r.min()))
    c[3].metric("Meilleure année", _pct(r.max()))

    _graphique_annees(r, v95, c95)

    infl = d["infl"]["backtest"]["annuel"]
    enonce = ips.INFLATION_TARGET * 100

    st.table(pd.DataFrame([
        ("Une année sur vingt", f"perte de plus de {_pct(-v95)}",
         f"en moyenne {_pct(-c95)}"),
        ("Une année sur cent", f"perte de plus de {_pct(-v99)}",
         f"en moyenne {_pct(-c99)}"),
        ("Années en perte", _pct((r < 0).mean() * 100, 0) + " des années",
         ""),
        ("Années sous l'inflation constatée",
         _pct((r < infl).mean() * 100, 0) + " des années",
         f"l'inflation a fait {_pct(infl, 2)} par an"),
        ("Années sous les 4 % de l'énoncé",
         _pct((r < enonce).mean() * 100, 0) + " des années",
         "seuil d'un régime d'inflation qui n'a pas eu lieu"),
    ], columns=["", "Sur un an", "Dans ces années-là"]).set_index(""))

    st.warning(
        f"**Le chiffre qu'il vaut mieux donner soi-même.** Une année "
        f"glissante sur {round(100 / max((r < infl).mean() * 100, 1e-9))} "
        f"environ — {_pct((r < infl).mean() * 100, 0)} d'entre elles — n'a "
        f"pas battu l'inflation de son époque. **Préserver le pouvoir "
        f"d'achat est un objectif de moyenne longue, pas une garantie "
        f"annuelle**, et aucun portefeuille tenu à 15 % de perte maximum ne "
        f"peut promettre le contraire. Le dire avant qu'on le demande est "
        f"plus solide que de l'omettre : le chiffre est calculable par "
        f"n'importe qui à partir des données du dossier.",
        icon=":material/info:",
    )

    st.markdown(
        f"Sur un an, le portefeuille n'a jamais perdu plus de "
        f"{_pct(-r.min())}, alors que sa pire baisse depuis le plus haut "
        f"atteint {_pct(-d['t']['pire'])} : en 2008 comme en 2022, la perte "
        f"s'est accumulée sur plus d'un an. D'où la mesure depuis le plus "
        f"haut retenue à l'étape 4."
    )
    st.caption(
        f"Les {len(r)} années glissantes se chevauchent : vingt ans ne "
        f"contiennent qu'une vingtaine d'années indépendantes. La VaR à "
        f"95 % repose sur une poignée d'épisodes, celle à 99 % sur un seul. "
        f"Ce ne sont pas des prévisions."
    )
def _graphique_annees(r: pd.Series, v95: float, c95: float) -> None:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=r.values, xbins={"size": 1}, marker={
            "color": viz.CATEGORICAL[0],
            "line": {"color": viz.SURFACE, "width": 2}},
        hovertemplate="%{x} % sur un an : %{y} fins de mois<extra></extra>"))
    for x, nom in ((v95, "VaR 95 %"), (c95, "CVaR 95 %"), (-15, "−15 %")):
        fig.add_vline(x=x, line={"color": viz.INK_2, "width": 1,
                                 "dash": "dot"},
                      annotation={"text": nom, "font": {"color": viz.INK_2,
                                                        "size": 11}},
                      annotation_position="top")
    fig.update_layout(**viz.layout(
        "Résultat sur douze mois glissants, 2007-2026", height=360,
        showlegend=False, bargap=0,
        xaxis={"title": "Rendement sur un an (%)", "ticksuffix": " %",
               "gridcolor": viz.GRID},
        yaxis={"title": "Nombre de fins de mois", "gridcolor": viz.GRID}))
    st.plotly_chart(fig, width="stretch")
