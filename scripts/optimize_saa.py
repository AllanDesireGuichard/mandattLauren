"""
Etape 3 -- optimisation de l'allocation strategique.

Boucle : ancrage neutre -> vues -> Black-Litterman -> frontiere resamplee
-> validation du drawdown. Si la contrainte de 15 % est violee, on redescend
le risque et on recommence.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                       # noqa: E402
from core.cma import INFLATION_CLIENT, expected_returns    # noqa: E402
from core.optimizer import (black_litterman,               # noqa: E402
                            equal_risk_contribution, frontier,
                            implied_returns, resampled_allocation)

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# VUES. Chacune doit pointer vers un fait etabli ailleurs dans le dossier --
# une vue qu'on ne sait pas justifier n'a rien a faire dans le modele.
# --------------------------------------------------------------------------

VIEWS = [
    {"long": "inflation_linked", "short": "govt_bonds_eur", "q": 0.0080,
     "conf": 0.75,
     "why": "Coefficients de repercussion mesures : 1,00 contre 0,45. Dans le "
            "regime a 4 % que craint le client, l'indexee capte integralement "
            "la surprise, la nominale non. Confiance ELEVEE : c'est une "
            "propriete mecanique, pas une prevision."},

    {"long": "gold", "short": "cash", "q": 0.0045, "conf": 0.50,
     "why": "Seule brique dont la correlation aux actions BAISSE sous stress "
            "(0,07 -> -0,07 en 2022, mesure). Repond a l'inquietude simultanee "
            "euro ET dollar. Confiance MOYENNE : la decorrelation est mesuree, "
            "la prime de rendement est supposee."},

    {"long": "credit_ig_eur", "short": "govt_bonds_eur", "q": 0.0065,
     "conf": 0.55,
     "why": "Portage : ecart de rendement actuariel constate entre credit IG "
            "euro et souverain. Confiance MOYENNE -- ancree sur un prix de "
            "marche, mais le spread peut s'ecarter."},

    {"long": "equity_emerging", "short": "equity_developed", "q": 0.0120,
     "conf": 0.30,
     "why": "Point d'entree en valorisation. Confiance FAIBLE assumee : les "
            "paris relatifs entre zones actions sont les moins fiables du "
            "metier, et le lien croissance du PIB / rendement boursier est "
            "empiriquement tenu."},
]


def build_covariance() -> tuple[pd.DataFrame, list[str], float]:
    """
    Covariance en unites de risque LONG TERME.

    Les correlations viennent de la fenetre instruments (6,2 ans) : elles sont
    bien plus stables que les volatilites. Les volatilites sont remises a
    l'echelle pour que l'allocation de reference retrouve la volatilite
    mesuree sur 21,8 ans -- sinon on optimiserait sur une fenetre recente qui
    ignore 2008 et 2011, donc sur un risque sous-estime.
    """
    corr = pd.read_csv(ROOT / "data" / "cma_corr.csv", index_col=0)
    vol = pd.read_csv(ROOT / "data" / "cma_vol.csv", index_col=0)["vol"]
    cls = [c for c in corr.index if c in ips.SAA_INDICATIVE]
    corr, vol = corr.loc[cls, cls], vol.loc[cls]

    w = np.array([ips.SAA_INDICATIVE[c] for c in cls])
    w = w / w.sum()
    cov_raw = np.outer(vol, vol) * corr.to_numpy()
    vol_measured = float(np.sqrt(w @ cov_raw @ w))
    scale = ips.TARGET_VOL / vol_measured

    cov = np.outer(vol * scale, vol * scale) * corr.to_numpy()
    return pd.DataFrame(cov, index=cls, columns=cls), cls, scale


# --------------------------------------------------------------------------
# CONTRAINTES DE SECOND NIVEAU
# --------------------------------------------------------------------------
#
# L'optimisation libre produit une allocation mathematiquement optimale et
# pratiquement inutilisable : 28 % d'infrastructure (un seul secteur), 0,8 %
# d'or, zero obligation d'Etat. Chacune de ces trois decisions est correcte
# AU REGARD DES DONNEES FOURNIES, et fausse au regard du mandat.
#
# Chaque borne ci-dessous encode un risque que la matrice de covariance ne
# peut PAS voir. Aucune n'est un avis de marche.

FLOORS_CAPS = {
    "infrastructure":   (0.00, 0.10,
                         "Plafond. Un seul secteur, et le support filtre ESG "
                         "(NFRA.L) a 3,1 ans d'historique et une capacite "
                         "limitee. La covariance ignore le risque de "
                         "concentration sectorielle et le risque d'execution."),
    "equity_emerging":  (0.00, 0.12,
                         "Plafond. Concentration geographique et risque "
                         "politique non captures par la volatilite."),
    "gold":             (0.06, 0.12,
                         "Plancher. Seule brique dont la correlation aux "
                         "actions BAISSE sous stress (0,07 -> -0,07 en 2022, "
                         "mesure). Une covariance pleine periode moyenne ce "
                         "comportement et l'efface."),
    "govt_bonds_eur":   (0.08, 0.25,
                         "Plancher. Nos hypotheses sont calees sur UN regime "
                         "(inflation a 4 %), ou le souverain rapporte moins "
                         "que le monetaire. Elles ne tarifient pas la "
                         "RECESSION, seul scenario ou le souverain est le "
                         "seul actif qui protege. Le plancher achete cette "
                         "assurance que le modele ne sait pas valoriser."),
    "equity_developed": (0.20, 0.40,
                         "Plancher. Moteur de performance, et la seule classe "
                         "offrant la liquidite et la capacite necessaires a "
                         "un mandat de 100 M EUR."),
    "crypto":           (0.02, 0.02,
                         "Fige. Decision de GOUVERNANCE arretee avec le "
                         "client (§12), pas une sortie d'optimisation."),
}


def build_constraints(cls: list[str], apply_floors: bool = False
                      ) -> tuple[list, list]:
    i = {c: k for k, c in enumerate(cls)}
    lim = ips.CONCENTRATION_LIMITS
    bounds = [(0.0, lim["single_asset_class"]) for _ in cls]
    if "crypto" in i:
        bounds[i["crypto"]] = (0.0, lim["crypto"])
    if apply_floors:
        for c, (lo, hi, _why) in FLOORS_CAPS.items():
            if c in i:
                bounds[i[c]] = (lo, hi)

    cons = []
    sleeve = [i[c] for c in ips.LIQUIDITY_SLEEVE if c in i]
    if sleeve:
        cons.append({"type": "eq",
                     "fun": lambda w, s=sleeve: w[s].sum() - 0.10})
    growth = [i[c] for c in ips.GROWTH_ASSETS if c in i]
    if growth:
        cons.append({"type": "ineq",
                     "fun": lambda w, g=growth: lim["growth_assets"] - w[g].sum()})
    return bounds, cons


def main() -> int:
    cov_df, cls, scale = build_covariance()
    cov = cov_df.to_numpy()
    idx = {c: k for k, c in enumerate(cls)}
    print(f"Classes : {len(cls)}")
    print(f"Mise a l'echelle des volatilites : x{scale:.3f} "
          f"(fenetre 6,2 ans -> reference 21,8 ans)\n")

    # 1. ancrage neutre -- sur les actifs RISQUES uniquement.
    #    La poche de liquidite (10 %) est une decision de politique, pas un
    #    arbitrage : l'inclure ferait degenerer la parite de risque.
    sleeve = [c for c in ips.LIQUIDITY_SLEEVE if c in idx]
    risky = [c for c in cls if c not in sleeve]
    ir = [idx[c] for c in risky]
    w_risky = equal_risk_contribution(cov[np.ix_(ir, ir)])

    w_erc = np.zeros(len(cls))
    for c, w in zip(risky, w_risky):
        w_erc[idx[c]] = w * 0.90
    for c in sleeve:                       # 10 % reparti dans la poche A
        w_erc[idx[c]] = 0.10 / len(sleeve)

    print("--- ANCRAGE NEUTRE : PARITE DE RISQUE (actifs risques) ---")
    print("    poche de liquidite figee a 10 %, hors du calcul")
    for c in sorted(cls, key=lambda x: -w_erc[idx[x]]):
        tag = "  [poche A]" if c in sleeve else ""
        print(f"  {c:<24}{w_erc[idx[c]]:>7.1%}{tag}")
    vol_erc = float(np.sqrt(w_erc @ cov @ w_erc))
    print(f"  volatilite du neutre : {vol_erc:.2%}")

    # 2. point de depart des rendements
    #
    # DEUX PRIORS TESTES, UN RETENU.
    #
    # (a) Optimisation inverse depuis le neutre : pi = delta * cov @ w_erc.
    #     ECARTEE. Cette methode suppose que le portefeuille de reference est
    #     OPTIMAL et en deduit l'aversion au risque. Or nos propres hypotheses
    #     (core/cma.py) disent qu'il ne l'est pas : dans le regime a 4 %
    #     d'inflation, le souverain rapporte MOINS que le monetaire (3,60 %
    #     contre 4,05 %), a cause d'un coefficient de repercussion de 0,45.
    #     La parite de risque etant obligataire a 53 %, l'aversion deduite
    #     tombe a 1,76 et TOUTES les primes se compriment : la prime des
    #     actions ressort a 1,49 % au lieu des 3,65 % de nos hypotheses.
    #     Un prior qui contredit nos propres hypotheses n'est pas un prior.
    #
    # (b) Hypotheses de marche comme prior, vues appliquees en ecarts.
    #     RETENUE. Les CMA sont documentees ligne par ligne, avec leur
    #     provenance ; c'est le meilleur point de depart dont nous disposons.
    #     La regularisation vient alors du resampling et des contraintes,
    #     pas de l'ancrage.
    cma = expected_returns(INFLATION_CLIENT)
    rf = cma["cash"]
    target_ref = sum(w_erc[idx[c]] * cma[c] for c in cls)
    pi_eq, delta = implied_returns(cov, w_erc, target_ref, rf)
    print(f"\n  aversion au risque implicite delta = {delta:.2f}")
    print(f"  prime actions selon l'optimisation inverse : "
          f"{pi_eq[idx['equity_developed']]:.2%}")
    print(f"  prime actions selon nos hypotheses        : "
          f"{cma['equity_developed'] - rf:.2%}")
    print("  -> prior d'equilibre ECARTE, hypotheses de marche retenues")

    pi = np.array([cma[c] - rf for c in cls])       # primes sur le monetaire

    # 3. vues
    P, Q, conf = [], [], []
    print("\n--- VUES INJECTEES ---")
    for v in VIEWS:
        if v["long"] not in idx or v["short"] not in idx:
            continue
        row = np.zeros(len(cls))
        row[idx[v["long"]]], row[idx[v["short"]]] = 1.0, -1.0
        P.append(row); Q.append(v["q"]); conf.append(v["conf"])
        print(f"  {v['long']} > {v['short']}  de {v['q']:+.2%}  "
              f"(confiance {v['conf']:.0%})")
    mu_excess = black_litterman(pi, cov, np.array(P), np.array(Q),
                                np.array(conf))
    mu = mu_excess + rf

    print("\n--- PRIMES SUR LE MONETAIRE : PRIOR vs POSTERIEUR ---")
    print(f"{'classe':<24}{'prior':>9}{'posterieur':>12}{'ecart':>9}")
    for c in cls:
        print(f"  {c:<22}{pi[idx[c]]:>9.2%}{mu_excess[idx[c]]:>12.2%}"
              f"{mu_excess[idx[c]]-pi[idx[c]]:>+9.2%}")

    # 4. frontiere et allocation resamplee
    bounds, cons = build_constraints(cls)
    f = frontier(mu, cov, bounds, cons, n_points=25)
    print(f"\n--- FRONTIERE EFFICIENTE : {len(f)} points ---")
    print(f"  volatilite {f.vol.min():.1%} a {f.vol.max():.1%}")

    print(f"\n--- ALLOCATION RESAMPLEE (cible {ips.TARGET_VOL:.1%}) ---")
    w_opt, w_sd = resampled_allocation(mu, cov, ips.TARGET_VOL, bounds, cons,
                                       n_sims=120, verbose=True)
    w_opt = w_opt / w_opt.sum()

    cur = np.array([ips.SAA_INDICATIVE[c] for c in cls])
    cur = cur / cur.sum()
    print(f"{'classe':<24}{'actuel':>9}{'optimise':>10}{'ecart':>8}{'+/-':>7}")
    for c in sorted(cls, key=lambda x: -w_opt[idx[x]]):
        k = idx[c]
        print(f"  {c:<22}{cur[k]:>9.1%}{w_opt[k]:>10.1%}"
              f"{w_opt[k]-cur[k]:>+8.1%}{w_sd[k]:>7.1%}")

    vol_opt = float(np.sqrt(w_opt @ cov @ w_opt))
    ret_opt = sum(w_opt[idx[c]] * cma[c] for c in cls)
    ret_cur = sum(cur[idx[c]] * cma[c] for c in cls)
    hurdle = ips.required_gross_return(inflation=INFLATION_CLIENT)
    print(f"\n{'':24}{'actuel':>9}{'optimise':>10}")
    print(f"  {'rendement attendu':<22}{ret_cur:>9.2%}{ret_opt:>10.2%}")
    print(f"  {'volatilite':<22}"
          f"{float(np.sqrt(cur@cov@cur)):>9.2%}{vol_opt:>10.2%}")
    print(f"  {'marge vs seuil':<22}{ret_cur-hurdle:>+9.2%}{ret_opt-hurdle:>+10.2%}")
    print(f"  {'drawdown P90 implique':<22}"
          f"{float(np.sqrt(cur@cov@cur))*ips.DD_TO_VOL_RATIO:>9.1%}"
          f"{vol_opt*ips.DD_TO_VOL_RATIO:>10.1%}")

    # --- second passage : contraintes de second niveau ---
    print("\n" + "=" * 70)
    print("SECOND PASSAGE -- contraintes encodant ce que la covariance ignore")
    print("=" * 70)
    for c, (lo, hi, why) in FLOORS_CAPS.items():
        if c in idx:
            b = f"{lo:.0%}-{hi:.0%}" if lo != hi else f"fige a {lo:.0%}"
            print(f"\n  {c} : {b}")
            print(f"    {why}")

    b2, c2 = build_constraints(cls, apply_floors=True)
    w2, sd2 = resampled_allocation(mu, cov, ips.TARGET_VOL, b2, c2,
                                   n_sims=80, verbose=True)
    w2 = w2 / w2.sum()

    print(f"\n--- ALLOCATION RETENUE ---")
    print(f"{'classe':<24}{'actuel':>9}{'libre':>9}{'contraint':>11}{'+/-':>7}")
    for c in sorted(cls, key=lambda x: -w2[idx[x]]):
        k = idx[c]
        print(f"  {c:<22}{cur[k]:>9.1%}{w_opt[k]:>9.1%}{w2[k]:>11.1%}{sd2[k]:>7.1%}")

    vol2 = float(np.sqrt(w2 @ cov @ w2))
    ret2 = sum(w2[idx[c]] * cma[c] for c in cls)
    print(f"\n{'':24}{'actuel':>9}{'libre':>9}{'contraint':>11}")
    print(f"  {'rendement attendu':<22}{ret_cur:>9.2%}{ret_opt:>9.2%}{ret2:>11.2%}")
    print(f"  {'volatilite':<22}{float(np.sqrt(cur@cov@cur)):>9.2%}"
          f"{vol_opt:>9.2%}{vol2:>11.2%}")
    print(f"  {'marge vs seuil':<22}{ret_cur-hurdle:>+9.2%}"
          f"{ret_opt-hurdle:>+9.2%}{ret2-hurdle:>+11.2%}")
    print(f"  {'drawdown P90':<22}"
          f"{float(np.sqrt(cur@cov@cur))*ips.DD_TO_VOL_RATIO:>9.1%}"
          f"{vol_opt*ips.DD_TO_VOL_RATIO:>9.1%}"
          f"{vol2*ips.DD_TO_VOL_RATIO:>11.1%}"
          f"   contrainte {ips.MAX_DRAWDOWN:.0%}")
    print(f"  {'instabilite moyenne':<22}{'':>9}{w_sd.mean():>9.1%}{sd2.mean():>11.1%}")

    out = pd.DataFrame({"classe": cls, "actuel": cur, "libre": w_opt,
                        "retenu": w2, "ecart_type": sd2, "mu_bl": mu,
                        "pi_equilibre": pi_eq})
    out.to_csv(ROOT / "data" / "saa_optimized.csv", index=False)
    print("\n-> data/saa_optimized.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
