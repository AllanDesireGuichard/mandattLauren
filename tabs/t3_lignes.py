"""
Étape 3 — Analyse ligne à ligne.

Construit bloc par bloc, comme l'onglet 2. Blocs 1 et 2 (2026-09-18) :
l'entonnoir et les exclusions, puis la notation des actions européennes et
la sélection des 30 titres. Bloc 3 (2026-09-24) : ce que les analystes
attendent, qui resserre les 30 en 15. Bloc 4 : les emprunts d'État en direct.
Bloc 5 (tabs/t3_fonds.py) : les fonds et ETF des autres classes. Bloc 6
(tabs/t3_credit.py) : le crédit.

Décisions validées avec Allan : grandes capitalisations (10 Md€ et plus) ;
cinq piliers à poids égaux, dont « Résistance » ; exclusions par industrie +
décisions nommées, chacune avec sa raison ; 30 titres sur le constaté, puis
15 sur l'attendu (2026-09-24). Les attentes des analystes forment un étage
SÉPARÉ et non un sixième pilier : les piliers classent, l'avenir élimine.
"""
from __future__ import annotations

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import (actions, fiches, obligations, outlook, pedago, scoring,
                  taux, viz, vue_secteurs)
from tabs import t3_credit, t3_fonds


# Nombre de titres retenus au second étage. 15 est le résultat mesuré des
# plafonds (2 par secteur, 4 par pays) appliqués aux 20 titres qui franchissent
# les garde-fous : en demander 16 n'en donne pas davantage.
NB_FINAL = outlook.N_FINAL

# Ordre d'affichage des garde-fous, et surtout : liste EXHAUSTIVE. Les motifs
# sont sinon déduits des titres écartés, et un garde-fou qui ne mord sur
# personne disparaîtrait silencieusement de la page.
ORDRE_MOTIFS = ("Cours au-dessus de la cible sans relais des bénéfices",
                "Prévisions en net recul", "Avenir illisible")


@st.cache_data(show_spinner="Notation des 600 titres…")
def _univers() -> pd.DataFrame:
    return actions.univers()


def render() -> None:
    pedago.chaine(3)
    pedago.etape(
        3, "Analyse ligne à ligne",
        "L'étape 2 a dit combien chaque classe d'actifs peut rapporter. "
        "Celle-ci choisit avec quoi l'investir. Pour les actions "
        "européennes, on sélectionne des titres en direct parmi les 600 "
        "plus grandes valeurs d'Europe. Pour les autres classes, on "
        "choisira les meilleurs fonds.",
    )
    d = _univers()
    _bloc_entonnoir(d)
    _bloc_notation(d)
    _bloc_avenir(d)
    _bloc_souverains()
    t3_fonds.bloc()
    t3_credit.bloc()
    _suite()


# --------------------------------------------------------------------------
# Bloc 1 — l'entonnoir et les exclusions
# --------------------------------------------------------------------------

def court(nom: str) -> str:
    """Nom sans forme juridique : « Thales S.A. » -> « Thales »."""
    return re.sub(r"(,?\s+(plc|p\.l\.c\.|s\.a\.|s\.p\.a\.|sa|ag|se|n\.v\.|"
                  r"asa|ab|\(publ\)|holdings?|société anonyme|"
                  r"aktiengesellschaft))+\.?$", "", nom,
                  flags=re.IGNORECASE).strip()


def _bloc_entonnoir(d: pd.DataFrame) -> None:
    n = len(d)
    excl = d[d["exclusion"].notna()]
    inv = d[d["societe_invest"]]
    petites = d[d["trop_petite"] & d["exclusion"].isna() & ~d["societe_invest"]]
    notes = d[d["note"].notna()]
    sel = actions.selection(d)

    st.markdown(f"#### De 600 valeurs à {NB_FINAL} : l'entonnoir")
    st.markdown(
        "Point de départ : le **STOXX Europe 600**. On ne garde que les "
        "capitalisations de **10 Md€ et plus**."
    )
    pedago.fil([
        (f"{n} valeurs", "le STOXX Europe 600"),
        (f"− {len(excl)} exclues", "tabac, armement, charbon"),
        (f"− {len(inv)} non notables", "sociétés d'investissement"),
        (f"− {len(petites)} trop petites", "moins de 10 Md€"),
        (f"{len(notes)} notées", "sur cinq piliers"),
        (f"− {len(notes[vue_secteurs.ecartees(notes)])} écartées", "vue sectorielle du gérant"),
        (f"{len(sel)} présélectionnées", "les meilleures notes, diversifiées"),
        (f"{NB_FINAL} retenues", "ce que les analystes attendent"),
    ])

    lignes = "\n".join(
        f"- **{motif.capitalize()} ({len(g)})** : "
        + ", ".join(sorted(court(x) for x in g["longName"]))
        for motif, g in excl.groupby("exclusion"))
    st.markdown("**Les exclusions**, au seuil du mandat (5 % du chiffre "
                "d'affaires, 0 % pour la production de tabac) :\n" + lignes)

    _vue_sectorielle(d)

    st.caption(
        "Exclusion automatique par industrie, puis examen à la main des "
        "sociétés dont la description contient « militaire », « lignite » "
        "ou équivalent. Limite : la vente de tabac par la grande "
        f"distribution n'est pas repérable. Les {len(inv)} sociétés "
        "d'investissement sont notées à part — leur bénéfice inclut la "
        "hausse de valeur de leurs participations."
    )
def _vue_sectorielle(d: pd.DataFrame) -> None:
    """
    La vue du gérant : des métiers écartés par décision, et son prix affiché.

    Séparée des exclusions du client juste au-dessus, et à dessein : celles-ci
    sont une contrainte du mandat, celle-là un arbitrage qu'il faut défendre.
    """
    c = vue_secteurs.cout(d)

    st.markdown(
        "**Notre vue sectorielle**, qui n'est pas une contrainte du client "
        "mais une décision de gestion : nous nous interdisons quatre métiers, "
        f"soit {c['titres_notes']} sociétés notées."
    )
    st.table(vue_secteurs.table().set_index("Industrie"))
    st.caption(
        f"Coût de la décision : {c['titres_notes']} sociétés notées sortent "
        f"de l'univers. La meilleure, {court(c['meilleur_titre'])} "
        f"({_pilier_fr(c['meilleure_note'])}), était la trentième. "
        f"Sélection finale et risque du panier inchangés."
    )
# --------------------------------------------------------------------------
# Bloc 2 — la notation et les 30 titres
# --------------------------------------------------------------------------

def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


def _pilier_fr(v: float) -> str:
    return "—" if pd.isna(v) else ("+" if v > 0 else "") + viz.fr(v, "", 2)


def _bloc_notation(d: pd.DataFrame) -> None:
    sel = actions.selection(d)

    st.markdown(f"#### La notation : {len(sel)} titres présélectionnés")
    st.markdown(
        "Cinq piliers à poids égaux, chaque société comparée aux sociétés "
        "de **son propre secteur** : **valorisation** (bon marché ?), "
        "**croissance**, **dynamique** (le marché la soutient ?), "
        "**qualité** (solide et rentable ?), **résistance** (tient-elle en "
        "crise ?)."
    )

    plaf = scoring.plafonds_volatilite(d)
    st.caption(
        f"Note : écart à la moyenne du secteur en écarts-types. Au plus 4 "
        f"titres par secteur et 6 par pays ; volatilité plafonnée dans son "
        f"métier, de {viz.fr(scoring.plafond_volatilite(d), '%', 1)} à "
        f"{viz.fr(plaf.max(), '%', 1)} selon le secteur."
    )
    c = st.columns(3)
    c[0].metric("Secteurs représentés", sel["secteur"].nunique(), "sur 11",
                delta_color="off")
    c[1].metric("Pays représentés", sel["pays"].nunique(), delta_color="off")
    c[2].metric("Part de l'indice STOXX 600",
                viz.fr(sel["poids"].sum(), "%", 1),
                "poids cumulé dans l'indice", delta_color="off")
    st.caption(
        "La note ignore la taille des sociétés : la sélection ne ressemble "
        "pas à l'indice, et c'est voulu. Les 30 titres et leurs notes sont "
        "sur le nuage de points du bloc suivant."
    )

# --------------------------------------------------------------------------
# Bloc 3 — ce que les analystes attendent, et le resserrement à 15 titres
# --------------------------------------------------------------------------

def _bloc_avenir(d: pd.DataFrame) -> None:
    sel = actions.selection(d)
    x = outlook.indicateurs()
    j = outlook.juger(sel, x)
    fin = outlook.selectionner(j, n=NB_FINAL)
    retenus = set(fin["ticker"])

    st.markdown(f"#### De 30 à {NB_FINAL} : ce que les analystes attendent")
    st.markdown(
        "Les cinq piliers mesurent ce que ces sociétés **sont**. Ce second "
        "étage mesure **où elles vont**, et resserre les 30 en "
        f"{NB_FINAL}."
    )
    st.markdown(
        "**Classent** : la révision du bénéfice attendu sur 90 jours, et le "
        "solde des révisions du mois. **Éliminent seulement** : le "
        "potentiel (cours face à l'objectif) et la dispersion des "
        "estimations. L'avis « acheter / conserver / vendre » est affiché, "
        "jamais noté — il manque sur 6 des 30, dont des sociétés suivies "
        "par 14 analystes."
    )

    _nuage(j, retenus)

    ecartes = j[j["motif"].notna()]
    # Chaque titre compte sous TOUS les motifs qui s'appliquent, pas sous le
    # premier : `juger` les accumule volontairement (Rio Tinto cumule un
    # consensus en recul et un avenir illisible), n'en montrer qu'un donnerait
    # une raison plus faible que la réalité.
    par_motif = {}
    for _, r in ecartes.iterrows():
        for m in r["motif"].split(" · "):
            par_motif.setdefault(m, []).append(court(r["longName"]))
    # Un garde-fou qui n'écarte personne doit être annoncé quand même : son
    # zéro est un résultat, pas un oubli. C'est le cas du premier au relevé
    # du 2026-09-24 (voir le docstring de core/outlook.py).
    lignes = []
    for m in ORDRE_MOTIFS:
        v = par_motif.get(m, [])
        lignes.append(f"- **{m}** ({len(v)}) : " + (", ".join(sorted(v))
                      if v else "_aucun titre au relevé du jour_"))
    st.markdown(
        "**Ce qui fait sortir un titre.** Trois garde-fous, appliqués avant "
        "tout classement :\n" + "\n".join(lignes)
        + "\n\nLes autres sortants sont bien classés mais arrivent dans un "
        "secteur ou un pays déjà complet."
    )

    seuil = outlook.plafond_dispersion(x)
    st.caption(
        f"Seuils : bénéfice attendu coupé de plus de 5 % en trois mois ; "
        f"dispersion au-delà de {viz.fr(seuil, '%', 0)}, mesurée comme le "
        f"niveau des 10 % les plus dispersés ; cours au-dessus de "
        f"l'objectif **et** bénéfices qui ne suivent pas."
    )
    _bloc_fiches(fin)
    _fiche(d, sel, j)
    _panier(sel, fin)


def _bloc_fiches(fin: pd.DataFrame) -> None:
    """
    Les titres retenus, un par ligne : le métier, et pourquoi il est là.

    Demande d'Allan du 2026-09-25. Le tableau des mesures répond à « sur quoi
    les a-t-on choisis » ; celui-ci répond à la question qu'un client pose en
    premier, « qu'est-ce que j'achète, et pourquoi celui-là ». Le texte vit
    dans core/fiches.py ; les chiffres cités y sont recalculés à l'affichage.
    """
    st.markdown(f"**Les {len(fin)} titres retenus : le métier, et pourquoi**")
    st.table(fiches.table(fin).set_index("Société"))
    if (manque := fiches.manquantes(fin)):
        st.warning("Fiche à rédiger pour : " + ", ".join(manque))


def _nuage(j: pd.DataFrame, retenus: set) -> None:
    """Le constaté en abscisse, l'attendu en ordonnée : la décision en une image."""
    fig = go.Figure()
    for garde, nom, couleur in [
            (False, f"Écartés ({len(j) - len(retenus)})", "#b9b7b1"),
            (True, f"Retenus ({len(retenus)})", viz.CATEGORICAL[0])]:
        g = j[j["ticker"].isin(retenus) == garde]
        fig.add_trace(go.Scatter(
            x=g["note"], y=g["note_avenir"], name=nom, mode="markers+text",
            marker={"size": 11, "color": couleur,
                    "line": {"width": 1, "color": viz.SURFACE}},
            text=[court(n) for n in g["longName"]],
            textposition="top center",
            textfont={"size": 9, "color": viz.INK_2 if garde else "#8f8d88"},
            customdata=g[["revision", "potentiel", "dispersion"]],
            hovertemplate="<b>%{text}</b><br>Note des cinq piliers : %{x:.2f}"
                          "<br>Note d'avenir : %{y:.2f}"
                          "<br>Révision : %{customdata[0]:.1f} %"
                          "<br>Potentiel : %{customdata[1]:.1f} %"
                          "<br>Dispersion : %{customdata[2]:.0f} %<extra></extra>"))
    fig.add_hline(y=0, line={"color": viz.INK_2, "width": 1, "dash": "dot"})
    fig.update_layout(**viz.layout(
        "Ce que les sociétés sont (abscisse) et ce qu'on en attend (ordonnée)",
        height=460,
        xaxis={"gridcolor": viz.GRID, "title": "Note des cinq piliers"},
        yaxis={"gridcolor": viz.GRID, "title": "Note d'avenir"}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(
        "En haut : le consensus se redresse. À droite : la société est bien "
        "notée sur les cinq piliers. Les retenus sont en haut à droite, "
        "sous les plafonds de 2 par secteur et 4 par pays."
    )

def _panier(sel: pd.DataFrame, fin: pd.DataFrame) -> None:
    """
    Ce que le resserrement change, chiffré. Les deux paniers sont construits
    à parts égales et en euros, et comparés à l'indice. La comparaison est
    volontairement montrée dans les deux sens : resserrer coûte du risque, et
    le dossier le dit plutôt que de le laisser trouver.
    """
    p30 = actions.panier_face_indice(sel)
    p15 = actions.panier_face_indice(fin)
    a, b, ind = p15["panier"], p30["panier"], p30["indice"]

    st.markdown("**Ce que le resserrement change : les deux paniers face à "
                "l'indice**")
    st.markdown(
        f"Les {len(fin)} titres à parts égales, en euros, face aux "
        f"{len(sel)} présélectionnés et au STOXX Europe 600."
    )
    mesures = [("Volatilité sur 3 ans", "vol_3a"),
               ("Perte maximale en 2020", "dd_2020"),
               ("Perte maximale en 2022", "dd_2022")]
    st.table(pd.DataFrame(
        [[viz.fr(src[cle], "%", 1) for _, cle in mesures]
         for src in (a, b, ind)],
        index=[f"Les {len(fin)} retenus", "Les 30 présélectionnés",
               "Indice STOXX Europe 600"],
        columns=[nom for nom, _ in mesures]))

    st.caption(
        f"Le resserrement coûte {viz.fr(a['vol_3a'] - b['vol_3a'], 'pt', 2)} "
        f"de volatilité et {viz.fr(a['dd_2020'] - b['dd_2020'], 'pt', 1)} "
        f"en 2020 : le garde-fou du potentiel frappe les défensives, qui "
        f"cotent souvent au-dessus de leur objectif. La poche vaut 12,2 % du "
        f"patrimoine, l'écart y pèse 0,16 point."
    )

    fig = go.Figure()
    series = [("indice", p30, "STOXX Europe 600", viz.CATEGORICAL[1]),
              ("panier", p30, "Les 30 présélectionnés", "#b9b7b1"),
              ("panier", p15, f"Les {len(fin)} retenus", viz.CATEGORICAL[0])]
    for cle, src, nom, couleur in series:
        s = src["series"][cle]
        s = s / s.iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=s.index, y=s, name=nom, mode="lines",
            line={"color": couleur, "width": 2},
            hovertemplate=f"{nom} : %{{y:.0f}}<extra></extra>"))
    fig.update_layout(**viz.layout(
        "Les deux paniers et l'indice depuis 2019, en euros (base 100)",
        height=380, hovermode="x unified",
        yaxis={"gridcolor": viz.GRID}, xaxis={"gridcolor": viz.GRID}))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Les titres ont été choisis avec les données d'aujourd'hui : leur "
        "passé est flatteur par construction. Seule leur tenue en crise est "
        "informative."
    )


def _fiche(d: pd.DataFrame, sel: pd.DataFrame, j: pd.DataFrame) -> None:
    st.markdown("**Fiche par titre**")
    options = list(sel["ticker"])
    noms = dict(zip(sel["ticker"], sel["longName"]))
    t = st.selectbox("Choisir une société", options,
                     format_func=lambda k: noms[k], key="fiche_titre")
    r = d[d["ticker"] == t].iloc[0]
    a = j[j["ticker"] == t].iloc[0]
    secteur = d[(d["secteur"] == r["secteur"]) & d["note"].notna()]

    rang_sect = int((secteur["note"] > r["note"]).sum()) + 1
    verdict = (f"écartée — {a['motif'].lower()}" if pd.notna(a["motif"])
               else "retenue au second étage")
    st.markdown(f"**{r['longName']}** · {r['secteur']} · {r['pays']} — note "
                f"**{_pilier_fr(r['note'])}**, {rang_sect}e sur "
                f"{len(secteur)} dans son secteur. {verdict.capitalize()}.")
    fig = go.Figure(go.Bar(
        x=[r[p] for p in scoring.PILIERS], y=scoring.PILIERS,
        orientation="h",
        marker={"color": [viz.CATEGORICAL[0] if (r[p] or 0) >= 0
                          else viz.CATEGORICAL[1]
                          for p in scoring.PILIERS], "cornerradius": 4},
        text=[_pilier_fr(r[p]) for p in scoring.PILIERS],
        textposition="outside", textfont={"color": viz.INK_2},
        hovertemplate="%{y} : %{x:.2f}<extra></extra>",
    ))
    fig.add_vline(x=0, line={"color": viz.INK_2, "width": 1})
    fig.update_layout(**viz.layout(
        "Notes par pilier, face au secteur (bleu : mieux que la moyenne)",
        height=280,
        xaxis={"gridcolor": viz.GRID, "range": [-3, 3.5]},
        yaxis={"autorange": "reversed"}, showlegend=False))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    _attentes(a)


def _attentes(a: pd.Series) -> None:
    """Ce que les analystes attendent du titre affiché dans la fiche."""
    dev = "p" if a["devise_cours"] == "GBp" else a["devise_cours"]
    n = "—" if pd.isna(a["analystes"]) else f"{int(a['analystes'])}"
    st.markdown(
        f"**Ce que les analystes attendent** — {n} suivent la société, "
        f"avis moyen : {a['avis'].lower()}."
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[a["cible_basse"], a["cible_haute"]], y=["Objectif", "Objectif"],
        mode="lines", line={"color": "#b9b7b1", "width": 6},
        hoverinfo="skip", showlegend=False))
    for val, nom, couleur, pos in [
            (a["cible_basse"], "Plus bas", "#b9b7b1", "bottom center"),
            (a["cible_haute"], "Plus haut", "#b9b7b1", "bottom center"),
            (a["cible"], "Objectif moyen", viz.CATEGORICAL[0], "top center"),
            (a["cours"], "Cours du jour", viz.CATEGORICAL[1], "top center")]:
        fig.add_trace(go.Scatter(
            x=[val], y=["Objectif"], mode="markers+text", name=nom,
            marker={"size": 13, "color": couleur,
                    "line": {"width": 1, "color": viz.SURFACE}},
            text=[f"{nom}<br>{viz.fr(val, dev, 2)}"], textposition=pos,
            textfont={"size": 10, "color": viz.INK_2}, showlegend=False,
            hovertemplate=f"{nom} : {viz.fr(val, dev, 2)}<extra></extra>"))
    marge = (a["cible_haute"] - a["cible_basse"]) * 0.35 or 1
    fig.update_layout(**viz.layout(
        "Le cours d'aujourd'hui face aux objectifs des analystes",
        height=210,
        xaxis={"gridcolor": viz.GRID,
               "range": [min(a["cible_basse"], a["cours"]) - marge,
                         max(a["cible_haute"], a["cours"]) + marge]},
        yaxis={"showgrid": False, "showticklabels": False}))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    sens = "relevé" if a["revision"] >= 0 else "abaissé"
    nrev = int(a["revisions_30j"])
    solde = (f"sur {nrev} révisions du dernier mois, "
             f"{viz.fr(a['solde'], '%', 0)} vont à la hausse"
             if nrev >= outlook.REVISIONS_MIN else
             f"une seule révision le dernier mois" if nrev == 1 else
             f"{nrev} révisions le dernier mois, trop peu pour conclure"
             if nrev else "aucune révision le dernier mois")
    st.markdown(
        f"- Le bénéfice attendu a été **{sens} de "
        f"{viz.fr(abs(a['revision']), '%', 1)}** en trois mois ; {solde}.\n"
        f"- L'objectif moyen est **{viz.fr(a['potentiel'], '%', 1)}** "
        "au-dessus du cours."
        if a["potentiel"] >= 0 else
        f"- Le bénéfice attendu a été **{sens} de "
        f"{viz.fr(abs(a['revision']), '%', 1)}** en trois mois ; {solde}.\n"
        f"- Le cours est **{viz.fr(abs(a['potentiel']), '%', 1)} au-dessus** "
        "de l'objectif moyen."
    )
    st.markdown(
        f"- Les analystes s'écartent de **{viz.fr(a['dispersion'], '%', 0)}** "
        "entre leur prévision la plus haute et la plus basse."
    )


# --------------------------------------------------------------------------
# Bloc 3 — les emprunts d'État en direct
# --------------------------------------------------------------------------

ECHEANCES = [2, 3, 5, 7, 10, 15, 20, 30]
ECHELLE_LONGUE = [2, 3, 5, 7, 10]
TRANCHES = {0.5: 2.5e6, 1.0: 2.5e6, 1.5: 2.5e6, 2.0: 2.5e6}


def _me(v: float) -> str:
    return viz.fr(v / 1e6, "M€", 2)


def _bloc_souverains() -> None:
    photo = taux.charger()
    sv = photo["svensson"]
    estr = photo["points"]["estr"]["valeur"]
    aaa, zone = sv["aaa"], sv["toutes"]

    st.markdown("#### Les emprunts d'État en direct")
    st.markdown(
        "Pour la partie la plus sûre, pas besoin de fonds : on achète "
        "directement des obligations d'État. Pas de frais de gestion, et on "
        "connaît à l'avance la date et le montant de chaque remboursement."
    )

    # --- les 10 M€ ------------------------------------------------------
    e = obligations.echelle(TRANCHES, aaa)
    cout = sum(x["cout"] for x in e)
    cout_mon = sum(m / (1 + estr / 100) ** t for t, m in TRANCHES.items())
    st.markdown(
        "**Les 10 M€ à décaisser : une échelle.** Le client aura besoin de "
        "10 M€ dans les deux ans. Hypothèse de travail, faute de calendrier "
        "(question ouverte à l'étape 1) : **quatre versements de 2,5 M€, dans "
        "6, 12, 18 et 24 mois**. On achète des obligations d'État notées AAA "
        "(Allemagne, Pays-Bas) qui arrivent à échéance à ces dates, à des taux "
        f"garantis de {_pct(e[0]['taux'])} à {_pct(e[-1]['taux'])}."
    )
    c = st.columns(3)
    c[0].metric("Coût de l'échelle aujourd'hui", _me(cout))
    c[1].metric("En monétaire, il faudrait", _me(cout_mon),
                f"au taux de {_pct(estr)}", delta_color="off")
    c[2].metric("Gain de l'échelle", viz.fr((cout_mon - cout) / 1e3, "k€", 0),
                "et un taux garanti", delta_color="off")

    # --- la poche longue ----------------------------------------------
    st.markdown(
        "**La poche longue : jusqu'où allonger ?** Plus une obligation est "
        "longue, plus elle rapporte, mais plus son prix baisse quand les taux "
        "montent."
    )
    _graphique_souverains(aaa, zone, estr)

    # Poche longue sur l'ensemble de la zone euro : décision d'Allan du
    # 2026-09-18 (« tout l'investment grade, globalement ça se suit »).
    # L'échelle des 10 M€ reste en AAA : argent à décaisser à date fixe.
    ech = [obligations.analyse(m, zone) for m in ECHELLE_LONGUE]
    rdt = sum(x["rendement"] for x in ech) / len(ech)
    choc = sum(x["choc_plus_1"] for x in ech) / len(ech)
    a2, a10 = obligations.analyse(2, aaa), obligations.analyse(10, aaa)
    st.info(
        f"**Allonger rapporte peu et coûte cher en risque.** De 2 à 10 ans, "
        f"on gagne {viz.fr(a10['rendement_1an'] - a2['rendement_1an'], 'point', 2)} "
        f"de rendement, mais la perte en cas de hausse des taux est "
        f"multipliée par {viz.fr(a10['choc_plus_1'] / a2['choc_plus_1'], '', 0)}. "
        f"Avec une inflation qui remonte (étape 2), on n'allonge pas. "
        f"Proposition : une **échelle 2-3-5-7-10 ans** à parts égales, en "
        f"emprunts d'État de toute la zone euro (tous « investment grade », "
        f"près d'un demi-point de plus que l'AAA à 10 ans) : {_pct(rdt)} en "
        f"moyenne, {viz.fr(choc, '%', 1)} si les taux montent d'un point.",
        icon=":material/lightbulb:",
    )

def _graphique_souverains(aaa: dict, zone: dict, estr: float) -> None:
    fig = go.Figure()
    for p, nom, couleur in [(aaa, "États notés AAA", viz.CATEGORICAL[0]),
                            (zone, "Ensemble de la zone euro",
                             viz.CATEGORICAL[1])]:
        pts = [obligations.analyse(m, p) for m in ECHEANCES]
        fig.add_trace(go.Scatter(
            x=[-a["choc_plus_1"] for a in pts],
            y=[a["rendement_1an"] for a in pts], name=nom,
            mode="lines+markers+text",
            text=[f"{m} ans" for m in ECHEANCES], textposition="top center",
            textfont={"color": viz.INK_2, "size": 10},
            line={"color": couleur, "width": 2},
            marker={"size": 9, "color": couleur,
                    "line": {"color": viz.SURFACE, "width": 2}},
            hovertemplate=(nom + "<br>%{text} : %{y:.2f} % sur un an<br>"
                           "perte si +1 pt : %{x:.1f} %<extra></extra>")))
    fig.add_hline(y=estr, line={"color": viz.INK_2, "width": 1, "dash": "dot"},
                  annotation={"text": f"Monétaire : {_pct(estr)}",
                              "font": {"color": viz.INK_2, "size": 11}},
                  annotation_position="bottom right")
    fig.update_layout(**viz.layout(
        "Ce que rapporte un an de plus de durée, et ce qu'il fait risquer",
        height=420,
        xaxis={"title": "Perte de prix si les taux montent d'un point (%)",
               "gridcolor": viz.GRID, "ticksuffix": " %"},
        yaxis={"title": "Rendement sur un an, courbe inchangée (%)",
               "gridcolor": viz.GRID, "ticksuffix": " %"}))
    st.plotly_chart(fig, width="stretch")
    st.caption("Chaque point est une échéance. Vers la droite, le risque "
               "augmente vite ; vers le haut, le rendement augmente "
               "lentement.")


# --------------------------------------------------------------------------
# Suite de l'onglet
# --------------------------------------------------------------------------

def _suite() -> None:
    """Sortie de l'étape 3 : un support par classe, rien de plus."""
    import json
    from pathlib import Path
    from core import fonds
    racine = Path(__file__).resolve().parents[1] / "data"
    cl = fonds.charger()["classes"]
    cr = json.loads((racine / "fonds_credit.json").read_text(encoding="utf-8"))
    st.markdown("#### Conclusion de l'étape 3 : un support par classe")
    lignes = [
        ("Actions européennes", f"{NB_FINAL} titres en direct", "—"),
        ("Emprunts d'État, 10 M€ à décaisser",
         "Échelle AAA en direct, 6 à 24 mois", "—"),
        ("Emprunts d'État, poche longue",
         "Échelle zone euro en direct, 2 à 10 ans", "—"),
    ]
    for k in fonds.ORDRE:
        c = cl[k]
        r = c["candidats"][c["retenu"]]
        lignes.append((c["libelle"], f"{c['retenu'].split('.')[0]} · {r['nom']}",
                       viz.fr(r["frais"], "%", 2)))
    x = cr["fonds"][cr["retenu"]]
    lignes.append(("Crédit euro bien noté, court",
                   f"{cr['retenu'].split('.')[0]} · {x['nom']}",
                   viz.fr(x["frais"], "%", 2)))
    st.table(pd.DataFrame(lignes, columns=["Classe", "Support",
                                           "Frais par an"]).set_index("Classe"))
    st.caption("Combien placer sur chacun, sous la limite de perte de "
               "15 % : c'est l'étape 4.")
