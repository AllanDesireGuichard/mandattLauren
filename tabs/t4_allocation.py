"""Étape 4 — Allocation. À construire."""
from __future__ import annotations

from core import pedago


def render() -> None:
    pedago.chaine(4)
    pedago.etape(
        4, "Allocation",
        "La combinaison des supports de l'étape 3 sous les contraintes de "
        "l'étape 1, avec les hypothèses de l'étape 2. Cet onglet est celui "
        "où la transparence compte le plus : un poids de portefeuille sans "
        "son chemin de calcul est un poids qu'on ne peut pas défendre.",
    )
    pedago.a_construire(
        4, "Allocation",
        "**Trois estimateurs de covariance comparés côte à côte** : "
        "covariance d'échantillon, rétrécissement de Ledoit-Wolf, et modèle "
        "factoriel. L'effet de chacun sur les poids finaux est mesuré, pas "
        "supposé.",
        "**Les corrélations en période de stress**, estimées sur des crises "
        "définies à l'avance et non par sélection statistique — conditionner "
        "sur une somme biaise mécaniquement les corrélations entre ses "
        "composantes.",
        "**Black-Litterman**, avec les vues de l'étape 2 — et la mesure "
        "honnête de son apport. Dans la version précédente, l'écart entre le "
        "portefeuille avant et après incorporation des vues plafonnait à "
        "0,09 %, parce que les vues découlaient des mêmes hypothèses que le "
        "point d'ancrage. Le modèle sera montré avec ce constat, pas sans.",
        "**Le résultat de l'optimisation libre, affiché AVANT le résultat "
        "contraint.** C'est lui qui révèle ce que le modèle ignore : la "
        "version précédente sortait 27,8 % d'infrastructure, 0,8 % d'or et "
        "zéro souverain — correct au regard des données, inutilisable au "
        "regard du mandat.",
        "**Chaque contrainte listée une par une**, avec ce qu'elle encode "
        "que la covariance ne voit pas, et son coût chiffré en rendement.",
        "**L'écart entre le portefeuille libre et le portefeuille retenu**, "
        "chiffré poste par poste.",
    )
