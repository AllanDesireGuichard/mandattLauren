"""
Étape 4 — Allocation.

Construite bloc par bloc, comme les onglets 2 et 3. Plan validé avec Allan
le 2026-09-18 : 1 les entrées ; 2 le risque ; 3 l'optimisation libre ;
4 les contraintes et leur coût ; 5 le portefeuille retenu, en M€.

Décisions d'Allan (2026-09-18) :
  - la perte de 15 % se mesure DEPUIS LE PLUS HAUT, sur les 100 M€
    consolidés en euros, et doit tenir au PIRE CAS des crises passées ; si
    aucun portefeuille ne tient, repli sur une limite en probabilité (5 %) ;
  - un seul modèle de risque (covariance sur séries longues, vérifiée sur
    les crises) ; Black-Litterman retiré, les vues de l'étape 2 étant déjà
    dans les rendements espérés ;
  - pas de crypto (d'abord envisagée à 1-2 %, écartée par Allan).
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import (actions, allocation, fonds, ips, obligations, pedago,
                  taux, viz)


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)



def render() -> None:
    pedago.chaine(4)
    pedago.etape(
        4, "Allocation",
        "Combien placer sur chaque support pour rapporter au moins 4 % par an "
        "sans jamais perdre plus de 15 %. Cinq temps : les ingrédients, le "
        "risque de chaque support, un calcul sans garde-fou, les garde-fous "
        "et leur coût, puis le portefeuille en millions d'euros.",
    )
    _bloc_entrees()
    _bloc_risque()
    _bloc_libre()
    _bloc_regles()
    _bloc_retenu()


# ----------------------------------------------------------------------
def _bloc_entrees() -> None:
    e = allocation.entrees()
    m = allocation.meta()
    ctl = e["controle"]

    st.markdown("#### Ce qui entre dans le calcul")
    st.markdown(
        "**La règle.** L'étape 1 laissait les 15 % à préciser ; on retient "
        "la lecture la plus exigeante : une perte mesurée **depuis le plus "
        "haut**, sur **les 100 M€ ensemble**, qui ne dépasse jamais 15 % "
        "dans **les crises de 2008, 2011, 2020 et 2022**. Pas de crypto : "
        "elle ne rapporte rien (étape 2) et baisse avec les actions."
    )

    st.markdown("**Ce que chaque support doit rapporter.**")
    _graphique_rendements(e)
    calc = e[~e["hors_calcul"]]
    bat = calc[calc["rendement"] > 4]
    st.markdown(
        f"**Lecture.** Seules {len(bat)} lignes sur {len(calc)} dépassent les "
        f"4 % : les quatre zones d'actions et les obligations indexées. "
        f"Chaque euro placé ailleurs devra être compensé par des actions : "
        f"c'est la tension entre les 4 % et les 15 %."
    )

    st.markdown(
        "**L'historique.** Pour savoir si un portefeuille aurait tenu en "
        "2008, il faut l'historique de chaque support. Or la plupart des "
        "fonds retenus datent de 2018-2019. On prend donc **le vrai support "
        "dès qu'il existe, et avant lui un remplaçant** qui suit le même "
        "marché : un fonds plus ancien converti en euros, ou, pour les "
        "emprunts d'État, une obligation recalculée sur la courbe des taux "
        "de la BCE. Toutes les séries partent d'octobre 2006, avant le "
        "sommet des actions de juillet 2007."
    )
    pedago.explique(
        "Les limites de ces remplaçants",
        "<strong>Actions, or, matières premières</strong> : les remplaçants "
        "suivent bien leur support (corrélation de 0,83 à 0,95). Les fonds "
        "émergents et japonais filtrés ESG ont toutefois un peu plus baissé "
        f"que leur remplaçant "
        f"({viz.fr(ctl['emergents']['baisse_support'], '%', 0)} contre "
        f"{viz.fr(ctl['emergents']['baisse_remplacant'], '%', 0)} pour les "
        f"émergents) : 2008 et 2011 sont peut-être un peu sous-estimés sur "
        f"ces deux lignes.",
        "<strong>Obligations indexées</strong> : avant 2009, le remplaçant "
        "est un emprunt d'État classique, qui a mieux tenu en 2008 que les "
        "vraies indexées. Cette ligne est flattée.",
        f"<strong>Crédit</strong> : la prime est reconstituée avant 2016 à "
        f"partir des écarts de crédit américains. Le lien est faible "
        f"(corrélation {viz.fr(ctl['credit_court']['correlation'], '', 2)}) : "
        f"c'est la ligne la moins bien mesurée.",
        f"<strong>Actions européennes</strong> : risque mesuré sur l'indice, "
        f"pas sur les 30 titres. Choisis avec les données d'aujourd'hui, ils "
        f"ont un passé flatteur par construction "
        f"({viz.fr(ctl['actions_europe']['perf_support'], '%', 1)} par an "
        f"depuis 2019, contre "
        f"{viz.fr(ctl['actions_europe']['perf_remplacant'], '%', 1)} pour "
        f"l'indice).",
        source="Yahoo Finance (fonds et change) ; BCE, courbe des emprunts "
               "d'État de la zone euro ; FRED, écarts de crédit ICE BofA. "
               "Script : scripts/fetch_indices.py. Relevé du "
               f"{pd.Timestamp(m['releve']).strftime('%d/%m/%Y')}.",
    )

    st.markdown(
        "**➜ Dix supports, vingt ans d'historique.** Chacun a un rendement "
        "espéré et une série en euros qui traverse les quatre crises. "
        "Reste à savoir ce qu'ils y ont perdu, et s'ils ont perdu ensemble."
    )


# ----------------------------------------------------------------------
NOMS = {"poche_actions": "Poche actions (40/35/10/15)",
        "actions_europe": "dont Europe (40 %)", "usa": "dont États-Unis (35 %)",
        "japon": "dont Japon (10 %)", "emergents": "dont émergents (15 %)"}


def _nom(k: str, e: pd.DataFrame) -> str:
    return NOMS.get(k, e.loc[k, "classe"] if k in e.index else k)


def _v(x: float, signe: bool = False) -> str:
    if pd.isna(x):
        return "—"
    return ("+" if signe and x > 0 else "") + viz.fr(x, "%", 0)



@st.cache_data(show_spinner="Calcul des pertes dans chaque crise…")
def _risque() -> dict:
    s = allocation.series_risque()
    pendant, dates = allocation.pendant_la_baisse(s)
    return {"s": s, "pertes": allocation.pertes_crises(s),
            "pendant": pendant, "dates": dates}


def _bloc_risque() -> None:
    e = allocation.entrees()
    r = _risque()
    pertes, p = r["pertes"], r["pendant"]
    crises = allocation.CRISES

    st.markdown("#### Le risque de chaque support")
    st.markdown(
        "Deux questions : combien chaque support a perdu dans les crises, et "
        "s'il a perdu **en même temps** que les actions. Les actions forment "
        "désormais **une seule poche**, répartie selon une clé fixée à "
        "l'avance : Europe 40 %, États-Unis 35 %, Japon 10 %, émergents 15 %."
    )
    lignes = [[_nom(k, e)] + [_v(pertes.loc[k, c]) for c in crises]
              for k in pertes.index if k not in allocation.MIX_ACTIONS]
    st.table(pd.DataFrame(lignes, columns=["Pire baisse depuis le plus haut"]
                          + [f"{c} · {lib}" for c, (_, _, lib) in crises.items()])
             .set_index("Pire baisse depuis le plus haut"))
    st.caption("En 2011, la perte des actions part encore du sommet de 2007 : "
               "c'est la règle. Bitcoin : cotations depuis 2014.")
    pa = pertes.loc["poche_actions", "2008"]
    st.markdown(
        f"**Lecture.** Les actions perdent jusqu'à {viz.fr(-pa, '%', 0)}. "
        f"Sans amortisseur, on ne pourrait donc pas en détenir plus de "
        f"{viz.fr(15 / -pa * 100, '%', 0)} (15 ÷ {viz.fr(-pa, '', 0)}). Pour "
        f"aller au-delà, il faut des supports qui tiennent quand elles "
        f"baissent :"
    )
    st.markdown(
        f"- **2008 et 2011, crises de récession** : les emprunts d'État "
        f"montent ({_v(p.loc['etats_longs', '2008'], True)} en 2008), l'or "
        f"aussi ({_v(p.loc['or', '2008'], True)}).\n"
        f"- **2022, crise d'inflation** : plus d'amortisseur. États "
        f"{_v(p.loc['etats_longs', '2022'])}, indexées "
        f"{_v(p.loc['indexees', '2022'])}, avec les actions. C'est le régime "
        f"décrit à l'étape 2.\n"
        f"- **L'or** est le seul à tenir dans les quatre crises.\n"
        f"- **Matières premières et bitcoin** baissent avec les actions."
    )
    _graphique_baisses(r["s"])
    st.markdown(
        "Comme ce lien change d'une crise à l'autre, le calcul ne s'appuie "
        "pas sur une corrélation moyenne. Il fait traverser à chaque "
        "portefeuille candidat les vingt années, jour après jour, et mesure "
        "directement sa pire baisse."
    )

    st.markdown(
        "**➜ Les États amortissent les récessions, pas l'inflation ; l'or "
        "tient partout.** Reste à trouver la répartition qui rapporte le plus "
        "sans jamais perdre plus de 15 %."
    )


def _graphique_baisses(s: pd.DataFrame) -> None:
    fig = go.Figure()
    series = [("poche_actions", "Poche actions"),
              ("etats_longs", "États zone euro, 2-10 ans"),
              ("indexees", "Obligations indexées"), ("or", "Or")]
    for (k, nom), couleur in zip(series, viz.CATEGORICAL):
        dd = allocation.baisse_depuis_plus_haut(s[k]) * 100
        dd = dd.resample("W-FRI").min()
        fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values, name=nom, mode="lines",
            line={"color": couleur, "width": 2},
            hovertemplate=nom + " : %{y:.1f} %<extra></extra>"))
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
        "Baisse depuis le plus haut, octobre 2006 – aujourd'hui", height=440,
        hovermode="x unified",
        xaxis={"gridcolor": viz.GRID},
        yaxis={"title": "Écart au plus haut (%)", "gridcolor": viz.GRID,
               "ticksuffix": " %"}))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Chaque courbe est à 0 quand le support est à son plus haut, et "
        "descend quand il s'en éloigne. Zones grises : les quatre crises. "
        "Supports pris séparément : la baisse d'un portefeuille qui les "
        "combine sera calculée au bloc 3."
    )


# ----------------------------------------------------------------------
COURTS = {"actions_europe": "Europe", "usa": "États-Unis", "japon": "Japon",
          "emergents": "émergents", "etats_courts": "échelle AAA",
          "etats_longs": "États 2-10 ans", "credit_court": "crédit",
          "indexees": "indexées", "or": "or", "matieres": "matières premières"}


def _poids(x: float) -> str:
    return "—" if x < 0.005 else viz.fr(x * 100, "%", 0)


# Quatre familles, une couleur chacune, dans le même ordre sur tous les
# graphiques de répartition de l'onglet.
FAMILLES = {
    "Actions": ("actions_europe", "usa", "japon", "emergents"),
    "Emprunts d'État": ("etats_courts", "etats_longs"),
    "Obligations indexées": ("indexees",),
    "Or et autres": ("or", "credit_court", "matieres"),
}
COULEUR = dict(zip(FAMILLES, viz.CATEGORICAL))


def _graphique_supports(poids: dict, titre: str, montant: float | None = None
                        ) -> None:
    """Une barre par support, couleur = famille. Étiquette : % (et M€)."""
    fig = go.Figure()
    for fam, ks in FAMILLES.items():
        ks = [k for k in ks if poids.get(k, 0) >= 0.005]
        if not ks:
            continue
        noms = [COURTS[k][0].upper() + COURTS[k][1:] for k in ks]
        x = [poids[k] * 100 for k in ks]
        txt = [viz.fr(v, "%", 0) + (f" · {viz.fr(v * montant / 100 / 1e6, 'M€', 1)}"
                                    if montant else "") for v in x]
        fig.add_trace(go.Bar(
            y=noms, x=x, name=fam, orientation="h", text=txt,
            textposition="outside", cliponaxis=False,
            textfont={"color": viz.INK_2},
            marker={"color": COULEUR[fam], "cornerradius": 4},
            hovertemplate="%{y} : %{text}<extra>" + fam + "</extra>"))
    n = sum(1 for k in poids if poids[k] >= 0.005)
    fig.update_layout(**viz.layout(
        titre, height=90 + 34 * n, bargap=.25, showlegend=True,
        xaxis={"visible": False, "range": [0, max(poids.values()) * 125]},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)",
               "categoryorder": "array",
               "categoryarray": [COURTS[k][0].upper() + COURTS[k][1:]
                                 for ks in FAMILLES.values() for k in ks]}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _graphique_familles(poids: dict, titre: str) -> None:
    """Anneau des quatre familles : la répartition en un coup d'œil."""
    fam = {f: sum(poids.get(k, 0) for k in ks) for f, ks in FAMILLES.items()}
    fam = {f: v for f, v in fam.items() if v >= 0.005}
    fig = go.Figure(go.Pie(
        labels=list(fam), values=[v * 100 for v in fam.values()], hole=.55,
        sort=False, direction="clockwise",
        marker={"colors": [COULEUR[f] for f in fam],
                "line": {"color": "#ffffff", "width": 2}},
        texttemplate="%{value:.0f} %", textfont={"color": "#ffffff"},
        hovertemplate="%{label} : %{value:.1f} %<extra></extra>"))
    fig.update_layout(**viz.layout(titre, height=340))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _graphique_etapes(cols: dict, noms: dict) -> None:
    """Barres empilées à 100 % : la répartition par famille, règle après règle."""
    fig = go.Figure()
    etapes = [noms[n] for n in cols]
    for fam, ks in FAMILLES.items():
        x = [sum(c.get(k, 0) for k in ks) * 100 for c in cols.values()]
        if max(x) < 0.5:
            continue
        fig.add_trace(go.Bar(
            y=etapes, x=x, name=fam, orientation="h",
            text=[viz.fr(v, "%", 0) if v >= 4 else "" for v in x],
            textposition="inside", insidetextanchor="middle",
            textfont={"color": "#ffffff"},
            marker={"color": COULEUR[fam],
                    "line": {"color": "#ffffff", "width": 2}},
            hovertemplate="%{y} · " + fam + " : %{x:.1f} %<extra></extra>"))
    fig.update_layout(**viz.layout(
        "La répartition, règle après règle", height=330, barmode="stack",
        bargap=.3,
        xaxis={"visible": False, "range": [0, 100]},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)"}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _graphique_compte(serie: pd.Series, titre: str, par_titre: float) -> None:
    """Nombre de titres par catégorie, une seule couleur (une seule série)."""
    v = serie.value_counts().sort_values(ascending=False)
    fig = go.Figure(go.Bar(
        y=v.index, x=v.values, orientation="h",
        text=[f"{n} · {viz.fr(n * par_titre / 1e6, 'M€', 1)}" for n in v.values],
        textposition="outside", cliponaxis=False,
        textfont={"color": viz.INK_2},
        marker={"color": viz.CATEGORICAL[0], "cornerradius": 4},
        hovertemplate="%{y} : %{x} titres<extra></extra>"))
    fig.update_layout(**viz.layout(
        titre, height=90 + 28 * len(v), bargap=.3,
        xaxis={"visible": False, "range": [0, v.max() * 1.45]},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)"}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})



def _graphique_rendements(e: pd.DataFrame) -> None:
    """Rendement espéré par support, couleur = famille, repère à 4 %."""
    calc = e[~e["hors_calcul"]]
    fig = go.Figure()
    for fam, ks in FAMILLES.items():
        ks = [k for k in ks if k in calc.index]
        v = [calc.loc[k, "rendement"] for k in ks]
        fig.add_trace(go.Bar(
            y=[COURTS[k][0].upper() + COURTS[k][1:] for k in ks], x=v,
            name=fam, orientation="h", text=[viz.fr(x, "%", 2) for x in v],
            textposition="outside", cliponaxis=False,
            textfont={"color": viz.INK_2},
            marker={"color": COULEUR[fam], "cornerradius": 4},
            hovertemplate="%{y} : %{text}<extra>" + fam + "</extra>"))
    fig.add_vline(x=4, line={"color": viz.INK_2, "width": 1, "dash": "dot"},
                  annotation={"text": "4 % à battre",
                              "font": {"color": viz.INK_2, "size": 11}},
                  annotation_position="top")
    fig.update_layout(**viz.layout(
        "Rendement espéré par an", height=90 + 34 * len(calc), bargap=.25,
        xaxis={"visible": False, "range": [0, calc["rendement"].max() * 1.2]},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)"}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _bloc_libre() -> None:
    res = allocation.resultats()
    sc = res["scenarios"]
    lib = sc["libre"]
    p = lib["poids"]

    st.markdown("#### Ce que propose un calcul sans garde-fou")
    st.markdown(
        "On demande la répartition qui rapporte le plus, avec une seule "
        "exigence : jamais plus de 15 % de baisse entre 2006 et aujourd'hui "
        "(portefeuille remis à ses poids chaque mois). Aucune autre règle, "
        "pas même les 10 M€. Ce n'est pas une proposition : c'est pour voir "
        "ce que fait le calcul quand on le laisse seul."
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        _graphique_supports(p, "Le portefeuille du calcul libre")
    with c2:
        st.metric("Rendement espéré", _pct(lib["rendement_espere"]))
        st.metric("Pire baisse depuis le plus haut",
                  viz.fr(lib["pire_baisse"], "%", 1))

    top = sorted(p, key=p.get, reverse=True)[:2]
    st.markdown(
        f"**Lecture.** Deux supports font "
        f"{viz.fr((p[top[0]] + p[top[1]]) * 100, '%', 0)} du portefeuille : "
        f"les obligations indexées et les actions japonaises. La limite est "
        f"respectée, le rendement est élevé, et pourtant ce portefeuille est "
        f"inutilisable."
    )

    mj, ju = sc["moins_japon"], sc["japon_egal_usa"]
    jp = _risque()["pendant"]
    st.markdown(
        f"**Pourquoi ces deux-là ?** Pas pour leur rendement. Ramené à "
        f"{_pct(mj['variante']['rendement'])}, sous l'Europe, le Japon reste "
        f"à {_poids(mj['poids']['japon'])} ; il ne tombe à "
        f"{_poids(ju['poids']['japon'])} qu'au niveau des États-Unis. Le "
        f"calcul le garde pour sa **tenue en crise** "
        f"({_v(jp.loc['japon', '2020'])} en 2020, contre "
        f"{_v(jp.loc['actions_europe', '2020'])} pour l'Europe), en partie "
        # yen / euro : EURJPY=X (Yahoo), du sommet au creux des actions,
        # relevé le 2026-09-18 : +35 % en 2008, −8 % en 2022
        f"grâce au yen, +35 % contre l'euro en 2008 mais −8 % en 2022. Les "
        f"indexées sont les seules obligations au-dessus de 4 %, et leur "
        f"2008 est flatté par le remplaçant. Le calcul a **appris le passé "
        f"par cœur**."
    )
    st.markdown(
        f"**Ce qu'il ignore.**\n"
        f"- Le besoin de 10 M€ : {_poids(p['etats_courts'])} seulement sur "
        f"l'échelle AAA.\n"
        f"- La diversification : deux supports pour près de 90 %.\n"
        f"- La qualité des données : il charge la ligne la moins bien "
        f"mesurée en 2008.\n"
        f"- La clé des actions : l'Europe à zéro, alors que c'est la poche "
        f"construite titre par titre à l'étape 3."
    )

    st.markdown(
        f"**➜ {_pct(lib['rendement_espere'])} sur le papier, mais "
        f"inutilisable.** Les quatre défauts se corrigent par des règles, une "
        f"à une, en chiffrant ce que chacune coûte."
    )


# ----------------------------------------------------------------------
def _par_ligne(poids: dict) -> dict:
    """Poids par support, la poche actions éclatée selon la clé."""
    out = dict(poids)
    poche = out.pop("poche_actions", None)
    if poche is not None:
        for k, m in allocation.MIX_ACTIONS.items():
            out[k] = poche * m
    return out



def _bloc_regles() -> None:
    e = allocation.entrees()
    res = allocation.resultats()
    sc = res["scenarios"]
    ordre = ["libre"] + res["etapes"]

    st.markdown("#### Les règles, une par une, et ce qu'elles coûtent")
    st.markdown(
        "On reprend le calcul libre et on ajoute les règles l'une après "
        "l'autre, chaque ligne gardant les précédentes."
    )
    regles = {
        "r1_aaa": ("Au moins 10 % sur l'échelle AAA", "Les 10 M€ à décaisser"),
        "r2_cle": ("Actions 40 / 35 / 10 / 15", "Pas de pari sur le yen"),
        "r3_plafonds": ("Indexées ≤ 15 %, or ≤ 10 %, matières premières "
                        "≤ 5 %, crédit ≤ 20 %", "Pas de concentration"),
        "r4_marge": ("Pire baisse visée : 14 %", "Marge pour les remplaçants"),
    }
    lignes, prec = [], None
    for n in ordre:
        x = sc[n]
        regle, pourquoi = regles.get(n, ("Seule la limite de 15 %", "—"))
        lignes.append((regle, pourquoi, _pct(x["rendement_espere"]),
                       "—" if prec is None else
                       viz.fr(x["rendement_espere"] - prec, "pt", 2),
                       viz.fr(x["pire_baisse"], "%", 1)))
        prec = x["rendement_espere"]
    st.table(pd.DataFrame(lignes, columns=[
        "Règle ajoutée", "Pourquoi", "Rendement espéré", "Coût",
        "Pire baisse"]).set_index("Règle ajoutée"))

    cols = {n: _par_ligne(sc[n]["poids"]) for n in ordre}
    noms = {"libre": "Libre", "r1_aaa": "+ AAA", "r2_cle": "+ clé",
            "r3_plafonds": "+ plafonds", "r4_marge": "+ marge"}
    _graphique_etapes(cols, noms)

    r1, r2, r3, r4 = (sc[n] for n in res["etapes"])
    c2, c3 = cols["r2_cle"], cols["r3_plafonds"]
    t2 = sum(c2[k] for k in allocation.MIX_ACTIONS)
    t3 = sum(c3[k] for k in allocation.MIX_ACTIONS)
    t4 = sum(cols["r4_marge"][k] for k in allocation.MIX_ACTIONS)
    jp = _risque()["pendant"]

    def cout(a: dict, b: dict) -> str:
        return viz.fr(a["rendement_espere"] - b["rendement_espere"], "pt", 2)

    st.markdown(
        f"**Lecture.**\n"
        f"- **Les 10 M€ en AAA** ne coûtent presque rien ({cout(r1, sc['libre'])}).\n"
        f"- **La clé des actions** est la règle la plus chère "
        f"({cout(r2, r1)}) : privé du Japon, le calcul se replie sur les "
        f"indexées ({_poids(c2['indexees'])}) et réduit les actions à "
        f"{_poids(t2)}.\n"
        f"- **Les plafonds** ({cout(r3, r2)}) remplacent les indexées par "
        f"des États à 2-10 ans, et les actions **remontent** à {_poids(t3)} : "
        f"en 2020, les indexées avaient baissé avec les actions "
        f"({_v(jp.loc['indexees', '2020'])}), les États presque pas "
        f"({_v(jp.loc['etats_longs', '2020'])}).\n"
        f"- **La marge** ({cout(r4, r3)}) retire un point de perte ; les "
        f"actions passent à {_poids(t4)}.\n\n"
        f"Crédit et matières premières restent à zéro partout : le crédit "
        f"court rapporte moins que les États "
        f"({_pct(e.loc['credit_court', 'rendement'])} contre "
        f"{_pct(e.loc['etats_longs', 'rendement'])}), les matières premières "
        f"baissent avec les actions."
    )

    total = r4["rendement_espere"] - sc["libre"]["rendement_espere"]
    c = st.columns(4)
    c[0].metric("Rendement espéré retenu", _pct(r4["rendement_espere"]))
    c[1].metric("Au-dessus des 4 % à battre",
                viz.fr(r4["rendement_espere"] - 4, "pt", 2))
    c[2].metric("Coût total des règles", viz.fr(total, "pt", 2))
    c[3].metric("Pire baisse, 2006-2026", viz.fr(r4["pire_baisse"], "%", 1))

    st.markdown(
        f"**➜ Les règles coûtent {viz.fr(-total, 'point', 2)} et laissent "
        f"{viz.fr(r4['rendement_espere'] - 4, 'point', 2)} au-dessus des "
        f"4 %.** Reste à passer des pourcentages aux millions d'euros."
    )


# ----------------------------------------------------------------------
def _me(v: float, dec: int = 2) -> str:
    return viz.fr(v / 1e6, "M€", dec)


@st.cache_data(show_spinner="Sélection des 30 titres…")
def _trente() -> pd.DataFrame:
    return actions.selection(actions.univers())



def _bloc_retenu() -> None:
    e = allocation.entrees()
    res = allocation.resultats()
    r4 = res["scenarios"][allocation.RETENU]
    w = allocation.poids_retenus()
    M = allocation.MONTANT
    cl = fonds.charger()["classes"]
    fonds_de = ("usa", "japon", "emergents", "indexees", "or", "matieres")

    st.markdown("#### Le portefeuille retenu, en millions d'euros")
    g1, g2 = st.columns([2, 3])
    with g1:
        _graphique_familles(w, "Par grande famille")
    with g2:
        _graphique_supports(w, "Par support, en % et en M€", montant=M)

    lignes, contrib = [], 0.0
    for k, x in w.items():
        if x < 0.0005:
            continue
        sup = e.loc[k, "support"]
        if k in fonds_de:
            c = cl[k]
            sup = f"{c['retenu'].split('.')[0]} · {c['candidats'][c['retenu']]['nom']}"
        ct = x * e.loc[k, "rendement"]
        contrib += ct
        lignes.append((e.loc[k, "classe"], sup, _me(x * M, 1),
                       _pct(e.loc[k, "rendement"])))
    st.table(pd.DataFrame(lignes, columns=[
        "Classe", "Support", "Montant", "Rendement espéré"]).set_index("Classe"))

    part_act = sum(w[k] for k in allocation.MIX_ACTIONS)
    oblig = w["etats_courts"] + w["etats_longs"] + w["indexees"]
    st.markdown(
        f"**Lecture.** Les actions font {_poids(part_act)} du patrimoine mais "
        f"{_poids(sum(w[k] * e.loc[k, 'rendement'] for k in allocation.MIX_ACTIONS) / contrib)} "
        f"du rendement espéré : elles portent l'objectif de 4 %, les "
        f"obligations tiennent la limite de 15 %."
    )

    # --- les 30 actions européennes ----------------------------------
    sel = _trente()
    par_titre = w["actions_europe"] * M / len(sel)
    st.markdown(
        f"**Les 30 actions européennes** : {_me(w['actions_europe'] * M, 1)} "
        f"à parts égales, soit {_me(par_titre)} par titre."
    )
    g1, g2 = st.columns(2)
    with g1:
        _graphique_compte(sel["secteur"], "Par secteur (titres · M€)", par_titre)
    with g2:
        _graphique_compte(sel["pays"], "Par pays (titres · M€)", par_titre)

    # --- en direct et en fonds ---------------------------------------
    sv = taux.charger()["svensson"]
    ech = obligations.echelle(allocation.TRANCHES, sv["aaa"])
    investi = w["etats_courts"] * M
    f = investi / sum(x["cout"] for x in ech)
    par_marche = w["etats_longs"] * M / len(allocation.ECHELLE_LONGUE)
    frais = sum(w[k] * M * cl[k]["candidats"][cl[k]["retenu"]]["frais"] / 100
                for k in fonds_de if w[k] >= 0.0005)
    part_max = max(w[k] * M / (cl[k]["candidats"][cl[k]["retenu"]]["taille"] * 1e6)
                   for k in fonds_de if w[k] >= 0.0005)
    st.markdown(
        f"**Les emprunts d'État en direct** : {_me(investi)} sur l'échelle "
        f"AAA, en {len(ech)} tranches de 6 à 24 mois, qui rendront "
        f"{_me(sum(x['montant'] for x in ech) * f)} ; les 10 M€ sont couverts. "
        f"Puis {len(allocation.ECHELLE_LONGUE)} × {_me(par_marche)} sur "
        f"l'échelle zone euro de 2 à 10 ans.\n\n"
        f"**Les fonds** : aucune ligne ne dépasse "
        f"{viz.fr(part_max * 100, '%', 2)} de son fonds, on entre et sort "
        f"sans peser sur les prix. Frais : {viz.fr(frais / 1e3, 'k€', 0)} "
        f"par an, soit {viz.fr(frais / M * 100, '%', 2)} du patrimoine."
    )

    # --- brut, puis net : l'objectif du client est un objectif NET --------
    f_inst = frais / M * 100
    f_mandat = ips.FRAIS_MANDAT * 100
    net = ips.rendement_net(r4["rendement_espere"], f_inst)
    seuil = ips.INFLATION_TARGET * 100

    st.markdown("**Du rendement brut à ce qui reste au client.**")
    st.table(pd.DataFrame([
        ("Rendement espéré, brut", _pct(r4["rendement_espere"]),
         "Somme des rendements de chaque ligne, pondérée"),
        ("− Frais des instruments", "− " + viz.fr(f_inst, "pt", 2),
         f"{viz.fr(frais / 1e3, 'k€', 0)} par an, ETF uniquement"),
        ("− Frais de mandat", "− " + viz.fr(f_mandat, "pt", 2),
         "Négocié sur la taille d'actifs"),
        ("**Rendement net**", "**" + _pct(net) + "**",
         "**C'est lui qui doit battre l'inflation**"),
    ], columns=["", "Taux", "D'où il vient"]).set_index(""))

    st.markdown(
        f"**Pourquoi ce détour.** L'objectif du client n'est pas de produire "
        f"{_pct(seuil)} bruts, c'est de **conserver** son pouvoir d'achat : "
        f"ce qui doit battre l'inflation, c'est ce qui reste dans sa poche. "
        f"Comparer un rendement brut à un seuil net surévalue la marge de "
        f"{viz.fr(f_inst + f_mandat, 'point', 2)}. La fiscalité, hors "
        f"périmètre de cet exercice, en retirerait encore environ 0,30."
    )

    c = st.columns(4)
    c[0].metric("Rendement espéré, brut", _pct(r4["rendement_espere"]))
    c[1].metric("Rendement net", _pct(net),
                delta=viz.fr(net - seuil, "pt", 2) + " vs inflation")
    c[2].metric("Pire baisse, 2006-2026", viz.fr(r4["pire_baisse"], "%", 1))
    c[3].metric("Rendement obtenu, 2006-2026*",
                viz.fr(r4["realise"], "%", 2) + " / an")
    st.caption(
        "* Rééquilibré chaque mois sur les séries du bloc 1. Ne se compare "
        "pas au rendement espéré : le passé comptait dix ans de taux "
        "négatifs, l'avenir part de taux à 3 %. Et il s'est déroulé sous une "
        "autre inflation que les 4 % de l'énoncé — l'étape 5 le juge contre "
        "l'inflation réellement constatée."
    )

    st.markdown("#### Conclusion de l'étape 4")
    st.markdown(
        f"100 M€ : {_poids(part_act)} d'actions en quatre zones, dont 30 "
        f"titres européens en direct ; {_poids(oblig)} d'obligations d'État, "
        f"dont deux échelles en direct ; {_poids(w['or'])} d'or. Rendement "
        f"espéré {_pct(r4['rendement_espere'])} brut, soit {_pct(net)} net "
        f"de frais — {viz.fr(net - seuil, 'point', 2)} au-dessus de "
        f"l'inflation de l'énoncé. Pire baisse "
        f"{viz.fr(r4['pire_baisse'], '%', 1)}. Question que le calcul ne "
        f"s'est pas posée : combien de temps reste-t-il sous son plus haut ? "
        f"C'est l'étape 5."
    )
