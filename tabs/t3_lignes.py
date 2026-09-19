"""
Étape 3 — Analyse ligne à ligne.

Construit bloc par bloc, comme l'onglet 2. Blocs 1 et 2 (2026-09-18) :
l'entonnoir et les exclusions, puis la notation des actions européennes et
la sélection des 30 titres. Bloc 3 : les emprunts d'État en direct. Bloc 4
(tabs/t3_fonds.py) : les fonds et ETF des autres classes. Bloc 5
(tabs/t3_credit.py) : le crédit.

Décisions validées avec Allan : 30 titres ; grandes capitalisations
(10 Md€ et plus) ; cinq piliers à poids égaux, dont « Résistance » ;
exclusions par industrie + décisions nommées, chacune avec sa raison.
"""
from __future__ import annotations

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import actions, obligations, pedago, scoring, taux, viz
from tabs import t3_credit, t3_fonds


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
    _bloc_souverains()
    t3_fonds.bloc()
    t3_credit.bloc()
    _suite()


# --------------------------------------------------------------------------
# Bloc 1 — l'entonnoir et les exclusions
# --------------------------------------------------------------------------

def _bloc_entonnoir(d: pd.DataFrame) -> None:
    n = len(d)
    excl = d[d["exclusion"].notna()]
    inv = d[d["societe_invest"]]
    petites = d[d["trop_petite"] & d["exclusion"].isna() & ~d["societe_invest"]]
    notes = d[d["note"].notna()]
    sel = actions.selection(d)

    st.markdown("#### De 600 valeurs à 30 : l'entonnoir")
    st.markdown(
        "Point de départ : le **STOXX Europe 600**, les 600 plus grandes "
        "entreprises cotées d'Europe. On ne garde que les **grandes "
        "capitalisations (10 Md€ et plus)**, suivies par de nombreux analystes "
        "et faciles à acheter ou vendre, même en crise."
    )
    pedago.fil([
        (f"{n} valeurs", "le STOXX Europe 600"),
        (f"− {len(excl)} exclues", "tabac, armement, charbon"),
        (f"− {len(inv)} non notables", "sociétés d'investissement"),
        (f"− {len(petites)} trop petites", "moins de 10 Md€"),
        (f"{len(notes)} notées", "sur cinq piliers"),
        (f"{len(sel)} retenues", "les meilleures notes, diversifiées"),
    ])

    def court(nom: str) -> str:
        """Nom sans forme juridique : « Thales S.A. » -> « Thales »."""
        return re.sub(r"(,?\s+(plc|p\.l\.c\.|s\.a\.|s\.p\.a\.|sa|ag|se|n\.v\.|"
                      r"asa|ab|\(publ\)|holdings?|société anonyme|"
                      r"aktiengesellschaft))+\.?$", "", nom,
                      flags=re.IGNORECASE).strip()

    lignes = "\n".join(
        f"- **{motif.capitalize()} ({len(g)})** : "
        + ", ".join(sorted(court(x) for x in g["longName"]))
        for motif, g in excl.groupby("exclusion"))
    st.markdown("**Les exclusions**, au seuil du mandat (5 % du chiffre "
                "d'affaires, 0 % pour la production de tabac) :\n" + lignes)

    cons = d[d["niveau"] == "conservé"]
    pedago.explique(
        "Comment les exclusions ont été décidées",
        "<strong>D'abord automatiquement</strong> : toutes les sociétés "
        "classées « tabac », « aéronautique et défense » ou « charbon » sont "
        "exclues. Pour Airbus ou Safran, la défense n'est pas le cœur de "
        "métier, mais elle dépasse largement 5 %.",
        "<strong>Puis au cas par cas</strong> : on cherche dans la "
        "description de chaque société des mots comme « militaire », "
        "« munitions » ou « lignite ». Les "
        f"{len(cons) + len(excl[excl['niveau'] == 'décision'])} sociétés "
        f"signalées ont été examinées une à une ; {len(cons)} sont restées "
        "(par exemple un éditeur de logiciels qui compte l'armée parmi ses "
        "clients). Limite : la vente de tabac par la grande distribution "
        "n'est pas repérable de façon fiable.",
        f"<strong>Les {len(inv)} sociétés d'investissement</strong> "
        f"({', '.join(sorted(scoring.SOCIETES_INVESTISSEMENT.values()))}) "
        "ne sont pas exclues mais pas notées : leur bénéfice inclut la hausse "
        "de valeur de leurs participations, ce qui fausse PER et rentabilité.",
        source="core/exclusions.py · classification et descriptions Yahoo "
               "Finance",
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

    st.markdown("#### La notation et les 30 titres retenus")
    st.markdown(
        "Chaque société reçoit une note sur cinq piliers à poids égaux, en "
        "comparaison avec **les sociétés de son propre secteur** (une banque "
        "face aux banques) :\n"
        "- **Valorisation** : est-elle bon marché ?\n"
        "- **Croissance** : ses résultats progressent-ils ?\n"
        "- **Dynamique** : le marché la soutient-il ?\n"
        "- **Qualité** : est-elle solide et rentable ?\n"
        "- **Résistance** : tient-elle bon quand le marché chute ?"
    )

    tab = sel.assign(Rang=range(1, len(sel) + 1),
                     Note=sel["note"].map(_pilier_fr))[
        ["Rang", "longName", "secteur", "pays", "Note"]]
    tab.columns = ["Rang", "Société", "Secteur", "Pays", "Note"]
    st.markdown("**Les 30 titres retenus**")
    st.table(tab.set_index("Rang"))
    st.caption(
        "Note : écart à la moyenne du secteur (0 = dans la moyenne, +1 = "
        "nettement meilleure). Au plus 4 titres par secteur et 6 par pays, "
        "aucun parmi les 10 % les plus volatils (au-delà de "
        f"{viz.fr(scoring.plafond_volatilite(d), '%', 1)})."
    )
    c = st.columns(3)
    c[0].metric("Secteurs représentés", sel["secteur"].nunique(), "sur 11",
                delta_color="off")
    c[1].metric("Pays représentés", sel["pays"].nunique(), delta_color="off")
    c[2].metric("Part de l'indice STOXX 600",
                viz.fr(sel["poids"].sum(), "%", 1),
                "poids cumulé dans l'indice", delta_color="off")
    st.markdown(
        "La sélection ne ressemble pas à l'indice, et c'est voulu : la note "
        "ignore la taille, et les plafonds par secteur et par pays évitent "
        "qu'un seul thème (les mines d'or, par exemple) prenne toute la place."
    )

    _fiche(d, sel)
    _panier(sel)

    pedago.explique(
        "Comment la note est calculée",
        "Pour chaque indicateur (PER, marges, endettement, performance, "
        "volatilité…), on mesure l'écart de la société à la moyenne de son "
        "secteur, en écarts-types. Les ratios sont tournés pour que « plus "
        "haut » veuille toujours dire « mieux », et les données aberrantes de "
        "Yahoo (un PER de 1 042) sont écartées. La note d'un pilier est la "
        "moyenne de ses indicateurs, la note finale la moyenne des cinq "
        "piliers.",
        source=f"core/scoring.py · composition iShares STOXX Europe 600 au "
               f"{d['date_composition'].iloc[0].replace('.', ' ')} · Yahoo "
               f"Finance, relevé du {taux.date_fr(actions.releve())}",
    )


def _panier(sel: pd.DataFrame) -> None:
    p = actions.panier_face_indice(sel)
    a, b = p["panier"], p["indice"]
    st.markdown("**Le panier face à l'indice : résiste-t-il mieux ?**")
    st.markdown(
        "Plus la poche d'actions baisse modérément en crise, plus on peut en "
        "détenir sous la limite de 15 %. D'où la comparaison des 30 titres, à "
        "parts égales et en euros, avec l'indice."
    )
    c = st.columns(3)
    c[0].metric("Volatilité sur 3 ans", viz.fr(a["vol_3a"], "%", 1),
                f"indice : {viz.fr(b['vol_3a'], '%', 1)}", delta_color="off")
    c[1].metric("Perte maximale en 2020", viz.fr(a["dd_2020"], "%", 1),
                f"indice : {viz.fr(b['dd_2020'], '%', 1)}", delta_color="off")
    c[2].metric("Perte maximale en 2022", viz.fr(a["dd_2022"], "%", 1),
                f"indice : {viz.fr(b['dd_2022'], '%', 1)}", delta_color="off")

    lecture = []
    lecture.append("moins agité que l'indice au quotidien" if a["vol_3a"] < b["vol_3a"]
                   else "plus agité que l'indice au quotidien")
    for an in ("2020", "2022"):
        ecart = a[f"dd_{an}"] - b[f"dd_{an}"]
        if abs(ecart) < 1:
            lecture.append(f"à égalité avec lui en {an}")
        elif ecart > 0:
            lecture.append(f"a mieux résisté en {an} "
                           f"({viz.fr(ecart, 'points', 1)} de perte en moins)")
        else:
            lecture.append(f"a davantage baissé en {an} "
                           f"({viz.fr(-ecart, 'points', 1)} de perte en plus)")
    st.markdown(
        "**Lecture.** Le panier est " + ", ".join(lecture[:-1]) + " et "
        + lecture[-1] + ". Mais il perd bien plus que 15 % en crise : c'est "
        "le dosage avec les obligations et l'or, à l'étape 4, qui tiendra la "
        "limite."
    )

    fig = go.Figure()
    for cle, nom, couleur in [("indice", "STOXX Europe 600", viz.CATEGORICAL[1]),
                              ("panier", "Les 30 titres retenus",
                               viz.CATEGORICAL[0])]:
        s = p["series"][cle]
        s = s / s.iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=s.index, y=s, name=nom, mode="lines",
            line={"color": couleur, "width": 2},
            hovertemplate=f"{nom} : %{{y:.0f}}<extra></extra>"))
    fig.update_layout(**viz.layout(
        "Les 30 titres et l'indice depuis 2019, en euros (base 100)",
        height=380, hovermode="x unified",
        yaxis={"gridcolor": viz.GRID}, xaxis={"gridcolor": viz.GRID}))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Ce graphique ne mesure pas la méthode : les titres ont été choisis "
        "aujourd'hui, leur passé est flatteur par construction. Il ne sert "
        "qu'à vérifier leur comportement en crise."
    )


def _fiche(d: pd.DataFrame, sel: pd.DataFrame) -> None:
    st.markdown("**Fiche par titre**")
    options = list(sel["ticker"])
    noms = dict(zip(sel["ticker"], sel["longName"]))
    t = st.selectbox("Choisir une société", options,
                     format_func=lambda k: noms[k], key="fiche_titre")
    r = d[d["ticker"] == t].iloc[0]
    secteur = d[(d["secteur"] == r["secteur"]) & d["note"].notna()]

    rang_sect = int((secteur["note"] > r["note"]).sum()) + 1
    st.markdown(f"**{r['longName']}** · {r['secteur']} · {r['pays']} — note "
                f"**{_pilier_fr(r['note'])}**, {rang_sect}e sur "
                f"{len(secteur)} dans son secteur.")
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

    pedago.explique(
        "Comment on évalue une obligation, et les mots du gérant",
        "Une obligation est une suite de paiements connus (coupons, puis "
        "remboursement). Son prix est la somme de ces paiements, chacun "
        "ramené à sa valeur d'aujourd'hui avec le taux de la courbe de la "
        "BCE à sa date.",
        "<strong>Duration</strong> : durée de vie moyenne, coupons compris "
        "(8,6 ans pour une obligation à 10 ans). <strong>Sensibilité</strong> : "
        "le pourcentage de prix perdu si les taux montent d'un point. "
        "<strong>Glissement</strong> : en vieillissant, l'obligation glisse "
        "vers des échéances où les taux sont plus bas, et son prix monte.",
        "<strong>AAA ou toute la zone euro ?</strong> L'écart rémunère un "
        "risque : en 2011-2012 et en 2022, les taux italiens se sont envolés "
        "quand les allemands baissaient. D'où l'AAA pour l'argent attendu à "
        "date fixe, et la zone euro, diversifiée, pour la poche longue.",
        source=f"Courbes zéro-coupon de la BCE (modèle de Svensson) au "
               f"{taux.date_fr(sv['date'])} · core/obligations.py",
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
        ("Actions européennes", "30 titres en direct", "—"),
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
