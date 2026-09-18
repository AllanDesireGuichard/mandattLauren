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
        "Le point de départ est le **STOXX Europe 600**, l'indice des 600 "
        "plus grandes entreprises cotées d'Europe, de toutes tailles et de "
        "17 pays. À chaque étage de l'entonnoir, on retire des titres pour "
        "une raison précise, affichée ci-dessous. On ne garde que les "
        "**grandes capitalisations, 10 milliards d'euros et plus** : des "
        "sociétés suivies par de nombreux analystes, dont les titres "
        "s'achètent et se vendent sans difficulté, même en crise."
    )
    pedago.fil([
        (f"{n} valeurs", "le STOXX Europe 600"),
        (f"− {len(excl)} exclues", "tabac, armement, charbon"),
        (f"− {len(inv)} non notables", "sociétés d'investissement"),
        (f"− {len(petites)} trop petites", "moins de 10 Md€"),
        (f"{len(notes)} notées", "sur cinq piliers"),
        (f"{len(sel)} retenues", "les meilleures notes, diversifiées"),
    ])

    st.markdown("**Les exclusions**")
    st.markdown(
        "Le client exclut le tabac, l'armement et le charbon. Le mandat fixe "
        "des seuils de chiffre d'affaires : 0 % pour la production de tabac "
        "et les armes controversées, 5 % pour le reste. Les mesurer "
        "exactement demande une base de données payante. On s'en approche en "
        "deux temps."
    )
    ex = excl.assign(
        Motif=excl["exclusion"].str.capitalize(),
        Comment=excl["niveau"].map({"industrie": "Industrie de la société",
                                    "décision": "Examen au cas par cas"}),
    )[["longName", "pays", "Motif", "Comment", "raison"]]
    ex.columns = ["Société", "Pays", "Motif", "Comment", "Raison"]
    st.table(ex.sort_values(["Motif", "Comment", "Société"]).set_index("Société"))

    cons = d[d["niveau"] == "conservé"][["longName", "signal", "raison"]]
    cons.columns = ["Société", "Signalée pour", "Pourquoi elle est conservée"]
    with st.expander(f"Les {len(cons)} sociétés signalées puis conservées"):
        st.table(cons.sort_values("Société").set_index("Société"))

    pedago.explique(
        "Comment les exclusions ont été décidées",
        "<strong>Premier temps, automatique.</strong> Chaque société porte "
        "une classification d'industrie. Toutes celles classées « tabac », "
        "« aéronautique et défense » ou « charbon » sont exclues. Pour "
        "Airbus, Safran ou Rolls-Royce, la défense n'est pas le cœur de "
        "métier, mais elle pèse bien plus que le seuil de 5 %.",
        "<strong>Second temps, au cas par cas.</strong> On cherche dans la "
        "description d'activité de chaque société des mots comme "
        "« militaire », « munitions », « cigarettes » ou « lignite ». Les "
        f"{len(cons) + len(excl[excl['niveau'] == 'décision'])} sociétés "
        "signalées ont été examinées une par une. Un fournisseur de "
        "logiciels qui compte l'armée parmi ses clients reste ; un groupe "
        "qui fabrique des composants d'avions de combat sort. Chaque "
        "décision est écrite avec sa raison.",
        "<strong>Ce que la méthode ne voit pas.</strong> La vente de tabac "
        "par la grande distribution n'est pas repérable de façon fiable. "
        "Certaines décisions sont marquées « à confirmer sur le rapport "
        "annuel » : la part réelle de l'activité concernée mériterait d'y "
        "être vérifiée avant un investissement réel.",
        source="core/exclusions.py · classification et descriptions Yahoo "
               "Finance",
    )
    pedago.explique(
        "Pourquoi les sociétés d'investissement ne sont pas notées",
        f"Parmi les 600 valeurs figurent {len(inv)} sociétés "
        f"d'investissement : {', '.join(sorted(scoring.SOCIETES_INVESTISSEMENT.values()))}. "
        "Ce sont des portefeuilles de participations cotés. Leur bénéfice "
        "comptable inclut la hausse de valeur de ces participations, si bien "
        "que leur PER ou leur rentabilité n'ont pas le sens qu'ils ont pour "
        "une entreprise.",
        "Notées comme les autres, elles arrivaient en tête du classement, "
        "pour une raison purement comptable. Elles ne sont pas exclues pour "
        "une raison de conviction : elles sortent simplement d'une notation "
        "qui ne sait pas les mesurer.",
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
        "Chaque société reçoit une note sur cinq piliers, à poids égaux. "
        "Elle n'est jamais comparée à l'ensemble du marché, mais **aux "
        "sociétés de son propre secteur** : une banque face aux banques, un "
        "laboratoire face aux laboratoires."
    )
    piliers = pd.DataFrame([
        ("Valorisation", "Est-elle bon marché ?",
         "Rendement des bénéfices, bénéfices attendus, valeur comptable, "
         "flux de trésorerie libre, dividende"),
        ("Croissance", "Ses résultats progressent-ils ?",
         "Croissance des bénéfices et du chiffre d'affaires, bénéfice attendu "
         "face au bénéfice passé"),
        ("Dynamique", "Le marché la soutient-il ?",
         "Performance sur 12 mois hors dernier mois, performance sur 6 mois"),
        ("Qualité", "Est-elle solide et rentable ?",
         "Rentabilité des fonds propres et des actifs, marges, endettement"),
        ("Résistance", "Tient-elle bon quand le marché chute ?",
         "Volatilité sur 3 ans, pertes maximales en 2020 et en 2022, "
         "sensibilité aux mouvements du marché (bêta)"),
    ], columns=["Pilier", "La question", "Ce qu'on mesure"])
    st.table(piliers.set_index("Pilier"))

    tab = sel.assign(
        Rang=range(1, len(sel) + 1),
        Note=sel["note"].map(_pilier_fr),
        **{p: sel[p].map(_pilier_fr) for p in scoring.PILIERS},
    )[["Rang", "longName", "secteur", "pays", "Note", *scoring.PILIERS]]
    tab.columns = ["Rang", "Société", "Secteur", "Pays", "Note",
                   *scoring.PILIERS]
    st.markdown("**Les 30 titres retenus**")
    st.table(tab.set_index("Rang"))
    st.caption(
        "Notes en écart à la moyenne du secteur : 0 = dans la moyenne, +1 = "
        "nettement meilleure que ses concurrentes (un écart-type). Au plus 4 "
        "titres par secteur et 6 par pays, et aucun titre parmi les 10 % les "
        f"plus agités (volatilité au-delà de "
        f"{viz.fr(scoring.plafond_volatilite(d), '%', 1)}). « — » : donnée insuffisante pour "
        "ce pilier ; la note finale exige au moins quatre piliers sur cinq."
    )

    c = st.columns(3)
    c[0].metric("Secteurs représentés", sel["secteur"].nunique(), "sur 11",
                delta_color="off")
    c[1].metric("Pays représentés", sel["pays"].nunique(), delta_color="off")
    c[2].metric("Part de l'indice STOXX 600",
                viz.fr(sel["poids"].sum(), "%", 1),
                "poids cumulé dans l'indice", delta_color="off")

    st.info(
        "**La sélection ne ressemble pas à l'indice, et c'est voulu.** "
        "L'indice est dominé par quelques très grandes valeurs ; la notation, "
        "elle, ne regarde que les qualités de chaque société face à ses "
        "concurrentes, quelle que soit sa taille. Le résultat mélange grandes "
        "valeurs et entreprises moyennes. Les plafonds par secteur et par "
        "pays évitent qu'un seul thème, comme les mines d'or portées par la "
        "hausse du métal, ne prenne toute la place.",
        icon=":material/lightbulb:",
    )

    _panier(sel)
    _fiche(d, sel)

    pedago.explique(
        "Comment la note est calculée",
        "<strong>1. Des indicateurs tournés dans le bon sens.</strong> Pour "
        "que « plus haut » veuille toujours dire « mieux », on retourne "
        "certains ratios : on prend le rendement des bénéfices plutôt que le "
        "PER, et on compte l'endettement en négatif.",
        "<strong>2. Les données fausses écartées.</strong> Une base comme "
        "Yahoo contient des erreurs : un PER de 1 042, un bénéfice par "
        "action de 111 944 €. Des bornes de plausibilité les écartent, puis "
        "les valeurs extrêmes sont ramenées aux 5 % les plus hauts et les "
        "plus bas, pour qu'un seul chiffre ne fasse pas toute la note.",
        "<strong>3. Chaque société face à son secteur.</strong> Pour chaque "
        "indicateur, on mesure l'écart de la société à la moyenne de son "
        "secteur, en nombre d'écarts-types. C'est ce qui permet de comparer "
        "une banque, dont le PER est structurellement bas, à un éditeur de "
        "logiciels, dont il est structurellement haut.",
        "<strong>4. Des moyennes.</strong> La note d'un pilier est la "
        "moyenne de ses indicateurs ; la note finale, la moyenne des cinq "
        "piliers. Pour les banques et assurances, l'endettement et les flux "
        "de trésorerie, qui n'ont pas de sens pour elles, sont ignorés.",
        source="core/scoring.py",
    )
    pedago.explique(
        "D'où viennent les données, et comment elles ont été contrôlées",
        "La composition de l'indice vient du fichier de positions de l'ETF "
        "iShares STOXX Europe 600, au "
        f"{d['date_composition'].iloc[0].replace('.', ' ')}. Les données "
        "financières viennent de Yahoo Finance, relevées le "
        f"{taux.date_fr(actions.releve())}.",
        "Chaque ticker a été vérifié : le nom renvoyé par Yahoo doit "
        "correspondre à celui de la composition. Les 600 correspondances "
        "ont été établies, dont trois à la main (Bank Pekao, K+S, M&G). "
        "Trois tickers sont partagés par deux sociétés sur deux places "
        "différentes (Santander et Sanofi, Boliden et Bolloré, Unipol et "
        "Unicaja) : ils sont distingués par leur place de cotation.",
        "Limite : les performances de la dynamique sont mesurées en devise "
        "locale. Pour comparer des sociétés d'un même secteur, l'effet est "
        "faible ; il sera pris en compte au niveau du portefeuille.",
        source="scripts/fetch_actions.py · data/actions/",
    )


def _panier(sel: pd.DataFrame) -> None:
    p = actions.panier_face_indice(sel)
    a, b = p["panier"], p["indice"]
    st.markdown("**Le panier face à l'indice : résiste-t-il mieux ?**")
    st.markdown(
        "La limite de perte de 15 % s'applique au portefeuille entier : elle "
        "se tiendra à l'étape 4, en dosant la part d'actions face aux "
        "obligations et à l'or. Mais plus la poche d'actions baisse "
        "modérément en crise, plus on peut en détenir pour la même limite. "
        "On mesure donc ce qu'auraient fait les 30 titres retenus, à parts "
        "égales et en euros, face à l'indice."
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
        + lecture[-1] + ". Un panier d'actions reste un panier d'actions : "
        "en crise, il perd bien plus que 15 %. C'est le dosage avec les "
        "obligations et l'or, à l'étape 4, qui tiendra la limite."
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
        "Attention, ce graphique ne mesure pas la performance de la méthode. "
        "Les titres ont été choisis aujourd'hui avec des données "
        "d'aujourd'hui, dont leur performance passée : le panier est avantagé "
        "par construction. Il ne sert qu'à vérifier son comportement en "
        "crise, ce que mesurent les pertes maximales ci-dessus. Le test "
        "honnête de la méthode est l'objet de l'étape 5."
    )


def _fiche(d: pd.DataFrame, sel: pd.DataFrame) -> None:
    st.markdown("**Fiche par titre**")
    options = list(sel["ticker"])
    noms = dict(zip(sel["ticker"], sel["longName"]))
    t = st.selectbox("Choisir une société", options,
                     format_func=lambda k: noms[k], key="fiche_titre")
    r = d[d["ticker"] == t].iloc[0]
    secteur = d[(d["secteur"] == r["secteur"]) & d["note"].notna()]

    c = st.columns([1, 1])
    with c[0]:
        st.markdown(f"**{r['longName']}**  \n{r['secteur']} · {r['pays']} · "
                    f"{r['industry']}")
        rang_sect = int((secteur["note"] > r["note"]).sum()) + 1
        st.markdown(f"Note **{_pilier_fr(r['note'])}**, "
                    f"{rang_sect}e sur {len(secteur)} dans son secteur.")
        x = scoring.indicateurs(d.loc[[r.name]])
        xs = scoring.indicateurs(secteur)
        lignes = []
        for k, (pil, lib, *_rest) in scoring.INDICATEURS.items():
            v, med = x[k].iloc[0], xs[k].median()
            if pd.isna(v) and pd.isna(med):
                continue
            pct = k not in ("mom_12_1", "mom_6", "rdt_dividende",
                            "valeur_comptable", "dette", "vol", "dd_2020",
                            "dd_2022", "beta")
            f = (lambda z: "—" if pd.isna(z) else
                 viz.fr(-z, "%", 0) if k == "dette" else
                 viz.fr(-z, "%", 1) if k == "vol" else
                 viz.fr(-z, "", 2) if k == "beta" else
                 viz.fr(z * 100, "%", 1) if pct else
                 viz.fr(z, "%", 1) if k in ("mom_12_1", "mom_6", "dd_2020",
                                             "dd_2022", "rdt_dividende") else
                 viz.fr(z, "", 2))
            lib = {"dette": "Endettement (dette / fonds propres, plus bas = "
                            "mieux)",
                   "vol": "Volatilité sur 3 ans (plus bas = mieux)",
                   "beta": "Bêta face à l'indice (plus bas = mieux)"}.get(k, lib)
            lignes.append((pil, lib, f(v), f(med)))
        st.table(pd.DataFrame(lignes, columns=[
            "Pilier", "Indicateur", "Société", "Médiane du secteur"]).set_index(
                "Pilier"))
    with c[1]:
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
            "Notes par pilier, face au secteur", height=300,
            xaxis={"gridcolor": viz.GRID, "range": [-3, 3.5],
                   "title": "écart à la moyenne du secteur"},
            yaxis={"autorange": "reversed"}, showlegend=False))
        st.plotly_chart(fig, width="stretch")
        st.caption("Bleu : meilleure que la moyenne de son secteur ; "
                   "orange : moins bonne.")


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
        "Pour la partie obligataire la plus sûre, on n'a pas besoin de "
        "fonds : on achète directement des obligations d'État. C'est moins "
        "cher (aucuns frais de gestion) et, surtout, on connaît à l'avance "
        "la date et le montant de chaque remboursement. On les évalue à "
        "partir de la courbe des taux publiée chaque jour par la BCE, comme "
        "le fait un gérant obligataire."
    )

    # --- les 10 M€ ------------------------------------------------------
    st.markdown("**Les 10 M€ à décaisser : une échelle d'obligations**")
    st.markdown(
        "Le client aura besoin de 10 M€ dans les deux ans. Plutôt que de les "
        "laisser en monétaire, on achète des obligations d'État qui arrivent "
        "à échéance au moment où l'argent sera nécessaire. Faute de "
        "calendrier précis (c'était l'une des questions de l'étape 1), on "
        "retient une **hypothèse de travail : quatre versements égaux de "
        "2,5 M€, dans 6, 12, 18 et 24 mois**."
    )
    e = obligations.echelle(TRANCHES, aaa)
    cout = sum(x["cout"] for x in e)
    cout_mon = sum(m / (1 + estr / 100) ** t for t, m in TRANCHES.items())
    lignes = [(f"Dans {int(x['echeance'] * 12)} mois", _me(x["montant"]),
               _me(x["cout"]), _pct(x["taux"])) for x in e]
    st.table(pd.DataFrame(lignes, columns=[
        "Échéance", "Montant reçu", "À investir aujourd'hui",
        "Taux garanti"]).set_index("Échéance"))
    c = st.columns(3)
    c[0].metric("Coût de l'échelle aujourd'hui", _me(cout))
    c[1].metric("En monétaire, il faudrait", _me(cout_mon),
                f"au taux de {_pct(estr)}", delta_color="off")
    c[2].metric("Gain de l'échelle", viz.fr((cout_mon - cout) / 1e3, "k€", 0),
                "et un taux garanti", delta_color="off")
    st.caption(
        "Obligations d'État notées AAA (type Allemagne, Pays-Bas) : aucun "
        "risque de défaut raisonnable, et une valeur connue à l'échéance. "
        "En pratique, on achète des titres existants dont l'échéance tombe "
        "au plus près de chaque date."
    )

    # --- la poche longue ----------------------------------------------
    st.markdown("**La poche d'emprunts d'État : quelle durée ?**")
    st.markdown(
        "Au-delà des 10 M€, la question est de savoir jusqu'où allonger. "
        "Plus une obligation est longue, plus elle rapporte, mais plus son "
        "prix baisse quand les taux montent. Le tableau met les deux en "
        "regard, pour les États notés AAA et pour l'ensemble de la zone "
        "euro."
    )
    lignes = []
    for m in ECHEANCES:
        a, z = obligations.analyse(m, aaa), obligations.analyse(m, zone)
        lignes.append((f"{m} ans", _pct(a["rendement"]),
                       _pct(a["rendement_1an"]),
                       viz.fr(a["choc_plus_1"], "%", 1),
                       _pct(z["rendement"]), _pct(z["rendement_1an"]),
                       viz.fr(z["choc_plus_1"], "%", 1)))
    tab = pd.DataFrame(lignes, columns=[
        "Échéance", "AAA : rendement", "AAA : sur un an*",
        "AAA : si les taux +1 pt", "Zone euro : rendement",
        "Zone euro : sur un an*", "Zone euro : si les taux +1 pt"])
    st.table(tab.set_index("Échéance"))
    st.caption(
        "* Ce que rapporte l'obligation sur un an si la courbe des taux ne "
        "bouge pas : le coupon, plus le gain de prix quand l'obligation "
        "« vieillit » vers des échéances où les taux sont plus bas (le "
        "glissement). « Si les taux +1 pt » : la variation de prix immédiate "
        "si tous les taux montent d'un point."
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
        f"**Allonger rapporte peu et coûte cher en risque.** Passer de 2 à "
        f"10 ans ajoute {viz.fr(a10['rendement_1an'] - a2['rendement_1an'], 'point', 2)} "
        f"de rendement sur un an, mais multiplie par "
        f"{viz.fr(a10['choc_plus_1'] / a2['choc_plus_1'], '', 0)} la perte en "
        f"cas de hausse des taux. Dans un régime où l'inflation remonte et "
        f"où les banques centrales resserrent (étape 2), ce n'est pas le "
        f"moment d'allonger. Proposition : une **échelle de 2 à 10 ans** "
        f"(2, 3, 5, 7 et 10 ans à parts égales) en emprunts d'État de "
        f"l'ensemble de la zone euro, tous notés « investment grade », qui "
        f"rapporte en moyenne "
        f"{_pct(rdt)} et perdrait environ {viz.fr(-choc, '%', 1)} si les "
        f"taux montaient d'un point. Sa part exacte sera fixée à l'étape 4, "
        f"sous la limite de perte de 15 %.",
        icon=":material/lightbulb:",
    )

    pedago.explique(
        "Comment on calcule le prix d'une obligation",
        "Une obligation, c'est une suite de paiements connus : un coupon "
        "chaque année, puis le remboursement à l'échéance. Son prix est la "
        "somme de ces paiements, chacun ramené à sa valeur d'aujourd'hui. Un "
        "euro reçu dans dix ans vaut moins qu'un euro aujourd'hui, et le taux "
        "de la courbe à dix ans dit exactement combien moins.",
    )
    pedago.formule(
        r"\text{prix} \;=\; \sum_{t} \text{paiement}_t \times "
        r"e^{-\,\text{taux}(t)\,\times\,t}",
        "On additionne chaque paiement futur, multiplié par un facteur "
        "d'actualisation d'autant plus petit que le paiement est lointain et "
        "que le taux de la courbe à cette date est élevé.",
    )
    pedago.explique(
        "Duration, sensibilité, portage, glissement : les mots du gérant",
        "<strong>La duration</strong> est la durée de vie moyenne de "
        "l'obligation, en tenant compte des coupons versés en route : 8,6 ans "
        "pour une obligation à 10 ans. <strong>La sensibilité</strong> en "
        "découle : c'est le pourcentage de prix perdu si les taux montent "
        "d'un point.",
        "<strong>Le portage</strong> est ce que l'obligation rapporte par "
        "ses coupons. <strong>Le glissement</strong> est un gain plus "
        "subtil : comme la courbe monte avec la durée, une obligation qui "
        "vieillit d'un an se retrouve à une échéance où les taux sont plus "
        "bas, et son prix monte, même si rien ne bouge sur les marchés.",
        "<strong>La convexité</strong> explique pourquoi une baisse des "
        "taux fait gagner un peu plus qu'une hausse ne fait perdre. C'est "
        "visible dans les chiffres : l'obligation à 30 ans perd 16 % si les "
        "taux montent d'un point, mais gagnerait 21 % s'ils baissaient "
        "d'autant.",
    )
    pedago.explique(
        "États notés AAA ou ensemble de la zone euro ?",
        "La courbe « AAA » ne retient que les États les mieux notés, comme "
        "l'Allemagne ou les Pays-Bas. La courbe « zone euro » inclut aussi "
        "la France, l'Italie ou l'Espagne, qui empruntent plus cher. L'écart "
        "rémunère un risque : en 2011-2012 ou en 2022, les taux italiens se "
        "sont envolés quand les taux allemands baissaient.",
        "Pour les 10 M€ à décaisser, on prend le plus sûr : AAA, car c'est "
        "de l'argent attendu à date fixe. Pour la poche longue, on retient "
        "l'ensemble de la zone euro : tous ses États sont aujourd'hui notés "
        "« investment grade », les deux courbes évoluent ensemble la plupart "
        "du temps, et l'écart rapporte près d'un demi-point à 10 ans.",
        "La contrepartie est à connaître : lors des crises proprement "
        "européennes, l'écart se creuse. La diversification entre États "
        "limite ce risque, et l'étape 5 mesurera ce qu'il aurait coûté en "
        "2011 et en 2022.",
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
    st.markdown("#### Ce que l'étape 3 transmet à l'étape 4")
    lignes = [
        ("Actions européennes", "30 titres en direct", "blocs 1 et 2"),
        ("Emprunts d'État, 10 M€ à décaisser",
         "Échelle AAA en direct, 6 à 24 mois", "bloc 3"),
        ("Emprunts d'État, poche longue",
         "Échelle zone euro en direct, 2 à 10 ans", "bloc 3"),
    ]
    for k in fonds.ORDRE:
        c = cl[k]
        lignes.append((c["libelle"],
                       f"{c['retenu']} · {c['candidats'][c['retenu']]['nom']}",
                       "bloc 4"))
    lignes.append(("Crédit euro bien noté, court",
                   f"{cr['retenu']} · {cr['fonds'][cr['retenu']]['nom']}",
                   "bloc 5"))
    lignes.append(("Infrastructure", "retirée : aucun fonds conforme",
                   "bloc 4"))
    st.table(pd.DataFrame(lignes, columns=["Classe", "Support", "Où"])
             .set_index("Classe"))
    st.caption("L'étape 4 décidera combien placer sur chacun, sous la "
               "limite de perte de 15 %.")
