"""
Fonds et ETF des classes non investies en direct -> data/fonds.json

Lancer :  PYTHONPATH=. python3 scripts/fetch_fonds.py

Pour chaque classe d'actifs, trois à quatre candidats, tous cotés à Francfort
en euros (même devise, même heure de clôture : des performances comparables).

CONTRÔLES À CHAQUE PASSAGE, parce que l'univers hérité contenait neuf
libellés faux (voir core/fonds.py, CORRECTIONS) :
  - Yahoo : devise EUR et mot-clé attendu dans le nom ;
  - justETF : la page de l'ISIN doit porter le même mot-clé. Un ISIN recopié
    de travers est rejeté (cas réel : celui noté pour XDWU.DE renvoyait un
    fonds technologie).

SOURCES : justETF pour les frais, la taille, l'indice suivi et la
réplication (Yahoo ne donne ni la taille ni les frais de la plupart des ETC) ;
Yahoo pour les prix et les volumes échangés.

EXCLUSIONS : lues dans les méthodologies MSCI (voir core/fonds.py). Le
verdict est posé à la main, par famille d'indices, et non déduit du nom.

LA RÈGLE DE CHOIX est mécanique et écrite ici, pas dans l'app :
  1. exclusions conformes au mandat (ou sans objet) ;
  2. taille d'au moins 1 Md€ ;
  3. parmi les survivants, les frais les plus bas ; à égalité, le plus gros.
L'écart mesuré face à un fonds de référence sert à VÉRIFIER, pas à choisir.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from scripts.fetch_marches import controler, retirer_allers_retours

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "fonds.json"
TAILLE_MIN = 1000.0          # M€
H = {"User-Agent": "Mozilla/5.0"}

# exclusions : conforme · non conforme · non filtré · à vérifier · sans objet
# ticker : (ISIN, mot-clé attendu, filtre, exclusions)
CLASSES = {
    "usa": {
        "libelle": "Actions États-Unis",
        "reference": "SXR8.DE",
        "candidats": {
            "XZMU.DE": ("IE00BFMNPS42", "USA ESG", "SRI", "conforme"),
            "QDVR.DE": ("IE00BYVJRR92", "USA SRI", "SRI", "conforme"),
            "SGAS.DE": ("IE00BFNM3G45", "USA Screened", "Screened",
                        "non conforme"),
            "SXR8.DE": ("IE00B5BMR087", "S&P 500", "aucun", "non filtré"),
        },
    },
    "japon": {
        "libelle": "Actions Japon",
        "reference": "EUNN.DE",
        "candidats": {
            "XZMJ.DE": ("IE00BG36TC12", "Japan ESG", "SRI", "conforme"),
            "SGAJ.DE": ("IE00BFNM3L97", "Japan Screened", "Screened",
                        "non conforme"),
            "EUNN.DE": ("IE00B4L5YX21", "Japan IMI", "aucun", "non filtré"),
        },
    },
    "emergents": {
        "libelle": "Actions émergentes",
        "reference": "IS3N.DE",
        "candidats": {
            "XZEM.DE": ("IE00BG370F43", "Emerging Markets ESG", "SRI",
                        "conforme"),
            "AYEM.DE": ("IE00BFNM3P36", "EM IMI Screened", "Screened",
                        "non conforme"),
            "IS3N.DE": ("IE00BKM4GZ66", "EM IMI", "aucun", "non filtré"),
        },
    },
    "indexees": {
        "libelle": "Obligations indexées sur l'inflation",
        "reference": "IBCI.DE",
        "candidats": {
            "IBCI.DE": ("IE00B0M62X26", "Inflation", "—", "sans objet"),
            "XEIN.DE": ("LU0290358224", "Inflation", "—", "sans objet"),
        },
    },
    "infrastructure": {
        "libelle": "Infrastructure cotée",
        "reference": "IQQI.DE",
        "candidats": {
            "RIZD.DE": ("IE000QUCVEN9", "Sustainable Infrastructure",
                        "durable (Solactive)", "à vérifier"),
            "ZPRI.DE": ("IE00BQWJFQ70", "Infrastructure", "aucun",
                        "non filtré"),
            "IQQI.DE": ("IE00B1FZS467", "Infrastructure", "aucun",
                        "non filtré"),
        },
    },
    "or": {
        "libelle": "Or",
        "reference": "PPFB.DE",
        "candidats": {
            "4GLD.DE": ("DE000A0S9GB0", "Gold", "—", "sans objet"),
            "PPFB.DE": ("IE00B4ND3602", "Gold", "—", "sans objet"),
            "8PSG.DE": ("IE00B579F325", "Gold", "—", "sans objet"),
            "XAD5.DE": ("DE000A1E0HR8", "Gold", "—", "sans objet"),
        },
    },
    "matieres": {
        "libelle": "Matières premières",
        "reference": "SXRS.DE",
        "candidats": {
            "SXRS.DE": ("IE00BDFL4P12", "Commodity", "—", "sans objet"),
            "CRB.PA": ("LU1829218749", "Commodity", "—", "sans objet"),
            "XDBC.DE": ("LU0292106167", "Commodity", "—", "sans objet"),
        },
    },
    "crypto": {
        "libelle": "Bitcoin",
        "reference": "BTCE.DE",
        "candidats": {
            "IB1T.DE": ("XS2940466316", "Bitcoin", "—", "sans objet"),
            "BTCE.DE": ("DE000A27Z304", "Bitcoin", "—", "sans objet"),
            "VBTC.DE": ("DE000A28M8D0", "Bitcoin", "—", "sans objet"),
            "2BTC.DE": ("CH0454664001", "Bitcoin", "—", "sans objet"),
        },
    },
}
SAUT_MAX = {"crypto": 0.30, "matieres": 0.15}
# Les séries Yahoo antérieures à 2019 contiennent des prix aberrants sur
# plusieurs lignes Xetra (8PSG.DE : +40 % / −26 % à répétition en 2013-2014 ;
# SXR8.DE : −25 % le 01/11/2010). On mesure sur les sept dernières années.
FENETRE_ANS = 7
# Tolérance de retour élargie à 5 % : le 24/10/2025, plusieurs lignes Xetra
# (or, émergents) affichent +15 % puis −16,5 % à la séance suivante.
RETOUR_MAX = 0.05


def _texte(page: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


def justetf(isin: str, mot: str) -> dict:
    for i in range(3):
        try:
            r = requests.get("https://www.justetf.com/en/etf-profile.html",
                             params={"isin": isin}, headers=H, timeout=25)
            r.raise_for_status()
            break
        except Exception:                            # noqa: BLE001
            if i == 2:
                raise
            time.sleep(3 + 3 * i)
    titre = re.search(r"<title>(.*?)</title>", r.text, re.S)
    nom = html.unescape(titre.group(1)).split("|")[0].strip() if titre else ""
    mots = mot.lower().split()
    if not all(m in nom.lower() for m in mots):
        raise RuntimeError(f"ISIN {isin} : justETF affiche « {nom} »")
    t = _texte(r.text)

    def champ(motif: str) -> str | None:
        m = re.search(motif, t)
        return m.group(1).strip() if m else None

    ter = champ(r"Total expense ratio ([\d.]+)% p\.a\.")
    taille = champ(r"Fund size EUR ([\d,]+) m")
    return {
        "nom_justetf": nom,
        "frais": float(ter) if ter else None,
        "taille": float(taille.replace(",", "")) if taille else None,
        "lancement": champ(r"Inception Date (\d{1,2} \w+ \d{4})"),
        "replication": champ(r"Replication (\w+ \( [^)]+ \))"),
        "domicile": champ(r"Fund domicile (\w+)"),
        "indice": champ(r"tracks the ([^.]{5,120}?) index"),
    }


def prix(ticker: str, saut_max: float) -> pd.Series:
    h = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).normalize()
    s = s[s.index >= s.index[-1] - pd.DateOffset(years=FENETRE_ANS)]
    # Pas pour le bitcoin : un aller-retour de 8 % en deux séances y est
    # ordinaire, le retirer effacerait de vrais mouvements.
    retires = []
    if saut_max < SAUT_MAX["crypto"]:
        s, retires = retirer_allers_retours(s, RETOUR_MAX)
    for d in retires:
        print(f"          {ticker} : aller-retour d'un jour retiré le {d}")
    saut = s.pct_change().abs().max()
    if saut > saut_max:
        raise RuntimeError(f"saut quotidien de {saut:.0%} : série suspecte")
    return s


def ecart(s: pd.Series, ref: pd.Series) -> dict:
    """Écart mensuel face à la référence, sur la fenêtre commune."""
    m = pd.concat([s, ref], axis=1, join="inner").resample("ME").last()
    r = m.pct_change().dropna()
    if len(r) < 12:
        return {}
    d = r.iloc[:, 0] - r.iloc[:, 1]
    return {"ecart_moyen": round(float(d.mean() * 12 * 100), 2),
            "ecart_type": round(float(d.std() * np.sqrt(12) * 100), 2),
            "fenetre": round(len(r) / 12, 1),
            "debut_fenetre": r.index[0].date().isoformat()}


def choisir(lignes: dict) -> tuple[str | None, str]:
    ok = {t: x for t, x in lignes.items()
          if x["exclusions"] in ("conforme", "sans objet")
          and (x["taille"] or 0) >= TAILLE_MIN and x["frais"] is not None}
    if not ok:
        return None, "aucun candidat ne passe à la fois les exclusions et la taille"
    t = min(ok, key=lambda k: (ok[k]["frais"], -ok[k]["taille"]))
    return t, "frais les plus bas parmi les candidats conformes de plus de 1 Md€"


def raison(x: dict) -> str:
    if x["exclusions"] == "non conforme":
        return "n'exclut pas l'armement conventionnel"
    if x["exclusions"] == "non filtré":
        return "aucun filtre d'exclusion"
    if x["exclusions"] == "à vérifier":
        return "exclusions non vérifiées"
    if (x["taille"] or 0) < TAILLE_MIN:
        return "taille inférieure à 1 Md€"
    return "plus cher qu'un candidat équivalent"


def main() -> int:
    sortie = {"releve": date.today().isoformat(), "taille_min": TAILLE_MIN,
              "classes": {}}
    echecs = []
    for cle, c in CLASSES.items():
        print(f"\n{c['libelle']}")
        series, lignes = {}, {}
        for t, (isin, mot, filtre, excl) in c["candidats"].items():
            try:
                nom = controler(t, mot.split()[0])
                j = justetf(isin, mot.split()[0])
                s = prix(t, SAUT_MAX.get(cle, 0.12))
                info = yf.Ticker(t).info
                vol = info.get("averageVolume") or 0
                series[t] = s
                r = s.pct_change().dropna()
                lignes[t] = {
                    "isin": isin, "nom": nom, "filtre": filtre,
                    "exclusions": excl, **j,
                    "echange_jour": round(vol * float(s.iloc[-1]) / 1e6, 2),
                    "vol": round(float(r[-756:].std() * np.sqrt(252) * 100), 1),
                    "date": s.index[-1].date().isoformat(),
                }
                print(f"  ok      {t:9} {j['frais']} %  {j['taille']} M€  {nom}")
            except Exception as e:                   # noqa: BLE001
                echecs.append(t)
                print(f"  ÉCHEC   {t:9} {e}")
            time.sleep(1.0)
        ref = c["reference"]
        for t, x in lignes.items():
            if t != ref and ref in series:
                x.update(ecart(series[t], series[ref]))
        retenu, pourquoi = choisir(lignes)
        for t, x in lignes.items():
            x["verdict"] = "retenu" if t == retenu else raison(x)
        sortie["classes"][cle] = {"libelle": c["libelle"], "reference": ref,
                                  "retenu": retenu, "pourquoi": pourquoi,
                                  "candidats": lignes}
    SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit"
          + (f" — {len(echecs)} échec(s) : {', '.join(echecs)}" if echecs else ""))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
