"""
Inflation zone euro RÉALISÉE sur la période du backtest -> data/inflation_realisee.json

Lancer :  PYTHONPATH=. python3 scripts/fetch_inflation_longue.py

POURQUOI CE FICHIER EXISTE. L'étape 5 rejoue le portefeuille d'octobre 2006 à
aujourd'hui et compare son rendement au seuil de 4 %. Or ce seuil est bâti
pour un monde à 4 % d'inflation, alors que la période mesurée a vécu une tout
autre inflation. Comparer les deux, c'est juger un résultat dans un régime
avec l'exigence d'un autre — exactement le piège que la v1 du dossier avait
identifié comme sa correction la plus importante (archive/docs/02_ips.md).

Ce que le fichier fournit : l'inflation zone euro effectivement constatée sur
la fenêtre exacte du backtest, pour que l'étape 5 puisse juger le rendement
réalisé contre le SEUIL DE LA PÉRIODE et non contre celui de l'énoncé.

SÉRIE. FRED, CP0000EZCCM086NEST — indice des prix à la consommation
harmonisé de la zone euro, mensuel, base 2015 = 100. C'est la même série que
scripts/fetch_macro.py utilise pour le glissement annuel : on prend ici tout
l'historique au lieu des seuls points récents.

PIÈGE ÉCARTÉ. On ne fait pas la moyenne des glissements annuels : elle
surpondère les années de forte inflation et ne redonne pas l'érosion réelle
du pouvoir d'achat. On calcule le taux composé entre les deux bornes, qui est
la seule mesure comparable à un rendement annualisé.
"""
from __future__ import annotations

import json
import sys
import tomllib
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from core import allocation  # noqa: E402

SERIE = "CP0000EZCCM086NEST"
SORTIE = RACINE / "data" / "inflation_realisee.json"


def _cle() -> str:
    from core.sources import CleManquante, fred_key
    try:
        return fred_key()
    except CleManquante:
        f = RACINE / ".streamlit" / "secrets.toml"
        return tomllib.loads(f.read_text())["FRED_API_KEY"]


def indice() -> pd.Series:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": SERIE, "api_key": _cle(),
                             "file_type": "json",
                             "observation_start": "1995-01-01"}, timeout=90)
    r.raise_for_status()
    s = pd.Series({o["date"]: float(o["value"])
                   for o in r.json()["observations"] if o["value"] != "."})
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def compose(s: pd.Series, debut: pd.Timestamp, fin: pd.Timestamp) -> dict:
    """Taux d'inflation composé entre deux dates, et ce qu'il a coûté."""
    a = s[s.index <= debut].iloc[-1]
    b = s[s.index <= fin].iloc[-1]
    da = s[s.index <= debut].index[-1]
    db = s[s.index <= fin].index[-1]
    ans = (db - da).days / 365.25
    return {
        "debut": da.date().isoformat(), "fin": db.date().isoformat(),
        "annees": round(ans, 2),
        "indice_debut": round(float(a), 2), "indice_fin": round(float(b), 2),
        "cumul": round(float(b / a - 1) * 100, 2),
        "annuel": round((float(b / a) ** (1 / ans) - 1) * 100, 2),
    }


def main() -> int:
    s = indice()
    # La fenêtre EXACTE du backtest, lue sur les séries de l'étape 4 : le
    # seuil doit porter sur la même période que le rendement qu'il juge.
    # Bitcoin EXCLU du dropna, comme dans scripts/optimiser.py : sa série ne
    # commence qu'en 2014 et tronquerait la fenêtre de huit ans.
    cles = [k for k in allocation.ORDRE if k not in allocation.HORS_CALCUL]
    series = allocation.series()[cles].dropna()
    debut, fin = series.index[0], series.index[-1]

    bt = compose(s, debut, fin)
    out = {
        "source": f"FRED, {SERIE} (IPCH zone euro, indice, base 2015 = 100)",
        "releve": date.today().isoformat(),
        "dernier_point": s.index[-1].date().isoformat(),
        "backtest": bt,
        # Quelques fenêtres de lecture, pour situer le chiffre.
        "fenetres": {
            lib: compose(s, pd.Timestamp(d), fin)
            for lib, d in (("10 ans", "2016-09-01"), ("5 ans", "2021-09-01"))
        },
        # Par année civile pleine, pour le graphique de l'étape 5.
        "annuel": {
            str(an): round(float(s[s.index <= f"{an}-12-01"].iloc[-1]
                                 / s[s.index <= f"{an - 1}-12-01"].iloc[-1]
                                 - 1) * 100, 2)
            for an in range(debut.year + 1, fin.year + 1)
            if len(s[s.index <= f"{an}-12-01"])
        },
    }
    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print(f"IPCH zone euro, dernier point {out['dernier_point']}")
    print(f"backtest {bt['debut']} -> {bt['fin']} ({bt['annees']} ans)")
    print(f"  inflation cumulée {bt['cumul']} %  soit {bt['annuel']} % par an")
    print("->", SORTIE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
