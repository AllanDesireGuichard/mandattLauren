"""
Séries longues, en euros, pour mesurer le risque de chaque support
-> data/indices_longs.csv (quotidien, base 100) + data/indices_longs.json

Lancer :  python3 scripts/fetch_indices.py

POURQUOI. La limite de 15 % se mesure depuis le plus haut, au pire cas des
crises passées (décision d'Allan, 2026-09-18). Or les supports retenus à
l'étape 3 sont jeunes : les 30 titres depuis 2019 dans nos données, XZEM
depuis 2019, XZMU et XZMJ depuis 2018, IB1T depuis 2025. Et Yahoo ne
remonte pas avant janvier 2008 sur les places européennes, alors que les
actions européennes ont atteint leur plus haut en juillet 2007 : partir de 2008
amputerait la baisse de 2008 de sa première partie. D'où des séries de
remplacement qui commencent en octobre 2006 :

  - actions et or : fonds cotés à New York (historique complet depuis 2006),
    convertis en euros au cours EUR/USD du jour ;
  - matières premières : ETN sur l'indice Bloomberg Commodity, le même indice
    que SXRS ;
  - emprunts d'État en direct : RECONSTITUÉS à partir de la courbe de la BCE
    (paramètres de Svensson publiés chaque jour depuis septembre 2004), ce
    qui est le plus fidèle pour des obligations détenues en direct ;
  - indexées : une obligation d'État à 7 ans reconstituée ;
  - crédit court : l'obligation d'État à 1,5 an reconstituée, plus une prime
    de crédit dont la sensibilité aux écarts de crédit est MESURÉE sur QDVL
    (2016-2026), pas supposée.

RACCORD. Chaque vrai support (Xetra, EUR) prend le relais de son remplaçant
dès sa première cotation. Exception : les actions européennes gardent
l'indice, le « panier » des 30 titres étant reconstitué avec la sélection
d'aujourd'hui (biais de sélection).

CONTRÔLE. Chaque série de remplacement est comparée au vrai support sur la
période où les deux existent : corrélation hebdomadaire, volatilités, pires
baisses. Un remplaçant qui ne suit pas son support serait écarté.
"""
from __future__ import annotations

import io
import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from scripts.fetch_marches import retirer_allers_retours   # noqa: E402

CSV = RACINE / "data" / "indices_longs.csv"
META = RACINE / "data" / "indices_longs.json"
DEBUT = "2006-10-02"

# ticker Yahoo : mot qui doit figurer dans son nom (garde-fou libellé)
YAHOO = {
    "VGK": "FTSE Europe", "SPY": "S&P 500", "EWJ": "MSCI Japan",
    "EEM": "Emerging Markets", "GLD": "Gold", "DJP": "Bloomberg Commodity",
    "BTC-USD": "Bitcoin", "EURUSD=X": "EUR/USD",
    # vrais supports, pour le contrôle
    "XZMU.DE": "MSCI USA ESG", "XZMJ.DE": "MSCI Japan ESG",
    "XZEM.DE": "Emerging Markets ESG", "IBCI.DE": "Inflation Linked",
    "4GLD.DE": "Xetra-Gold", "SXRS.DE": "Diversified Commodity",
    "IB1T.DE": "Bitcoin", "QDVL.DE": "Corp Bond 0-3yr ESG SRI",
    "EXSA.DE": "STOXX Europe 600", "EUNH.DE": "Core € Govt Bond",
    "IBGS.AS": "Govt Bond 1-3yr",
}
EN_USD = {"VGK", "SPY", "EWJ", "EEM", "GLD", "DJP", "BTC-USD"}

# classe : libellé, support réel (étape 3), source longue, ticker de contrôle
CLASSES = {
    "actions_europe": ("Actions européennes", "30 titres en direct",
                       "Vanguard FTSE Europe (VGK), en euros", "panier"),
    "usa": ("Actions américaines", "XZMU", "SPDR S&P 500 (SPY), en euros",
            "XZMU.DE"),
    "japon": ("Actions japonaises", "XZMJ", "iShares MSCI Japan (EWJ), en "
              "euros", "XZMJ.DE"),
    "emergents": ("Actions émergentes", "XZEM", "iShares MSCI Emerging "
                  "Markets (EEM), en euros", "XZEM.DE"),
    "etats_courts": ("États AAA, 6 à 24 mois (les 10 M€)", "échelle en direct",
                     "Reconstitué : courbe AAA de la BCE", "IBGS.AS"),
    "etats_longs": ("États zone euro, 2 à 10 ans", "échelle en direct",
                    "Reconstitué : courbe de la BCE, toutes émissions",
                    "EUNH.DE"),
    "credit_court": ("Crédit euro bien noté, court", "QDVL",
                     "QDVL dès 2016, État 1,5 an + prime de crédit "
                     "reconstitués avant", "QDVL.DE"),
    "indexees": ("Obligations indexées euro", "IBCI", "IBCI dès 2009, État "
                 "7 ans reconstitué avant", "IBCI.DE"),
    "or": ("Or", "4GLD", "SPDR Gold Shares (GLD), en euros", "4GLD.DE"),
    "matieres": ("Matières premières", "SXRS", "iPath Bloomberg Commodity "
                 "(DJP), en euros", "SXRS.DE"),
    "crypto": ("Bitcoin", "IB1T", "Bitcoin (BTC-USD), en euros, depuis 2014",
               "IB1T.DE"),
}
ECHELLE_LONGUE = (2, 3, 5, 7, 10)
ECHELLE_COURTE = (0.5, 1, 1.5, 2)


def _essayer(fn, essais: int = 4):
    for i in range(essais):
        try:
            return fn()
        except Exception:                            # noqa: BLE001
            if i == essais - 1:
                raise
            time.sleep(2 + 2 * i)


def yahoo(t: str, mot: str) -> pd.Series:
    tk = yf.Ticker(t)
    nom = (_essayer(lambda: tk.info).get("longName")
           or tk.info.get("shortName") or "")
    if mot.lower() not in nom.lower():
        raise RuntimeError(f"{t} : nom Yahoo « {nom} » sans « {mot} »")
    h = _essayer(lambda: tk.history(period="max", auto_adjust=True))
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).normalize()
    return s[~s.index.duplicated()]


# ---------------------------------------------------------------- BCE
def svensson_histo(code: str) -> pd.DataFrame:
    url = (f"https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F."
           f"{code}.SV_C_YM.BETA0+BETA1+BETA2+BETA3+TAU1+TAU2")
    r = _essayer(lambda: requests.get(url, params={"format": "csvdata"},
                                      timeout=300))
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    p = d.pivot_table(index="TIME_PERIOD", columns="DATA_TYPE_FM",
                      values="OBS_VALUE")
    p.index = pd.to_datetime(p.index)
    return p.sort_index()


def taux(p: pd.DataFrame, m: float | np.ndarray) -> pd.Series:
    """Taux zéro-coupon (%, composé en continu) d'échéance m années."""
    b0, b1, b2, b3 = (p[f"BETA{i}"] for i in range(4))
    x1, x2 = m / p["TAU1"], m / p["TAU2"]
    f1 = (1 - np.exp(-x1)) / x1
    f2 = (1 - np.exp(-x2)) / x2
    return b0 + b1 * f1 + b2 * (f1 - np.exp(-x1)) + b3 * (f2 - np.exp(-x2))


def zero_constant(p: pd.DataFrame, m: float) -> pd.Series:
    """
    Rendement quotidien d'une obligation zéro-coupon d'échéance m, revendue
    chaque jour pour garder la même échéance. Exact au sens de la courbe :
    on achète au taux z_t(m), on revend le lendemain au taux z_t+1(m - dt),
    ce qui compte le portage ET le glissement le long de la courbe.
    """
    dt = p.index.to_series().diff().dt.days / 365.25
    achat = taux(p, m).shift(1) * m
    revente = taux(p, m - dt) * (m - dt)
    return np.exp((achat - revente) / 100) - 1


def echelle(p: pd.DataFrame, marches: tuple) -> pd.Series:
    return pd.concat([zero_constant(p, m) for m in marches], axis=1).mean(1)


# ---------------------------------------------------------------- mesures
def hebdo(s: pd.Series) -> pd.Series:
    return s.resample("W-FRI").last().pct_change().dropna()


def pire_baisse(s: pd.Series) -> float:
    return float((s / s.cummax() - 1).min() * 100)


def controle(proxy: pd.Series, reel: pd.Series) -> dict:
    debut = max(proxy.first_valid_index(), reel.first_valid_index())
    a, b = proxy[debut:].dropna(), reel[debut:].dropna()
    ra, rb = hebdo(a), hebdo(b)
    ra, rb = ra.align(rb, join="inner")
    ans = len(ra) / 52
    return {
        "debut": debut.date().isoformat(), "annees": round(ans, 1),
        "correlation": round(float(ra.corr(rb)), 2),
        "vol_remplacant": round(float(ra.std() * 52 ** .5 * 100), 1),
        "vol_support": round(float(rb.std() * 52 ** .5 * 100), 1),
        "baisse_remplacant": round(pire_baisse((1 + ra).cumprod()), 1),
        "baisse_support": round(pire_baisse((1 + rb).cumprod()), 1),
        "perf_remplacant": round(float((1 + ra).prod() ** (1 / ans) - 1) * 100,
                                 2),
        "perf_support": round(float((1 + rb).prod() ** (1 / ans) - 1) * 100, 2),
    }


def panier_30() -> pd.Series:
    from core import actions
    sel = actions.selection(actions.univers())
    return actions.panier_face_indice(sel)["series"]["panier"]


# ---------------------------------------------------------------- main
def main() -> int:
    brut, nettoye = {}, {}
    for t, mot in YAHOO.items():
        s = yahoo(t, mot)
        if t not in ("BTC-USD", "EURUSD=X"):
            s, faux = retirer_allers_retours(s)
            if faux:
                nettoye[t] = faux
        brut[t] = s
        print(f"{t:9} {s.index[0].date()}  {len(s)} cours")
    eurusd = brut["EURUSD=X"]
    eur = {}
    for t, s in brut.items():
        if t in EN_USD:
            fx = eurusd.reindex(s.index).ffill(limit=5)
            s = (s / fx).dropna()
        eur[t] = s

    aaa, tout = svensson_histo("G_N_A"), svensson_histo("G_N_C")
    print("BCE", tout.index[0].date(), len(tout), "jours")

    jours = pd.bdate_range(DEBUT, date.today())

    def niveau(r: pd.Series) -> pd.Series:
        r = r.reindex(jours).fillna(0.0)
        return 100 * (1 + r).cumprod()

    def depuis_prix(s: pd.Series) -> pd.Series:
        s = s.reindex(s.index.union(jours)).ffill(limit=5).reindex(jours)
        return 100 * s / s.dropna().iloc[0]

    out = {
        "actions_europe": depuis_prix(eur["VGK"]),
        "usa": depuis_prix(eur["SPY"]),
        "japon": depuis_prix(eur["EWJ"]),
        "emergents": depuis_prix(eur["EEM"]),
        "or": depuis_prix(eur["GLD"]),
        "matieres": depuis_prix(eur["DJP"]),
        "etats_courts": niveau(echelle(aaa, ECHELLE_COURTE)),
        "etats_longs": niveau(echelle(tout, ECHELLE_LONGUE)),
    }
    btc = eur["BTC-USD"].reindex(jours).ffill(limit=5)
    out["crypto"] = 100 * btc / btc.dropna().iloc[0]

    # indexées : État 7 ans reconstitué (IBCI prend le relais au raccord)
    out["indexees"] = niveau(zero_constant(tout, 7))

    # crédit court : État 1,5 an + prime de crédit, sensibilité mesurée
    g15 = zero_constant(tout, 1.5)
    oas = (pd.read_csv(RACINE / "data" / "credit_histo.csv", index_col=0,
                       parse_dates=True)["BAMLC0A0CM"].dropna())
    g15_niv = niveau(g15)
    qdvl = eur["QDVL.DE"]
    exc = (hebdo(qdvl) - hebdo(g15_niv[qdvl.index[0]:])).dropna()
    doas = oas.resample("W-FRI").last().diff().reindex(exc.index)
    ok = doas.notna()
    pente, constante = np.polyfit(doas[ok], exc[ok], 1)
    r2 = float(np.corrcoef(doas[ok], exc[ok])[0, 1] ** 2)
    doas_j = oas.reindex(jours).ffill().diff().fillna(0.0)
    prime = constante / 5 + pente * doas_j          # constante hebdo -> jour
    r_cred = g15.reindex(jours).fillna(0.0) + prime
    out["credit_court"] = 100 * (1 + r_cred).cumprod()
    print(f"crédit : sensibilité {pente * 100:.2f} % par point d'écart, "
          f"R² {r2:.2f}")

    # Raccord : le vrai support dès sa première cotation, le remplaçant
    # avant. Sauf les actions européennes : le « panier » des 30 titres est
    # reconstitué avec la sélection d'aujourd'hui, son passé est flatteur par
    # construction (biais de sélection) ; on garde l'indice.
    reels = dict(eur)
    reels["panier"] = panier_30()
    proxys = pd.DataFrame(out)
    raccords = {}
    for k, (_, _, _, ctrl) in CLASSES.items():
        if ctrl.endswith(".DE") and not k.startswith("etats"):
            vrai = reels[ctrl].reindex(jours).ffill(limit=5)
            debut = vrai.first_valid_index()
            r = proxys[k].pct_change(fill_method=None).where(
                jours < debut, vrai.pct_change(fill_method=None))
            premier = proxys[k].first_valid_index()
            out[k] = 100 * (1 + r[premier:].fillna(0.0)).cumprod()
            raccords[k] = debut.date().isoformat()

    df = pd.DataFrame(out)[list(CLASSES)]
    df.index.name = "date"
    df.round(4).to_csv(CSV)
    meta = {"releve": date.today().isoformat(), "debut": DEBUT,
            "fin": df.index[-1].date().isoformat(),
            "echelle_longue": ECHELLE_LONGUE,
            "echelle_courte": ECHELLE_COURTE,
            "credit": {"sensibilite": round(float(pente) * 100, 2),
                       "r2": round(r2, 2),
                       "prime_annuelle": round(float(constante) * 52 * 100, 2),
                       "serie_ecart": "ICE BofA US Corporate (FRED "
                                      "BAMLC0A0CM)",
                       "fenetre": qdvl.index[0].date().isoformat()},
            "raccords": raccords,
            "nettoyes": nettoye, "classes": {}}
    for k, (lib, support, source, ctrl) in CLASSES.items():
        s = df[k].dropna()
        meta["classes"][k] = {
            "libelle": lib, "support": support, "source": source,
            "debut": s.index[0].date().isoformat(),
            "controle_ticker": ctrl,
            "raccord": raccords.get(k),
            "controle": controle(proxys[k], reels[ctrl]),
        }
        c = meta["classes"][k]["controle"]
        print(f"{k:15} corr {c['correlation']:.2f}  vol {c['vol_remplacant']}"
              f" vs {c['vol_support']}  baisse {c['baisse_remplacant']} vs "
              f"{c['baisse_support']}  perf {c['perf_remplacant']} vs "
              f"{c['perf_support']}  ({c['debut']}, {c['annees']} ans)")
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
