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
    _bloc_calcul()
    _bloc_retenu()


# ----------------------------------------------------------------------
def _bloc_entrees() -> None:
    e = allocation.entrees()
    ctl = e["controle"]

    st.markdown("#### Ce qui entre dans le calcul")
    st.markdown(
        "**La règle.** L'étape 1 laissait les 15 % à préciser ; on retient "
        "la lecture la plus exigeante : une perte mesurée **depuis le plus "
        "haut**, sur **les 100 M€ ensemble**, qui ne dépasse jamais 15 % "
        "dans **les crises de 2008, 2011, 2020 et 2022**. Pas de crypto : "
        "elle ne rapporte rien (étape 2) et baisse avec les actions."
    )

    # Le graphique des rendements espérés par classe a été retiré le
    # 2026-09-25 : il reproduisait à l'identique celui de l'étape 2, qui les
    # PRODUIT. Ici, seule la lecture qu'on en tire est utile.
    calc = e[~e["hors_calcul"]]
    bat = calc[calc["rendement"] > 4]
    st.markdown(
        f"**Ce que chaque support doit rapporter.** Seules {len(bat)} lignes "
        f"sur {len(calc)} dépassent les 4 % : les quatre zones d'actions et "
        f"les obligations indexées (rendements espérés détaillés à "
        f"l'étape 2). Chaque euro placé ailleurs devra être compensé par des "
        f"actions : c'est la tension entre les 4 % et les 15 %."
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
    st.caption(
        f"**Limites assumées.** Les remplaçants suivent bien leur support "
        f"(corrélation de 0,83 à 0,95), sauf deux lignes. Les **indexées** "
        f"sont flattées : avant 2009 le remplaçant est un emprunt d'État "
        f"classique, qui a mieux tenu en 2008. Le **crédit** est la ligne la "
        f"moins bien mesurée — sa prime est reconstituée avant 2016 sur les "
        f"écarts américains, corrélation "
        f"{viz.fr(ctl['credit_court']['correlation'], '', 2)}. Et le risque "
        f"des **actions européennes** est mesuré sur l'indice, pas sur les "
        f"titres retenus : choisis avec les données d'aujourd'hui, ils ont "
        f"un passé flatteur par construction."
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

    _correlations(r)
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
        "Le tableau précédent dit combien chacun a perdu. Celui-ci dit s'ils "
        "perdent **en même temps**. Deux supports à 100 font la même chose ; "
        "à 0 ils sont indépendants ; en dessous de 0, l'un monte quand "
        "l'autre baisse. La mesure est faite deux fois : sur les semaines "
        "ordinaires, puis sur les seules semaines de crise — parce que c'est "
        "là, et seulement là, que la question compte."
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
    pire = ecarts.stack().idxmax()
    st.markdown(
        f"**Lecture.** Face aux actions, deux supports se retournent quand la "
        f"crise arrive :\n"
        f"- **L'échelle AAA** passe de {_v(hors.loc[a, 'etats_courts'] * 100)} "
        f"à {_v(crise.loc[a, 'etats_courts'] * 100)} : elle ne suit pas les "
        f"actions en temps normal, et s'y oppose franchement quand elles "
        f"chutent.\n"
        f"- **L'or** fait le même chemin, de "
        f"{_v(hors.loc[a, 'or'] * 100, True)} à "
        f"{_v(crise.loc[a, 'or'] * 100, True)}. C'est ce qui le rend utile "
        f"malgré un rendement espéré de 4 % seulement.\n"
        f"- **Les matières premières** restent le support le plus lié aux "
        f"actions ({_v(crise.loc[a, 'matieres'] * 100, True)} en crise) : "
        f"elles diversifient peu, d'où la place réduite qu'elles prendront.\n"
        f"- **Le revers, et il est réel** : la poche défensive se resserre "
        f"sur elle-même. {CORR_NOMS[pire[0]]} et {CORR_NOMS[pire[1]]} "
        f"passent de {_v(hors.loc[pire] * 100)} à {_v(crise.loc[pire] * 100)}. "
        f"Les amortisseurs deviennent un seul pari au moment où on compte "
        f"sur eux — c'est la raison de ne pas concentrer le défensif sur une "
        f"seule maturité."
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
# Bloc 4 bis — comment le calcul trouve sa réponse, et le cas de l'or
# ----------------------------------------------------------------------
def _bloc_calcul() -> None:
    """
    La mécanique de l'optimisation, et l'or comme cas d'école.

    Ajouté le 2026-09-25 : Allan a demandé « comment l'optimisateur s'en
    sort » et « pourquoi on se retrouve avec 3 % de gold ». Les deux
    questions n'en font qu'une — l'or est le meilleur endroit pour montrer
    ce que le calcul fait vraiment, parce que c'est le seul poids que
    personne n'a choisi et qu'aucune contrainte ne fixe.
    """
    res = allocation.resultats()
    w = allocation.poids_retenus()
    e = allocation.entrees()
    part_act = sum(w[k] for k in allocation.MIX_ACTIONS)

    st.markdown("#### Comment le calcul trouve sa réponse")
    st.markdown(
        "**La question posée au calcul tient en une phrase** : parmi tous "
        "les partages possibles des 100 M€, lequel rapporte le plus sans "
        "jamais avoir perdu plus que la limite ? Trois pièces, et c'est "
        "tout."
    )
    st.table(pd.DataFrame([
        ("Ce qu'on maximise", "Le rendement espéré du portefeuille",
         "La moyenne des rendements de chaque support, pondérée par son "
         "poids. Les rendements viennent de l'étape 2 pour les actions et "
         "les indexées, de l'étape 3 pour les obligations."),
        ("Ce qu'on s'interdit", "Une perte au-delà de la limite",
         f"Pour chaque partage essayé, on **rejoue les vingt ans** : on "
         f"place les 100 M€ selon ces poids en octobre 2006, on les remet à "
         f"ces mêmes poids **chaque mois**, et on suit la valeur semaine "
         f"après semaine. On mesure alors la plus forte baisse depuis un "
         f"sommet. Elle doit rester sous "
         f"{viz.fr(allocation.LIMITE_MARGE * 100, '%', 0)}."),
        ("Ce qui borne les poids", "Positifs, somme de 100 %, et les règles",
         "Pas de vente à découvert ni de levier, au moins 10 % sur l'échelle "
         "AAA pour les 10 M€ à décaisser, la clé actions 40/35/10/15, et les "
         "plafonds par support."),
    ], columns=["", "En un mot", "Comment c'est calculé"]).set_index(""))

    st.markdown(
        "**Pourquoi ça ne se résout pas par une formule.** Le Markowitz des "
        "manuels a une solution fermée parce qu'il mesure le risque par la "
        "variance, qui est lisse et convexe. Notre exigence ne l'est pas : "
        "la pire baisse est un **minimum sur vingt ans de dates**, et "
        "déplacer un poids d'un dixième de point peut faire basculer la date "
        "qui la donne — 2008 devient 2020, et la contrainte saute d'un coup "
        "au lieu de varier doucement. Aucune dérivée fiable, donc aucune "
        "formule. **On cherche.**"
    )
    st.markdown(
        "**Comment on cherche.** Un solveur sous contraintes (SLSQP) part "
        "d'un partage donné et l'améliore de proche en proche jusqu'à ne "
        "plus pouvoir. Comme il ne trouve qu'un optimum **local**, on le "
        "relance depuis seize points de départ différents et on garde le "
        "meilleur résultat admissible. Quatre précautions rendent ce "
        "procédé fiable, et chacune corrige une panne réelle :"
    )
    st.table(pd.DataFrame([
        ("Partir de points déjà admissibles",
         "Un tirage au hasard ignore les plafonds : il pose en moyenne 14 % "
         "par support quand les matières premières plafonnent à 5 %. "
         "3 tirages sur 200 respectaient les bornes, et SLSQP ne sait pas "
         "revenir dans le domaine quand il en part."),
        ("Garder un point de repli certain",
         "Un portefeuille très obligataire, construit d'avance, dont on sait "
         "qu'il tient la limite. Piège rencontré : le repli naturel, tout en "
         "États 2-10 ans, est lui-même inadmissible — 100 % de ce support "
         "perd 15,3 %. Le repli est donc sur l'échelle AAA, qui perd 7,1 %."),
        ("Repartir de seize endroits",
         "Avant correction, un seul départ sur seize aboutissait, et trois "
         "graines sur huit ne trouvaient aucune solution : le résultat du "
         "dossier tenait à un départ heureux."),
        ("Vérifier la limite pour de bon",
         "Le solveur accepte une contrainte à 5 pour 10 000 près, ce qui "
         "laissait passer un portefeuille à −14,05 % pour une limite de "
         "−14 %. On ramène la solution dans la limite avant de la comparer "
         "aux autres, sinon on compare des rendements obtenus sous des "
         "risques différents."),
    ], columns=["Précaution", "Ce qu'elle corrige"]).set_index("Précaution"))
    c = st.columns(3)
    c[0].metric("Points de départ", res.get("departs", 16))
    c[1].metric("Départs qui aboutissent", "16 / 16", "1 / 16 avant correction",
                delta_color="off")
    c[2].metric("Graines testées", "8", "même optimum pour toutes",
                delta_color="off")
    st.caption(
        "Huit tirages aléatoires indépendants donnent le même portefeuille : "
        "c'est ce qui permet d'affirmer que le résultat n'est pas un accident "
        "de départ. Code : scripts/optimiser.py."
    )

    # --- l'or : le seul poids que personne n'a choisi --------------------
    s = allocation.series_risque()
    perfs = {}
    for nom, (a, b, _lib) in allocation.CRISES.items():
        x = s["or"][a:b].dropna()
        y = s["poche_actions"][a:b].dropna()
        perfs[nom] = ((x.iloc[-1] / x.iloc[0] - 1) * 100,
                      (y.iloc[-1] / y.iloc[0] - 1) * 100)

    or_pct = viz.fr(w["or"] * 100, "%", 1)
    st.markdown(f"#### Pourquoi seulement {or_pct} d'or ?")
    st.markdown(
        f"**Parce que personne n'a choisi ce chiffre.** C'est un résidu de "
        f"calcul, et c'est ce qui le rend intéressant : le plafond autorise "
        f"{_poids(allocation.PLAFONDS['or'])} et le calcul n'en prend que "
        f"{or_pct}. **Le plafond n'est donc pas la contrainte qui "
        f"mord** — si on le relevait, rien ne bougerait."
    )
    st.table(pd.DataFrame(
        [(nom, viz.fr(o, "%", 1), viz.fr(a, "%", 1))
         for nom, (o, a) in perfs.items()],
        columns=["Crise", "L'or", "La poche d'actions"]).set_index("Crise"))
    st.caption(
        "Performance sur les fenêtres de crise datées au bloc 2, en euros. "
        "L'or est le seul support du portefeuille à finir positif sur les "
        "quatre. À ne pas confondre avec la table des pires baisses du "
        "bloc 2 : l'or a bien reculé de 25,7 % à l'intérieur de la fenêtre "
        "2008, avant de la finir en hausse."
    )
    st.markdown(
        f"**Ce que le calcul arbitre.** L'or a le rendement espéré le plus "
        f"faible du modèle, {_pct(e.loc['or', 'rendement'])}, à peine au-"
        f"dessus des {_pct(e.loc['etats_longs', 'rendement'])} des emprunts "
        f"d'État à 2-10 ans. On ne le détient donc pas pour ce qu'il "
        f"rapporte, mais pour sa tenue en crise : c'est de la protection "
        f"achetée avec du rendement. Le calcul en prend **juste ce qu'il "
        f"faut** pour que la poche d'actions puisse atteindre "
        f"{viz.fr(part_act * 100, '%', 2)} sous la limite de perte. Au-delà, chaque euro "
        f"d'or supplémentaire coûte du rendement sans acheter assez de "
        f"protection pour financer une action de plus."
    )
    st.markdown(
        f"**Et c'est stable** : huit tirages aléatoires différents donnent "
        f"tous {or_pct}. Ce n'est pas un artefact du hasard."
    )


# ----------------------------------------------------------------------
def _lien_macro(w: dict, r4: dict) -> None:
    """
    Ce que la lecture macro de l'étape 2 décide, et ce qu'elle ne décide pas.

    Ajouté le 2026-09-25 à la demande d'Allan. Le dossier annonce que chaque
    étape nourrit la suivante, mais il n'écrivait nulle part PAR QUEL CANAL
    la macro arrive dans l'allocation — et le deck l'écrivait faux, en lui
    attribuant le crédit à zéro, qui est une mesure de marché de l'étape 3.
    """
    e = allocation.entrees()
    st.markdown("#### Ce que la macro décide ici, et ce qu'elle ne décide pas")
    st.markdown(
        "**La lecture macro ne choisit aucun poids.** Elle fixe les "
        "rendements espérés de chaque classe, et c'est le calcul qui les "
        "convertit en poids sous la limite de perte. La distinction n'est "
        "pas cosmétique : elle explique pourquoi une erreur de diagnostic "
        "macro ne déforme pas le portefeuille dans les mêmes proportions."
    )
    st.table(pd.DataFrame([
        ("Combien d'actions au total", "OUI",
         f"Par les rendements espérés des quatre zones "
         f"({_pct(e.loc['actions_europe', 'rendement'])} en Europe contre "
         f"{_pct(e.loc['etats_longs', 'rendement'])} pour les États 2-10 ans)"),
        ("Quelle zone d'actions", "NON",
         "La clé 40 / 35 / 10 / 15 est fixée d'avance, précisément pour que "
         "la vue de zone ne devienne pas un pari"),
        ("Quels secteurs", "NON",
         "La note de l'étape 3 compare chaque société à son propre secteur : "
         "elle est aveugle aux secteurs par construction"),
        ("Combien d'indexées", "OUI",
         f"L'inflation de l'énoncé les porte à "
         f"{_pct(e.loc['indexees', 'rendement'])}, le meilleur rendement "
         f"obligataire du tableau : le calcul sature leur plafond de 15 %"),
        ("Combien de crédit", "NON",
         f"Zéro, mais par une mesure de marché de l'étape 3 : "
         f"{_pct(e.loc['credit_court', 'rendement'])} défauts déduits, sous "
         f"les {_pct(e.loc['etats_longs', 'rendement'])} des États"),
    ], columns=["Décision", "La macro tranche ?", "Par quel canal"]
    ).set_index("Décision"))
    st.markdown(
        f"**Et la contrainte qui commande tout le reste n'est pas macro.** "
        f"Des dix bornes du problème, deux seulement mordent — le plancher "
        f"de 10 % en AAA, qui vient du besoin de liquidité du client, et le "
        f"plafond de 15 % sur les indexées. L'or s'arrête à "
        f"{viz.fr(w['or'] * 100, '%', 1)} pour un plafond de 10 %, les "
        f"matières premières à zéro pour un plafond de 5 %. Ce qui borne "
        f"vraiment le portefeuille, c'est la limite de perte : elle est "
        f"atteinte à {viz.fr(r4['pire_baisse'], '%', 2)}, exactement la "
        f"valeur visée. Tout le reste s'ajuste autour d'elle."
    )


# ----------------------------------------------------------------------
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
    # Le graphique par support a été retiré le 2026-09-25 : il donnait les
    # mêmes montants en M€ que le tableau juste en dessous, à la même maille,
    # alors que le tableau ajoute le nom du support et son rendement espéré.
    # Le camembert reste : il agrège en quatre familles, ce que le tableau ne
    # fait pas, et donne la forme du portefeuille d'un coup d'œil.
    g1, _ = st.columns([3, 2])
    with g1:
        _graphique_familles(w, "Par grande famille")

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

    _lien_macro(w, r4)

    st.markdown("#### Conclusion de l'étape 4")
    st.markdown(
        f"100 M€ : {_poids(part_act)} d'actions en quatre zones, dont "
        f"{len(sel)} titres européens en direct ; "
        f"{_poids(oblig)} d'obligations d'État, "
        f"dont deux échelles en direct ; {_poids(w['or'])} d'or. Rendement "
        f"espéré {_pct(r4['rendement_espere'])} brut, soit {_pct(net)} net "
        f"de frais — {viz.fr(net - seuil, 'point', 2)} au-dessus de "
        f"l'inflation de l'énoncé. Pire baisse "
        f"{viz.fr(r4['pire_baisse'], '%', 1)}. Question que le calcul ne "
        f"s'est pas posée : combien de temps reste-t-il sous son plus haut ? "
        f"C'est l'étape 5."
    )
