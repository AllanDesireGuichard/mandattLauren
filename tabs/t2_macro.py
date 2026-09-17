"""Étape 2 — Macro top-down. À construire."""
from __future__ import annotations

from core import pedago


def render() -> None:
    pedago.chaine(2)
    pedago.etape(
        2, "Macro top-down",
        "L'analyse descendante, zone par zone, sur le modèle du process TCP "
        "Kenz : on part de l'activité, on en déduit l'inflation, puis la "
        "politique monétaire, puis la courbe des taux, et seulement à la fin "
        "les primes de risque par classe d'actifs. La sortie de cet onglet "
        "est un jeu d'hypothèses chiffrées, qui devient l'entrée de "
        "l'étape 4.",
    )
    pedago.a_construire(
        2, "Macro top-down",
        "**La chaîne causale**, explicitée maillon par maillon pour les "
        "États-Unis, la zone euro et les émergents : croissance → inflation "
        "→ politique monétaire → courbe → prime de risque.",
        "**Les indicateurs d'activité** depuis FRED : PIB, PMI manufacturier "
        "et services, confiance des ménages, production industrielle, "
        "emploi, chômage.",
        "**Les courbes de taux** : courbe zéro-coupon AAA de la zone euro "
        "(source BCE, quotidienne), courbe des Treasuries, pente 2-10 ans.",
        "**Les spreads de crédit** observés : investment grade, high yield "
        "euro et dollar, dette émergente en devise forte (indices ICE BofA).",
        "**Le point d'inflation anticipé par le marché**, à comparer à "
        "l'hypothèse de 4 % du mandat.",
        "**Le tableau de momentum multi-horizon** des grands indices et "
        "secteurs, sur le modèle des pages 18 et 19 du document Kenz.",
        "**La détection de régime**, tenue volontairement simple et lisible "
        "plutôt que confiée à un modèle opaque.",
        "**La recalibration des hypothèses de rendement** sur ces courbes "
        "vivantes : la version actuelle s'ancre sur un taux monétaire EUR de "
        "2,05 %, alors que le taux de dépôt BCE est à 2,50 %.",
    )
