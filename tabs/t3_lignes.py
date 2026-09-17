"""Étape 3 — Analyse ligne à ligne. À construire."""
from __future__ import annotations

from core import pedago


def render() -> None:
    pedago.chaine(3)
    pedago.etape(
        3, "Analyse ligne à ligne",
        "L'entonnoir de sélection, sur le modèle du process TCP Kenz : "
        "univers brut, filtre macro issu de l'étape 2, filtre d'exclusion, "
        "puis notation. Trois familles d'instruments y sont traitées "
        "séparément parce qu'elles ne s'analysent pas de la même façon — des "
        "fonds, des actions en direct, des obligations en direct.",
    )
    pedago.a_construire(
        3, "Analyse ligne à ligne",
        "**Fonds et ETF** : les 48 supports déjà retenus, avec frais, écart "
        "de suivi, encours et liquidité.",
        "**Actions en direct** : univers de départ le STOXX Europe 600, noté "
        "sur les quatre piliers du modèle Kenz — Valorisation, Croissance, "
        "Momentum, Qualité — avec des notes normalisées au sein de chaque "
        "secteur, et une fiche par titre retenu.",
        "**Obligations souveraines en direct** : construites sur la courbe "
        "zéro-coupon de la BCE plutôt que cherchées en cotation. On price "
        "une obligation bullet et on en sort rendement, duration, convexité, "
        "portage et effet de glissement sur la courbe.",
        "**Crédit** : représenté par courbe plus spread d'indice observé, "
        "avec l'analyse de spreads des pages 48 et 49 du document Kenz. Une "
        "ligne corporate nommée n'est pas accessible de façon fiable sans "
        "source de données payante — la limite est assumée plutôt que "
        "contournée par une donnée douteuse.",
        "**Le filtre d'exclusion**, appliqué là où il a un objet.",
    )
