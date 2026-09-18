"""
Lecture de la dynamique des marchés actions (data/marches.json).

Produite par scripts/fetch_marches.py : performances en euros, supports cotés
à Francfort, libellés et devises contrôlés à chaque passage.
"""
from __future__ import annotations

import json
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "data" / "marches.json"


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))
