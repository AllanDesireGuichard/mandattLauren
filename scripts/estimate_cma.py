"""
Assemble les hypotheses de marche complètes : rendements (core/cma.py),
volatilites et correlations (mesurees), puis teste l'allocation contre
l'objectif du client -- DANS LES DEUX REGIMES D'INFLATION.

Pour les correlations, on retient par classe d'actifs l'instrument au plus
long historique, et non le support d'execution : une correlation est une
propriete de la CLASSE, pas du fonds qui la met en oeuvre. Cela allonge la
fenetre commune, qui est le facteur limitant.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                    # noqa: E402
from core.cma import (INFLATION_BASE, INFLATION_CLIENT,  # noqa: E402
                      expected_returns, portfolio_return)
from core.metrics import describe, load_prices          # noqa: E402
from core.quality import VOLATILE_CLASSES, audit        # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRESS = [("2008 GFC", "2007-06", "2009-06"),
          ("2011 dette EUR", "2011-04", "2012-07"),
          ("2020 COVID", "2020-01", "2020-06"),
          ("2022 inflation", "2021-12", "2022-12")]


MIN_YEARS_PROXY = 5.0


def pick_proxies() -> dict[str, str]:
    """
    Un ticker par classe pour l'estimation du risque.

    Regle : le support PRINCIPAL, qui a deja passe les filtres de devise,
    de place et d'ESG. On ne lui substitue le plus long historique que s'il
    est trop court pour estimer une correlation.

    La regle precedente -- "toujours le plus long" -- avait retenu ERND.L
    (iShares $ Ultrashort, libelle en DOLLARS) comme proxy du monetaire EURO,
    parce qu'il avait 12,9 ans contre 10,0 a XEON.DE. Une correlation estimee
    sur le mauvais actif contamine toute la matrice.
    """
    uni = pd.read_csv(ROOT / "data" / "universe.csv")
    from core.quality import venue_matches_currency
    out = {}
    for c, grp in uni.groupby("saa_class"):
        g = grp[grp.role != "RECALE"]
        if not len(g):
            continue
        g = g[[venue_matches_currency(t, c) for t in g.ticker]] if len(
            g[[venue_matches_currency(t, c) for t in g.ticker]]) else g
        prim = g[g.role == "primary"]
        if len(prim) and prim.iloc[0]["years"] >= MIN_YEARS_PROXY:
            out[c] = prim.iloc[0]["ticker"]
        else:
            out[c] = g.loc[g["years"].idxmax(), "ticker"]
    return out


def main() -> int:
    picks = pick_proxies()
    picks = {k: v for k, v in picks.items() if k in ips.SAA_INDICATIVE}
    px = load_prices(list(picks.values()))

    rets = {}
    for cls, t in picks.items():
        if t not in px.columns:
            continue
        s = px[t].dropna()
        s = audit(s, allow_volatile=cls in VOLATILE_CLASSES)["series"]
        rets[cls] = s.pct_change()
    R = pd.DataFrame(rets).dropna()

    print(f"Fenetre commune : {R.index[0].date()} -> {R.index[-1].date()} "
          f"({(R.index[-1]-R.index[0]).days/365.25:.1f} ans)")
    print("Proxys par classe :", ", ".join(f"{k}={v}" for k, v in picks.items()))

    vol = R.std() * np.sqrt(252)
    corr = R.corr()
    cov = np.outer(vol, vol) * corr.to_numpy()

    print("\n--- VOLATILITES MESUREES ---")
    for k in sorted(vol.index, key=lambda x: -ips.SAA_INDICATIVE.get(x, 0)):
        print(f"  {k:<24}{ips.SAA_INDICATIVE.get(k,0):>5.0%}  vol {vol[k]:>6.1%}")

    print("\n--- CORRELATIONS (fenetre complete) ---")
    print((corr * 100).round(0).astype(int).to_string())

    # --- correlations en regime de stress ---
    #
    # ERREUR STATISTIQUE CORRIGEE : la premiere version selectionnait le
    # decile des jours ou la moyenne des actifs etait la plus basse. Or
    # conditionner sur une SOMME biaise mecaniquement a la BAISSE les
    # correlations entre ses composantes. Le tableau produit montrait des
    # correlations qui DIMINUENT en crise -- l'inverse du phenomene connu.
    # On utilise donc des periodes de crise definies A PRIORI.
    eq = "equity_developed"
    corr_s = None
    print("\n--- CORRELATIONS AUX ACTIONS, PAR EPISODE ---")
    hdr = f"{'classe':<24}{'complet':>9}"
    episodes = []
    for name, a, b in STRESS:
        sub = R.loc[a:b]
        if len(sub) > 60:
            episodes.append((name, sub.corr()))
            hdr += f"{name.split()[0]:>9}"
    print(hdr)
    for k in corr.index:
        if k == eq:
            continue
        line = f"  {k:<22}{corr.loc[eq, k]:>9.2f}"
        for _, cs in episodes:
            line += f"{cs.loc[eq, k]:>9.2f}" if k in cs.index else f"{'-':>9}"
        print(line)
    if episodes:
        corr_s = episodes[-1][1]
        print(f"\n  Episodes couverts par la fenetre : "
              f"{', '.join(n for n, _ in episodes)}")

    # --- portefeuille ---
    w = pd.Series({k: ips.SAA_INDICATIVE[k] for k in R.columns})
    w = w / w.sum()
    pvol = float(np.sqrt(w.to_numpy() @ cov @ w.to_numpy()))

    print("\n" + "=" * 68)
    print("TEST DE L'OBJECTIF, DANS LES DEUX REGIMES D'INFLATION")
    print("=" * 68)
    wd = w.to_dict()
    for label, infl in [("Consensus / cible BCE", INFLATION_BASE),
                        ("Hypothese client (stress)", INFLATION_CLIENT)]:
        er = portfolio_return(wd, infl)
        hurdle = ips.required_gross_return(inflation=infl)
        print(f"\n{label} -- inflation {infl:.1%}")
        print(f"  Rendement brut attendu    {er:>7.2%}")
        print(f"  Seuil requis              {hurdle:>7.2%}")
        print(f"  MARGE                     {er-hurdle:>+7.2%}"
              f"   {'ATTEINT' if er >= hurdle else 'NON ATTEINT'}")
        real_net = er - ips.ANNUAL_COST - infl
        print(f"  Rendement reel net        {real_net:>+7.2%}")

    print(f"\nVolatilite du portefeuille  {pvol:>7.2%}"
          f"   (cible IPS {ips.TARGET_VOL:.1%})")
    saa_long = ROOT / "data" / "saa_risk.csv"
    if saa_long.exists():
        d = pd.read_csv(saa_long)
        ref = d.loc[(d["eq"] - 0.47).abs().idxmin()]
        print(f"  CONTROLE -- meme allocation sur 21,8 ans "
              f"(scripts/validate_saa_risk.py) : vol {ref['vol']:.1%}")
        print(f"  L'ecart tient a la fenetre : {(R.index[-1]-R.index[0]).days/365.25:.1f} ans "
              f"ici, sans 2008 ni 2011. La volatilite mesuree sur fenetre "
              f"recente est SOUS-ESTIMEE.")
        print(f"  Reference retenue pour le budget de risque : "
              f"l'estimation longue.")
    print(f"Drawdown P90 implique       {pvol*ips.DD_TO_VOL_RATIO:>7.2%}"
          f"   (contrainte {ips.MAX_DRAWDOWN:.0%})")

    pd.DataFrame({"vol": vol}).to_csv(ROOT / "data" / "cma_vol.csv")
    corr.to_csv(ROOT / "data" / "cma_corr.csv")
    if corr_s is not None:
        corr_s.to_csv(ROOT / "data" / "cma_corr_stress.csv")
    print("\n-> data/cma_vol.csv, cma_corr.csv, cma_corr_stress.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
