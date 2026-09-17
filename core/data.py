"""
Chargement de prix robuste.

yfinance renvoie des echecs intermittents par ticker (rate-limiting Yahoo) :
un ticker qui repond a un instant donne peut echouer quelques minutes plus
tard. D'ou : une tentative a la fois, avec backoff, tickers de repli, et
cache incremental pour ne jamais reperdre ce qui est deja telecharge.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "prices"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker.replace('.', '_').replace('=', '_')}.parquet"


def fetch_one(ticker: str, attempts: int = 4, pause: float = 3.0) -> pd.DataFrame:
    """Serie Close d'un ticker, avec retry. DataFrame vide si echec."""
    import yfinance as yf

    for i in range(attempts):
        try:
            raw = yf.download(ticker, period="max", progress=False,
                              auto_adjust=True, threads=False)
        except Exception:                                   # noqa: BLE001
            raw = None
        if raw is not None and not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            return raw[["Close"]].dropna().rename(columns={"Close": ticker})
        if i < attempts - 1:
            time.sleep(pause * (i + 1))
    return pd.DataFrame()


def get(ticker: str, fallbacks: tuple[str, ...] = (),
        use_cache: bool = True) -> tuple[str, pd.DataFrame]:
    """
    Serie du ticker, ou du premier repli qui repond.
    Retourne (ticker effectivement utilise, serie).
    """
    for t in (ticker, *fallbacks):
        p = _path(t)
        if use_cache and p.exists():
            df = pd.read_parquet(p)
            if not df.empty:
                return t, df
        df = fetch_one(t)
        if not df.empty:
            df.to_parquet(p)
            return t, df
    return ticker, pd.DataFrame()


def get_panel(spec: dict[str, tuple[str, ...]],
              use_cache: bool = True) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    spec : {ticker_principal: (replis...)}
    Retourne (panel de Close aligne, {principal: ticker retenu}).
    """
    series, used = {}, {}
    for t, fb in spec.items():
        got, df = get(t, fb, use_cache)
        if df.empty:
            print(f"  ECHEC  {t} (et ses replis)")
            continue
        series[t] = df.iloc[:, 0]
        used[t] = got
        tag = "" if got == t else f"  [repli {got}]"
        print(f"  ok     {t:<10} {len(df):>6} j  depuis {df.index[0].date()}{tag}")
    return pd.DataFrame(series), used
