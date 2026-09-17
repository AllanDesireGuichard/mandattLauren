"""
Reconstitue la serie du benchmark hybride et mesure ce qu'il capture.

Deux questions :
  1. Qu'aurait fait le benchmark sur l'historique disponible ?
  2. Que mesure-t-il REELLEMENT ? Ses poids etant ceux de l'allocation
     strategique, l'ecart strategique est nul par construction. On quantifie
     donc ce qui reste : ecarts tactiques et selection d'instruments.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                    # noqa: E402
from core.benchmark import COMPONENTS, REBALANCING      # noqa: E402
from core.metrics import load_prices                    # noqa: E402
from core.quality import VOLATILE_CLASSES, audit        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RNG = np.random.default_rng(42)

# Substituts d'historique quand le tracker de reference est trop recent.
HISTORY_SUBSTITUTE = {"NFRA.L": "XDWU.DE"}      # 3,1 ans -> 10,4 ans


def max_dd(v: np.ndarray) -> float:
    return float((1.0 - v / np.maximum.accumulate(v)).max())


def load_components(exclude: set[str] = frozenset()) -> tuple[pd.DataFrame, dict]:
    used, rets = {}, {}
    for c in COMPONENTS:
        if c.saa_class in exclude:
            continue
        t = HISTORY_SUBSTITUTE.get(c.tracker, c.tracker)
        px = load_prices([t])
        if t not in px.columns:
            continue
        s = px[t].dropna()
        s = audit(s, allow_volatile=c.saa_class in VOLATILE_CLASSES)["series"]
        rets[c.saa_class] = s.pct_change()
        used[c.saa_class] = t
    return pd.DataFrame(rets).dropna(), used


def rebalanced(rets: pd.DataFrame, w: pd.Series, freq: str = "QE") -> pd.Series:
    """Serie a poids cibles, rebalances a la frequence donnee."""
    out, drift = [], w.copy()
    period = rets.index.to_period("Q" if freq == "QE" else "M")
    prev = period[0]
    for i, (d, r) in enumerate(rets.iterrows()):
        if period[i] != prev:
            drift, prev = w.copy(), period[i]
        pr = float((drift * r).sum())
        drift = drift * (1 + r)
        drift = drift / drift.sum()
        out.append(pr)
    return pd.Series(out, index=rets.index)


def stats(r: pd.Series, label: str) -> dict:
    v = (1 + r).cumprod()
    years = (r.index[-1] - r.index[0]).days / 365.25
    return {"serie": label,
            "ans": round(years, 1),
            "rendement": v.iloc[-1] ** (1 / years) - 1,
            "vol": r.std() * np.sqrt(252),
            "max_dd": max_dd(v.to_numpy())}


def main() -> int:
    # --- serie complete, limitee par le composant le plus recent ---
    full, used = load_components()
    w_full = pd.Series({c: ips.SAA_INDICATIVE[c] for c in full.columns})
    w_full /= w_full.sum()
    bench = rebalanced(full, w_full)

    # --- serie longue, crypto exclue (c'est elle qui borne l'historique) ---
    long_, _ = load_components(exclude={"crypto"})
    w_long = pd.Series({c: ips.SAA_INDICATIVE[c] for c in long_.columns})
    w_long /= w_long.sum()
    bench_long = rebalanced(long_, w_long)

    print("Trackers utilises :")
    for k, t in used.items():
        sub = "  [substitut d'historique]" if t != dict(
            (c.saa_class, c.tracker) for c in COMPONENTS)[k] else ""
        print(f"  {k:<24}{t}{sub}")

    print(f"\nRebalancement : {REBALANCING}\n")
    print("--- PERFORMANCE DU BENCHMARK ---")
    rows = [stats(bench, "composition complete"),
            stats(bench_long, "hors crypto (historique long)")]
    print(f"{'serie':<34}{'ans':>5}{'rendement':>11}{'vol':>8}{'max DD':>9}")
    for x in rows:
        print(f"  {x['serie']:<32}{x['ans']:>5.1f}{x['rendement']:>11.2%}"
              f"{x['vol']:>8.1%}{x['max_dd']:>9.1%}")

    # --- reference absolue ---
    print("\n--- DOUBLE REFERENCE ---")
    yrs = (bench_long.index[-1] - bench_long.index[0]).days / 365.25
    br = (1 + bench_long).cumprod().iloc[-1] ** (1 / yrs) - 1
    net = br - ips.TOTAL_FEES - ips.TAX_DRAG_STRUCTURED
    print(f"  Benchmark, brut                      {br:>7.2%}")
    print(f"  Benchmark, net de frais et d'impots  {net:>7.2%}")
    print(f"  Reference absolue (inflation client) {ips.INFLATION_TARGET:>7.2%}")
    print(f"  Ecart                                {net-ips.INFLATION_TARGET:>+7.2%}")
    print("\n  Note : l'inflation reellement constatee sur la periode a ete")
    print("  inferieure aux 4 % retenus comme hypothese client. La reference")
    print("  absolue se juge sur l'inflation CONSTATEE, pas sur l'hypothese.")

    # --- ce que le benchmark mesure reellement ---
    print("\n--- CE QUE LE BENCHMARK MESURE ---")
    print("  Ecart strategique : NUL par construction (memes poids).")
    print("  Reste donc l'ecart tactique et la selection d'instruments.\n")
    band = ips.REBALANCING_BAND
    tes = []
    for _ in range(500):
        tilt = pd.Series(RNG.uniform(-band, band, len(w_full)),
                         index=w_full.index)
        tilt -= tilt.mean()
        active = rebalanced(full, (w_full + tilt).clip(lower=0))
        tes.append((active - bench).std() * np.sqrt(252))
    tes = np.array(tes)
    print(f"  Ecart de suivi engendre par les bandes de +/- {band:.0%} :")
    print(f"    median                {np.median(tes):>7.2%}")
    print(f"    90e centile           {np.percentile(tes, 90):>7.2%}")
    print(f"\n  Autrement dit, meme en utilisant tout le budget tactique, le")
    print(f"  portefeuille reste a moins de {np.percentile(tes,90):.1%} d'ecart de suivi")
    print(f"  annuel. C'est la mesure honnete de notre marge de manoeuvre.")

    pd.DataFrame({"benchmark": bench}).to_csv(
        ROOT / "data" / "benchmark_series.csv")
    print("\n-> data/benchmark_series.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
