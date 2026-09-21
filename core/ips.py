"""
Paramètres du mandat : les données du problème, pas des variables de
décision. Aucune n'est réglable dans l'application.

Allégé le 2026-09-18 : la SAA, les hypothèses de marché et les contrôles de
la v1 (core/cma.py) ont été retirés ; l'allocation est désormais construite
à l'étape 4 (core/allocation.py). L'ancien contenu reste dans l'historique
git (commit 70b0b67 et antérieurs).
"""
from __future__ import annotations

TOTAL_ASSETS = 100_000_000.0      # EUR, produit de cession
LIQUIDITY_NEED = 10_000_000.0     # EUR, à décaisser sous 24 mois
INFLATION_TARGET = 0.0400         # hypothèse du client, figée (étape 1)
MAX_DRAWDOWN = 0.15               # depuis le plus haut, 100 M€ consolidés

# Frais de mandat, ajoutés le 2026-09-21.
#
# POURQUOI ILS MANQUAIENT, ET POURQUOI C'ÉTAIT UNE ERREUR. L'objectif du
# client — préserver son pouvoir d'achat — est un objectif NET : ce qui doit
# battre l'inflation, c'est ce qui reste dans sa poche. Or les rendements
# espérés de l'étape 2 sont BRUTS. Comparer les deux directement surévalue
# la marge, et un jury pose la question en une phrase : « votre 5,31 %,
# c'est avant frais ? »
#
# Le chiffre : 0,40 % par an, négocié sur la taille d'actifs. C'est celui
# que retenait la première version du dossier (archive/docs/02_ips.md, § 3).
# Les frais d'instruments, eux, ne sont pas ici : ils dépendent des supports
# retenus et se calculent à l'étape 4.
#
# LA FISCALITÉ RESTE HORS PÉRIMÈTRE (décision du 2026-09-17, l'exercice
# porte sur la chaîne d'investissement). La v1 y ajoutait 0,30 % de friction
# fiscale annuelle, ce qui portait le seuil brut requis à 4,85 %.
FRAIS_MANDAT = 0.0040


def rendement_net(brut: float, frais_instruments: float) -> float:
    """
    Ce qui reste au client, en points de pourcentage.

    `brut` et `frais_instruments` sont en points (5.31 pour 5,31 %). C'est
    CE chiffre qui se compare au seuil d'inflation, jamais le brut.
    """
    return brut - frais_instruments - FRAIS_MANDAT * 100
