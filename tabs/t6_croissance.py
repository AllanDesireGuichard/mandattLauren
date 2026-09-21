"""
Variante — portefeuille croissance.

Ce n'est PAS une sixième étape de la chaîne : c'est une branche qui part de
l'étape 4 et change une seule chose, la façon de lire la limite de 15 %.
D'où l'absence de `pedago.chaine()` en tête d'onglet.

Demandé par Allan le 2026-09-21, après le test qui a montré qu'un objectif
de 4 % AU-DESSUS de l'inflation (8 % nominal) est hors d'atteinte sous la
règle de l'étape 4, mais atteignable si la limite devient une limite en
fréquence. Trois blocs, dans cet ordre : ligne à ligne, allocation, risque.

Les chiffres viennent de data/allocation_croissance.json
(scripts/optimiser_croissance.py). Rien n'est recalculé ici, sauf les deux
chemins affichés dans le bloc risque.
"""
from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import allocation, fonds, pedago, viz
from tabs.t4_allocation import COULEUR, COURTS, FAMILLES

CIBLE = 8.0            # 4 % d'inflation + 4 % au-dessus
FONDS_DE = ("usa", "japon", "emergents", "indexees", "or", "matieres")


def _pct(v: float, dec: int = 2) -> str:
    return viz.fr(v, "%", dec)


def _poids(x: float) -> str:
    return "—" if x < 0.005 else viz.fr(x * 100, "%", 0)


def _me(v: float, dec: int = 1) -> str:
    return viz.fr(v / 1e6, "M€", dec)


@st.cache_data(show_spinner=False)
def _donnees() -> dict:
    return json.loads(
        (allocation.DATA / "allocation_croissance.json").read_text(
            encoding="utf-8"))


@st.cache_data(show_spinner="Rejeu des deux portefeuilles…")
def _chemins() -> pd.DataFrame:
    """Baisse depuis le plus haut, jour par jour, pour les deux portefeuilles."""
    d = _donnees()["portefeuilles"]
    s = allocation.series()
    out = {}
    for nom in ("croissance", "retenu"):
        w = {k: x for k, x in d[nom]["poids"].items() if x > 0.0005}
        v = allocation.portefeuille(s, w)
        out[nom] = allocation.baisse_depuis_plus_haut(v) * 100
    return pd.DataFrame(out).dropna()


# ----------------------------------------------------------------------
def render() -> None:
    d = _donnees()
    pedago.etape(
        6, "Variante — portefeuille croissance",
        "Les cinq étapes répondent à l'énoncé tel qu'il est écrit : protéger "
        "le pouvoir d'achat, donc battre 4 % d'inflation. Cet onglet répond à "
        "une autre question, celle que M. Lauren posera peut-être en séance : "
        "« et si je voulais gagner 4 % **au-dessus** de l'inflation ? » Un seul "
        "paramètre change, la façon de lire la limite de perte. Le reste de la "
        "chaîne — supports de l'étape 3, rendements de l'étape 2 — est "
        "inchangé.",
    )
    st.warning(
        "**Ce n'est pas la proposition faite au client.** C'est la branche "
        "qu'on garde en réserve, chiffrée, pour pouvoir dire précisément ce "
        "que coûterait un objectif plus ambitieux. Le portefeuille du mandat "
        "reste celui de l'étape 4.",
        icon=":material/alt_route:",
    )
    _bloc_regle(d)
    _bloc_lignes(d)
    _bloc_alloc(d)
    _bloc_risque(d)


# ----------------------------------------------------------------------
def _bloc_regle(d: dict) -> None:
    p = d["portefeuilles"]
    # Lus, jamais écrits en dur : le plafond de l'étape 4 vient de son
    # propre fichier de résultats, le plafond absolu de l'étape 2.
    libre = allocation.resultats()["scenarios"]["libre"]["rendement_espere"]
    e = allocation.entrees()
    plafond = e[~e["hors_calcul"]]["rendement"].max()

    st.markdown("#### La règle qu'on change, et elle seule")

    pedago.fil([
        ("Étape 4", "jamais plus de 15 % de baisse, pire cas"),
        ("Variante", f"plus de 15 % sur un an, au plus {1 - d['niveau']:.0%} "
                     f"des années"),
        ("Effet", "les actions cessent d'être plafonnées"),
    ])

    st.markdown(
        f"L'étape 4 exigeait que le portefeuille **n'ait jamais** perdu plus "
        f"de 15 % depuis son plus haut, sur toute la période 2006-2026. "
        f"C'est la lecture la plus exigeante de l'énoncé, et c'est elle qui "
        f"plafonne le rendement. On la remplace ici par une limite en "
        f"**fréquence** : une perte de plus de 15 % sur douze mois est "
        f"tolérée, mais au plus une année sur vingt. C'est la **VaR à 95 %**, "
        f"mesurée sur les {d['n_fenetres']} années glissantes de la période."
    )

    pedago.formule(
        r"\text{VaR}_{95\%} \;=\; \text{la perte dépassée par les 5 \% "
        r"pires années}",
        f"On classe les {d['n_fenetres']} années glissantes de la pire à la "
        f"meilleure, et on lit la douzième : une année sur vingt a fait "
        f"moins bien que "
        "celle-là. La VaR dit à partir de quel niveau on est dans les "
        "mauvaises années — elle ne dit rien de ce qui se passe une fois "
        "qu'on y est. Ce sera tout l'objet du troisième bloc.",
    )

    c = st.columns(3)
    c[0].metric("Objectif visé ici", _pct(CIBLE, 0),
                help="4 % d'inflation + 4 % au-dessus")
    c[1].metric("Atteignable sous la règle de l'étape 4", _pct(libre),
                delta=viz.fr(libre - CIBLE, "pt", 2))
    c[2].metric("Atteignable sous la règle de fréquence",
                _pct(p["croissance"]["rendement_espere"]),
                delta=viz.fr(p["croissance"]["rendement_espere"] - CIBLE,
                             "pt", 2))
    st.markdown(
        f"**➜ La cible devient atteignable, et de peu.** "
        f"{_pct(p['croissance']['rendement_espere'])} espérés contre "
        f"{_pct(CIBLE, 0)} visés. Le plafond absolu, si on ne contraignait "
        f"plus rien du tout, serait {_pct(plafond)} — le rendement des "
        f"actions japonaises, la classe la mieux payée de l'étape 2. Viser "
        f"{_pct(CIBLE, 0)} oblige donc à être investi en actions à "
        f"{_poids(sum(p['croissance']['poids'].get(k, 0) for k in allocation.MIX_ACTIONS))}. "
        f"Les deux blocs suivants montrent lesquelles, et ce que cela coûte."
    )


# ----------------------------------------------------------------------
def _bloc_lignes(d: dict) -> None:
    w = d["portefeuilles"]["croissance"]["poids"]
    ret = d["portefeuilles"]["retenu"]["poids"]
    e = allocation.entrees()
    cl = fonds.charger()["classes"]

    st.markdown("#### Ligne à ligne : ce que le portefeuille contient")
    st.markdown(
        "Aucun support nouveau. Ce sont ceux retenus à l'étape 3, dans des "
        "proportions différentes : le calcul n'en garde que quatre sur dix."
    )

    lignes = []
    for k in allocation.ORDRE:
        x = w.get(k, 0.0)
        if x < 0.005:
            continue
        sup = e.loc[k, "support"]
        if k in FONDS_DE and k in cl:
            c = cl[k]
            sup = (f"{c['retenu'].split('.')[0]} · "
                   f"{c['candidats'][c['retenu']]['nom']}")
        lignes.append((e.loc[k, "classe"], sup, _poids(x),
                       _pct(e.loc[k, "rendement"])))
    st.table(pd.DataFrame(lignes, columns=[
        "Classe", "Support", "Poids", "Rendement espéré"]).set_index("Classe"))

    # Noms courts (ceux des graphiques de l'étape 4) : les libellés longs
    # passent mal en énumération — « les 10 M€ » s'y retrouve en minuscules.
    ecartes = [COURTS[k] for k in allocation.ORDRE
               if k not in allocation.HORS_CALCUL and w.get(k, 0.0) < 0.005]
    st.markdown(
        f"**Les {len(ecartes)} lignes écartées** : {', '.join(ecartes)}. "
        f"Toutes rapportent moins que la cible de {_pct(CIBLE, 0)} : à ce "
        f"niveau d'exigence, le calcul ne peut plus s'offrir d'obligations. "
        f"Même les indexées, seule obligation au-dessus de 4 % et pièce "
        f"maîtresse de l'étape 4 ({_poids(ret['indexees'])} du portefeuille "
        f"retenu), "
        f"disparaissent complètement."
    )

    pedago.explique(
        "Pourquoi l'Europe et les émergents, et pas les États-Unis",
        "Le portefeuille croissance met plus de la moitié de l'argent sur "
        "les actions européennes et un tiers sur les émergentes, mais rien "
        "aux États-Unis. Ce n'est pas un pari géographique du calcul : c'est "
        "mécanique. Les rendements espérés de l'étape 2 viennent des "
        "valorisations, et l'action américaine se paie un PER de 30 contre "
        "18,5 en Europe. À ce prix, elle rapporte 7,19 % espérés contre "
        "9,23 % — donc quand on cherche le rendement maximum, elle sort.",
        "C'est une faiblesse assumée de cette variante, et la même que celle "
        "du calcul libre de l'étape 4 : un portefeuille qui met 86 % sur "
        "deux zones fait reposer tout son résultat sur une seule hypothèse, "
        "celle que les valorisations se rattrapent. Si l'Amérique reste "
        "chère et continue de monter, ce portefeuille passe à côté.",
        "L'or est la seule ligne qui ne soit pas là pour le rendement : à "
        "4,00 % espérés, il abaisse la cible. Le calcul le garde parce qu'il "
        "a tenu dans les quatre crises étudiées, et c'est lui qui permet de "
        "respecter la limite de fréquence.",
    )


# ----------------------------------------------------------------------
def _bloc_alloc(d: dict) -> None:
    p = d["portefeuilles"]
    croi, avec = p["croissance"], p["croissance_10me"]
    M = allocation.MONTANT

    st.markdown("#### L'allocation, en millions d'euros")
    g1, g2 = st.columns([3, 2])
    with g1:
        _graphique(croi["poids"], "Portefeuille croissance", M)
    with g2:
        _graphique(p["retenu"]["poids"], "Portefeuille retenu (étape 4)", M)

    part_act = sum(croi["poids"].get(k, 0) for k in allocation.MIX_ACTIONS)
    part_ret = sum(p["retenu"]["poids"].get(k, 0)
                   for k in allocation.MIX_ACTIONS)
    st.markdown(
        f"**Lecture.** {_poids(part_act)} d'actions contre "
        f"{_poids(part_ret)} dans le portefeuille du mandat. C'est tout "
        f"l'écart : les {_pct(croi['rendement_espere'] - p['retenu']['rendement_espere'], 2)} "
        f"de rendement espéré en plus s'achètent en triplant la part "
        f"d'actions."
    )

    st.markdown("**Ce que coûtent les 10 M€ à décaisser.**")
    st.markdown(
        f"Le calcul ci-dessus ignore le seul besoin du client qui ne se "
        f"négocie pas : {_me(10e6, 0)} disponibles sous deux ans. En "
        f"imposant {_poids(allocation.MIN_AAA)} sur l'échelle AAA, le "
        f"rendement espéré passe de {_pct(croi['rendement_espere'])} à "
        f"{_pct(avec['rendement_espere'])}, soit "
        f"{viz.fr(avec['rendement_espere'] - croi['rendement_espere'], 'pt', 2)}. "
        f"C'est peu, et c'est une bonne nouvelle : **la liquidité n'est pas "
        f"ce qui empêche d'atteindre 8 %.** La cible reste tenue "
        f"({viz.fr(avec['rendement_espere'] - CIBLE, 'pt', 2)} au-dessus). "
        f"Ce qui coûte cher, c'est le risque — bloc suivant."
    )


def _graphique(poids: dict, titre: str, montant: float) -> None:
    """Une barre par support, couleur = famille, même palette que l'étape 4."""
    fig = go.Figure()
    for fam, ks in FAMILLES.items():
        ks = [k for k in ks if poids.get(k, 0) >= 0.005]
        if not ks:
            continue
        x = [poids[k] * 100 for k in ks]
        fig.add_trace(go.Bar(
            y=[COURTS[k][0].upper() + COURTS[k][1:] for k in ks], x=x,
            name=fam, orientation="h",
            text=[f"{viz.fr(v, '%', 0)} · {viz.fr(v * montant / 100 / 1e6, 'M€', 0)}"
                  for v in x],
            textposition="outside", cliponaxis=False,
            textfont={"color": viz.INK_2},
            marker={"color": COULEUR[fam], "cornerradius": 4},
            hovertemplate="%{y} : %{text}<extra>" + fam + "</extra>"))
    fig.update_layout(**viz.layout(
        titre, height=310, bargap=.25, showlegend=False,
        xaxis={"visible": False, "range": [0, 68]},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)"}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ----------------------------------------------------------------------
def _bloc_risque(d: dict) -> None:
    p = d["portefeuilles"]
    croi, ret = p["croissance"], p["retenu"]

    st.markdown("#### Le risque : ce que la règle de fréquence laisse passer")
    st.markdown(
        "La VaR dit à partir de quand on est dans les mauvaises années. La "
        "question que le client posera est l'autre : **quand ça dépasse, ça "
        "fait combien ?** C'est la CVaR, la perte moyenne de ces années-là."
    )

    c = st.columns(4)
    c[0].metric("Rendement espéré", _pct(croi["rendement_espere"]),
                delta=viz.fr(croi["rendement_espere"]
                             - ret["rendement_espere"], "pt", 2))
    c[1].metric("VaR 95 % à un an", _pct(croi["var95"], 1),
                delta=viz.fr(croi["var95"] - ret["var95"], "pt", 1),
                delta_color="inverse")
    c[2].metric("CVaR 95 % à un an", _pct(croi["cvar95"], 1),
                delta=viz.fr(croi["cvar95"] - ret["cvar95"], "pt", 1),
                delta_color="inverse")
    c[3].metric("Pire baisse, 2006-2026", _pct(croi["pire_baisse"], 1),
                delta=viz.fr(croi["pire_baisse"] - ret["pire_baisse"],
                             "pt", 1), delta_color="inverse")
    st.caption("Écart affiché par rapport au portefeuille retenu de l'étape 4.")

    st.error(
        f"**Le chiffre qui décide.** La limite est respectée au sens de la "
        f"VaR : on ne dépasse 15 % qu'une année sur vingt. Mais ces "
        f"années-là coûtent **{_pct(croi['cvar95'], 1)} en moyenne**, et la "
        f"pire baisse depuis le plus haut atteint "
        f"**{_pct(croi['pire_baisse'], 1)}** — en 2008, la moitié du "
        f"patrimoine. Un client qui a écrit « ne jamais perdre plus de 15 % » "
        f"ne lira pas cela comme une limite respectée.",
        icon=":material/warning:",
    )

    _graphique_baisses()

    st.markdown("**Les deux portefeuilles, crise par crise.**")
    lignes = []
    for c_, (_, _, nom) in allocation.CRISES.items():
        lignes.append((f"{c_} — {nom}", _pct(ret["crises"][c_], 1),
                       _pct(croi["crises"][c_], 1)))
    lignes += [
        ("Pire année (12 mois glissants)", _pct(ret["pire_12m"], 1),
         _pct(croi["pire_12m"], 1)),
        ("Années en perte", _pct(ret["annees_en_perte"], 0),
         _pct(croi["annees_en_perte"], 0)),
        ("Temps passé à plus de 10 % sous le plus haut",
         _pct(ret["temps_sous_10"], 0), _pct(croi["temps_sous_10"], 0)),
        ("Rendement obtenu, 2006-2026", _pct(ret["realise"]) + " / an",
         _pct(croi["realise"]) + " / an"),
    ]
    st.table(pd.DataFrame(lignes, columns=[
        "", "Retenu (étape 4)", "Croissance"]).set_index(""))

    st.markdown(
        f"**Lecture.** Le portefeuille croissance a bien mieux payé sur la "
        f"période — {_pct(croi['realise'])} par an contre "
        f"{_pct(ret['realise'])} — mais il a passé "
        f"{_pct(croi['temps_sous_10'], 0)} du temps à plus de 10 % sous son "
        f"plus haut, contre {_pct(ret['temps_sous_10'], 0)}. Huit fois plus. "
        f"Et il n'atteint pas l'objectif de 4 % plus souvent : "
        f"{_pct(croi['annees_sous_4'], 0)} de ses années glissantes sont "
        f"sous 4 %, contre {_pct(ret['annees_sous_4'], 0)} pour le "
        f"portefeuille retenu. **Il ne rate pas la cible moins souvent : il "
        f"la rate beaucoup plus violemment.**"
    )

    pedago.explique(
        "La limite de cette variante, et elle est sérieuse",
        f"La VaR et la CVaR ci-dessus sont estimées sur les "
        f"{d['n_fenetres']} années glissantes qui ont servi à construire le "
        f"portefeuille, et ces fenêtres se chevauchent : deux années "
        f"glissantes consécutives partagent onze mois sur douze. Le nombre "
        f"d'épisodes de baisse réellement distincts entre 2006 et 2026 est "
        f"de sept. Le seuil « une année sur vingt » repose donc sur une "
        f"poignée d'observations, pas sur un échantillon.",
        "C'est exactement le reproche que l'étape 4 fait au calcul libre — "
        "avoir appris le passé par cœur — et il vaut ici davantage encore, "
        "parce que la contrainte porte sur la queue de la distribution, "
        "c'est-à-dire sur la partie la moins bien mesurée. Une crise d'un "
        "genre nouveau ne se contenterait pas de dépasser les 15 % : rien "
        "dans ce calcul ne borne de combien.",
        "C'est pourquoi cette variante est présentée comme une réserve "
        "chiffrée et non comme une proposition. Elle sert à répondre à « "
        "pourquoi pas plus de rendement ? » avec des chiffres plutôt qu'avec "
        "une opinion.",
    )

    st.markdown("#### Conclusion de la variante")
    st.markdown(
        f"Viser 4 % au-dessus de l'inflation est **possible** : "
        f"{_pct(croi['rendement_espere'])} espérés, "
        f"{_pct(p['croissance_10me']['rendement_espere'])} en gardant les "
        f"10 M€ sécurisés. Le prix est connu et il est élevé : "
        f"{_poids(sum(croi['poids'].get(k, 0) for k in allocation.MIX_ACTIONS))} "
        f"d'actions sur deux zones, une perte moyenne de "
        f"{_pct(croi['cvar95'], 1)} les mauvaises années, et "
        f"{_pct(croi['pire_baisse'], 1)} dans le pire cas connu. "
        f"**À M. Lauren de dire si l'objectif a changé.** Tant qu'il est "
        f"écrit « protéger contre l'inflation » et « ne jamais perdre plus "
        f"de 15 % », c'est le portefeuille de l'étape 4 qui répond à "
        f"l'énoncé."
    )


def _graphique_baisses() -> None:
    """Les deux courbes de baisse depuis le plus haut, superposées."""
    b = _chemins()
    fig = go.Figure()
    for nom, etiq, couleur in (("retenu", "Retenu (étape 4)", viz.CATEGORICAL[0]),
                               ("croissance", "Croissance", viz.CATEGORICAL[1])):
        fig.add_trace(go.Scatter(
            x=b.index, y=b[nom], name=etiq, mode="lines",
            line={"color": couleur, "width": 1.4},
            hovertemplate="%{x|%m/%Y} : %{y:.1f} %<extra>" + etiq + "</extra>"))
    fig.add_hline(y=-15, line={"color": viz.INK_2, "width": 1, "dash": "dot"},
                  annotation={"text": "limite de 15 %",
                              "font": {"color": viz.INK_2, "size": 11}},
                  annotation_position="bottom right")
    fig.update_layout(**viz.layout(
        "Baisse depuis le plus haut, jour par jour", height=330,
        yaxis={"ticksuffix": " %"},
        legend={"orientation": "h", "y": -0.12, "x": 0}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(
        "Les deux portefeuilles remis à leurs poids chaque mois, sur les "
        "mêmes séries que l'étape 4. La limite de 15 % n'est pas une "
        "prévision : elle n'a jamais été franchie par le portefeuille "
        "retenu sur cette période parce que le calcul l'a imposée dessus."
    )
