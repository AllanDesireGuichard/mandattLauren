"""
Optimisation de l'allocation -> data/allocation_optim.json

Lancer :  python3 scripts/optimiser.py            (quelques minutes)

LE PROBLÈME. Chercher les poids qui maximisent le rendement espéré (étape 2,
corrigé à l'étape 3) sous une seule exigence de risque : que le portefeuille,
rééquilibré chaque mois, ne perde jamais plus de 15 % depuis son plus haut
sur les séries d'octobre 2006 à aujourd'hui (décision d'Allan : pire cas
historique). Poids positifs, somme 100 %, bitcoin hors calcul.

La pire baisse n'est pas une fonction lisse des poids : on part de plusieurs
points de départ tirés au hasard et on garde le meilleur résultat qui
respecte la limite. Tirage fixé (graine 0) : le résultat est reproductible.

SCÉNARIOS. Le bloc 3 montre le calcul libre, puis l'éprouve : on abaisse
un rendement espéré d'un demi-point (dans la marge d'erreur de l'étape 2),
puis le Japon jusqu'au niveau des États-Unis. CONSTAT (2026-09-18) : la
concentration résiste. Le calcul ne choisit pas le Japon et les indexées
pour leur rendement espéré mais pour leur tenue dans les crises passées
(yen refuge, indexées flattées en 2008 par leur remplaçant). Le bloc 4
ajoutera ses contraintes comme de nouveaux scénarios.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from core import allocation  # noqa: E402

DEPARTS = 16


def optimiser(chemin: allocation.Chemin, mu: np.ndarray,
              bornes: list[tuple[float, float]], limite: float) -> np.ndarray:
    n = len(mu)
    contraintes = [
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "ineq", "fun": lambda w: limite + chemin.pire_baisse(w)},
    ]
    rng = np.random.default_rng(0)
    meilleur = None
    for _ in range(DEPARTS):
        w0 = rng.dirichlet(np.ones(n))
        r = minimize(lambda w: -w @ mu, w0, method="SLSQP", bounds=bornes,
                     constraints=contraintes,
                     options={"maxiter": 400, "ftol": 1e-9})
        w = np.clip(r.x, 0, None)
        w = w / w.sum()
        if chemin.pire_baisse(w) < -limite - 5e-4:
            continue
        if meilleur is None or w @ mu > meilleur @ mu:
            meilleur = w
    if meilleur is None:
        raise RuntimeError("aucun portefeuille ne respecte la limite")
    return meilleur


def decrire(nom: str, cles: list[str], w: np.ndarray, mu: np.ndarray,
            s: pd.DataFrame, note: str) -> dict:
    poids = {k: float(x) for k, x in zip(cles, w)}
    v = allocation.portefeuille(s, {k: x for k, x in poids.items() if x > 0})
    dd = allocation.baisse_depuis_plus_haut(v)
    creux = dd.idxmin()
    sommet = v[:creux].idxmax()
    ans = (v.index[-1] - v.index[0]).days / 365.25
    crises = {}
    for c, (a, b, _) in allocation.CRISES.items():
        crises[c] = round(float(dd[a:b].min() * 100), 1)
    return {
        "nom": nom, "note": note,
        "poids": {k: round(x, 4) for k, x in poids.items()},
        "rendement_espere": round(float(w @ mu), 3),
        "pire_baisse": round(float(dd.min() * 100), 2),
        "sommet": sommet.date().isoformat(), "creux": creux.date().isoformat(),
        "crises": crises,
        "realise": round(float((v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1)
                         * 100, 2),
    }


def main() -> int:
    e = allocation.entrees()
    cles = [k for k in allocation.ORDRE if k not in allocation.HORS_CALCUL]
    s = allocation.series()[cles].dropna()
    chemin = allocation.Chemin(s)
    mu = e.loc[cles, "rendement"].to_numpy()
    libre = [(0.0, 1.0)] * len(cles)
    lim = allocation.LIMITE

    scenarios = {}
    t0 = time.time()

    w = optimiser(chemin, mu, libre, lim)
    scenarios["libre"] = decrire(
        "Calcul libre", cles, w, mu, s,
        "Seule exigence : ne jamais perdre plus de 15 % depuis le plus haut.")
    print("libre", scenarios["libre"]["rendement_espere"],
          f"{time.time() - t0:.0f} s")

    # Épreuve : un demi-point de moins sur les deux lignes les plus chargées,
    # dans la marge d'erreur des estimations de l'étape 2.
    # Puis le Japon ramené au rendement espéré des États-Unis : le seuil où
    # le calcul cesse de le préférer (vérifié le 2026-09-18 : à 8,0 %, il
    # en garde encore 26 %).
    ecart_usa = mu[cles.index("usa")] - mu[cles.index("japon")]
    for nom, k, delta in (("moins_japon", "japon", -0.5),
                          ("japon_egal_usa", "japon", ecart_usa),
                          ("moins_indexees", "indexees", -0.5)):
        mu2 = mu.copy()
        mu2[cles.index(k)] += delta
        w = optimiser(chemin, mu2, libre, lim)
        scenarios[nom] = decrire(
            f"Calcul libre, {e.loc[k, 'classe'].lower()} à "
            f"{mu2[cles.index(k)]:.2f} %", cles, w, mu2, s,
            f"Même calcul, rendement espéré {e.loc[k, 'classe'].lower()} "
            f"abaissé de {-delta:.2f} point.")
        scenarios[nom]["variante"] = {
            "cle": k, "delta": float(delta),
            "rendement": float(mu2[cles.index(k)])}
        print(nom, scenarios[nom]["rendement_espere"],
              f"{time.time() - t0:.0f} s")

    out = {"releve": date.today().isoformat(), "limite": lim,
           "rebalancement": "mensuel", "departs": DEPARTS,
           "fenetre": [s.index[0].date().isoformat(),
                       s.index[-1].date().isoformat()],
           "cles": cles, "scenarios": scenarios}
    allocation.RESULTATS.write_text(json.dumps(out, ensure_ascii=False,
                                               indent=1), encoding="utf-8")
    for n, sc in scenarios.items():
        print(n, sc["rendement_espere"], sc["pire_baisse"], sc["crises"],
              {k: round(v * 100, 1) for k, v in sc["poids"].items()
               if v > .005})
    return 0


if __name__ == "__main__":
    sys.exit(main())
