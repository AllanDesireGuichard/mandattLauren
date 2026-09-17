"""
Univers investissable du mandat Lauren.

Filtres appliques (IPS §5.2 et §5.3) :
  - UCITS / ETC europeen uniquement (resident francais retail, PRIIPs)
  - indices filtres ESG sur les classes ou ils existent (cf. core/esg.py)
  - supports CAPITALISANTS hors assurance-vie (report d'imposition)
  - domiciliation IRLANDAISE privilegiee sur l'exposition actions US
    (retenue a la source 15 % vs 30 % -- cf. archive/core/tax.py)

AVERTISSEMENT SUR LES DONNEES
  Les TER sont INDICATIFS et doivent etre verifies sur les documents
  d'information cle (DIC/KID) avant toute mise en oeuvre. Ils ne sont
  volontairement PAS repris de state/etf_universe.csv d'equitydb2, dont la
  colonne expense_ratio melange les conventions decimale et pourcentage
  (ex. IBGS.L a 0.2 = 20 %).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.ips import SAA_INDICATIVE

UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "data" / "universe.csv"
CANDIDATES_PATH = UNIVERSE_PATH.parent / "universe_candidates.csv"
STATS_PATH = UNIVERSE_PATH.parent / "instrument_stats.csv"


def load_universe() -> pd.DataFrame:
    """Univers retenu : principal + suppleants par classe d'actifs."""
    df = pd.read_csv(UNIVERSE_PATH)
    df["ticker"] = df["ticker"].str.strip().str.upper()
    return df


def load_candidates() -> pd.DataFrame:
    """Les 226 candidats avant selection."""
    return pd.read_csv(CANDIDATES_PATH)


def primary_instruments() -> pd.DataFrame:
    """Un support par classe d'actifs : l'implementation de reference."""
    df = load_universe()
    return df[df["role"] == "primary"].set_index("saa_class")


# --------------------------------------------------------------------------
# Trous identifies — a combler hors ETF cotes
# --------------------------------------------------------------------------

GAPS = {
    "trend_following": {
        "weight": 0.0,
        "issue": "LA BRIQUE 'SUIVI DE TENDANCE' N'EST PAS ACHETABLE EN ETF "
                 "UCITS. Verification faite sur l'univers de 226 candidats : "
                 "CTA.L n'est pas un fonds de tendance mais CT Automotive "
                 "Group plc (un equipementier, volatilite 55 %) ; DBMF.L "
                 "(iMGP DBi Managed Futures) n'a que 1,4 an d'historique.",
        "resolution": "Deux options. (a) La poche alternatifs est implementee "
                      "en matieres premieres diversifiees -- XDBC.DE, 18,7 ans "
                      "-- qui portent une partie du beta inflation mais PAS la "
                      "convexite du trend. (b) Un fonds UCITS de managed "
                      "futures loge dans le contrat luxembourgeois, hors "
                      "univers ETF. L'option (b) renforce l'argument du §10 : "
                      "le contrat donne acces a ce que le CTO ne permet pas.",
        "impact_pitch": "Le §7 de l'argumentaire cite le suivi de tendance "
                        "parmi les cinq briques anti-60/40. A reformuler : "
                        "soit on retire la brique, soit on assume qu'elle "
                        "passe par un fonds et non un ETF.",
    },
    "infrastructure": {
        "weight": 0.07,
        "issue": "NFRA.L (Rize Global Sustainable Infrastructure) est le seul "
                 "support filtre ESG de la classe, mais il n'a que 3,1 ans "
                 "d'historique.",
        "resolution": "Retenu comme support d'execution ; le backtest utilise "
                      "XDWU.DE (10,4 ans, non filtre) comme proxy de la classe. "
                      "Ecart de suivi a mesurer sur la periode commune.",
        "impact_pitch": "Aucun si l'on presente bien le backtest comme portant "
                        "sur la STRATEGIE et non sur les fonds (cf. §11 de "
                        "archive/docs/02_ips.md).",
    },
}

# Constats de verification, a garder en memoire
TICKER_TRAPS = {
    "CTA.L":   "CT Automotive Group plc -- PAS un fonds de tendance",
    "XZEC.DE": "Xtrackers Stoxx European Market Leaders -- actions, PAS du credit",
    "EEDS.L":  "iShares MSCI USA CTB -- actions, PAS du credit",
}

IMPLEMENTATION_NOTES = {
    "equity_developed": "Arbitrage a trancher : un support monde unique "
                        "(SUSW.L) ou un assemblage regional (US + Europe + "
                        "Japon). L'assemblage coute plus cher en frais de "
                        "transaction mais permet de piloter l'exposition "
                        "regionale — pertinent vu l'inquietude du client sur "
                        "les Etats-Unis ET l'Europe.",
    "equity_emerging": "Seul SUSM.L couvre le SRI emergent. Pas de version "
                       "ESG Screened equivalente : on accepte ici la "
                       "contrainte SRI plus stricte, faute d'alternative.",
    "gold": "ETC et non UCITS (titre de dette adosse a l'or physique). "
            "Accessible au retail francais, KID disponible. Non couvert en "
            "change par construction (IPS §6.4). Verifier l'allocation "
            "physique et le depositaire.",
    "cash": "Poche A. Echelonner les maturites sur le calendrier de "
            "decaissement plutot qu'un support unique. Le fonds monetaire "
            "sert de tampon, les obligations 1-3 ans portent le rendement.",
    "crypto": "ETP, hors UCITS. Acces direct possible mais l'implementation "
              "elegante passe par un compartiment du contrat luxembourgeois "
              "(FAS), ce qui isole aussi la ligne dans la poche transmission.",
}


if __name__ == "__main__":
    df = load_universe()
    print(f"Univers : {len(df)} supports\n")
    print(df.groupby("asset_class").agg(
        n=("ticker", "size"),
        ter_min=("ter", "min"),
        primary=("role", lambda s: (s == "primary").sum()),
    ).to_string())

    print("\n--- Couverture vs allocation strategique ---")
    covered = set(df[df.status == "candidate"].asset_class)
    for ac, w in sorted(SAA_INDICATIVE.items(), key=lambda kv: -kv[1]):
        flag = "OK " if ac in covered else "GAP"
        print(f"  {flag}  {ac:<20} {w:.0%}")

    gap_weight = sum(g["weight"] for g in GAPS.values())
    print(f"\nPoids total des classes a trou : {gap_weight:.0%}")
    for ac, g in GAPS.items():
        print(f"\n  [{g['priority'].split(' ')[0].upper()}] {ac} ({g['weight']:.0%})")
        print(f"    {g['issue']}")

    dist = df[(df.distribution == "dist")]
    if len(dist):
        print(f"\nATTENTION — supports distribuants (a eviter hors AV) :")
        print(dist[["ticker", "name", "asset_class"]].to_string(index=False))


# --------------------------------------------------------------------------
# Constat de validation  (scripts/validate_universe.py, 2026-09-17)
# --------------------------------------------------------------------------

BACKTEST_NOTE = """\
CONSEQUENCE METHODOLOGIQUE MAJEURE POUR L'ETAPE 7 (BACKTEST).

Les ETF filtres ESG ont ete lances entre 2016 et 2020 :

    SUSW.L  MSCI World ESG Screened   octobre 2017   ->  8,9 ans
    SUWS.L  MSCI World SRI            octobre 2017   ->  8,9 ans
    SUSM.L  MSCI EM SRI               juillet 2016   -> 10,2 ans
    EUNA.DE Core Euro Govt            novembre 2017  ->  8,8 ans

Aucun ne couvre 2008, et la plupart ne couvrent pas 2011-2012. Or ce sont
precisement les episodes sur lesquels la contrainte de drawdown doit etre
testee.

=> LE BACKTEST NE PEUT PAS ETRE CONDUIT SUR LES ETF. Il doit l'etre sur les
   SERIES D'INDICES (MSCI World SRI existe en historique reconstitue depuis
   2007, Bloomberg Euro Agg depuis bien avant), en retranchant le TER pour
   simuler l'instrument.

C'est la pratique institutionnelle correcte, et c'est aussi un point a
assumer explicitement devant le client : lui presenter un backtest 2008 sur
un fonds cree en 2017 serait malhonnete. La formulation a retenir :

    "Nous vous montrons le comportement de la STRATEGIE sur vingt ans,
     reconstitue a partir des indices, frais deduits. Les fonds qui la
     mettent en oeuvre sont plus recents : nous vous montrons separement
     leur ecart de suivi reel depuis leur lancement."

Deux tickers Amundi (ex-Lyxor) ne repondent plus sur yfinance apres la
fusion Lyxor/Amundi : LYXIB.PA et SEUH.PA. Aucun des deux n'etait un support
principal (STHE.L et IBGS.L couvrent les memes expositions avec 12,9 et
18,7 ans d'historique). A resourcer si on veut un second candidat.
"""
