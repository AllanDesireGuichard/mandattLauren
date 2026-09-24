"""
Attentes des analystes sur les titres retenus -> data/actions/outlook.csv

Lancer :  PYTHONPATH=. python3 scripts/fetch_outlook.py

L'étape 3 note les sociétés sur ce qu'elles SONT (bilan, marges, valorisation,
comportement passé). Ce relevé apporte la matière du second étage : ce que le
consensus des analystes ATTEND d'elles. Il ne porte que sur les titres déjà
retenus par la notation -- la décision d'Allan du 2026-09-24 est de resserrer
les 30 en 14 à 16, pas de reclasser tout l'univers.

CE QUI EST RELEVÉ, et pourquoi ces champs-là :
  - objectif de cours consensus (moyen, haut, bas) et cours du jour ;
  - bénéfice par action attendu pour l'exercice suivant, tel qu'il était
    estimé aujourd'hui, il y a 7, 30, 60 et 90 jours -> la RÉVISION, qui est
    le signal utile ; le niveau du consensus ne l'est pas (voir plus bas) ;
  - nombre d'analystes qui ont relevé et abaissé leur estimation sur 30 jours ;
  - estimations haute et basse du bénéfice -> la DISPERSION, qui mesure à quel
    point l'avenir de la société est prévisible ;
  - l'avis achat/conserver/vendre, relevé pour mémoire seulement.

LIMITES CONNUES, mesurées sur les 30 titres le 2026-09-24 :
  - `recommendationMean` (l'avis moyen) MANQUE sur 7 des 30, dont des titres
    suivis par 14 à 16 analystes (United Utilities, Carrefour, Klépierre,
    Diploma). C'est un trou de Yahoo, pas une absence de couverture : cet
    avis ne peut donc pas servir de critère, il est gardé pour l'affichage ;
  - `growth_estimates` ne sert AUCUNE croissance long terme (LTG) en Europe :
    0 sur 30. Le champ n'est pas relevé ;
  - le niveau du consensus est structurellement optimiste, et l'objectif de
    cours monte mécaniquement quand un titre baisse (la cible bouge plus
    lentement que le cours). D'où le choix de la révision plutôt que du
    niveau, et du potentiel en garde-fou plutôt qu'en score.

DEVISES : les quatre indicateurs construits en aval sont des ratios
(cible/cours, BPA d'aujourd'hui / BPA d'il y a 90 jours, écart/moyenne), donc
la devise s'annule dans chacun. C'est délibéré : argenx et Airtel Africa
publient en dollars tout en cotant en euros et en pence. Aucun ratio ne doit
mélanger un montant Yahoo « financialCurrency » avec un cours de cotation.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from core import actions                                    # noqa: E402

DOSSIER = RACINE / "data" / "actions"
PAUSE = 0.6                                                 # s entre deux titres

INFO = ["currentPrice", "currency", "financialCurrency", "recommendationKey",
        "recommendationMean", "numberOfAnalystOpinions", "targetMeanPrice",
        "targetHighPrice", "targetLowPrice", "targetMedianPrice"]
AGES = ["current", "7daysAgo", "30daysAgo", "60daysAgo", "90daysAgo"]


def releve(ticker: str) -> dict:
    """Un titre. Chaque bloc est tenté à part : un bloc absent n'en perd pas d'autres."""
    k = yf.Ticker(ticker)
    ligne: dict = {"ticker": ticker}

    try:
        i = k.info
        ligne.update({c: i.get(c) for c in INFO})
    except Exception as e:                                  # noqa: BLE001
        ligne["erreur"] = f"info : {e}"[:120]
        return ligne

    try:                                                    # trajectoire du BPA
        t = k.eps_trend
        for age in AGES:
            ligne[f"bpa_{age}"] = t.loc["+1y", age]
    except Exception:                                       # noqa: BLE001
        pass

    try:                                                    # qui révise, dans quel sens
        r = k.eps_revisions
        ligne["rev_hausse_30j"] = r.loc["+1y", "upLast30days"]
        ligne["rev_baisse_30j"] = r.loc["+1y", "downLast30days"]
    except Exception:                                       # noqa: BLE001
        pass

    try:                                                    # dispersion et croissance
        e = k.earnings_estimate
        ligne["bpa_moyen"] = e.loc["+1y", "avg"]
        ligne["bpa_haut"] = e.loc["+1y", "high"]
        ligne["bpa_bas"] = e.loc["+1y", "low"]
        ligne["bpa_analystes"] = e.loc["+1y", "numberOfAnalysts"]
        ligne["bpa_croissance"] = e.loc["+1y", "growth"]
        ligne["bpa_devise"] = e["currency"].iloc[0] if "currency" in e else None
    except Exception:                                       # noqa: BLE001
        pass

    return ligne


def main() -> None:
    d = actions.univers()
    sel = actions.selection(d)
    lignes = []
    for n, t in enumerate(sel["ticker"], 1):
        lignes.append(releve(t))
        print(f"  {n:>2}/{len(sel)}  {t}", flush=True)
        time.sleep(PAUSE)

    out = pd.DataFrame(lignes)
    out["date_releve"] = pd.Timestamp.today().date().isoformat()
    out.to_csv(DOSSIER / "outlook.csv", index=False)

    manquants = {c: int(out[c].isna().sum()) for c in
                 ("targetMeanPrice", "bpa_90daysAgo", "bpa_moyen",
                  "recommendationMean") if c in out}
    print(f"\ndata/actions/outlook.csv  —  {len(out)} titres")
    for c, n in manquants.items():
        print(f"  {c:20s} manquant sur {n}")


if __name__ == "__main__":
    main()
