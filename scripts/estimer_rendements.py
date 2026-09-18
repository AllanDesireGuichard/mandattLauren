"""
Rendements espérés par classe d'actifs -> data/rendements.json

Lancer :  python3 scripts/estimer_rendements.py
          (après scripts/fetch_taux.py, dont il lit la photo)

C'EST LA SORTIE DE L'ONGLET 2 et l'entrée de l'allocation (étape 4).
Rendements annuels en euros, horizon 10 ans, dans le monde de l'énoncé :
inflation de 4 %. Méthode validée avec Allan le 2026-09-18 :

  OBLIGATIONS À TAUX FIXE : le taux à l'achat, point. Aucune répercussion de
    l'inflation n'est ajoutée (les anciens coefficients de core/cma.py étaient
    supposés, pas mesurés). Pour le crédit, on déduit la perte moyenne sur
    défauts publiée par Moody's.
  INDEXÉES : taux réel mesuré + 4 %.
  ACTIONS, par zone, deux méthodes sur données mesurées, puis leur moyenne :
    (1) rendement des bénéfices : réel ≈ 1 / PER ;
    (2) dividende + croissance réelle des bénéfices mesurée sur longue période
        (Shiller, S&P 500 depuis 1900) ;
    le tout + 4 % : les bénéfices suivent l'inflation (décision validée).
    Fourchette : la plus basse et la plus haute des deux méthodes, en faisant
    varier la croissance sur son intervalle mesuré ET le PER entre deux
    sources (iShares, Yahoo), qui divergent parfois fortement.
  OR, MATIÈRES PREMIÈRES : aucun flux, donc l'inflation seule. HYPOTHÈSE,
    étiquetée comme telle.
  CRYPTO : zéro, non estimable.

Repère externe : J.P. Morgan, Long-Term Capital Market Assumptions 2026,
hypothèses en euros (p. 84 du rapport complet, données au 30/09/2025,
inflation supposée de 2 %).
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

RACINE = Path(__file__).resolve().parents[1]


def fr(v: float, dec: int = 2) -> str:
    """Nombre au format français, pour les textes affichés dans l'app."""
    return f"{v:.{dec}f}".replace(".", ",")


TAUX = RACINE / "data" / "taux_marche.json"
SORTIE = RACINE / "data" / "rendements.json"
INFLATION = 4.0

# --------------------------------------------------------------------------
# Constantes publiées, avec leur source
# --------------------------------------------------------------------------

# Moody's, « Default and Recovery Rates of Corporate Bond Issuers, 1920-2004 »,
# Exhibit 11 : pertes cumulées moyennes à 5 ans, 1982-2004, en % du nominal.
# Bien noté 0,55 % -> 0,11 %/an ; haut rendement 14,88 % -> 3,17 %/an.
PERTE_IG = round((1 - (1 - 0.0055) ** (1 / 5)) * 100, 2)
PERTE_HY = round((1 - (1 - 0.1488) ** (1 / 5)) * 100, 2)
SOURCE_MOODYS = ("Moody's, Default and Recovery Rates of Corporate Bond "
                 "Issuers 1920-2004, pertes cumulées à 5 ans (1982-2004)")

# J.P. Morgan LTCMA 2026, hypothèses en euros, rendement composé annuel.
JPM = {"cash": 2.3, "govt_bonds_eur_short": None, "govt_bonds_eur": 3.4,
       "credit_ig_eur": 4.0, "inflation_linked": 3.6, "hy_euro": 5.3,
       "equity_developed": 6.3, "us": 6.1, "europe": 6.4, "zone_euro": 7.2,
       "japon": 8.2, "equity_emerging": 7.2, "infrastructure": 5.9,
       "gold": 4.9, "alternatives": 4.0, "crypto": None}
SOURCE_JPM = ("J.P. Morgan Asset Management, 2026 Long-Term Capital Market "
              "Assumptions, hypothèses en euros (p. 84), au 30/09/2025, "
              "inflation supposée 2 %")

# Zones actions : (ticker US de référence, page iShares, libellé)
ZONES = {
    "equity_developed": ("URTH", "239696/ishares-msci-world-etf",
                         "Actions des pays développés"),
    "us": ("IVV", "239726/ishares-core-sp-500-etf", "dont États-Unis"),
    "europe": ("IEUR", "264617/ishares-core-msci-europe-etf", "dont Europe"),
    "zone_euro": ("EZU", "239644/ishares-msci-emu-etf", "dont zone euro"),
    "japon": ("EWJ", "239665/ishares-msci-japan-etf", "dont Japon"),
    "equity_emerging": ("EEM", "239637/ishares-msci-emerging-markets-etf",
                        "Actions émergentes"),
    "infrastructure": ("IGF", "239746/ishares-global-infrastructure-etf",
                       "Infrastructure cotée"),
}
SHILLER = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"


# --------------------------------------------------------------------------
# Mesures
# --------------------------------------------------------------------------

def croissance_benefices() -> dict:
    """Croissance réelle des bénéfices par action, S&P 500, données Shiller."""
    r = requests.get(SHILLER, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    x = pd.read_excel(io.BytesIO(r.content), sheet_name="Data", header=None,
                      skiprows=8)[[0, 3, 4]]
    x.columns = ["date", "E", "CPI"]
    x = x[pd.to_numeric(x["date"], errors="coerce").notna()].dropna()
    x["an"] = x["date"].astype(float).astype(int)
    a = x.groupby("an").last()
    e10 = (a["E"] / a["CPI"]).rolling(10).mean()     # lissage sur 10 ans
    fin = int(a.index.max())

    def g(debut):
        return round(((e10[fin] / e10[debut]) ** (1 / (fin - debut)) - 1)
                     * 100, 2)

    periodes = {"1900": g(1900), "1950": g(1950), "1970": g(1970)}
    return {"central": periodes["1900"], "bas": 1.5,
            "haut": max(periodes.values()), "periodes": periodes,
            "fin": fin,
            "source": "R. Shiller, S&P 500 depuis 1871, bénéfices réels "
                      "lissés sur 10 ans"}


def ishares(ident: str) -> dict:
    u = f"https://www.ishares.com/us/products/{ident}"
    for i in range(3):
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"},
                             timeout=90)
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))
            pe = re.search(r"P/E Ratio (?:as of \S+ )?(\d+\.\d+)", t)
            dy = re.search(r"12m Trailing Yield (?:as of \S+ )?(\d+\.\d+)", t)
            quand = re.search(r"P/E Ratio as of (\S+)", t)
            if pe and dy:
                return {"per": float(pe.group(1)), "div": float(dy.group(1)),
                        "date": quand.group(1) if quand else None}
        except requests.RequestException:
            pass
        time.sleep(3)
    raise RuntimeError(f"page iShares {ident} illisible")


def yahoo_per(ticker: str) -> float | None:
    import yfinance as yf
    for i in range(3):
        try:
            v = yf.Ticker(ticker).info.get("trailingPE")
            return float(v) if v else None
        except Exception:                            # noqa: BLE001
            time.sleep(3)
    return None


# --------------------------------------------------------------------------
# Estimations
# --------------------------------------------------------------------------

def actions(nom: str, ticker: str, ident: str, g: dict) -> dict:
    ish = ishares(ident)
    per_y = yahoo_per(ticker)
    pers = [ish["per"]] + ([per_y] if per_y else [])
    m1 = 100 / ish["per"]                             # rendement des bénéfices
    m2 = ish["div"] + g["central"]                    # dividende + croissance
    reel = (m1 + m2) / 2
    candidats = [100 / p for p in pers] + [ish["div"] + g["bas"],
                                           ish["div"] + g["haut"]]
    return {
        "libelle": nom, "etiquette": "estimé",
        "central": round(reel + INFLATION, 2),
        "bas": round(min(candidats) + INFLATION, 2),
        "haut": round(max(candidats) + INFLATION, 2),
        "detail": {"per_ishares": ish["per"], "per_yahoo": per_y,
                   "dividende": ish["div"], "m1_reel": round(m1, 2),
                   "m2_reel": round(m2, 2), "date": ish["date"]},
        "methode": (f"Moyenne de deux méthodes : rendement des bénéfices "
                    f"(1 / PER de {fr(ish['per'], 1)}, soit {fr(m1)} %) et "
                    f"dividende ({fr(ish['div'])} %) + croissance réelle des "
                    f"bénéfices ({fr(g['central'], 1)} %), plus 4 % d'inflation."),
    }


def main() -> int:
    t = json.loads(TAUX.read_text())["points"]
    c = json.loads(TAUX.read_text())["courbes"]
    g = croissance_benefices()
    print(f"  croissance réelle des bénéfices : {g['periodes']} "
          f"-> central {g['central']} %")

    out: dict[str, dict] = {}
    out["cash"] = {
        "libelle": "Monétaire", "etiquette": "mesuré",
        "central": t["estr"]["valeur"], "bas": t["estr"]["valeur"],
        "haut": t["depot_bce"]["valeur"],
        "methode": "Taux monétaire du jour (€STR). S'il restait durablement "
                   "4 % d'inflation, ce taux monterait : ce supplément n'est "
                   "pas compté."}
    court = (c["toutes"][0] + c["toutes"][2]) / 2
    out["govt_bonds_eur_short"] = {
        "libelle": "États zone euro, 1-3 ans", "etiquette": "mesuré",
        "central": round(court, 2), "bas": c["toutes"][0],
        "haut": c["toutes"][2],
        "methode": "Taux à l'achat, courbe de la BCE entre 1 et 3 ans."}
    out["govt_bonds_eur"] = {
        "libelle": "États zone euro, ensemble", "etiquette": "mesuré",
        "central": t["etat_euro"]["valeur"],
        "bas": t["etat_euro"]["valeur"], "haut": t["etat_euro"]["valeur"],
        "methode": "Taux à l'achat moyen du marché des emprunts d'État de la "
                   "zone euro. Gardé jusqu'au bout, c'est ce qu'il rapporte."}
    ig = t["credit_ig_euro"]["valeur"]
    out["credit_ig_eur"] = {
        "libelle": "Crédit euro bien noté", "etiquette": "mesuré",
        "central": round(ig - PERTE_IG, 2), "bas": round(ig - PERTE_IG, 2),
        "haut": ig,
        "methode": f"Taux à l'achat ({fr(ig)} %) moins la perte moyenne sur "
                   f"défauts publiée par Moody's ({fr(PERTE_IG)} % par an)."}
    hy = t["hy_euro"]["valeur"]
    out["hy_euro"] = {
        "libelle": "Haut rendement euro (pour mémoire)", "etiquette": "mesuré",
        "central": round(hy - PERTE_HY, 2), "bas": round(hy - PERTE_HY, 2),
        "haut": round(hy - PERTE_HY, 2),
        "methode": f"Taux à l'achat ({fr(hy)} %) moins la perte moyenne sur "
                   f"défauts publiée par Moody's ({fr(PERTE_HY)} % par an)."}
    reel = t["indexees_reel"]["valeur"]
    out["inflation_linked"] = {
        "libelle": "Obligations indexées euro", "etiquette": "mesuré",
        "central": round(reel + INFLATION, 2), "bas": round(reel + INFLATION, 2),
        "haut": round(reel + INFLATION, 2),
        "methode": f"Taux réel mesuré ({fr(reel)} %) plus l'inflation de "
                   f"l'énoncé ({fr(INFLATION, 0)} %)."}

    for cle, (tk, ident, nom) in ZONES.items():
        try:
            out[cle] = actions(nom, tk, ident, g)
            d = out[cle]["detail"]
            print(f"  ok      {cle:17} PER iShares {fr(d['per_ishares'], 1)} / "
                  f"Yahoo {d['per_yahoo']}  div {fr(d['dividende'])}  "
                  f"-> {fr(out[cle]['central'])} %")
        except Exception as e:                       # noqa: BLE001
            print(f"  ÉCHEC   {cle} — {e}")
            return 1

    out["gold"] = {
        "libelle": "Or", "etiquette": "supposé",
        "central": INFLATION, "bas": INFLATION - 2, "haut": INFLATION + 2,
        "methode": "L'or ne verse rien : on suppose qu'il conserve son "
                   "pouvoir d'achat, soit l'inflation. Fourchette de deux "
                   "points de part et d'autre."}
    out["alternatives"] = {
        "libelle": "Matières premières", "etiquette": "supposé",
        "central": INFLATION, "bas": t["estr"]["valeur"], "haut": INFLATION + 2,
        "methode": "Aucun flux : on suppose qu'elles suivent l'inflation, "
                   "dont elles sont souvent la cause. Au minimum, le taux "
                   "monétaire placé en garantie."}
    out["crypto"] = {
        "libelle": "Crypto", "etiquette": "supposé",
        "central": 0.0, "bas": 0.0, "haut": 0.0,
        "methode": "Compté à zéro : non estimable avec une précision utile. "
                   "Toute performance sera un bonus, jamais un élément du plan."}

    for k, v in out.items():
        v["jpm"] = JPM.get(k)

    SORTIE.write_text(json.dumps({
        "releve": date.today().isoformat(), "inflation": INFLATION,
        "croissance": g,
        "sources": {"moodys": SOURCE_MOODYS, "jpm": SOURCE_JPM,
                    "perte_ig": PERTE_IG, "perte_hy": PERTE_HY},
        "classes": out}, ensure_ascii=False, indent=2) + "\n")
    print(f"\n{SORTIE.relative_to(RACINE)} écrit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
