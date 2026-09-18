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
    pedago.a_construire(
        4, "Allocation",
        "**Le risque** : ce que chaque support a perdu en 2008, 2011, 2020 "
        "et 2022, depuis son plus haut, et comment les supports ont bougé "
        "ensemble — ou non — dans ces crises.",
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
