"""
Dynamique des marchés actions -> data/marches.json

Lancer :  python3 scripts/fetch_marches.py

Performances sur plusieurs horizons, EN EUROS, de grandes zones et des
secteurs mondiaux, sur le modèle du tableau de momentum du process TCP Kenz.

CHOIX DES SUPPORTS (vérifiés un par un le 2026-09-18) :
  - tous cotés à Francfort (Xetra) en euros : même devise, même fenêtre
    horaire de clôture, donc des performances comparables entre elles et
    directement lisibles par un client en euros ;
  - libellé et devise CONTRÔLÉS à chaque passage (garde-fou `mot`), parce que
    l'univers EquityDB2 contenait trois libellés faux : EXS2.DE est le TecDAX
    et non l'EURO STOXX 50, XDWC.DE la consommation discrétionnaire et non
    les télécoms, XDWY.DE un MSCI World filtré et non un secteur.
Garde-fou qualité, en deux temps :
  1. on retire les ALLERS-RETOURS D'UN JOUR : une séance à plus de 8 %, suivie
     d'un mouvement inverse qui ramène le prix à moins de 3 % de la veille.
     C'est la signature d'un mauvais prix enregistré, pas d'un marché. Cas
     réel : XMME.DE et XMBR.DE le 24/10/2025, +16 % puis −13 % le lendemain,
     sur une seule cotation. Ce jour tombait un vendredi, donc dans la série
     hebdomadaire du graphique ;
  2. s'il reste un mouvement quotidien de plus de 15 % sur un ETF actions
     diversifié, la série est jugée cassée et la ligne ÉCARTÉE, pas corrigée.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "marches.json"

# ticker : (libellé affiché, groupe, mot qui doit figurer dans le nom Yahoo)
SUPPORTS = {
    "EUNL.DE": ("Monde (pays développés)", "zone", "MSCI World"),
    "SXR8.DE": ("États-Unis", "zone", "S&P 500"),
    "EXSA.DE": ("Europe", "zone", "STOXX Europe 600"),
    "XESC.DE": ("Zone euro (50 grandes valeurs)", "zone", "Euro Stoxx 50"),
    "EUNN.DE": ("Japon", "zone", "Japan"),
    "XMME.DE": ("Émergents", "zone", "Emerging Markets"),
    "XCS6.DE": ("Chine", "zone", "China"),
    "QDV5.DE": ("Inde", "zone", "India"),
    "XMBR.DE": ("Brésil", "zone", "Brazil"),
    "XDWT.DE": ("Technologie", "secteur", "Information Technology"),
    "XWTS.DE": ("Télécoms et médias", "secteur", "Communication Services"),
    "XDWC.DE": ("Consommation discrétionnaire", "secteur",
                "Consumer Discretionary"),
    "XDWS.DE": ("Consommation de base", "secteur", "Consumer Staples"),
    "XDWH.DE": ("Santé", "secteur", "Health Care"),
    "XDWF.DE": ("Finance", "secteur", "Financials"),
    "XDWI.DE": ("Industrie", "secteur", "Industrials"),
    "XDW0.DE": ("Énergie", "secteur", "Energy"),
    "XDWM.DE": ("Matériaux", "secteur", "Materials"),
    "XDWU.DE": ("Services aux collectivités", "secteur", "Utilities"),
    "4GLD.DE": ("Or", "reel", "Gold"),
}
HORIZONS = {"1 mois": 1, "3 mois": 3, "6 mois": 6, "12 mois": 12}
SAUT_MAX = 0.15
PIC_MIN, RETOUR_MAX = 0.08, 0.03


def _essayer(fn, essais: int = 4):
    for i in range(essais):
        try:
            return fn()
        except Exception:                            # noqa: BLE001
            if i == essais - 1:
                raise
            time.sleep(2 + 2 * i)


def controler(ticker: str, mot: str) -> str:
    info = _essayer(lambda: yf.Ticker(ticker).info)
    nom = info.get("longName") or info.get("shortName") or ""
    if info.get("currency") != "EUR":
        raise RuntimeError(f"devise {info.get('currency')} au lieu de EUR")
    if mot.lower() not in nom.lower():
        raise RuntimeError(f"libellé inattendu : « {nom} »")
    return nom


def prix(ticker: str) -> pd.Series:
    h = _essayer(lambda: yf.Ticker(ticker).history(period="2y",
                                                   auto_adjust=True))
    s = h["Close"].dropna()
    if len(s) < 300:
        raise RuntimeError(f"historique trop court ({len(s)} séances)")
    s.index = s.index.tz_localize(None).normalize()
    s, retires = retirer_allers_retours(s)
    for d in retires:
        print(f"          {ticker} : aller-retour d'un jour retiré le {d}")
    saut = s.pct_change().abs().max()
    if saut > SAUT_MAX:
        raise RuntimeError(f"saut quotidien de {saut:.0%} : série suspecte")
    return s


def retirer_allers_retours(s: pd.Series) -> tuple[pd.Series, list[str]]:
    r = s.pct_change()
    veille, lendemain = s.shift(1), s.shift(-1)
    faux = ((r.abs() > PIC_MIN)
            & (r * r.shift(-1) < 0)
            & ((lendemain / veille - 1).abs() < RETOUR_MAX))
    return s[~faux], [d.date().isoformat() for d in s.index[faux]]


def perf(s: pd.Series) -> dict:
    fin = s.index[-1]
    out = {}
    for nom, mois in HORIZONS.items():
        debut = s[s.index <= fin - pd.DateOffset(months=mois)]
        out[nom] = round(float(s.iloc[-1] / debut.iloc[-1] - 1) * 100, 1)
    janvier = s[s.index < pd.Timestamp(fin.year, 1, 1)]
    out["Depuis janvier"] = round(float(s.iloc[-1] / janvier.iloc[-1] - 1)
                                  * 100, 1)
    mm200 = s.rolling(200).mean().iloc[-1]
    out["ecart_mm200"] = round(float(s.iloc[-1] / mm200 - 1) * 100, 1)
    return out


def main() -> int:
    ancien = json.loads(SORTIE.read_text()) if SORTIE.exists() else {}
    lignes = dict(ancien.get("lignes", {}))
    base100 = dict(ancien.get("base100", {}))
    echecs = []
    for t, (lib, groupe, mot) in SUPPORTS.items():
        try:
            nom = controler(t, mot)
            s = prix(t)
            lignes[t] = {"libelle": lib, "groupe": groupe, "nom": nom,
                         "date": s.index[-1].date().isoformat()} | perf(s)
            an = s[s.index >= s.index[-1] - pd.DateOffset(months=12)]
            hebdo = an.resample("W-FRI").last().dropna()
            base100[t] = {"dates": [d.date().isoformat() for d in hebdo.index],
                          "valeurs": [round(float(v), 2)
                                      for v in hebdo / hebdo.iloc[0] * 100]}
            print(f"  ok      {t:9} {lib}")
        except Exception as e:                       # noqa: BLE001
            echecs.append(t)
            print(f"  ÉCHEC   {t:9} {lib} — {e} (ancienne valeur conservée)")
    SORTIE.write_text(json.dumps(
        {"releve": date.today().isoformat(), "lignes": lignes,
         "base100": base100}, ensure_ascii=False, indent=1) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit"
          + (f" — {len(echecs)} échec(s) : {', '.join(echecs)}" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
