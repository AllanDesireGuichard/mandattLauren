"""
Teste l'allocation strategique reelle contre la contrainte de 15 %.

Remplace le balayage generique de estimate_dd_ratio.py par la SAA proposee,
en tenant compte de la poche A sans risque (IPS §6.1) : la contrainte porte
sur le consolide, donc 10 % d'actifs sans risque attenuent mecaniquement le
drawdown de l'ensemble.

Teste aussi la sensibilite du block bootstrap a la longueur des blocs --
un point qui s'est revele contre-intuitif.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data import get_panel          # noqa: E402
from core.ips import MAX_DRAWDOWN        # noqa: E402

RNG = np.random.default_rng(42)
START = "2004-11-19"

PROXY = {                       # classe SAA -> (ticker, replis)
    "equity_us":        ("SPY",  ("IVV", "VOO")),
    "equity_dev_exus":  ("EFA",  ("VEA", "IEFA")),
    "equity_emerging":  ("EEM",  ("IEMG", "VWO")),
    "infrastructure":   ("VNQ",  ("IYR", "SCHH")),
    "govt_bonds":       ("IEF",  ("GOVT", "IEI")),
    "inflation_linked": ("TIP",  ("SCHP", "VTIP")),
    "credit_ig":        ("LQD",  ("VCIT", "USIG")),
    "gold":             ("GLD",  ("IAU",)),
}
HEDGE = {"equity_us": 0.40, "equity_dev_exus": 0.40, "equity_emerging": 0.00,
         "infrastructure": 0.40, "govt_bonds": 1.00, "inflation_linked": 1.00,
         "credit_ig": 1.00, "gold": 0.00}

# SAA de l'IPS, hors poches sans risque et hors crypto (traitee a part).
# SAA issue de l'optimisation (scripts/optimize_saa.py, second passage),
# projetee sur les proxys longs. Les actions developpees sont scindees
# 60/40 entre US et hors-US, conformement a la composition d'un indice monde.
SAA_RISKY = {
    "equity_us": 0.156, "equity_dev_exus": 0.104, "equity_emerging": 0.12,
    "infrastructure": 0.10, "govt_bonds": 0.08, "inflation_linked": 0.14,
    "credit_ig": 0.08, "gold": 0.06,
}
RISKLESS_W = 0.10          # poche A : monetaire + souverain court
ALTS_W = 0.04              # alternatifs : modelises en sans risque (conservateur)
RISKLESS_YIELD = 0.022


def max_dd(v: np.ndarray) -> float:
    return float((1.0 - v / np.maximum.accumulate(v)).max())


def rolling_dd(r: pd.Series, win: int = 252) -> np.ndarray:
    v = (1 + r).cumprod().to_numpy()
    return np.array([max_dd(v[i:i + win]) for i in range(len(v) - win)])


def boot_dd(r: pd.Series, block: int, win: int = 252, n: int = 10_000) -> np.ndarray:
    a = r.to_numpy()
    nb = int(np.ceil(win / block))
    st = RNG.integers(0, len(a) - block, size=(n, nb))
    return np.array([max_dd(np.cumprod(1 + np.concatenate(
        [a[s:s + block] for s in st[i]])[:win])) for i in range(n)])


def main() -> int:
    spec = {t: fb for t, fb in PROXY.values()}
    spec["EURUSD=X"] = ("EUR=X",)
    print("Chargement :")
    px, _ = get_panel(spec)
    px = px.loc[START:].ffill().dropna()

    fx_ret = -px["EURUSD=X"].pct_change()
    loc = px.pct_change()
    rets = pd.DataFrame({
        k: loc[t] + (1 - HEDGE[k]) * fx_ret for k, (t, _) in PROXY.items()
    }).dropna()

    print(f"\nPeriode : {rets.index[0].date()} -> {rets.index[-1].date()} "
          f"({(rets.index[-1]-rets.index[0]).days/365.25:.1f} ans)")

    rl_daily = RISKLESS_YIELD / 252
    scale = 1.0 - RISKLESS_W - ALTS_W          # part reellement risquee

    def build(mult: float) -> pd.Series:
        """Portefeuille consolide, part risquee multipliee par `mult`."""
        w = {k: v * scale * mult for k, v in SAA_RISKY.items()}
        risky = (rets[list(w)] * pd.Series(w)).sum(axis=1)
        cash_w = 1.0 - sum(w.values())
        return risky + cash_w * rl_daily

    print("\n--- SAA DE L'IPS ET VARIANTES (mult = echelle du risque) ---")
    print(f"{'mult':>5} {'actions':>8} {'vol':>7} {'DD P90':>8} {'DD pire':>8} "
          f"{'2008':>7} {'2022':>7}  contrainte 15 %")
    rows = []
    for mult in [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]:
        r = build(mult)
        eq = (SAA_RISKY["equity_us"] + SAA_RISKY["equity_dev_exus"]
              + SAA_RISKY["equity_emerging"] + SAA_RISKY["infrastructure"]) * scale * mult
        vol = r.std() * np.sqrt(252)
        hist = rolling_dd(r)
        p90, worst = np.percentile(hist, 90), hist.max()
        v = (1 + r).cumprod()
        dd08 = max_dd(v.loc["2007-06":"2009-06"].to_numpy())
        dd22 = max_dd(v.loc["2021-12":"2022-12"].to_numpy())
        ok = "OK" if p90 <= MAX_DRAWDOWN else "VIOLEE"
        print(f"{mult:>5.1f} {eq:>8.0%} {vol:>7.1%} {p90:>8.1%} {worst:>8.1%} "
              f"{dd08:>7.1%} {dd22:>7.1%}  {ok}")
        rows.append({"mult": mult, "eq": eq, "vol": vol, "p90": p90,
                     "worst": worst, "dd08": dd08, "dd22": dd22})

    df = pd.DataFrame(rows)
    ok = df[df.p90 <= MAX_DRAWDOWN]
    if len(ok):
        b = ok.iloc[-1]  # noqa
        print(f"\n=> Contrainte mordante a mult={b.mult:.1f} : "
              f"{b['eq']:.0%} actions, vol {b['vol']:.1%}, P90 DD {b['p90']:.1%}")
        print(f"   Ratio DD/vol implique : {b['p90']/b['vol']:.2f}")

    print("\n--- SENSIBILITE DU BOOTSTRAP A LA LONGUEUR DES BLOCS ---")
    r = build(1.0)
    hist_p90 = np.percentile(rolling_dd(r), 90)
    print(f"{'blocs':>8} {'DD P90':>9}   ecart vs historique ({hist_p90:.1%})")
    for block in [21, 63, 126, 189, 252]:
        p = np.percentile(boot_dd(r, block), 90)
        print(f"{block:>5} j  {p:>8.1%}   {p-hist_p90:>+7.1%}")

    print("\n--- CONTRIBUTION MARGINALE DE LA CRYPTO ---")
    btc, _ = get_panel({"BTC-USD": ()})
    if not btc.empty:
        b = btc["BTC-USD"].pct_change().dropna()
        b = b + fx_ret.reindex(b.index).fillna(0)
        base = build(1.0)
        common = base.index.intersection(b.index)
        for w in [0.0, 0.01, 0.02, 0.03, 0.05]:
            mix = base.loc[common] * (1 - w) + b.loc[common] * w
            h = rolling_dd(mix)
            print(f"  crypto {w:>4.0%}   vol {mix.std()*np.sqrt(252):>5.1%}   "
                  f"DD P90 {np.percentile(h,90):>5.1%}   pire {h.max():>5.1%}")

    df.to_csv(Path(__file__).resolve().parent.parent / "data" / "saa_risk.csv",
              index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
