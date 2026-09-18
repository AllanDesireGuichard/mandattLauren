"""
Lecture des primes de crédit (data/credit.json, data/credit_histo.csv).

Produits par scripts/fetch_credit.py. L'historique est conservé dans le dépôt
parce que FRED ne diffuse plus que trois ans des indices ICE.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def charger() -> dict:
    return json.loads((DATA / "credit.json").read_text(encoding="utf-8"))


def histo() -> pd.DataFrame:
    return pd.read_csv(DATA / "credit_histo.csv", index_col="date",
                       parse_dates=True)
