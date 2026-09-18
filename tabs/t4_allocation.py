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
  - crypto : poche de 1 à 2 %, choix du client, hors optimisation.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import allocation, pedago, viz


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


def render() -> None:
    pedago.chaine(4)
    pedago.etape(
        4, "Allocation",
        "Combien placer sur chacun des supports retenus à l'étape 3, avec "
        "les rendements espérés de l'étape 2, pour rapporter au moins 4 % par "
        "an sans jamais perdre plus de 15 %. On avance en cinq temps : ce qui "
        "entre dans le calcul, le risque de chaque support, ce que "
        "proposerait un calcul sans garde-fou, les garde-fous un par un et "
        "leur coût, puis le portefeuille retenu, en millions d'euros.",
    )
    _bloc_entrees()
    _bloc_risque()
    pedago.a_construire(
        4, "Allocation",
        "**L'optimisation libre, affichée avant le résultat retenu** : ce "
        "que propose le calcul quand on ne lui impose que la limite de "
        "perte. C'est elle qui montre ce que le modèle ignore.",
        "**Chaque contrainte listée une par une**, avec ce qu'elle encode et "
        "son coût chiffré en rendement.",
        "**Le portefeuille retenu**, en pourcentages puis en millions "
        "d'euros par support, et son écart au portefeuille libre.",
    )


# ----------------------------------------------------------------------
def _bloc_entrees() -> None:
    e = allocation.entrees()
    m = allocation.meta()

    st.markdown("#### Ce qui entre dans le calcul")
    st.markdown(
        "Un calcul d'allocation a besoin de trois choses : une règle à "
        "respecter, ce que chaque support doit rapporter, et la façon dont "
        "chaque support se comporte quand les marchés baissent. Les deux "
        "premières viennent des étapes précédentes ; la troisième demande "
        "de remonter loin dans le passé, et c'est là que se trouve la "
        "principale difficulté de cet onglet."
    )

    # --- 1. la règle ---------------------------------------------------
    st.markdown("**1. La règle de perte : l'hypothèse de travail**")
    st.markdown(
        "L'étape 1 avait laissé ouverte la définition exacte des 15 %. Faute "
        "de réponse du client, on retient la lecture la plus exigeante."
    )
    st.table(pd.DataFrame([
        ("Perte mesurée comment ?",
         "Depuis le plus haut jamais atteint, sans limite de durée",
         "C'est ce que le client verra : l'écart entre ce qu'il a eu et ce "
         "qu'il a. Une mesure sur douze mois glissants oublierait une partie "
         "des baisses longues : en 2008, les actions européennes ont baissé "
         "vingt mois d'affilée, de juillet 2007 à mars 2009."),
        ("Sur quel montant ?",
         "Les 100 M€ ensemble, en euros",
         "Le client raisonne sur son patrimoine, pas poche par poche. Les "
         "10 M€ à décaisser en font partie."),
        ("Avec quelle tolérance ?",
         "Jamais au-delà de 15 % dans les crises passées : 2008, 2011, "
         "2020, 2022",
         "Facile à expliquer et à vérifier. Si aucun portefeuille ne tient "
         "en rapportant 4 %, on passera à une limite en probabilité "
         "(dépassée moins d'une fois sur vingt)."),
        ("Et la crypto ?",
         "Une poche de 1 à 2 %, posée à côté du calcul",
         "Son rendement espéré est nul (étape 2) : un calcul ne la choisirait "
         "jamais. La détenir est un choix du client, dont on montrera le "
         "coût en risque."),
    ], columns=["Question laissée ouverte", "Hypothèse retenue", "Pourquoi"])
        .set_index("Question laissée ouverte"))

    # --- 2. les rendements --------------------------------------------
    st.markdown("**2. Ce que chaque support doit rapporter**")
    st.markdown(
        "Les rendements espérés de l'étape 2, corrigés là où l'étape 3 a "
        "appris quelque chose en choisissant les supports. Les emprunts "
        "d'État sont achetés en direct : ils rapportent le taux de l'échelle "
        "retenue, pas celui du marché entier. Le crédit passe par un fonds "
        "court, qui rapporte moins que l'indice toutes durées."
    )
    lignes = [(r.classe, r.support, _pct(r.rendement), r.origine)
              for r in e.itertuples()]
    st.table(pd.DataFrame(lignes, columns=[
        "Classe", "Support (étape 3)", "Rendement espéré par an",
        "D'où vient ce chiffre"]).set_index("Classe"))
    calc = e[~e["hors_calcul"]]
    bat = calc[calc["rendement"] > 4]["classe"].tolist()
    st.markdown(
        f"**Lecture.** Seules {len(bat)} classes sur {len(calc)} rapportent "
        f"plus que les 4 % à battre : "
        + ", ".join(c.lower() for c in bat[:-1]) + f" et {bat[-1].lower()}. "
        "Tout le reste rapporte moins : chaque euro placé en obligations ou "
        "en or devra être compensé par des actions. C'est, en "
        "chiffres, la tension annoncée à l'étape 1 entre les 4 % et les 15 %."
    )
    st.caption(
        "Actions européennes : on garde le rendement espéré de l'indice. Le "
        "panier des 30 titres n'est pas supposé battre son marché ; le "
        "supposer serait compter deux fois la sélection."
    )

    # --- 3. les séries longues ----------------------------------------
    st.markdown("**3. Mesurer le risque sur vingt ans : les séries de "
                "remplacement**")
    st.markdown(
        "Pour savoir si le portefeuille aurait tenu en 2008, il faut savoir "
        "comment chaque support s'est comporté en 2008. Or la plupart des "
        "supports retenus sont récents : les fonds américain et japonais "
        "datent de 2018, le fonds émergent de 2019, le fonds bitcoin de "
        "2025. On utilise donc **le vrai support dès qu'il existe, et avant "
        "lui un remplaçant** qui suit le même marché : un fonds plus ancien "
        "sur le même indice, converti en euros, ou, pour les emprunts "
        "d'État détenus en direct, une obligation reconstituée à partir de "
        "la courbe des taux de la BCE."
    )
    lignes = []
    for r in e.itertuples():
        c = r.controle
        if isinstance(r.raccord, str):
            propre = pd.Timestamp(r.raccord).strftime("%m/%Y")
        elif r.Index == "actions_europe":
            propre = "non utilisé (voir plus bas)"
        else:
            propre = "reconstitué sur toute la période"
        lignes.append((
            r.classe, propre, r.source,
            viz.fr(c["correlation"], "", 2),
            f"{viz.fr(c['baisse_remplacant'], '%', 0)} / "
            f"{viz.fr(c['baisse_support'], '%', 0)}",
            f"{viz.fr(c['annees'], 'ans', 0)}"))
    st.table(pd.DataFrame(lignes, columns=[
        "Classe", "Vrai support utilisé depuis", "Remplaçant, avant",
        "Ressemblance*", "Pire baisse : remplaçant / support**",
        "Comparés sur"]).set_index("Classe"))
    st.caption(
        "* Corrélation des variations hebdomadaires sur la période où les "
        "deux existent : 1 = ils bougent exactement ensemble, 0 = aucun "
        "lien. ** Sur cette même période commune. Pour les emprunts d'État "
        "reconstitués, la comparaison se fait avec un fonds voisin (IBGS "
        "pour l'échelle courte, EUNH pour la longue), dont la durée diffère : "
        "c'est un ordre de grandeur, pas un contrôle exact. Toutes les "
        f"séries commencent en octobre 2006, sauf le bitcoin (septembre "
        f"2014). Relevé du {pd.Timestamp(m['releve']).strftime('%d/%m/%Y')}."
    )

    st.markdown(
        "**Lecture.** Les remplaçants d'actions, d'or et de matières "
        "premières suivent bien leur support (ressemblance de 0,83 à 0,95). "
        "Quatre limites sont à connaître :"
    )
    ctl = e["controle"]
    st.table(pd.DataFrame([
        ("Actions émergentes et japonaises",
         f"Les fonds retenus, filtrés ESG, ont davantage baissé que leur "
         f"remplaçant ({viz.fr(ctl['emergents']['baisse_support'], '%', 0)} "
         f"contre {viz.fr(ctl['emergents']['baisse_remplacant'], '%', 0)} "
         f"pour les émergents). Le remplaçant n'est utilisé qu'avant 2018-"
         f"2019 : le risque de 2008 et 2011 est peut-être un peu sous-"
         f"estimé sur ces deux lignes."),
        ("Obligations indexées",
         "Avant janvier 2009, on utilise un emprunt d'État classique à "
         "7 ans. En 2008, les indexées ont moins bien tenu que les emprunts "
         "classiques (l'inflation attendue s'est effondrée) : le remplaçant "
         "flatte cette ligne pendant la crise de 2008."),
        ("Crédit court",
         f"La prime de crédit est reconstituée avant 2016 à partir des "
         f"écarts de crédit américains, avec une sensibilité mesurée sur le "
         f"vrai fonds ({viz.fr(-m['credit']['sensibilite'], '%', 2)} par "
         f"point d'écart). Le lien est faible (ressemblance "
         f"{viz.fr(ctl['credit_court']['correlation'], '', 2)}) : cette "
         f"ligne est la moins bien mesurée en 2008 et 2011."),
        ("Actions européennes",
         "On mesure le risque sur l'indice européen, pas sur le panier des "
         "30 titres. Le panier est choisi avec les données d'aujourd'hui : "
         f"son passé est flatteur par construction "
         f"({viz.fr(ctl['actions_europe']['perf_support'], '%', 1)} par an "
         f"depuis 2019 contre "
         f"{viz.fr(ctl['actions_europe']['perf_remplacant'], '%', 1)} pour "
         f"l'indice). Son risque, lui, est proche de celui de l'indice "
         f"(étape 3)."),
    ], columns=["Ligne", "Ce qu'il faut savoir"]).set_index("Ligne"))

    pedago.explique(
        "Pourquoi commencer en octobre 2006, et pas en 2008",
        "Les actions européennes ont atteint leur plus haut en juillet 2007. "
        "Une série qui commencerait en janvier 2008 ne verrait la baisse de "
        "2008 qu'à partir d'un point déjà plus bas, et la sous-estimerait. "
        "Comme on mesure les pertes depuis le plus haut, il faut que le plus "
        "haut soit dans les données.",
        "Les cotations européennes gratuites (Yahoo) ne remontent pas avant "
        "2008. D'où le recours à des fonds cotés à New York, plus anciens, "
        "dont on convertit chaque jour le prix en euros au cours du dollar : "
        "c'est bien ce qu'aurait vécu un investisseur européen.",
        "Pour les emprunts d'État, on fait mieux qu'un remplaçant : la BCE "
        "publie chaque jour depuis 2004 les paramètres de sa courbe des "
        "taux. On en déduit, jour après jour, le prix d'une obligation de "
        "2, 3, 5, 7 ou 10 ans, et donc ce qu'aurait rapporté l'échelle "
        "retenue à l'étape 3.",
        source="Yahoo Finance (fonds et change) ; BCE, paramètres de la "
               "courbe des emprunts d'État de la zone euro ; FRED, écarts de "
               "crédit ICE BofA. Script : scripts/fetch_indices.py.",
    )

    st.markdown("#### Ce que le bloc 1 transmet au bloc 2")
    st.markdown(
        f"Onze supports, dont dix entrent dans le calcul, chacun avec un "
        f"rendement espéré et une série quotidienne en euros depuis octobre "
        f"2006, qui traverse les quatre crises de référence. Le bloc 2 "
        f"mesure ce que chacun y a perdu, et surtout s'ils ont perdu en même "
        f"temps."
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
            "vol": allocation.volatilite(s), "pendant": pendant,
            "dates": dates, "corr": allocation.correlations(s)}


def _bloc_risque() -> None:
    e = allocation.entrees()
    r = _risque()
    pertes, vol = r["pertes"], r["vol"]
    crises = allocation.CRISES

    st.markdown("#### Le risque de chaque support")
    st.markdown(
        "Pour tenir la limite de 15 %, il faut savoir deux choses sur chaque "
        "support : combien il a perdu dans les crises passées, et s'il a "
        "perdu **en même temps** que les autres. Un support qui baisse "
        "beaucoup mais à contretemps protège le portefeuille ; un support "
        "qui baisse peu mais toujours avec les actions ne le protège pas. "
        "Les actions entrent désormais dans le calcul comme **une seule "
        "poche**, répartie entre les zones selon la clé fixée à l'avance "
        "(Europe 40 %, États-Unis 35 %, Japon 10 %, émergents 15 %)."
    )

    # --- 1. les pertes ------------------------------------------------
    st.markdown("**1. Ce que chaque support a perdu, depuis son plus haut**")
    st.markdown(
        "Quatre crises, choisies à l'avance par leurs dates. Pour chacune, "
        "la pire baisse depuis le plus haut atteint auparavant — la mesure "
        "de la limite de 15 %."
    )
    lignes = []
    for k in pertes.index:
        lignes.append([_nom(k, e), viz.fr(vol[k], "%", 1)]
                      + [_v(pertes.loc[k, c]) for c in crises])
    cols = ["Support", "Volatilité annuelle*"] + [
        f"{c} · {lib}" for c, (_, _, lib) in crises.items()]
    st.table(pd.DataFrame(lignes, columns=cols).set_index("Support"))
    st.caption(
        "* Volatilité : l'amplitude habituelle des variations sur un an, "
        "calculée sur les variations hebdomadaires d'octobre 2006 à "
        "aujourd'hui. Elle décrit les jours ordinaires ; les colonnes de "
        "crise décrivent les pires. En 2011, les actions n'avaient pas "
        "retrouvé leur plus haut de 2007 : la perte comptée part de 2007, "
        "c'est la règle. Même chose pour les matières premières, qui n'ont "
        "jamais retrouvé leur sommet de 2008. Bitcoin : cotations depuis "
        "2014 seulement."
    )
    pa = pertes.loc["poche_actions", "2008"]
    st.markdown(
        f"**Lecture.** Les actions perdent entre "
        f"{viz.fr(-pertes.loc['poche_actions'].max(), '%', 0)} et "
        f"{viz.fr(-pa, '%', 0)} dans ces crises, les emprunts d'État à "
        f"court terme presque rien. Une règle simple en découle : si rien "
        f"d'autre n'amortissait, une perte de {viz.fr(-pa, '%', 0)} sur les "
        f"actions ne laisserait pas y placer plus de "
        f"{viz.fr(15 / -pa * 100, '%', 0)} du patrimoine (15 ÷ "
        f"{viz.fr(-pa, '', 0)}). Tout ce qui dépasse ce chiffre doit être "
        f"payé par des supports qui montent quand les actions baissent. "
        f"D'où la question suivante."
    )

    # --- 2. pendant la baisse ----------------------------------------
    st.markdown("**2. Que faisaient les autres pendant que les actions "
                "baissaient ?**")
    pendant, dates = r["pendant"], r["dates"]
    lignes = []
    for k in pendant.index:
        if k in allocation.MIX_ACTIONS:
            continue
        lignes.append([_nom(k, e)] + [_v(pendant.loc[k, c], True)
                                      for c in crises])
    cols = ["Support"] + [
        f"{c} : du {a.strftime('%d/%m/%y')} au {b.strftime('%d/%m/%y')}"
        for c, (a, b) in dates.items()]
    st.table(pd.DataFrame(lignes, columns=cols).set_index("Support"))
    st.caption(
        "Pour chaque crise, du sommet au creux de la poche actions ; la "
        "première ligne rappelle sa baisse. Sommet cherché dans la crise "
        "elle-même, pour mesurer la crise et non les années qui la "
        "précèdent."
    )
    p = pendant
    st.table(pd.DataFrame([
        ("2008 et 2011 : les emprunts d'État amortissent",
         f"Les actions perdent {_v(-p.loc['poche_actions', '2008'])}, "
         f"l'échelle d'États à 2-10 ans gagne "
         f"{_v(p.loc['etats_longs', '2008'], True)} et l'or "
         f"{_v(p.loc['or', '2008'], True)}. C'est le cas d'école : quand "
         f"l'économie s'effondre, les banques centrales baissent leurs taux "
         f"et les obligations montent."),
        ("2022 : plus d'amortisseur",
         f"Les actions perdent {_v(-p.loc['poche_actions', '2022'])}, et les "
         f"emprunts d'État aussi ({_v(p.loc['etats_longs', '2022'])}), comme "
         f"les indexées ({_v(p.loc['indexees', '2022'])}). Quand la baisse "
         f"vient de l'inflation, les banques centrales montent leurs taux : "
         f"actions et obligations baissent ensemble. C'est le régime que "
         f"décrit l'étape 2 aujourd'hui."),
        ("L'or : le seul qui tient dans les quatre crises",
         f"Hausse en 2008, 2011 et 2022, léger recul en 2020 "
         f"({_v(p.loc['or', '2020'], True)}). Mais il a sa propre baisse de "
         f"{_v(-pertes.loc['or', '2008'])} depuis son plus haut en 2008 : "
         f"il protège contre les actions, pas contre lui-même."),
        ("Matières premières et bitcoin : ils baissent avec les actions",
         f"Les matières premières perdent "
         f"{_v(-p.loc['matieres', '2008'])} en 2008 et "
         f"{_v(-p.loc['matieres', '2020'])} en 2020 ; le bitcoin "
         f"{_v(-p.loc['crypto', '2022'])} en 2022. Aucun amortisseur à en "
         f"attendre."),
        ("Obligations indexées : attention à 2008",
         "Leur hausse de 2008 vient du remplaçant (un emprunt d'État "
         "classique, bloc 1). Les vraies indexées ont moins bien tenu "
         "cette année-là : cette ligne est flattée."),
    ], columns=["Constat", "Détail"]).set_index("Constat"))

    _graphique_baisses(r["s"])

    # --- 3. corrélations ---------------------------------------------
    st.markdown("**3. Bouger ensemble : le lien avec les actions**")
    c = r["corr"]

    def lien(x: float) -> str:
        if x >= .6:
            return "suit les actions"
        if x >= .3:
            return "les suit en partie"
        if x > -.1:
            return "sans lien"
        return "va à contretemps"

    lignes = []
    for k in c.index:
        if k in allocation.MIX_ACTIONS or k == "poche_actions":
            continue
        lignes.append((_nom(k, e),
                       viz.fr(round(c.loc[k, "hors_crise"], 2) + 0.0, "", 2),
                       viz.fr(round(c.loc[k, "en_crise"], 2) + 0.0, "", 2),
                       lien(c.loc[k, "en_crise"])))
    st.table(pd.DataFrame(lignes, columns=[
        "Support", "Hors crise", "Pendant les quatre crises",
        "En crise, il…"]).set_index("Support"))
    st.caption(
        "Corrélation des variations hebdomadaires avec la poche actions : "
        "1 = mêmes mouvements, 0 = aucun lien, négatif = mouvements "
        "opposés. Moyenne sur les quatre crises réunies : elle mélange "
        "2008 (États à contretemps) et 2022 (États avec les actions), "
        "d'où un chiffre proche de zéro qui ne dit pas que les États "
        "n'ont servi à rien — il dit qu'ils ont servi une fois sur deux."
    )

    pedago.explique(
        "Pourquoi la corrélation ne suffit pas, et ce que le calcul utilisera",
        "La corrélation résume en un chiffre une relation qui change selon "
        "la crise. Les emprunts d'État ont une corrélation proche de zéro "
        "avec les actions sur l'ensemble des crises : c'est la moyenne "
        "d'un très bon amortisseur (2008) et d'un amortisseur absent "
        "(2022). Un modèle qui ne verrait que ce chiffre moyen se "
        "tromperait dans les deux cas.",
        "C'est pourquoi le calcul du bloc 3 ne s'appuie pas sur la "
        "corrélation pour tenir la limite de perte : il fait traverser à "
        "chaque portefeuille candidat les vingt années de données, jour "
        "après jour, avec un rééquilibrage chaque mois, et mesure "
        "directement sa pire baisse depuis le plus haut. Les crises de "
        "2008 et de 2022 sont donc prises telles qu'elles ont eu lieu, "
        "chacune avec son propre comportement.",
        source="Séries du bloc 1 (scripts/fetch_indices.py). Crises "
               "définies à l'avance dans core/allocation.py (CRISES).",
    )

    st.markdown("#### Ce que le bloc 2 transmet au bloc 3")
    st.markdown(
        "Une poche actions qui perd jusqu'à "
        f"{viz.fr(-pa, '%', 0)} ; des emprunts d'État qui amortissent les "
        "crises de récession mais pas celles d'inflation ; un or qui tient "
        "dans les quatre ; des matières premières et un bitcoin qui "
        "n'amortissent rien. Le bloc 3 cherche la répartition qui rapporte "
        "le plus, en exigeant qu'elle ne perde jamais plus de 15 % sur les "
        "vingt années de données."
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
