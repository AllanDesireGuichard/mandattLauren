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

from core import actions, obligations, outlook, pedago, scoring, taux, viz
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
        (f"{len(sel)} présélectionnées", "les meilleures notes, diversifiées"),
        (f"{NB_FINAL} retenues", "ce que les analystes attendent"),
    ])

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

    st.markdown("#### La notation : les 30 titres présélectionnés")
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
    st.markdown("**Les 30 titres présélectionnés**")
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
        "Les cinq piliers mesurent ce que ces sociétés **sont** : leurs "
        "comptes, leurs marges, leur comportement dans les crises passées. "
        "Tout y est constaté. Reste la question qu'un gérant pose ensuite : "
        "**où vont-elles ?** On interroge pour cela le consensus des "
        "analystes qui suivent chaque titre — entre 5 et 25 selon la société."
    )
    st.markdown(
        "Quatre mesures, et aucune n'est l'avis « acheter / conserver / "
        "vendre » :\n"
        "- **La révision** : de combien le bénéfice attendu a bougé en trois "
        "mois. C'est le **sens** dans lequel le consensus se déplace ;\n"
        "- **Le solde des révisions** : sur le dernier mois, quelle part des "
        "analystes qui ont changé d'avis l'ont fait à la hausse ;\n"
        "- **Le potentiel** : l'objectif de cours moyen, comparé au cours "
        "d'aujourd'hui ;\n"
        "- **La dispersion** : l'écart entre la prévision la plus optimiste "
        "et la plus pessimiste. Elle mesure si l'avenir de la société est "
        "**lisible**."
    )
    st.markdown(
        "**Pourquoi écarter l'avis lui-même.** Il est presque toujours "
        "positif — les analystes recommandent rarement de vendre — donc il "
        "sépare mal. Et il manque purement et simplement sur 7 des 30 "
        "sociétés, dont des groupes suivis par 14 à 16 analystes. En faire "
        "un critère les écarterait pour une raison technique. Il est affiché "
        "dans le tableau, il ne décide de rien."
    )

    _nuage(j, retenus)
    _table_avenir(j, retenus)

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
    pedago.explique(
        "Les trois garde-fous, et ce qu'ils coûtent",
        "<strong>Le cours au-dessus de l'objectif, sans relais des "
        "bénéfices</strong> : coter plus haut que son objectif de cours ne "
        "suffit pas à faire sortir un titre, car l'objectif est lent — "
        "l'analyste relève son estimation de bénéfice d'abord, et ne remonte "
        "sa cible qu'ensuite. Un cours au-dessus de la cible signale donc "
        "souvent une hausse récente que le consensus n'a pas encore "
        "rattrapée. Le titre ne sort que si les bénéfices attendus ne suivent "
        "pas. <strong>Au relevé du jour, aucune société n'est dans ce "
        "cas</strong> : les huit qui cotent au-dessus de leur objectif ont "
        "toutes un bénéfice attendu en hausse — Endesa +1,8 %, Orion +6,4 %, "
        "Vår Energi +7,3 %.",
        "<strong>Les prévisions en net recul</strong> : un bénéfice attendu "
        "coupé de plus de 5 % en trois mois est un signal qu'on ne discute "
        "pas. Norsk Hydro sort à −17 %, Rio Tinto à −5 %.",
        "<strong>L'avenir illisible</strong> : quand les analystes ne "
        "s'accordent pas sur le bénéfice à venir, la sélection n'a pas de "
        f"prise. Au-delà de {viz.fr(seuil, '%', 0)} d'écart entre la "
        "prévision la plus haute et la plus basse, le titre sort. Le seuil "
        "n'est pas choisi : c'est le niveau des 10 % les plus dispersés. "
        "Ce garde-fou vise surtout les pétrolières et les minières, dont le "
        "bénéfice dépend d'un prix que personne ne sait prévoir — OMV "
        "atteint 90 %, Rio Tinto 68 %.",
        "<strong>Ce que ces règles coûtent, dit franchement</strong> : même "
        "sans écarter personne à tort, resserrer trente titres en quinze "
        "enlève de la diversification, et le panier resserré en ressort plus "
        "agité que celui de trente. C'est le prix du choix, pas une erreur de "
        "réglage. Le chiffrage est juste en dessous.",
        source=f"core/outlook.py · consensus Yahoo Finance, relevé du "
               f"{taux.date_fr(outlook.releve())}",
    )

    _fiche(d, sel, j)
    _panier(sel, fin)


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
    st.markdown(
        "**Lecture.**\n"
        "- **En haut** : le consensus se redresse. **En bas** : il se "
        "dégrade. La ligne pointillée est le point mort.\n"
        "- **À droite** : les mieux notées sur le passé et le présent.\n"
        "- Les deux mesures ne se recouvrent pas — c'est tout l'intérêt de "
        "poser la seconde question. argenx est la mieux notée des trente "
        "**et** bien orientée : elle est retenue sans discussion. Endesa est "
        "deuxième au classement et mieux orientée encore ; elle cote pourtant "
        "16 % au-dessus de son objectif de cours, parce que ses bénéfices "
        "attendus montent plus vite que la cible des analystes.\n"
        "- Un point en bas à droite est le piège que cette étape sert à "
        "éviter : une société qui a tout pour elle **sauf** la suite. "
        "United Utilities est cinquième des trente sur les cinq piliers et "
        "dernière sur l'avenir — son bénéfice attendu recule de 2 % et aucun "
        "analyste ne relève. Elle ne passe pas."
    )


def _table_avenir(j: pd.DataFrame, retenus: set) -> None:
    t = j.sort_values("note_avenir", ascending=False)
    tab = pd.DataFrame({
        "Société": [court(n) for n in t["longName"]],
        "Note": t["note"].map(_pilier_fr),
        "Suivi par": t["analystes"].map(
            lambda v: "—" if pd.isna(v) else f"{int(v)} analystes"),
        "Avis": t["avis"],
        "Révision": t["revision"].map(lambda v: viz.fr(v, "%", 1)),
        "Solde": t["solde"].map(lambda v: viz.fr(v, "%", 0)),
        "Potentiel": t["potentiel"].map(lambda v: viz.fr(v, "%", 1)),
        "Dispersion": t["dispersion"].map(lambda v: viz.fr(v, "%", 0)),
        "Avenir": t["note_avenir"].map(_pilier_fr),
        "Retenu": ["Oui" if k in retenus else "—" for k in t["ticker"]],
        "Motif de sortie": t["motif"].fillna("—"),
    })
    st.markdown("**Les 30 présélectionnés, classés sur l'avenir**")
    st.table(tab.set_index("Société"))
    st.caption(
        "Révision : variation du bénéfice attendu sur trois mois. Solde : "
        "part des révisions du dernier mois qui vont à la hausse, tenue pour "
        "neutre en dessous de trois révisions — sur une seule, elle ne "
        "pourrait valoir que −100 ou +100 %. Potentiel : objectif de cours "
        "moyen comparé au cours. Dispersion : écart entre la prévision la "
        "plus haute et la plus basse. La note d'avenir ne retient que la "
        "révision et le solde ; le potentiel et la dispersion servent de "
        f"garde-fous. Au plus {outlook.MAX_SECTEUR} titres par secteur et "
        f"{outlook.MAX_PAYS} par pays."
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
        "Plus la poche d'actions baisse modérément en crise, plus on peut en "
        "détenir sous la limite de 15 %. Passer de 30 à "
        f"{len(fin)} titres doit donc être payé, ou gagné, en risque — voici "
        "le prix."
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

    ecart_vol = a["vol_3a"] - b["vol_3a"]
    ecart_2020 = a["dd_2020"] - b["dd_2020"]
    st.markdown(
        f"**Lecture.** Resserrer à {len(fin)} titres rend le panier "
        f"**{viz.fr(abs(ecart_vol), 'point', 2)} "
        + ("plus" if ecart_vol > 0 else "moins")
        + " agité** au quotidien et lui fait perdre "
        f"**{viz.fr(abs(ecart_2020), 'points', 1)} de "
        + ("plus" if ecart_2020 < 0 else "moins")
        + " en 2020**. La raison est identifiable : le garde-fou de "
        "l'objectif de cours frappe surtout les valeurs **défensives**, qui "
        "cotent souvent au-dessus de leur cible quand elles sont chères — "
        "des services aux collectivités et de la santé. Chercher l'avenir "
        "coûte de la protection, c'est un arbitrage assumé.\n\n"
        "Il reste moins agité que l'indice, et l'ordre de grandeur compte : "
        "les actions européennes pèsent environ un huitième du portefeuille "
        "final, si bien que cet écart y vaut moins d'un cinquième de point. "
        "Le panier perd de toute façon bien plus que 15 % en crise : c'est le "
        "dosage avec les obligations et l'or, à l'étape 4, qui tiendra la "
        "limite."
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
        "Ce graphique ne mesure pas la méthode : les titres ont été choisis "
        "aujourd'hui, leur passé est flatteur par construction — et le "
        "resserrement repose sur des attentes d'analystes d'aujourd'hui, qui "
        "n'existaient pas en 2019. Il ne sert qu'à vérifier le comportement "
        "des deux paniers en crise."
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
