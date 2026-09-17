"""
Etape 6 -- backtest de la strategie.

METHODE ARRETEE A L'ETAPE 1, et ses deux refus.
  - PAS sur les ETF : les supports filtres ESG datent de 2016-2020 et ne
    couvrent aucune crise majeure.
  - PAS sur les series d'indices ESG reconstituees : elles sont retro-calculees,
    la methodologie ayant ete appliquee apres coup. Un indice n'est lance
    qu'une fois qu'il a montre qu'il fonctionnait : backtester dessus flatte
    systematiquement l'ESG.
  - RETENU : indices larges non filtres sur l'historique long, PLUS mesure
    separee de l'ecart de suivi du filtre ESG sur la periode ou il existe
    reellement.

Ce que l'on montre au client : « le comportement de la STRATEGIE sur vingt ans,
reconstitue a partir d'indices larges, frais deduits. L'effet du filtre
ethique, nous le mesurons separement sur la periode ou il existe. »
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                    # noqa: E402
from core.data import get_panel                         # noqa: E402
from core.metrics import load_prices                    # noqa: E402
from core.quality import audit                          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
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

STRATEGY = {"equity_us": 0.138, "equity_dev_exus": 0.092, "equity_emerging": 0.11,
            "infrastructure": 0.09, "govt_bonds": 0.10, "inflation_linked": 0.15,
            "credit_ig": 0.09, "gold": 0.07}
RISKLESS_W = 0.14          # poche A + alternatifs et crypto, modelises sans risque
RISKLESS_YIELD = 0.022

# 60/40 classique, en EUR, pour comparaison
NAIVE = {"equity_us": 0.36, "equity_dev_exus": 0.24, "govt_bonds": 0.40}

ANNUAL_COST = ips.TOTAL_FEES + ips.TAX_DRAG_STRUCTURED     # 0,85 %


def max_dd(v: np.ndarray) -> float:
    return float((1.0 - v / np.maximum.accumulate(v)).max())


def load_returns() -> pd.DataFrame:
    spec = {t: fb for t, fb in PROXY.values()}
    spec["EURUSD=X"] = ("EUR=X",)
    px, _ = get_panel(spec)
    px = px.loc[START:].ffill().dropna()
    fx = -px["EURUSD=X"].pct_change()
    loc = px.pct_change()
    return pd.DataFrame({k: loc[t] + (1 - HEDGE[k]) * fx
                         for k, (t, _) in PROXY.items()}).dropna()


def portfolio(rets: pd.DataFrame, w: dict, riskless: float,
              net: bool = True) -> pd.Series:
    ws = pd.Series(w)
    r = (rets[ws.index] * ws).sum(axis=1) + riskless * RISKLESS_YIELD / 252
    return r - (ANNUAL_COST / 252 if net else 0.0)


def describe(r: pd.Series, label: str) -> dict:
    v = (1 + r).cumprod()
    years = (r.index[-1] - r.index[0]).days / 365.25
    cagr = v.iloc[-1] ** (1 / years) - 1
    vol = r.std() * np.sqrt(252)
    return {"strategie": label, "CAGR": cagr, "vol": vol,
            "Sharpe": (cagr - RISKLESS_YIELD) / vol,
            "max_DD": max_dd(v.to_numpy()),
            "Calmar": cagr / max_dd(v.to_numpy())}


def main() -> int:
    print("Chargement :")
    rets = load_returns()
    strat = portfolio(rets, STRATEGY, RISKLESS_W)
    naive = portfolio(rets, NAIVE, 0.0)
    years = (strat.index[-1] - strat.index[0]).days / 365.25
    print(f"\nPeriode : {strat.index[0].date()} -> {strat.index[-1].date()} "
          f"({years:.1f} ans)")
    print(f"Frais et fiscalite deduits : {ANNUAL_COST:.2%} par an\n")

    print("=" * 72)
    print("1. PERFORMANCE, NETTE DE FRAIS ET D'IMPOTS")
    print("=" * 72)
    rows = [describe(strat, "Strategie Lauren"),
            describe(naive, "60/40 classique (EUR)")]
    df = pd.DataFrame(rows)
    print(f"\n{'strategie':<26}{'CAGR':>8}{'vol':>8}{'Sharpe':>8}"
          f"{'max DD':>9}{'Calmar':>8}")
    for _, x in df.iterrows():
        print(f"  {x['strategie']:<24}{x['CAGR']:>8.2%}{x['vol']:>8.1%}"
              f"{x['Sharpe']:>8.2f}{x['max_DD']:>9.1%}{x['Calmar']:>8.2f}")

    print("\n  Lecture : la strategie rend moins que le 60/40 en absolu, mais")
    print("  avec un drawdown nettement moindre. Le Calmar -- rendement par")
    print("  unite de perte maximale -- est la bonne mesure pour un mandat")
    print("  dont la contrainte est une perte, pas une volatilite.")

    # ------------------------------------------------------------------ 2
    print("\n" + "=" * 72)
    print("2. L'OBJECTIF EST-IL ATTEINT ? FENETRES GLISSANTES DE 10 ANS")
    print("=" * 72)
    v = (1 + strat).cumprod()
    win = 2520
    roll = np.array([(v.iloc[i + win] / v.iloc[i]) ** (252 / win) - 1
                     for i in range(len(v) - win)])
    print(f"\n  {len(roll)} fenetres de 10 ans observees\n")
    for q in [5, 25, 50, 75, 95]:
        print(f"  centile {q:>2}        {np.percentile(roll, q):>7.2%}")
    print(f"  pire fenetre       {roll.min():>7.2%}")
    print(f"  meilleure          {roll.max():>7.2%}")
    for h, lab in [(0.02, "inflation constatee ~2 %"),
                   (0.04, "hypothese client 4 %")]:
        print(f"\n  P(rendement net > {h:.0%})  {(roll > h).mean():>7.1%}"
              f"   {lab}")

    # ------------------------------------------------------------------ 3
    print("\n" + "=" * 72)
    print("3. COUT DU FILTRE ESG -- MESURE NON CONCLUANTE")
    print("=" * 72)
    print("""
  Objectif : mesurer ce que coute le filtre ESG, sur la periode ou il existe
  reellement, plutot que de le backtester sur des indices retro-calcules.

  RESULTAT : la mesure n'est pas fiable avec les donnees dont nous disposons.
  Cinq supports censes suivre des indices monde tres proches donnent :

      SAWD.L   MSCI World Screened        +1,03 %/an     ecart de suivi 4,7 %
      SUSW.L   MSCI World ESG Screened    +0,55 %/an                    8,7 %
      SUWS.L   MSCI World SRI             -0,33 %/an                    5,6 %
      XZW0.DE  MSCI World ESG             -2,16 %/an                    7,7 %

  Une dispersion de -2,2 % a +1,0 % entre des produits aussi proches n'est
  pas un signal, c'est du bruit de mesure. Trois causes identifiees :

    1. DEVISES. Les lignes londoniennes sont cotees en dollars, les
       allemandes en euros. Comparer sans convertir fabriquait un ecart de
       suivi de 19 %. Corrige, mais il faut le savoir ticker par ticker.
    2. COTATIONS NON SYNCHRONES. Londres ferme a 16h30, New York a 22h00
       CET. Meme en mensuel, les cours de fin de mois ne refletent pas la
       meme fenetre d'information.
    3. AJUSTEMENT DES DIVIDENDES. Rien ne garantit que yfinance traite de
       la meme facon un fonds capitalisant europeen et un fonds distribuant
       americain.

  CE QU'IL FAUT FAIRE AVANT LE PITCH : prendre les rendements OFFICIELS des
  indices sur les fiches MSCI -- meme devise, meme methode, meme date. Le
  cout du filtre ESG est une question a trancher sur donnees d'indices, pas
  sur des prix d'ETF cotes sur trois places differentes.

  Ne PAS presenter de chiffre de cout ESG tant que cette verification n'est
  pas faite. Un chiffre faux sur ce point serait releve immediatement : c'est
  une donnee publique que n'importe qui peut recouper.""")

    pd.DataFrame({"strategie": strat, "naive_60_40": naive}).to_csv(
        ROOT / "data" / "backtest_series.csv")
    print("\n-> data/backtest_series.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
