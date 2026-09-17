"""
Optimisation d'allocation strategique.

TROIS BRIQUES, et une raison pour chacune.

1. BLACK-LITTERMAN -- parce qu'une optimisation nourrie directement de
   previsions produit des portefeuilles absurdes (80 % sur une ligne). BL part
   d'un point neutre et n'en devie qu'a proportion de la confiance qu'on
   accorde a chaque vue.

   ANCRAGE NEUTRE : les poids de marche sont la reference habituelle, mais ils
   n'ont pas de sens ici -- il n'existe pas de "capitalisation boursiere" de
   l'or ou du monetaire comparable a celle des actions. On retient donc la
   PARITE DE RISQUE (equal risk contribution) : un portefeuille ou chaque
   classe contribue autant au risque total. C'est un neutre defendable, deduit
   des donnees, et qui ne suppose aucune vue.

   Les rendements de core/cma.py deviennent alors des VUES, avec une confiance
   explicite -- et non le point de depart. C'est la difference entre "voici ma
   prevision" et "voici de combien je m'ecarte du neutre, et pourquoi".

2. RESAMPLING (Michaud) -- parce que l'optimisation moyenne-variance est
   instable : deplacez une prevision de 20 pb et l'allocation bascule. On
   optimise des centaines de fois sur des hypotheses perturbees et on moyenne.

3. CONTRAINTES -- celles de l'IPS §5.5, plus la poche liquidite figee a 10 %.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

TAU = 0.05          # incertitude sur les rendements d'equilibre


# --------------------------------------------------------------------------
# Ancrage neutre : parite de risque
# --------------------------------------------------------------------------

def equal_risk_contribution(cov: np.ndarray) -> np.ndarray:
    """
    Poids ou chaque actif contribue egalement au risque total.

    ATTENTION -- A N'APPLIQUER QU'AUX ACTIFS RISQUES.
    Inclure le monetaire fait DEGENERER la parite de risque : pour egaliser
    les contributions, un actif a 0,4 % de volatilite doit peser enormement.
    Constate ici : 82 % de monetaire, et un "neutre" a 0,99 % de volatilite
    qui n'est pas un portefeuille multi-actifs mais un fonds monetaire. Les
    rendements d'equilibre qui en decoulaient etaient absurdes (actions a
    1,2 %, crypto a 3,3 %).

    La poche de liquidite est une decision de POLITIQUE (IPS §6.1), pas un
    arbitrage d'investissement : elle est figee a 10 % en dehors de ce calcul.
    """
    n = len(cov)

    def obj(w):
        pv = float(np.sqrt(w @ cov @ w))
        mrc = cov @ w / pv                 # contribution marginale
        rc = w * mrc                       # contribution au risque
        return float(((rc - rc.mean()) ** 2).sum()) * 1e4

    res = minimize(obj, np.full(n, 1 / n), method="SLSQP",
                   bounds=[(1e-4, 1.0)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"maxiter": 500, "ftol": 1e-12})
    return res.x / res.x.sum()


def implied_returns(cov: np.ndarray, w_ref: np.ndarray,
                    target_return: float, rf: float) -> tuple[np.ndarray, float]:
    """
    Rendements d'equilibre par optimisation inverse : pi = delta * cov @ w_ref.

    delta (aversion au risque) est calibre pour que le portefeuille neutre
    degage `target_return`.
    """
    var = float(w_ref @ cov @ w_ref)
    delta = (target_return - rf) / var
    return delta * cov @ w_ref, delta


# --------------------------------------------------------------------------
# Black-Litterman
# --------------------------------------------------------------------------

def black_litterman(pi: np.ndarray, cov: np.ndarray, P: np.ndarray,
                    Q: np.ndarray, confidence: np.ndarray,
                    tau: float = TAU) -> np.ndarray:
    """
    Rendements posterieurs.

    P : matrice des vues (une ligne par vue, +1/-1 sur les actifs concernes)
    Q : ampleur de chaque vue
    confidence : 0 a 1. Plus c'est eleve, plus la vue pese.
    """
    tau_cov = tau * cov
    # Omega : incertitude de chaque vue, proportionnelle a sa variance propre
    view_var = np.diag(P @ tau_cov @ P.T)
    omega = np.diag(view_var / np.clip(confidence, 1e-6, None))

    inv_tau_cov = np.linalg.inv(tau_cov)
    inv_omega = np.linalg.inv(omega)
    A = inv_tau_cov + P.T @ inv_omega @ P
    b = inv_tau_cov @ pi + P.T @ inv_omega @ Q
    return np.linalg.solve(A, b)


# --------------------------------------------------------------------------
# Optimisation sous contraintes
# --------------------------------------------------------------------------

def min_variance_for_return(mu: np.ndarray, cov: np.ndarray,
                            target: float, bounds: list[tuple[float, float]],
                            extra_constraints: list[dict]) -> np.ndarray | None:
    n = len(mu)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w, t=target: float(mu @ w) - t},
            *extra_constraints]
    res = minimize(lambda w: float(w @ cov @ w), np.full(n, 1 / n),
                   method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 800, "ftol": 1e-12})
    return res.x if res.success else None


def max_return_portfolio(mu: np.ndarray, bounds, extra_constraints) -> float:
    """
    Rendement du portefeuille le plus dynamique ATTEIGNABLE sous contraintes.

    Necessaire pour borner correctement la frontiere : une troncature
    arbitraire de la plage de rendements (ce que faisait la premiere version)
    elimine par construction les portefeuilles les plus dynamiques -- la
    frontiere plafonnait a 7,4 % de volatilite alors que la cible du mandat
    est 9,9 %, et le resampling ne pouvait jamais l'atteindre.
    """
    n = len(mu)
    res = minimize(lambda w: -float(mu @ w), np.full(n, 1 / n), method="SLSQP",
                   bounds=bounds,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1},
                                *extra_constraints],
                   options={"maxiter": 500, "ftol": 1e-12})
    return float(mu @ res.x) if res.success else float(mu.max())


def min_variance_portfolio(mu, cov, bounds, extra_constraints) -> float:
    n = len(mu)
    res = minimize(lambda w: float(w @ cov @ w), np.full(n, 1 / n),
                   method="SLSQP", bounds=bounds,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1},
                                *extra_constraints],
                   options={"maxiter": 500, "ftol": 1e-12})
    return float(mu @ res.x) if res.success else float(mu.min())


def frontier(mu: np.ndarray, cov: np.ndarray,
             bounds: list[tuple[float, float]],
             extra_constraints: list[dict],
             n_points: int = 25) -> pd.DataFrame:
    lo = min_variance_portfolio(mu, cov, bounds, extra_constraints)
    hi = max_return_portfolio(mu, bounds, extra_constraints)
    rows = []
    for t in np.linspace(lo, hi, n_points):
        w = min_variance_for_return(mu, cov, t, bounds, extra_constraints)
        if w is None:
            continue
        rows.append({"ret": float(mu @ w), "vol": float(np.sqrt(w @ cov @ w)),
                     "w": w})
    return pd.DataFrame(rows)


def resampled_allocation(mu: np.ndarray, cov: np.ndarray,
                         target_vol: float,
                         bounds: list[tuple[float, float]],
                         extra_constraints: list[dict],
                         n_sims: int = 300, n_obs: int = 2520,
                         seed: int = 42, verbose: bool = False
                         ) -> tuple[np.ndarray, np.ndarray]:
    """
    Allocation resamplee (Michaud).

    A chaque tirage, on perturbe les rendements attendus selon leur erreur
    d'estimation (ecart-type / racine(n_obs)), on reconstruit la frontiere, et
    on retient l'allocation la plus proche de la volatilite cible. La moyenne
    de ces allocations est nettement plus stable et plus diversifiee que
    l'optimum unique.

    Retourne (poids moyens, ecart-type des poids) -- le second quantifie la
    fragilite de chaque ligne.
    """
    rng = np.random.default_rng(seed)
    se = np.sqrt(np.diag(cov) / n_obs)
    keep = []
    for i in range(n_sims):
        mu_s = mu + rng.normal(0, se)
        f = frontier(mu_s, cov, bounds, extra_constraints, n_points=9)
        if f.empty:
            continue
        keep.append(f.loc[(f.vol - target_vol).abs().idxmin(), "w"])
        if verbose and (i + 1) % 20 == 0:
            print(f"    resampling {i+1}/{n_sims}", flush=True)
    W = np.array(keep)
    return W.mean(axis=0), W.std(axis=0)
