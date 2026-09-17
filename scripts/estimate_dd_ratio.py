"""
Estime empiriquement la relation entre volatilite annuelle et perte maximale
sur 12 mois -- le parametre DD_TO_VOL_RATIO de core/ips.py, qui traduit la
contrainte client de 15 % en budget de risque.

Methode
  1. Proxys longs par classe d'actifs (2004+), rendements quotidiens.
  2. Passage en EUR selon la politique de couverture de l'IPS §6.4.
  3. Portefeuilles a poids d'actions croissant -> une plage de volatilite.
  4. Pour chaque : vol annualisee, et distribution de la perte max sur
     fenetres glissantes de 252 jours.
  5. Estimation du ratio P90(DD 12m) / vol, par fenetres historiques
     ET par block bootstrap (blocs de 3 mois, pour preserver les
     enchainements de crise que ne capture pas un tirage i.i.d.).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data import get_panel  # noqa: E402

START = "2004-11-01"
RNG = np.random.default_rng(42)

# Proxys longs, avec tickers de repli equivalents. Pas de filtre ESG : on
# estime ici une relation statistique entre vol et drawdown, pas une
# performance -- le filtre ESG ne change pas cette relation de facon
# materielle (il retire ~5 % de la capitalisation).
PROXIES = {
    "SPY":  ("IVV", "VOO", "SPXS.L"),        # actions US
    "EFA":  ("VEA", "IEFA", "EFV"),          # actions dev. hors US
    "EEM":  ("IEMG", "VWO", "SUSM.L"),       # actions emergentes
    "IEF":  ("GOVT", "IEI", "DBXG.DE"),      # souverain 7-10 ans
    "LQD":  ("VCIT", "USIG", "CRPS.L"),      # credit IG
    "TIP":  ("SCHP", "VTIP", "STHE.L"),      # obligations indexees
    "GLD":  ("IAU", "SGLN.L", "PHAU.L"),     # or
    "VNQ":  ("IYR", "SCHH", "IWDP.L"),       # immobilier cote
}

# Couverture de change appliquee (IPS §6.4) : 1.0 = integralement couvert,
# donc rendement local ; 0.0 = expose au USD/EUR.
HEDGE = {"SPY": 0.40, "EFA": 0.40, "EEM": 0.00, "IEF": 1.00,
         "LQD": 1.00, "TIP": 1.00, "GLD": 0.00, "VNQ": 0.40}


def load() -> tuple[pd.DataFrame, dict[str, str]]:
    spec = dict(PROXIES)
    spec["EURUSD=X"] = ("EUR=X",)
    print("Chargement des proxys :")
    panel, used = get_panel(spec)
    missing = [t for t in list(PROXIES) + ["EURUSD=X"] if t not in panel.columns]
    if missing:
        raise SystemExit(f"\nProxys manquants, estimation impossible : {missing}")
    panel = panel.loc[START:].ffill().dropna()
    return panel, used


def to_eur(px: pd.DataFrame) -> pd.DataFrame:
    """Rendements quotidiens en EUR, couverture partielle appliquee."""
    fx = px["EURUSD=X"]                     # USD par EUR
    loc = px[list(PROXIES)].pct_change()
    fx_ret = -fx.pct_change()               # gain EUR quand l'EUR baisse
    out = {}
    for t in PROXIES:
        h = HEDGE[t]
        out[t] = loc[t] + (1.0 - h) * fx_ret
    return pd.DataFrame(out).dropna()


def portfolio(rets: pd.DataFrame, eq_w: float) -> pd.Series:
    """Portefeuille multi-actifs a poids d'actions eq_w, reste diversifie."""
    eq = {"SPY": 0.55, "EFA": 0.30, "EEM": 0.15}
    rest = {"IEF": 0.34, "LQD": 0.22, "TIP": 0.22, "GLD": 0.15, "VNQ": 0.07}
    w = {t: eq_w * s for t, s in eq.items()}
    w.update({t: (1 - eq_w) * s for t, s in rest.items()})
    return (rets[list(w)] * pd.Series(w)).sum(axis=1)


def max_dd(path: np.ndarray) -> float:
    """Perte max pic-a-creux d'une trajectoire de valeurs."""
    peak = np.maximum.accumulate(path)
    return float((1.0 - path / peak).max())


def rolling_dd(r: pd.Series, win: int = 252) -> np.ndarray:
    v = (1 + r).cumprod().to_numpy()
    n = len(v)
    if n <= win:
        return np.array([])
    return np.array([max_dd(v[i:i + win]) for i in range(n - win)])


def bootstrap_dd(r: pd.Series, block: int = 63, win: int = 252,
                 n_sims: int = 10_000) -> np.ndarray:
    """Block bootstrap : reechantillonne par blocs de ~3 mois."""
    a = r.to_numpy()
    n = len(a)
    n_blocks = int(np.ceil(win / block))
    starts = RNG.integers(0, n - block, size=(n_sims, n_blocks))
    out = np.empty(n_sims)
    for i in range(n_sims):
        seq = np.concatenate([a[s:s + block] for s in starts[i]])[:win]
        out[i] = max_dd(np.cumprod(1 + seq))
    return out


def main() -> int:
    px, used = load()
    subs = {k: v for k, v in used.items() if k != v}
    if subs:
        print(f"\nReplis utilises : {subs}")
    rets = to_eur(px)
    print(f"Periode : {rets.index[0].date()} -> {rets.index[-1].date()}  "
          f"({len(rets)} jours, {(rets.index[-1]-rets.index[0]).days/365.25:.1f} ans)\n")

    rows = []
    for eq_w in [0.20, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80]:
        r = portfolio(rets, eq_w)
        vol = r.std() * np.sqrt(252)
        hist = rolling_dd(r)
        boot = bootstrap_dd(r)
        rows.append({
            "actions": eq_w,
            "vol": vol,
            "dd_p90_hist": np.percentile(hist, 90),
            "dd_worst_hist": hist.max(),
            "dd_p90_boot": np.percentile(boot, 90),
            "ratio_hist": np.percentile(hist, 90) / vol,
            "ratio_boot": np.percentile(boot, 90) / vol,
            "ratio_worst": hist.max() / vol,
        })
    df = pd.DataFrame(rows)

    print("--- RELATION VOLATILITE / PERTE MAXIMALE 12 MOIS ---")
    print(f"{'actions':>8} {'vol':>7} {'DD P90':>8} {'DD pire':>8} "
          f"{'DD P90':>8} | {'ratio':>6} {'ratio':>6} {'ratio':>6}")
    print(f"{'':>8} {'':>7} {'hist':>8} {'hist':>8} {'boot':>8} | "
          f"{'hist':>6} {'boot':>6} {'pire':>6}")
    for _, x in df.iterrows():
        print(f"{x.actions:>7.0%} {x.vol:>7.1%} {x.dd_p90_hist:>8.1%} "
              f"{x.dd_worst_hist:>8.1%} {x.dd_p90_boot:>8.1%} | "
              f"{x.ratio_hist:>6.2f} {x.ratio_boot:>6.2f} {x.ratio_worst:>6.2f}")

    print(f"\nRatio median   historique P90 : {df.ratio_hist.median():.2f}")
    print(f"Ratio median   bootstrap  P90 : {df.ratio_boot.median():.2f}")
    print(f"Ratio median   pire cas       : {df.ratio_worst.median():.2f}")

    print("\n--- BUDGET DE RISQUE IMPLIQUE PAR LA CONTRAINTE DE 15 % ---")
    for label, ratio in [("historique P90", df.ratio_hist.median()),
                         ("bootstrap P90", df.ratio_boot.median()),
                         ("pire cas observe", df.ratio_worst.median())]:
        vol = 0.15 / ratio
        j = (df.vol - vol).abs().idxmin()
        print(f"  {label:<18} ratio {ratio:.2f}  ->  vol cible {vol:>5.1%}  "
              f"->  ~{df.loc[j,'actions']:.0%} actions")

    df.to_csv(Path(__file__).resolve().parent.parent / "data" / "dd_ratio.csv",
              index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
