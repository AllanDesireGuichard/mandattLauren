"""
Etape 4 -- stress tests et distribution complete du drawdown.

Le P90 dit qu'une annee sur dix depasse 12 %. Il ne dit ni ce que le client
vivrait dans une crise nommee, ni combien de temps il resterait sous l'eau,
ni quelle ligne du portefeuille aurait cause la perte.

Trois questions, trois sections :
  1. Que se passe-t-il dans les crises QUI ONT EU LIEU ?
  2. A quoi ressemble la distribution complete des pertes ?
  3. Combien de temps faut-il pour revenir au point haut ?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                  # noqa: E402
from core.data import get_panel                       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RNG = np.random.default_rng(42)
START = "2004-11-19"

PROXY = {
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

# SAA projetee sur les proxys longs (actions dev. scindees 60/40 US / hors-US)
W = {"equity_us": 0.138, "equity_dev_exus": 0.092, "equity_emerging": 0.11,
     "infrastructure": 0.09, "govt_bonds": 0.10, "inflation_linked": 0.15,
     "credit_ig": 0.09, "gold": 0.07}
RISKLESS_W = 0.14          # poche A (10 %) + alternatifs modelises sans risque
RISKLESS_YIELD = 0.022

CRISES = [
    ("Faillite de Lehman et crise financiere", "2007-10-01", "2009-12-31"),
    ("Crise de la dette souveraine europeenne", "2011-04-01", "2012-09-30"),
    ("Choc COVID",                              "2020-01-15", "2020-12-31"),
    ("Choc d'inflation et resserrement",        "2021-12-01", "2023-06-30"),
]


def max_dd(v: np.ndarray) -> float:
    return float((1.0 - v / np.maximum.accumulate(v)).max())


def drawdown_series(v: np.ndarray) -> np.ndarray:
    return 1.0 - v / np.maximum.accumulate(v)


def build() -> tuple[pd.Series, pd.DataFrame]:
    spec = {t: fb for t, fb in PROXY.values()}
    spec["EURUSD=X"] = ("EUR=X",)
    px, _ = get_panel(spec)
    px = px.loc[START:].ffill().dropna()
    fx = -px["EURUSD=X"].pct_change()
    loc = px.pct_change()
    rets = pd.DataFrame({k: loc[t] + (1 - HEDGE[k]) * fx
                         for k, (t, _) in PROXY.items()}).dropna()
    w = pd.Series(W)
    port = (rets[w.index] * w).sum(axis=1) + RISKLESS_W * RISKLESS_YIELD / 252
    return port, rets


def main() -> int:
    print("Chargement :")
    port, rets = build()
    v = (1 + port).cumprod()
    print(f"\nPeriode : {port.index[0].date()} -> {port.index[-1].date()} "
          f"({(port.index[-1]-port.index[0]).days/365.25:.1f} ans)\n")

    # ---------------------------------------------------------------- 1
    print("=" * 74)
    print("1. LES CRISES QUI ONT EU LIEU")
    print("=" * 74)
    w = pd.Series(W)
    for name, a, b in CRISES:
        sub = port.loc[a:b]
        if len(sub) < 40:
            continue
        vv = (1 + sub).cumprod().to_numpy()
        dd = max_dd(vv)
        trough = int(np.argmin(vv / np.maximum.accumulate(vv)))
        peak = int(np.argmax(vv[:trough + 1]))
        # temps de recouvrement, cherche au-dela de la fenetre
        after = (1 + port.loc[sub.index[peak]:]).cumprod()
        target = after.iloc[0]
        rec = after[after.index > sub.index[trough]]
        rec_idx = rec[rec >= target * (1 - 1e-9)]
        months = ((rec_idx.index[0] - sub.index[trough]).days / 30.4
                  if len(rec_idx) else np.nan)

        flag = "DEPASSE" if dd > ips.MAX_DRAWDOWN else "sous la contrainte"
        print(f"\n{name}")
        print(f"  perte maximale        {dd:>7.1%}   {flag}")
        print(f"  du {sub.index[peak].date()} au {sub.index[trough].date()}"
              f"   ({(sub.index[trough]-sub.index[peak]).days} jours de baisse)")
        print(f"  retour au point haut  "
              f"{f'{months:.0f} mois' if not np.isnan(months) else 'non atteint'}")

        # contribution de chaque classe a la perte
        seg = rets.loc[sub.index[peak]:sub.index[trough]]
        contrib = ((1 + seg).prod() - 1) * w
        top = contrib.sort_values().head(3)
        print("  principales contributions a la perte :")
        for k, c in top.items():
            print(f"      {k:<20}{c:>+7.2%}")

    # ---------------------------------------------------------------- 2
    print("\n" + "=" * 74)
    print("2. DISTRIBUTION DES PERTES SUR 12 MOIS GLISSANTS")
    print("=" * 74)
    arr = v.to_numpy()
    win = 252
    dds = np.array([max_dd(arr[i:i + win]) for i in range(len(arr) - win)])
    print(f"\n  {len(dds)} fenetres de 12 mois observees\n")
    for q in [50, 75, 90, 95, 99]:
        print(f"  centile {q:>2}       {np.percentile(dds, q):>7.1%}")
    print(f"  pire cas         {dds.max():>7.1%}")
    print(f"\n  P(perte > 15 %)  {(dds > ips.MAX_DRAWDOWN).mean():>7.1%}"
          f"   tolerance {ips.DD_BREACH_PROBABILITY:.0%}")
    print(f"  P(perte > 10 %)  {(dds > 0.10).mean():>7.1%}"
          f"   seuil de revue exceptionnelle")

    # ---------------------------------------------------------------- 3
    print("\n" + "=" * 74)
    print("3. TEMPS PASSE SOUS L'EAU")
    print("=" * 74)
    dd_path = drawdown_series(arr)
    print(f"\n  jours en perte latente        {(dd_path > 0.001).mean():>7.1%} du temps")
    print(f"  jours a plus de 5 % de perte  {(dd_path > 0.05).mean():>7.1%}")
    print(f"  jours a plus de 10 %          {(dd_path > 0.10).mean():>7.1%}")
    print(f"  jours a plus de 15 %          {(dd_path > 0.15).mean():>7.1%}")

    # duree des episodes sous l'eau
    under = dd_path > 0.001
    spells, cur = [], 0
    for u in under:
        if u:
            cur += 1
        elif cur:
            spells.append(cur); cur = 0
    if cur:
        spells.append(cur)
    sp = np.array(spells) / 21.0      # en mois
    print(f"\n  episodes de perte latente     {len(sp)}")
    print(f"  duree mediane                 {np.median(sp):>7.1f} mois")
    print(f"  duree du plus long            {sp.max():>7.1f} mois")

    pd.DataFrame({"drawdown_12m": dds}).to_csv(
        ROOT / "data" / "drawdown_distribution.csv", index=False)
    print("\n-> data/drawdown_distribution.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
