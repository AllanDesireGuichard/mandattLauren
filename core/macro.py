"""
Lecture de la photo des indicateurs macro (data/macro.json).

Produite par scripts/fetch_macro.py. Chaque indicateur porte sa valeur, sa
date, sa source, et sa valeur six mois plus tôt (un an pour le PIB) : on
montre toujours un niveau ET un sens.
"""
from __future__ import annotations

import json
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "data" / "macro.json"


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))
