"""Complete les libelles manquants des tickers d'extension via yfinance."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "extension_names.csv"


def main() -> int:
    import yfinance as yf

    uni = pd.read_csv(ROOT / "data" / "universe_candidates.csv")
    stats = pd.read_csv(ROOT / "data" / "instrument_stats.csv")
    todo = uni[(uni.source == "extension") & uni.ticker.isin(stats.ticker)].ticker.tolist()
    known = {}
    if OUT.exists():
        known = pd.read_csv(OUT).set_index("ticker")["name"].to_dict()

    rows = []
    for i, t in enumerate(todo, 1):
        if t in known and isinstance(known[t], str) and known[t]:
            rows.append({"ticker": t, "name": known[t], "ccy": ""})
            continue
        name, ccy = "", ""
        for _ in range(2):
            try:
                info = yf.Ticker(t).get_info()
                name = info.get("longName") or info.get("shortName") or ""
                ccy = info.get("currency", "") or ""
            except Exception:                                # noqa: BLE001
                time.sleep(2)
                continue
            break
        rows.append({"ticker": t, "name": name, "ccy": ccy})
        print(f"  [{i:>2}/{len(todo)}] {t:<12} {name[:58] or 'INTROUVABLE'}")
        time.sleep(0.6)

    pd.DataFrame(rows).to_csv(OUT, index=False)
    found = sum(1 for r in rows if r["name"])
    print(f"\nLibelles trouves : {found}/{len(rows)}  -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
