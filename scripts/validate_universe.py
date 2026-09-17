"""
Verifie que chaque support de data/universe.csv existe reellement et dispose
d'un historique exploitable. Met en cache les prix dans data/prices/.

Un support sans historique long n'est pas disqualifie : il peut etre recent.
Mais il ne pourra pas servir au backtest — il faudra lui substituer son indice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.universe import load_universe  # noqa: E402

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices"
CACHE.mkdir(exist_ok=True)
MIN_YEARS_BACKTEST = 10


def fetch(ticker: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(ticker, period="max", progress=False,
                      auto_adjust=True, threads=False)
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return raw[["Close"]].dropna()


def main() -> int:
    uni = load_universe()
    rows = []
    for t in uni["ticker"]:
        try:
            px = fetch(t)
        except Exception as exc:                       # noqa: BLE001
            rows.append({"ticker": t, "ok": False, "n": 0,
                         "start": None, "years": 0.0, "err": str(exc)[:50]})
            continue
        if px.empty:
            rows.append({"ticker": t, "ok": False, "n": 0,
                         "start": None, "years": 0.0, "err": "no data"})
            continue
        px.to_parquet(CACHE / f"{t.replace('.', '_')}.parquet")
        years = (px.index[-1] - px.index[0]).days / 365.25
        rows.append({"ticker": t, "ok": True, "n": len(px),
                     "start": px.index[0].date(), "years": round(years, 1),
                     "err": ""})

    res = pd.DataFrame(rows).merge(
        uni[["ticker", "asset_class", "role", "name"]], on="ticker", how="left")

    ok = res[res.ok]
    ko = res[~res.ok]
    short = ok[ok.years < MIN_YEARS_BACKTEST]

    print(f"Recuperes  : {len(ok)}/{len(res)}")
    print(f"Echecs     : {len(ko)}")
    print(f"Historique < {MIN_YEARS_BACKTEST} ans : {len(short)}\n")

    print("--- HISTORIQUE EXPLOITABLE POUR LE BACKTEST ---")
    print(ok[ok.years >= MIN_YEARS_BACKTEST]
          [["ticker", "asset_class", "role", "years", "start"]]
          .sort_values(["asset_class", "years"], ascending=[True, False])
          .to_string(index=False))

    if len(short):
        print("\n--- TROP RECENT : proxy indiciel requis pour le backtest ---")
        print(short[["ticker", "asset_class", "role", "years", "start"]]
              .sort_values("years").to_string(index=False))

    if len(ko):
        print("\n--- ECHEC : ticker a corriger ---")
        print(ko[["ticker", "asset_class", "name", "err"]].to_string(index=False))

    res.to_csv(CACHE.parent / "universe_validation.csv", index=False)
    print(f"\n-> data/universe_validation.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
