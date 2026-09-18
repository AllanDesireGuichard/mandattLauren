"""
Fonds de crédit euro bien noté -> data/fonds_credit.json

Lancer :  PYTHONPATH=. python3 scripts/fetch_fonds_credit.py

Pourquoi un script à part de fetch_fonds.py : pour le crédit, la question
n'est pas seulement « quel fonds » mais « quelle durée ». Il faut donc le
RENDEMENT À L'ÉCHÉANCE et la DURÉE de chaque fonds, que seules les fiches de
l'émetteur publient. On s'en tient aux fonds iShares : ce sont les seuls
dont la fiche donne ces deux chiffres dans un format lisible, et la gamme
couvre toutes les durées, avec et sans filtre.

CONTRÔLES : nom et devise EUR chez Yahoo ; l'ISIN affiché sur la fiche
iShares doit être celui attendu. Piège rencontré : la ligne londonienne du
fonds 0-3 ans (SUSS.L) est cotée en PENCE ; on prend la ligne de Francfort.

EXCLUSIONS (méthodologies Bloomberg MSCI lues le 2026-09-18) : pour les
obligations, la définition « Screened » de Bloomberg MSCI exclut
l'armement conventionnel (5 % du chiffre d'affaires), les systèmes d'armes
(10 %), le tabac (5 %) et le charbon (5 %). Les indices « ESG SRI » y
ajoutent pétrole et gaz (10 %) et la sélection des meilleurs émetteurs. À
ne pas confondre avec l'indice actions « MSCI Screened », qui laisse passer
l'armement conventionnel (voir core/fonds.py).

RÈGLE DE CHOIX : exclusions conformes, taille d'au moins 1 Md€, durée d'au
plus 3 ans (conclusion de l'étape 2 : crédit mal payé, préférer les durées
courtes), puis les frais les plus bas.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from scripts.fetch_marches import controler
from scripts.fetch_taux import (H, ISHARES, ISHARES_COOKIES, ISHARES_PARAMS,
                                 _date_ishares)

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "fonds_credit.json"
TAILLE_MIN = 1000.0          # M€
DUREE_MAX = 3.0              # ans

# ticker : (ISIN, identifiant iShares, mot-clé Yahoo, filtre, exclusions)
FONDS = {
    "QDVL.DE": ("IE00BYZTVV78", 280851, "0-3", "ESG SRI", "conforme"),
    "EUNS.DE": ("IE00B4L5ZY03", 251730, "ex-Financials 1-5", "ESG SRI",
                "conforme"),
    "EUNT.DE": ("IE00B4L60045", 251728, "1-5", "aucun", "non filtré"),
    "SUOE.L": ("IE00BYZTVT56", 297933, "ESG SRI", "ESG SRI", "conforme"),
    "EUN5.DE": ("IE00B3F81R35", 251726, "Core € Corp", "aucun",
                "non filtré"),
}
# Repère : emprunts d'État zone euro 1-3 ans (même échéance que le fonds
# court, sans risque d'entreprise). Seules ses baisses sont mesurées.
REPERE_ETAT = ("MTA.PA", "1-3")
# Épisodes de stress, définis à l'avance : un choc de crédit (les primes
# s'envolent) et un choc de taux (les taux montent, les primes peu).
EPISODES = {"2020": ("2020-02-15", "2020-04-30"),
            "2022": ("2022-01-01", "2022-12-31")}


def fiche(ident: int, isin: str) -> dict:
    for i in range(3):
        try:
            r = requests.get(ISHARES.format(id=ident, slug="x"),
                             params=ISHARES_PARAMS, headers=H,
                             cookies=ISHARES_COOKIES, timeout=90)
            r.raise_for_status()
            break
        except Exception:                            # noqa: BLE001
            if i == 2:
                raise
            time.sleep(4 + 4 * i)
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))

    def champ(motif: str) -> str | None:
        m = re.search(motif, t)
        return m.group(1) if m else None

    if champ(r"ISIN (\w{12})") != isin:
        raise RuntimeError(f"la fiche iShares {ident} n'affiche pas {isin}")
    ytm = champ(r"Weighted Average YTM as of \S+ (-?\d+\.\d+)")
    dur = champ(r"Effective Duration as of \S+ (-?\d+\.\d+)")
    if not ytm or not dur:
        raise RuntimeError(f"structure de page iShares changée ({ident})")
    aum = champ(r"Net Assets of Fund as of \S+ EUR ([\d,]+)")
    return {
        "rendement": float(ytm), "duree": float(dur),
        "maturite": float(champ(r"Weighted Avg Maturity as of \S+ (\d+\.\d+)")
                          or "nan"),
        "frais": float(champ(r"Total Expense Ratio (\d+\.\d+)%") or "nan"),
        "taille": round(int(aum.replace(",", "")) / 1e6) if aum else None,
        "indice": champ(r"Benchmark Index (.+?) (?:\(EUR\)|SDR classification)"),
        "date": _date_ishares(champ(r"Weighted Average YTM as of (\S+)")),
    }


def pires_baisses(ticker: str) -> dict:
    h = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).normalize()
    # Cours du vendredi : le 18/03/2020, QDVL.DE cote 4,17 entre 4,44 la
    # veille et 4,38 le lendemain (une cotation isolée en pleine panique, sur
    # une ligne peu échangée), ce qui ferait croire à −8 % sur un fonds
    # 0-3 ans. En hebdomadaire, même règle pour tous, ces points disparaissent.
    s = s.resample("W-FRI").last().dropna()
    out = {}
    for nom, (a, b) in EPISODES.items():
        x = s[(s.index >= a) & (s.index <= b)]
        if len(x) >= 8:
            out[nom] = round(float((x / x.cummax() - 1).min() * 100), 1)
    return out


def main() -> int:
    lignes, echecs = {}, []
    for t, (isin, ident, mot, filtre, excl) in FONDS.items():
        try:
            nom = controler(t, mot)
            lignes[t] = {"isin": isin, "nom": nom, "filtre": filtre,
                         "exclusions": excl, **fiche(ident, isin),
                         "pires_baisses": pires_baisses(t)}
            x = lignes[t]
            print(f"  ok      {t:8} {x['rendement']} %  durée {x['duree']}  "
                  f"{x['frais']} %  {x['taille']} M€  {x['pires_baisses']}")
        except Exception as e:                       # noqa: BLE001
            echecs.append(t)
            print(f"  ÉCHEC   {t:8} {e}")
        time.sleep(1.0)
    t, mot = REPERE_ETAT
    controler(t, mot)
    repere = {"ticker": t, "pires_baisses": pires_baisses(t)}
    print(f"  repère  {t:8} {repere['pires_baisses']}")
    ok = {t: x for t, x in lignes.items()
          if x["exclusions"] == "conforme" and (x["taille"] or 0) >= TAILLE_MIN
          and x["duree"] <= DUREE_MAX}
    retenu = min(ok, key=lambda k: (ok[k]["frais"], -ok[k]["taille"])) if ok else None
    for t, x in lignes.items():
        x["verdict"] = ("retenu" if t == retenu else
                        "aucun filtre d'exclusion" if x["exclusions"] != "conforme"
                        else "taille inférieure à 1 Md€" if x["taille"] < TAILLE_MIN
                        else "durée supérieure à 3 ans" if x["duree"] > DUREE_MAX
                        else "plus cher qu'un candidat équivalent")
    SORTIE.write_text(json.dumps(
        {"releve": date.today().isoformat(), "taille_min": TAILLE_MIN,
         "duree_max": DUREE_MAX, "retenu": retenu, "fonds": lignes,
         "repere_etat": repere},
        ensure_ascii=False, indent=1) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit — retenu : {retenu}"
          + (f" — {len(echecs)} échec(s) : {', '.join(echecs)}" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
