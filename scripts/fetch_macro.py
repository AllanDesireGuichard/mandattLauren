"""
Photo des indicateurs macro -> data/macro.json

Lancer :  python3 scripts/fetch_macro.py

Même principe que scripts/fetch_taux.py : l'application lit une photo datée,
elle ne va jamais chercher les chiffres en direct. Si une source échoue,
l'ancienne valeur est conservée avec son ancienne date.

SOURCES, choisies le 2026-09-18 après test :
  - FRED pour les États-Unis, l'inflation de la zone euro (indices HICP à
    composition variable, jusqu'en août 2026) et les indicateurs avancés de
    l'OCDE (Chine, Inde, États-Unis).
  - BCE pour le chômage de la zone euro.
  - Eurostat pour le PIB de la zone euro.
  - FMI (Perspectives de l'économie mondiale) pour les émergents : croissance
    et inflation, réalisé et prévu.
PIÈGES ÉCARTÉS :
  - les séries d'inflation de la BCE (ICP) et d'Eurostat (prc_hicp_manr)
    s'arrêtent en décembre 2025 — changement de nomenclature en 2026 ;
  - le chômage et la production industrielle zone euro de FRED s'arrêtent
    en 2023 ;
  - l'inflation « émergents » agrégée du FMI est tirée vers le haut par
    quelques pays en très forte inflation (Turquie, Argentine, Iran) : on
    montre la Chine, l'Inde et le Brésil plutôt que l'agrégat.
"""
from __future__ import annotations

import io
import json
import sys
import tomllib
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
SORTIE = RACINE / "data" / "macro.json"
DEBUT_HISTO = "2021-01-01"          # début de la vague d'inflation


def _fred_key() -> str:
    from core.sources import CleManquante, fred_key
    try:
        return fred_key()
    except CleManquante:
        f = RACINE / ".streamlit" / "secrets.toml"
        return tomllib.loads(f.read_text())["FRED_API_KEY"]


def fred(serie: str, debut: str = "2019-01-01") -> pd.Series:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": serie, "api_key": _fred_key(),
                             "file_type": "json", "observation_start": debut},
                     timeout=90)
    r.raise_for_status()
    s = pd.Series({o["date"]: float(o["value"])
                   for o in r.json()["observations"] if o["value"] != "."})
    s.index = pd.to_datetime(s.index)
    return s


def bce(cle: str, n: int = 24) -> pd.Series:
    url = f"https://data-api.ecb.europa.eu/service/data/{cle}"
    for _ in range(4):
        try:
            r = requests.get(url, params={"lastNObservations": n,
                                          "format": "csvdata"}, timeout=120)
            if r.status_code == 200:
                d = pd.read_csv(io.StringIO(r.text))
                return pd.Series(d["OBS_VALUE"].values,
                                 index=pd.to_datetime(d["TIME_PERIOD"]))
        except requests.RequestException:
            pass
    raise RuntimeError(f"BCE injoignable : {cle}")


def eurostat_pib() -> pd.Series:
    r = requests.get(
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        "namq_10_gdp",
        params={"geo": "EA20", "s_adj": "SCA", "na_item": "B1GQ",
                "unit": "CLV_PCH_SM", "lastTimePeriod": 8}, timeout=120)
    r.raise_for_status()
    j = r.json()
    t = {v: k for k, v in j["dimension"]["time"]["category"]["index"].items()}
    s = pd.Series({pd.Period(t[int(k)].replace("-", ""), "Q").start_time: v
                   for k, v in j["value"].items()}).sort_index()
    return s


def fmi(indicateur: str, zones: list[str]) -> dict:
    r = requests.get(
        f"https://www.imf.org/external/datamapper/api/v1/{indicateur}",
        timeout=120)
    r.raise_for_status()
    v = r.json()["values"][indicateur]
    return {z: {a: v[z].get(a) for a in ("2025", "2026", "2027")}
            for z in zones}


def glissement(s: pd.Series, n: int) -> pd.Series:
    return ((s / s.shift(n) - 1) * 100).dropna()


def dernier(s: pd.Series, source: str, dec: int = 2) -> dict:
    return {"valeur": round(float(s.iloc[-1]), dec),
            "date": s.index[-1].date().isoformat(), "source": source}


def tendance(s: pd.Series, pas: int, dec: int = 2) -> dict:
    """Valeur `pas` observations plus tôt (séries mensuelles, trimestrielles)."""
    return {"avant": round(float(s.iloc[-1 - pas]), dec),
            "date_avant": s.index[-1 - pas].date().isoformat()}


def tendance_mois(s: pd.Series, mois: int, dec: int = 2) -> dict:
    """Valeur `mois` mois plus tôt, pour les séries quotidiennes."""
    cible = s.index[-1] - pd.DateOffset(months=mois)
    v = s[s.index <= cible]
    return {"avant": round(float(v.iloc[-1]), dec),
            "date_avant": v.index[-1].date().isoformat()}


# --------------------------------------------------------------------------
# Construction des blocs
# --------------------------------------------------------------------------

def etats_unis() -> dict:
    pib = glissement(fred("GDPC1"), 4)
    cpi = glissement(fred("CPIAUCSL"), 12)
    core = glissement(fred("CPILFESL"), 12)
    chom = fred("UNRATE")
    emplois = fred("PAYEMS").diff().rolling(3).mean().dropna()
    fed = fred("DFF")
    us2 = fred("DGS2")
    us10 = fred("DGS10")
    cli = fred("USALOLITOAASTSAM")
    out = {
        "pib": dernier(pib, "FRED, GDPC1, PIB réel, glissement sur un an", 1)
               | tendance(pib, 4, 1),
        "chomage": dernier(chom, "FRED, UNRATE", 1) | tendance(chom, 6, 1),
        "emplois": dernier(emplois, "FRED, PAYEMS, créations d'emplois "
                           "mensuelles, moyenne sur 3 mois (milliers)", 0)
                   | tendance(emplois, 6, 0),
        "inflation": dernier(cpi, "FRED, CPIAUCSL, glissement sur un an")
                     | tendance(cpi, 6),
        "inflation_sj": dernier(core, "FRED, CPILFESL (hors énergie et "
                                "alimentation), glissement sur un an")
                        | tendance(core, 6),
        "banque_centrale": dernier(fed, "FRED, DFF, taux effectif des fonds "
                                   "fédéraux") | tendance_mois(fed, 6),
        "taux_2a": dernier(us2, "FRED, DGS2") | tendance_mois(us2, 6),
        "taux_10a": dernier(us10, "FRED, DGS10") | tendance_mois(us10, 6),
        "avance": dernier(cli, "OCDE via FRED, indicateur avancé composite "
                          "(100 = tendance longue)") | tendance(cli, 6),
    }
    out["histo"] = _histo(cpi, core, fed.resample("ME").mean())
    return out


def zone_euro() -> dict:
    hicp = glissement(fred("CP0000EZCCM086NEST"), 12)
    core = glissement(fred("00XEFDEZCCM086NEST"), 12)
    depot = fred("ECBDFR")
    ea2 = bce("YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y", 200)
    ea10 = bce("YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y", 200)
    chom = bce("LFSI/M.I9.S.UNEHRT.TOTAL0.15_74.T")
    pib = eurostat_pib()
    out = {
        "pib": dernier(pib, "Eurostat, namq_10_gdp, PIB réel zone euro, "
                       "glissement sur un an", 1) | tendance(pib, 4, 1),
        "chomage": dernier(chom, "BCE, LFSI, taux de chômage zone euro", 1)
                   | tendance(chom, 6, 1),
        "inflation": dernier(hicp, "FRED, CP0000EZCCM086NEST (IPCH zone "
                             "euro), glissement sur un an") | tendance(hicp, 6),
        "inflation_sj": dernier(core, "FRED, 00XEFDEZCCM086NEST (IPCH hors "
                                "énergie, alimentation, alcool et tabac), "
                                "glissement sur un an") | tendance(core, 6),
        "banque_centrale": dernier(depot, "FRED, ECBDFR, taux de dépôt BCE")
                           | tendance_mois(depot, 6),
        "taux_2a": dernier(ea2, "BCE, courbe des États notés AAA, 2 ans")
                   | tendance_mois(ea2, 6),
        "taux_10a": dernier(ea10, "BCE, courbe des États notés AAA, 10 ans")
                    | tendance_mois(ea10, 6),
    }
    out["histo"] = _histo(hicp, core, depot.resample("ME").last())
    return out


def emergents() -> dict:
    zones = ["OEMDC", "CHN", "IND", "BRA"]
    return {
        "croissance": fmi("NGDP_RPCH", zones),
        "inflation": fmi("PCPIPCH", zones),
        "source_fmi": "FMI, Perspectives de l'économie mondiale (DataMapper)",
        "avance": {
            "chine": dernier(fred("CHNLOLITOAASTSAM"), "OCDE via FRED")
                     | tendance(fred("CHNLOLITOAASTSAM"), 6),
            "inde": dernier(fred("INDLOLITOAASTSAM"), "OCDE via FRED")
                    | tendance(fred("INDLOLITOAASTSAM"), 6),
        },
    }


def _histo(inflation: pd.Series, sous_jacente: pd.Series,
           taux: pd.Series) -> dict:
    """Séries mensuelles pour le graphique inflation / taux directeur."""
    t = taux.copy()
    t.index = t.index.to_period("M").to_timestamp()
    df = pd.DataFrame({"inflation": inflation, "sous_jacente": sous_jacente,
                       "taux": t})
    df = df[df.index >= DEBUT_HISTO].dropna(how="all")
    out = {"dates": [d.date().isoformat() for d in df.index]}
    for c in df.columns:
        out[c] = [None if pd.isna(v) else round(float(v), 2) for v in df[c]]
    return out


# --------------------------------------------------------------------------

def main() -> int:
    ancien = json.loads(SORTIE.read_text()) if SORTIE.exists() else {}
    neuf = {"releve": date.today().isoformat()}
    echecs = []
    for nom, fn in [("etats_unis", etats_unis), ("zone_euro", zone_euro),
                    ("emergents", emergents)]:
        try:
            neuf[nom] = fn()
            print(f"  ok      {nom}")
        except Exception as e:                       # noqa: BLE001
            echecs.append(nom)
            if nom in ancien:
                neuf[nom] = ancien[nom]
            print(f"  ÉCHEC   {nom} — {e} (ancienne valeur conservée)")
    SORTIE.write_text(json.dumps(neuf, ensure_ascii=False, indent=2) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit"
          + (f" — {len(echecs)} échec(s)" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
