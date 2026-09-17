"""
Recupere les prix de tous les candidats.

  - source equitydb2 : copie depuis son cache (format {close}, index date)
    vers le notre ({ticker}), sans reseau
  - source extension : telechargement via core.data (retry + backoff)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data import CACHE_DIR, _path, fetch_one   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EQDB_CACHE = Path.home() / "projets" / "equitydb2" / "state" / "cache" / "etf"


def main() -> int:
    uni = pd.read_csv(ROOT / "data" / "universe_candidates.csv")

    copied = skipped = 0
    for t in uni[uni.source == "equitydb2"].ticker:
        dst = _path(t)
        if dst.exists():
            skipped += 1
            continue
        src = EQDB_CACHE / f"{t}.parquet"
        if not src.exists():
            continue
        d = pd.read_parquet(src)
        if d.empty:
            continue
        d.columns = [t]
        d.to_parquet(dst)
        copied += 1
    print(f"Copies depuis equitydb2 : {copied}  (deja presents : {skipped})")

    ext = uni[uni.source == "extension"].ticker.tolist()
    todo = [t for t in ext if not _path(t).exists()]
    print(f"A telecharger           : {len(todo)}\n")

    ok = ko = 0
    for i, t in enumerate(todo, 1):
        df = fetch_one(t, attempts=3, pause=2.0)
        if df.empty:
            ko += 1
            print(f"  [{i:>3}/{len(todo)}] {t:<12} ECHEC")
        else:
            df.to_parquet(_path(t))
            ok += 1
            print(f"  [{i:>3}/{len(todo)}] {t:<12} {len(df):>5} j  "
                  f"depuis {df.index[0].date()}")
    print(f"\nTelecharges : {ok}   Echecs : {ko}")
    print(f"Cache total : {len(list(CACHE_DIR.glob('*.parquet')))} fichiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
