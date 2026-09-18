"""
Lecture de la photo des taux de marché (data/taux_marche.json).

La photo est produite par scripts/fetch_taux.py ; l'application ne va jamais
chercher ces chiffres en direct (API BCE lente, pages iShares instables).
Chaque point porte sa PROPRE date : les sources ne publient pas au même
rythme, et la fiche mensuelle des obligations indexées a plusieurs semaines
de retard sur le reste.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

FICHIER = Path(__file__).resolve().parents[1] / "data" / "taux_marche.json"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))


def date_fr(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def courbe(photo: dict) -> pd.DataFrame:
    c = photo["courbes"]
    return pd.DataFrame({"Maturité (ans)": c["maturites"],
                         "États notés AAA": c["aaa"],
                         "Tous États de la zone euro": c["toutes"]})
