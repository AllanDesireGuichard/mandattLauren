"""
Lecture des rendements espérés par classe d'actifs (data/rendements.json).

Produits par scripts/estimer_rendements.py. C'est la SORTIE de l'onglet 2 et
l'entrée de l'allocation (étape 4). Remplace à terme core/cma.py, dont les
coefficients de répercussion de l'inflation étaient supposés, pas mesurés.
"""
from __future__ import annotations

import json
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "data" / "rendements.json"

ORDRE = ["cash", "govt_bonds_eur_short", "govt_bonds_eur", "credit_ig_eur",
         "inflation_linked", "equity_developed", "us", "europe", "zone_euro",
         "japon", "equity_emerging", "infrastructure", "gold", "alternatives",
         "crypto", "hy_euro"]
SOUS_LIGNES = {"us", "europe", "zone_euro", "japon"}


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))
