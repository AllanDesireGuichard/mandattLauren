"""
Primes de crédit et leur histoire -> data/credit_histo.csv + data/credit.json

Lancer :  python3 scripts/fetch_credit.py

POURQUOI UN FICHIER D'HISTORIQUE QUI S'ACCUMULE. Depuis 2023, FRED ne diffuse
plus que les TROIS DERNIÈRES ANNÉES des indices ICE BofA (licence ICE). Trois
ans ne contiennent aucune crise : impossible de dire si une prime est haute ou
basse. On conserve donc l'historique dans le dépôt, et chaque passage de ce
script y AJOUTE les nouvelles observations sans jamais rien effacer.

Amorçage (une seule fois, si le fichier n'existe pas) : les séries ICE haut
rendement US et BBB US depuis 2010, téléchargées par le projet EquityDB avant
la coupure (~/projets/equitydb/data/macro/macro_fred.parquet).

La série la plus longue, Moody's Baa moins Trésor 10 ans (BAA10Y), n'est pas
une série ICE : FRED la diffuse en entier depuis 1986. C'est elle qui porte
le diagnostic historique, parce qu'elle traverse 2008.
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
HISTO = RACINE / "data" / "credit_histo.csv"
RESUME = RACINE / "data" / "credit.json"
AMORCE = Path.home() / "projets" / "equitydb" / "data" / "macro" / "macro_fred.parquet"

SERIES = {
    "BAA10Y": "Entreprises notées Baa (Moody's), États-Unis",
    "BAMLC0A0CM": "Entreprises bien notées, États-Unis (ICE)",
    "BAMLC0A4CBBB": "Entreprises notées BBB, États-Unis (ICE)",
    "BAMLH0A0HYM2": "Haut rendement, États-Unis (ICE)",
    "BAMLHE00EHYIOAS": "Haut rendement, zone euro (ICE)",
    "BAMLEMCBPIOAS": "Entreprises émergentes, en dollars (ICE)",
}
CRISES = {"2008": ("2008-01-01", "2009-12-31"),
          "2020": ("2020-01-01", "2020-12-31"),
          "2022": ("2022-01-01", "2022-12-31")}


def _fred_key() -> str:
    from core.sources import CleManquante, fred_key
    try:
        return fred_key()
    except CleManquante:
        f = RACINE / ".streamlit" / "secrets.toml"
        return tomllib.loads(f.read_text())["FRED_API_KEY"]


def fred(serie: str) -> pd.Series:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": serie, "api_key": _fred_key(),
                             "file_type": "json"}, timeout=120)
    r.raise_for_status()
    s = pd.Series({o["date"]: float(o["value"])
                   for o in r.json()["observations"] if o["value"] != "."},
                  dtype=float)
    s.index = pd.to_datetime(s.index)
    return s


def charger_histo() -> pd.DataFrame:
    if HISTO.exists():
        return pd.read_csv(HISTO, index_col="date", parse_dates=True)
    if not AMORCE.exists():
        print("  (pas d'amorce EquityDB : historique limité à ce que FRED "
              "diffuse)")
        return pd.DataFrame()
    d = pd.read_parquet(AMORCE).set_index("date")
    d.index = pd.to_datetime(d.index)
    print("  amorçage depuis le cache EquityDB")
    return d[["BAMLH0A0HYM2", "BAMLC0A4CBBB"]].dropna(how="all")


def resume(s: pd.Series) -> dict:
    s = s.dropna()
    v = float(s.iloc[-1])
    out = {"valeur": round(v, 2), "date": s.index[-1].date().isoformat(),
           "debut": s.index[0].date().isoformat(),
           "mediane": round(float(s.median()), 2),
           # part du temps où la prime était PLUS BASSE qu'aujourd'hui
           "rang": round(float((s < v).mean()) * 100),
           "pics": {}}
    for nom, (a, b) in CRISES.items():
        x = s[a:b]
        if len(x) and s.index[0] <= pd.Timestamp(a):
            out["pics"][nom] = round(float(x.max()), 2)
    return out


def main() -> int:
    histo = charger_histo()
    echecs = []
    for serie in SERIES:
        try:
            neuf = fred(serie).rename(serie)
            ancien = histo[serie] if serie in histo else pd.Series(dtype=float)
            # les observations récentes de FRED priment ; l'ancien complète
            fusion = neuf.combine_first(ancien)
            histo = histo.reindex(histo.index.union(fusion.index))
            histo[serie] = fusion
            print(f"  ok      {serie}  ({fusion.dropna().index[0].date()} → "
                  f"{fusion.dropna().index[-1].date()})")
        except Exception as e:                       # noqa: BLE001
            echecs.append(serie)
            print(f"  ÉCHEC   {serie} — {e} (historique conservé)")

    histo = histo.sort_index()
    histo.index.name = "date"
    histo.round(3).to_csv(HISTO)
    # L'Europe n'a pas de série longue gratuite. On mesure, sur la période
    # commune, à quel point sa prime suit l'américaine : c'est ce qui autorise
    # (ou non) à lire l'historique américain comme un repère pour l'Europe.
    commun = histo[["BAMLH0A0HYM2", "BAMLHE00EHYIOAS"]].dropna()
    hebdo = commun.resample("W").last()
    lien = {"niveaux": round(float(hebdo.corr().iloc[0, 1]), 2),
            "variations_hebdo": round(float(hebdo.diff().corr().iloc[0, 1]), 2),
            "debut": commun.index[0].date().isoformat()}

    RESUME.write_text(json.dumps(
        {"releve": date.today().isoformat(),
         "lien_us_europe": lien,
         "series": {k: {"nom": n} | resume(histo[k])
                    for k, n in SERIES.items() if k in histo}},
        ensure_ascii=False, indent=2) + "\n")
    print(f"\n{HISTO.relative_to(RACINE)} et {RESUME.relative_to(RACINE)} "
          f"écrits" + (f" — {len(echecs)} échec(s)" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
