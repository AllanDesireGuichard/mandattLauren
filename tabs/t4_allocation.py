"""
Étape 4 — Allocation.

Construite bloc par bloc, comme les onglets 2 et 3. Plan validé avec Allan
le 2026-09-18 : 1 les entrées ; 2 le risque ; 3 l'optimisation libre ;
4 les contraintes et leur coût ; 5 le portefeuille retenu, en M€.
Bloc 4 bis ajouté le 2026-09-25, à la demande d'Allan : comment le calcul
trouve sa réponse, et pourquoi il ne retient que 3,3 % d'or.

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

from core import (actions, allocation, fonds, ips, obligations, outlook,
                  pedago, taux, viz)


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)



def render() -> None:
    pedago.chaine(4)
    pedago.etape(
        4, "Allocation",
        "Combien placer sur chaque support pour rapporter au moins 4 % par an "
        "sans jamais perdre plus de 15 %. Cinq temps : les ingrédients, le "
        "risque de chaque support, un calcul sans garde-fou, les garde-fous "
        "et leur coût, comment le calcul s'y prend, puis le portefeuille en "
        "millions d'euros.",
    )
    _bloc_entrees()
    _bloc_risque()
    _bloc_libre()
    _bloc_regles()
    _bloc_retenu()


# ----------------------------------------------------------------------
def _bloc_entrees() -> None:
    e = allocation.entrees()
    ctl = e["controle"]

    st.markdown("#### Ce qui entre dans le calcul")
    st.markdown(
        "**La règle retenue** : une perte mesurée **depuis le plus haut**, "
        "sur **les 100 M€ ensemble**, qui ne dépasse jamais 15 % dans les "
        "crises de 2008, 2011, 2020 et 2022. Pas de crypto."
    )

    # Le graphique des rendements espérés par classe a été retiré le
    # 2026-09-25 : il reproduisait à l'identique celui de l'étape 2, qui les
    # PRODUIT. Ici, seule la lecture qu'on en tire est utile.
    calc = e[~e["hors_calcul"]]
    bat = calc[calc["rendement"] > 4]
    calc = e[~e["hors_calcul"]]
    bat = calc[calc["rendement"] > 4]
    st.markdown(
        f"**{len(bat)} lignes sur {len(calc)} dépassent les 4 %** : les "
        f"quatre zones d'actions et les obligations indexées (rendements "
        f"espérés détaillés à l'étape 2)."
    )

    st.markdown(
        "**L'historique** : le vrai support dès qu'il existe, et avant lui "
        "un remplaçant qui suit le même marché. Toutes les séries partent "
        "d'octobre 2006, avant le sommet des actions de juillet 2007."
    )
    st.caption(
        f"Limites assumées : les **indexées** sont flattées avant 2009 (leur "
        f"remplaçant est un emprunt d'État classique, qui a mieux tenu en "
        f"2008) ; le **crédit** est la ligne la moins bien mesurée "
        f"(corrélation {viz.fr(ctl['credit_court']['correlation'], '', 2)}) ; "
        f"le risque des **actions européennes** est mesuré sur l'indice, pas "
        f"sur les titres retenus."
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
    hors, crise, semaines = allocation.correlations(s)
    return {"s": s, "pertes": allocation.pertes_crises(s),
            "pendant": pendant, "dates": dates,
            "corr": (hors, crise), "semaines": semaines}


def _bloc_risque() -> None:
    e = allocation.entrees()
    r = _risque()
    pertes, p = r["pertes"], r["pendant"]
    crises = allocation.CRISES

    st.markdown("#### Le risque de chaque support")
    st.markdown(
        "Ce que chaque support a perdu dans les quatre crises, et s'il a "
        "perdu **en même temps** que les actions."
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
        f"**Les actions perdent jusqu'à {viz.fr(-pa, '%', 0)}.** Sans "
        f"amortisseur, on ne pourrait donc en détenir que "
        f"{viz.fr(15 / -pa * 100, '%', 0)} du patrimoine."
    )
    st.markdown(
        "**2008 et 2011** (récession) : les emprunts d'État montent, ils "
        "amortissent. **2022** (inflation) : ils baissent avec les actions, "
        "l'amortisseur disparaît. **L'or est le seul à tenir dans les "
        "quatre.**"
    )
    _graphique_baisses(r["s"])

    _correlations(r)



# Libelles courts : dans deux graphiques cote a cote, les noms complets
# passent a l'oblique et deviennent illisibles.
CORR_NOMS = {"poche_actions": "Actions", "etats_courts": "AAA courts",
             "etats_longs": "États 2-10", "credit_court": "Crédit",
             "indexees": "Indexées", "or": "Or", "matieres": "Matières"}

# Echelle centree sur zero, bornee a la main : symetrique, sinon le gris du
# milieu ne tombe plus sur la corrélation nulle et la couleur ment.
CORR_BORNE = 0.8


def _heatmap_corr(m: pd.DataFrame, titre: str, barre: bool) -> go.Figure:
    """Une matrice de corrélation. Diagonale retirée : elle vaut 100 partout
    et n'apprend rien, mais elle écraserait l'échelle de couleur."""
    noms = [CORR_NOMS[k] for k in m.index]
    z = m.to_numpy(copy=True) * 100
    for i in range(len(z)):
        z[i, i] = float("nan")
    fig = go.Figure(go.Heatmap(
        z=z, x=noms, y=noms, zmin=-CORR_BORNE * 100, zmax=CORR_BORNE * 100,
        colorscale=viz.echelle_divergente(), showscale=barre,
        xgap=2, ygap=2,
        text=[[("" if pd.isna(v) else viz.fr(v, "", 0)) for v in ligne]
              for ligne in z],
        texttemplate="%{text}", textfont={"size": 12, "color": viz.INK},
        hovertemplate="%{y} et %{x} : %{z:.0f} %<extra></extra>",
        colorbar={"title": {"text": "%", "font": {"size": 11}},
                  "thickness": 10, "len": 0.8, "tickfont": {"size": 10},
                  "outlinewidth": 0},
    ))
    fig.update_layout(**viz.layout(titre, height=340))
    fig.update_xaxes(showgrid=False, zeroline=False, side="top")
    fig.update_yaxes(showgrid=False, zeroline=False, autorange="reversed")
    return fig


def _correlations(r: dict) -> None:
    hors, crise = r["corr"]
    n = r["semaines"]
    st.markdown("#### Les supports bougent-ils ensemble ?")
    st.markdown(
        "Corrélations hors crise, puis pendant les crises : 100 = les deux "
        "supports bougent ensemble, −100 = en sens contraire."
    )
    g, d = st.columns(2)
    with g:
        st.plotly_chart(_heatmap_corr(
            hors, f"Hors crise · {n['hors_crise']} semaines", False),
            width="stretch")
    with d:
        st.plotly_chart(_heatmap_corr(
            crise, f"En crise · {n['en_crise']} semaines", True),
            width="stretch")
    st.caption(
        "Variations hebdomadaires en euros, octobre 2006 - septembre 2026. "
        "Crises : les quatre fenêtres datées plus haut. Bitcoin écarté : ses "
        "cotations ne commencent qu'en 2014, le garder mélangerait deux "
        "périodes dans le même tableau. Diagonale retirée (elle vaut 100)."
    )

    # La paire de la poche defensive qui se resserre le plus : hors actions
    # et hors diagonale, le plus fort ecart entre la crise et le reste.
    a = "poche_actions"
    ecarts = (crise - hors).drop(index=a, columns=a)
    for k in ecarts.index:
        ecarts.loc[k, k] = float("nan")
    st.markdown(
        f"**Face aux actions, deux supports se retournent quand la crise "
        f"arrive** : l'échelle AAA passe de "
        f"{_v(hors.loc[a, 'etats_courts'] * 100)} à "
        f"{_v(crise.loc[a, 'etats_courts'] * 100)}, l'or de "
        f"{_v(hors.loc[a, 'or'] * 100, True)} à "
        f"{_v(crise.loc[a, 'or'] * 100, True)}."
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



def _bloc_libre() -> None:
    res = allocation.resultats()
    sc = res["scenarios"]
    lib = sc["libre"]
    p = lib["poids"]

    st.markdown("#### Ce que propose un calcul sans garde-fou")
    st.markdown(
        "Répartition qui rapporte le plus sous la **seule** limite de 15 %, "
        "sans aucune autre règle."
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
        f"Deux supports font "
        f"{viz.fr((p[top[0]] + p[top[1]]) * 100, '%', 0)} du portefeuille : "
        f"les indexées et les actions japonaises. La limite est respectée, "
        f"le rendement est élevé, **et ce portefeuille est inutilisable**."
    )

    st.markdown(
        f"Le calcul ne les garde pas pour leur rendement mais pour leur "
        f"tenue en crise : ramené au niveau de l'Europe, le Japon reste à "
        f"{_poids(sc['moins_japon']['poids']['japon'])}. Il a **appris le "
        f"passé par cœur**."
    )
    st.markdown(
        f"**Ce qu'il ignore** : le besoin de 10 M€ "
        f"({_poids(p['etats_courts'])} sur l'échelle AAA), la "
        f"diversification (deux supports pour près de 90 %), la qualité des "
        f"données (il charge la ligne la moins bien mesurée en 2008), et la "
        f"clé des actions — l'Europe à zéro, alors que c'est la poche "
        f"construite titre par titre à l'étape 3."
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
    t3 = sum(c3[k] for k in allocation.MIX_ACTIONS)

    def cout(a: dict, b: dict) -> str:
        return viz.fr(a["rendement_espere"] - b["rendement_espere"], "pt", 2)

    st.markdown(
        f"**Les 10 M€ en AAA** ne coûtent presque rien ({cout(r1, sc['libre'])}). "
        f"**La clé des actions** est la règle la plus chère ({cout(r2, r1)}) : "
        f"c'est le prix du renoncement au pari sur le yen. **Les plafonds** "
        f"({cout(r3, r2)}) font **remonter** les actions à {_poids(t3)}, les "
        f"États 2-10 ans amortissant mieux 2020 que les indexées. **La "
        f"marge** ({cout(r4, r3)}) retire un point de perte. Crédit et "
        f"matières premières restent à zéro partout."
    )

    total = r4["rendement_espere"] - sc["libre"]["rendement_espere"]
    c = st.columns(4)
    c[0].metric("Rendement espéré retenu", _pct(r4["rendement_espere"]))
    c[1].metric("Au-dessus des 4 % à battre",
                viz.fr(r4["rendement_espere"] - 4, "pt", 2))
    c[2].metric("Coût total des règles", viz.fr(total, "pt", 2))
    c[3].metric("Pire baisse, 2006-2026", viz.fr(r4["pire_baisse"], "%", 1))



def _ecartes(c: dict) -> str:
    """
    Ce qui a fait perdre les autres candidats, et non la règle de sélection.

    La règle est la même pour les cinq classes — conforme, plus de 1 Md€,
    puis les frais les plus bas — donc la recopier dans chaque ligne
    n'apprend rien. Ce qui diffère, c'est POURQUOI les concurrents sont
    tombés, et data/fonds.json porte un verdict par candidat.
    """
    par_motif: dict[str, list[str]] = {}
    for t, r in c["candidats"].items():
        if t == c["retenu"]:
            continue
        par_motif.setdefault(r["verdict"], []).append(t.split(".")[0])
    bouts = [f"{m} ({', '.join(sorted(v))})" for m, v in par_motif.items()]
    return f"{len(c['candidats'])} examinés · " + " · ".join(bouts)


def _echeance(a: float) -> str:
    """0.5 -> « 6 mois », 2.0 -> « 24 mois ». L'échelle courte se lit en mois."""
    return viz.fr(a * 12, "mois", 0)


def _me(v: float, dec: int = 2) -> str:
    return viz.fr(v / 1e6, "M€", dec)


@st.cache_data(show_spinner="Sélection des 30 titres…")
def _lignes_actions() -> pd.DataFrame:
    """
    Les titres RÉELLEMENT détenus, c'est-à-dire la sélection finale de
    l'étape 3 — pas les trente présélectionnés. Le 2026-09-25 cette fonction
    renvoyait encore les trente : le tableau du portefeuille annonçait
    « 15 titres en direct » et les deux graphiques juste en dessous
    répartissaient la même poche sur trente lignes, à 405 k€ au lieu de
    811 k€. Troisième fois que ce nombre est faux quelque part ; il ne doit
    venir que d'ici, et d'ici que de core/outlook.
    """
    return outlook.final(actions.selection(actions.univers()))



def _bloc_retenu() -> None:
    e = allocation.entrees()
    res = allocation.resultats()
    r4 = res["scenarios"][allocation.RETENU]
    w = allocation.poids_retenus()
    M = allocation.MONTANT
    cl = fonds.charger()["classes"]
    fonds_de = ("usa", "japon", "emergents", "indexees", "or", "matieres")

    st.markdown("#### Le portefeuille retenu, en millions d'euros")
    # Le graphique par support avait été retiré le 2026-09-25 comme doublon
    # du tableau qui suit, puis REMIS le même jour : Allan le voulait. Il
    # donne les mêmes montants, mais il les donne à l'œil — la longueur des
    # barres se compare, une colonne de chiffres se lit.
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
        # Le nombre de titres vient de l'étape 3, pas du libellé figé dans
        # data/indices_longs.json : il y était resté à 30 après le passage
        # à 15, et cet onglet démentait l'onglet 3.
        if k == "actions_europe":
            sup = f"{outlook.N_FINAL} {sup}"
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

    # --- les actions européennes en direct ---------------------------
    sel = _lignes_actions()
    par_titre = w["actions_europe"] * M / len(sel)
    st.markdown(
        f"**Les {len(sel)} actions européennes** : "
        f"{_me(w['actions_europe'] * M, 1)} à parts égales, soit "
        f"{_me(par_titre)} par titre."
    )
    g1, g2 = st.columns(2)
    with g1:
        _graphique_compte(sel["secteur"], "Par secteur (titres · M€)", par_titre)
    with g2:
        _graphique_compte(sel["pays"], "Par pays (titres · M€)", par_titre)

    # --- ce qu'on achète, en direct puis en fonds --------------------
    # Réécrit le 2026-09-25. Allan : « fait un truc très concret pour l'oblig
    # et les fonds, donne ce qu'il y a et décrit les fonds et pourquoi ils
    # sont choisis [...] je veux juste ce qu'on a et ce qu'on prend, détaillé
    # clair et synthétique ». Deux tableaux, aucun commentaire — et PAS de
    # graphique de courbe des taux : il est déjà à l'étape 2.
    sv = taux.charger()["svensson"]
    ech = obligations.echelle(allocation.TRANCHES, sv["aaa"])
    investi = w["etats_courts"] * M
    f = investi / sum(x["cout"] for x in ech)
    par_marche = w["etats_longs"] * M / len(allocation.ECHELLE_LONGUE)

    st.markdown("**Les obligations d'État, achetées en direct**")
    lignes = [(f"AAA · {_echeance(x['echeance'])}", _me(x["cout"] * f, 2),
               _me(x["montant"] * f, 2), _pct(x["taux"]), "—")
              for x in ech]
    for m in allocation.ECHELLE_LONGUE:
        a = obligations.analyse(m, sv["toutes"])
        # achetée au pair : le remboursement égale l'investi, le rendement
        # vient des coupons — contrairement à l'échelle AAA, achetée sous
        # le pair et remboursée au nominal.
        lignes.append((f"Zone euro · {m} ans", _me(par_marche, 2),
                       _me(par_marche, 2) + " + coupons",
                       _pct(a["rendement"]), viz.fr(a["sensibilite"], "", 1)))
    st.table(pd.DataFrame(lignes, columns=[
        "Ligne", "Investi", "Ce qu'on récupère", "Taux à l'achat",
        "Sensibilité"]).set_index("Ligne"))
    st.caption(
        f"L'échelle AAA couvre les 10 M€ à décaisser : {_me(investi)} "
        f"investis rendent {_me(sum(x['montant'] for x in ech) * f)} à date "
        f"fixe et sans rien vendre : elle est achetée sous le pair et "
        f"remboursée au nominal. L'échelle zone euro est achetée au pair et "
        f"détenue jusqu'à l'échéance — son rendement vient des coupons, et "
        f"la sensibilité indique ce que la ligne perdrait en prix si les "
        f"taux montaient d'un point, ce qui n'a d'effet que si on la vend "
        f"avant terme. Courbes de la BCE au {taux.date_fr(sv['date'])}."
    )

    st.markdown("**Les fonds, pour les classes qu'on ne détient pas en direct**")
    rows = []
    for k in fonds.ORDRE:
        if k not in cl or w.get(k, 0) < 0.0005:
            continue
        c = cl[k]
        r = c["candidats"][c["retenu"]]
        rows.append((
            e.loc[k, "classe"],
            f"{c['retenu'].split('.')[0]} · {r['nom']}",
            r["indice"] or "Or physique, pas d'indice",
            _me(w[k] * M, 1),
            _pct(r["frais"]),
            viz.fr(r["taille"] / 1000, "Md€", 1),
            _ecartes(c),
        ))
    st.table(pd.DataFrame(rows, columns=[
        "Classe", "Fonds retenu", "Indice suivi", "Montant", "Frais",
        "Taille", "Ce qui a écarté les autres"]).set_index("Classe"))

    frais = sum(w[k] * M * cl[k]["candidats"][cl[k]["retenu"]]["frais"] / 100
                for k in fonds_de if w[k] >= 0.0005)
    part_max = max(w[k] * M / (cl[k]["candidats"][cl[k]["retenu"]]["taille"] * 1e6)
                   for k in fonds_de if w[k] >= 0.0005)
    st.caption(
        f"Règle de sélection, la même pour tous : filtre ESG conforme aux "
        f"exclusions du mandat, taille supérieure à 1 Md€, puis les frais "
        f"les plus bas. Tous sont à réplication physique et domiciliés dans "
        f"l'Union, sauf l'or, adossé à du métal déposé en Allemagne. "
        f"Aucune ligne ne dépasse {viz.fr(part_max * 100, '%', 2)} de son "
        f"fonds. Frais totaux {viz.fr(frais / 1e3, 'k€', 0)} par an, soit "
        f"{viz.fr(frais / M * 100, '%', 2)} du patrimoine."
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


    c = st.columns(4)
    c[0].metric("Rendement espéré, brut", _pct(r4["rendement_espere"]))
    c[1].metric("Rendement net", _pct(net),
                delta=viz.fr(net - seuil, "pt", 2) + " vs inflation")
    c[2].metric("Pire baisse, 2006-2026", viz.fr(r4["pire_baisse"], "%", 1))
    c[3].metric("Rendement obtenu, 2006-2026*",
                viz.fr(r4["realise"], "%", 2) + " / an")
    st.caption(
        "* Rééquilibré chaque mois. Ne se compare pas au rendement espéré : "
        "le passé comptait dix ans de taux négatifs, l'avenir part de taux "
        "à 3 %."
    )

    st.markdown("#### Conclusion de l'étape 4")
    st.markdown(
        f"100 M€ : {_poids(part_act)} d'actions en quatre zones, dont "
        f"{len(sel)} titres européens en direct ; {_poids(oblig)} "
        f"d'obligations d'État ; {viz.fr(w['or'] * 100, '%', 1)} d'or. "
        f"Rendement espéré {_pct(net)} net de frais, "
        f"{viz.fr(net - seuil, 'point', 2)} au-dessus de l'inflation de "
        f"l'énoncé. Pire baisse {viz.fr(r4['pire_baisse'], '%', 1)}."
    )
