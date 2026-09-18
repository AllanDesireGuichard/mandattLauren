"""
Photo des taux de marché -> data/taux_marche.json

Lancer :  python3 scripts/fetch_taux.py

L'application ne va JAMAIS chercher ces chiffres en direct. Deux raisons,
constatées le 2026-09-18 :
  - l'API de la BCE met parfois plus d'une minute à répondre ;
  - les chiffres iShares sont lus dans des pages web, pas dans une API, et le
    site a déjà changé de structure une fois (l'ancien export des lignes
    détenues ne répond plus).
Elle lit donc une photo datée, que ce script rafraîchit. Si une source échoue,
l'ancienne valeur est CONSERVÉE avec son ancienne date : l'application affiche
toujours la date réelle de chaque chiffre, jamais une date de relevé flatteuse.

PIÈGE DOCUMENTÉ — obligations indexées. Le rendement « Weighted Average YTM »
affiché sur la page iShares de l'ETF indexé (IBCI) est un équivalent NOMINAL,
qui intègre une hypothèse d'inflation propre à iShares. Le taux RÉEL n'est
publié que dans la fiche PDF mensuelle, sous le libellé « Yield to Worst ».
Au 31/07/2026 : 3,47 % nominal contre 1,43 % réel.
"""
from __future__ import annotations

import io
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "taux_marche.json"

MATURITES = [1, 2, 3, 5, 7, 10, 15, 20, 30]
H = {"User-Agent": "Mozilla/5.0"}
ISHARES = "https://www.ishares.com/uk/individual/en/products/{id}/{slug}"
ISHARES_PARAMS = {"switchLocale": "y", "siteEntryPassthrough": "true"}
ISHARES_COOKIES = {"dcsrd": "1"}
FICHE_IBCI = ("https://www.ishares.com/uk/individual/en/literature/fact-sheet/"
              "ibci-ishares-inflation-linked-govt-bond-ucits-etf-fund-fact-"
              "sheet-en-gb.pdf")

ETF = {
    "etat_euro": (251740, "ishares-euro-government-bond-ucits-etf",
                  "iShares Core € Govt Bond (SEGA)"),
    "credit_ig_euro": (251726, "ishares-euro-corporate-bond-ucits-etf",
                       "iShares Core € Corp Bond (IEAC)"),
    "indexees_nominal": (251739,
                         "ishares-euro-inflation-linked-government-bond-ucits-etf",
                         "iShares € Inflation Linked Govt Bond (IBCI)"),
}


# Taux hors zone euro, FRED. Rendements EFFECTIFS (« EY ») des indices ICE
# BofA, pas leurs écarts de crédit (« OAS ») : on compare des rendements.
FRED = {
    "us_3m":   ("DGS3MO", "Trésor américain 3 mois"),
    "us_2a":   ("DGS2", "Trésor américain 2 ans"),
    "us_10a":  ("DGS10", "Trésor américain 10 ans"),
    "us_30a":  ("DGS30", "Trésor américain 30 ans"),
    "credit_ig_us": ("BAMLC0A0CMEY", "ICE BofA US Corporate, rendement effectif"),
    "hy_us":   ("BAMLH0A0HYM2EY", "ICE BofA US High Yield, rendement effectif"),
    "hy_euro": ("BAMLHE00EHYIEY", "ICE BofA Euro High Yield, rendement effectif"),
    "em_corp": ("BAMLEMCBPIEY",
                "ICE BofA Emerging Markets Corporate Plus, rendement effectif "
                "(obligations en dollars)"),
    "eurusd":  ("DEXUSEU", "Dollars pour un euro, Réserve fédérale"),
}


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

def _fred_key() -> str:
    import tomllib
    from core.sources import CleManquante, fred_key
    try:
        return fred_key()
    except CleManquante:
        f = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"
        return tomllib.loads(f.read_text())["FRED_API_KEY"]


def point_fred(serie: str, source: str) -> dict:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": serie, "api_key": _fred_key(),
                             "file_type": "json", "sort_order": "desc",
                             "limit": 15}, timeout=60)
    r.raise_for_status()
    for o in r.json()["observations"]:
        if o["value"] != ".":
            return {"valeur": float(o["value"]), "date": o["date"],
                    "source": f"FRED, {serie} — {source}"}
    raise RuntimeError(f"aucune valeur récente pour {serie}")


def _bce(cle: str) -> pd.DataFrame:
    url = f"https://data-api.ecb.europa.eu/service/data/{cle}"
    for _ in range(4):
        try:
            r = requests.get(url, params={"lastNObservations": 1,
                                          "format": "csvdata"}, timeout=120)
            if r.status_code == 200:
                return pd.read_csv(io.StringIO(r.text))
        except requests.RequestException:
            pass
    raise RuntimeError(f"BCE injoignable : {cle}")


def courbes() -> dict:
    mats = "+".join(f"SR_{m}Y" for m in MATURITES)
    d = _bce(f"YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM.{mats}")
    d["mat"] = d["DATA_TYPE_FM"].str.extract(r"SR_(\d+)Y")[0].astype(int)
    p = d.pivot_table(index="mat", columns="INSTRUMENT_FM", values="OBS_VALUE")
    return {
        "date": str(d["TIME_PERIOD"].max()),
        "source": "BCE, courbe zéro-coupon des emprunts d'État de la zone euro",
        "maturites": MATURITES,
        "aaa": [round(float(p.loc[m, "G_N_A"]), 3) for m in MATURITES],
        "toutes": [round(float(p.loc[m, "G_N_C"]), 3) for m in MATURITES],
    }


def point_bce(cle: str, source: str) -> dict:
    d = _bce(cle)
    return {"valeur": round(float(d["OBS_VALUE"].iloc[-1]), 3),
            "date": str(d["TIME_PERIOD"].iloc[-1]), "source": source}


def _date_ishares(txt: str) -> str:
    return datetime.strptime(txt.replace("Sept", "Sep"), "%d/%b/%Y").date().isoformat()


def etf_ishares(ident: int, slug: str, nom: str) -> dict:
    r = requests.get(ISHARES.format(id=ident, slug=slug), params=ISHARES_PARAMS,
                     headers=H, cookies=ISHARES_COOKIES, timeout=90)
    r.raise_for_status()
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))
    ytm = re.search(r"Weighted Average YTM as of (\S+) (-?\d+\.\d+)", t)
    dur = re.search(r"Effective Duration as of \S+ (-?\d+\.\d+)", t)
    if not ytm or not dur:
        raise RuntimeError(f"structure de page iShares changée : {nom}")
    return {"valeur": float(ytm.group(2)), "duration": float(dur.group(1)),
            "date": _date_ishares(ytm.group(1)),
            "source": f"{nom}, rendement moyen à l'échéance du portefeuille"}


def indexees_reel() -> dict:
    from pypdf import PdfReader
    r = requests.get(FICHE_IBCI, headers=H, timeout=90)
    r.raise_for_status()
    t = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(r.content)).pages)
    reel = re.search(r"Yield to Worst\s*:\s*(-?\d+\.\d+)", t)
    nominal = re.search(r"Weighted Avg YTM\s*:\s*(-?\d+\.\d+)", t)
    dur = re.search(r"Effective Duration\s*:\s*(-?\d+\.\d+)", t)
    quand = re.search(r"as at:\s*(\d{2}-\w{3}-\d{4})", t)
    if not (reel and dur and quand):
        raise RuntimeError("structure de la fiche IBCI changée")
    return {"valeur": float(reel.group(1)), "duration": float(dur.group(1)),
            "nominal_meme_date": float(nominal.group(1)) if nominal else None,
            "date": datetime.strptime(quand.group(1), "%d-%b-%Y").date().isoformat(),
            "source": "iShares € Inflation Linked Govt Bond (IBCI), fiche "
                      "mensuelle, taux réel (« Yield to Worst »)"}


def variations_change() -> dict:
    """
    Ampleur des variations de l'euro contre le dollar sur 12 mois glissants,
    mesurée sur toute l'histoire de l'euro (fin de mois, depuis 1999).
    Sert à dire ce que coûte, en risque, un placement en dollars non couvert.
    """
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params={"series_id": "DEXUSEU", "api_key": _fred_key(),
                             "file_type": "json",
                             "observation_start": "1999-01-01"}, timeout=90)
    r.raise_for_status()
    s = pd.Series({o["date"]: float(o["value"])
                   for o in r.json()["observations"] if o["value"] != "."})
    s.index = pd.to_datetime(s.index)
    m = s.resample("ME").last()
    v = (m / m.shift(12) - 1).dropna().abs()
    return {"mediane": round(float(v.median()) * 100, 1),
            "part_plus_5": round(float((v > 0.05).mean()) * 100),
            "part_plus_10": round(float((v > 0.10).mean()) * 100),
            "pire": round(float((m / m.shift(12) - 1).dropna().abs().max()) * 100),
            "debut": str(m.index[0].year), "date": str(s.index[-1].date()),
            "source": "FRED, DEXUSEU, fin de mois, variations sur 12 mois "
                      "glissants"}


# --------------------------------------------------------------------------

def main() -> int:
    ancien = json.loads(SORTIE.read_text()) if SORTIE.exists() else {}
    neuf = {"releve": date.today().isoformat(),
            "points": dict(ancien.get("points", {}))}
    echecs = []

    def essayer(nom, fn, *args, cible=None):
        try:
            val = fn(*args)
            if cible is None:
                neuf["points"][nom] = val
            else:
                neuf[cible] = val
            print(f"  ok      {nom}")
        except Exception as e:                       # noqa: BLE001
            echecs.append(nom)
            if cible and cible in ancien:
                neuf[cible] = ancien[cible]
            print(f"  ÉCHEC   {nom} — {e} (ancienne valeur conservée)")

    essayer("courbes", courbes, cible="courbes")
    essayer("estr", point_bce, "EST/B.EU000A2X2A25.WT",
            "BCE, €STR (taux monétaire au jour le jour)")
    essayer("depot_bce", point_bce, "FM/D.U2.EUR.4F.KR.DFR.LEV",
            "BCE, taux de la facilité de dépôt")
    for nom, (ident, slug, lib) in ETF.items():
        essayer(nom, etf_ishares, ident, slug, lib)
    essayer("indexees_reel", indexees_reel)
    for nom, (serie, lib) in FRED.items():
        essayer(nom, point_fred, serie, lib)
    essayer("change_12m", variations_change)

    SORTIE.write_text(json.dumps(neuf, ensure_ascii=False, indent=2) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit"
          + (f" — {len(echecs)} échec(s) : {', '.join(echecs)}" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
