"""Étape 5 — Backtests sous contraintes. À construire."""
from __future__ import annotations

from core import pedago


def render() -> None:
    pedago.chaine(5)
    pedago.etape(
        5, "Backtests sous contraintes",
        "La vérification. Non pas « combien ça aurait rapporté », mais "
        "« la contrainte de perte de 15 % aurait-elle tenu », et avec quelle "
        "marge. Le risque y est présenté sous forme de distributions de "
        "gains et de pertes plutôt que de chiffres uniques.",
    )
    pedago.a_construire(
        5, "Backtests sous contraintes",
        "**Les distributions de gains et de pertes** : histogramme des "
        "rendements, distribution des drawdowns, temps passé sous l'eau.",
        "**VaR et CVaR par trois méthodes** — paramétrique, historique, et "
        "sous modèle GARCH comme à la page 55 du document Kenz — pour "
        "montrer que le choix de méthode déplace le chiffre.",
        "**La contrainte de 15 % vérifiée par chacune** de ces méthodes, "
        "avec la marge dans chaque cas.",
        "**Les crises nommées** : 2008, 2011, 2020, 2022, en profondeur ET "
        "en durée de récupération.",
        "**Les fenêtres glissantes de dix ans**, avec la réserve statistique "
        "qui va avec — 21,8 ans ne contiennent que deux périodes de dix ans "
        "indépendantes, donc ces chemins se recoupent massivement.",
        "**Une limite énoncée d'emblée** : un backtest ligne à ligne serait "
        "malhonnête. Appliquer la notation actuelle à des prix passés "
        "utiliserait des fondamentaux qui n'étaient pas connus à l'époque. "
        "Le backtest porte donc sur l'allocation par classes d'actifs, et le "
        "seul pilier testable hors échantillon est le momentum, parce qu'il "
        "est le seul à ne se calculer que sur des prix.",
    )
