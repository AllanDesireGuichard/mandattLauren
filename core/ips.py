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
