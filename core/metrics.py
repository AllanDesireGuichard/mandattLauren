"""
Metriques de selection d'instruments.

Objectif : passer de ~218 candidats a un support principal et un suppleant
par classe d'actifs, sur des criteres explicites et defendables devant le
client -- pas sur une intuition.

Les series du cache couvrent au plus 10 ans (limite heritee d'equitydb2).
C'est suffisant pour SELECTIONNER : on compare des instruments entre eux sur
une fenetre commune. Ce n'est pas suffisant pour CALIBRER le risque du
portefeuille, qui passe par les proxys longs (scripts/validate_saa_risk.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.data import CACHE_DIR, _path
from core.esg import esg_required
from core.quality import (VOLATILE_CLASSES, audit, plausible_vol,
                          venue_matches_currency, venue_score)

TRADING_DAYS = 252
MIN_YEARS = 3.0


def load_prices(tickers: list[str]) -> pd.DataFrame:
    """Panel de prix de cloture, colonnes = tickers disponibles."""
    series = {}
    for t in tickers:
        p = _path(t)
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        if d.empty:
            continue
        s = d.iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        series[t] = s[~s.index.duplicated(keep="last")].sort_index()
    return pd.DataFrame(series)


def max_dd(v: np.ndarray) -> float:
    if len(v) < 2:
        return np.nan
    return float((1.0 - v / np.maximum.accumulate(v)).max())


def describe(px: pd.DataFrame,
             classes: dict[str, str] | None = None) -> pd.DataFrame:
    """
    Une ligne par ticker : historique, rendement, risque, qualite.

    Chaque serie passe par core.quality : reparation des ruptures d'echelle,
    puis audit. Le verdict est conserve dans la colonne `verdict`.
    """
    classes = classes or {}
    rows = []
    for t in px.columns:
        s = px[t].dropna()
        if len(s) < 60:
            continue
        cls = classes.get(t, "")
        a = audit(s, allow_volatile=cls in VOLATILE_CLASSES)
        s = a["series"]
        r = s.pct_change().dropna()
        years = (s.index[-1] - s.index[0]).days / 365.25
        v = s.to_numpy()
        # trous de cotation : proxy de liquidite / de qualite de la serie
        span = pd.bdate_range(s.index[0], s.index[-1])
        rows.append({
            "ticker": t,
            "years": round(years, 1),
            "start": s.index[0].date(),
            "end": s.index[-1].date(),
            "cagr": (v[-1] / v[0]) ** (1 / years) - 1 if years > 0 else np.nan,
            "vol": r.std() * np.sqrt(TRADING_DAYS),
            "max_dd": max_dd(v),
            "dd_2022": max_dd(s.loc["2021-12":"2022-12"].to_numpy())
                       if s.index[0] < pd.Timestamp("2022-01-01") else np.nan,
            "coverage": len(s) / max(len(span), 1),
            "stale_days": int((r == 0).sum()),
            "verdict": a["verdict"],
            "n_repairs": len(a["repairs"]),
            "venue": venue_score(t),
        })
    return pd.DataFrame(rows).set_index("ticker")


def rank_within_class(uni: pd.DataFrame, stats: pd.DataFrame,
                      saa_class: str) -> pd.DataFrame:
    """
    Classe les candidats d'une classe d'actifs.

    Criteres, par ordre de priorite :
      1. historique suffisant (>= MIN_YEARS)
      2. serie propre (peu de trous, peu de jours sans cotation)
      3. filtre ESG present
      4. support capitalisant (report d'imposition, IPS §7.3)
    """
    c = uni[uni.saa_class == saa_class].set_index("ticker")
    df = c.join(stats, how="inner")
    if df.empty:
        return df
    df["ok_hist"] = df["years"] >= MIN_YEARS
    df["ok_data"] = df["verdict"].eq("OK")
    df["ok_ccy"] = [venue_matches_currency(t, saa_class) for t in df.index]
    checks = df["vol"].apply(lambda v: plausible_vol(v, saa_class))
    df["ok_vol"] = [c[0] for c in checks]
    df["why_vol"] = [c[1] for c in checks]
    df["ok_clean"] = (df["coverage"] > 0.80) & (
        df["stale_days"] / (df["years"] * TRADING_DAYS) < 0.15)
    df["ok_esg"] = df["esg"].fillna(False).astype(bool)
    # Le filtre ESG n'est exige que sur les classes a emetteurs d'entreprise
    # (cf. core/esg.py) : sur la dette souveraine ou l'or, il est sans objet.
    if not esg_required(saa_class):
        df["ok_esg"] = True
    df["ok_acc"] = df["distribution"].fillna("").eq("acc")
    # IPS §6.4 : l'or ne doit PAS etre couvert en change -- couvrir annulerait
    # sa fonction de reserve de valeur. Un ETC "EUR Hedged" contredit le mandat.
    if saa_class == "gold":
        hedged = df["name"].fillna("").str.contains("hedg", case=False)
        df["ok_hedge"] = ~hedged
    else:
        df["ok_hedge"] = True
    df["score"] = (df.ok_hist.astype(int) * 16 + df.ok_clean.astype(int) * 8
                   + df.ok_esg.astype(int) * 4 + df.ok_hedge.astype(int) * 4
                   + df.ok_ccy.astype(int) * 3
                   + df.ok_acc.astype(int) * 2 + df.venue.fillna(2))
    return df.sort_values(["score", "years"], ascending=False)
