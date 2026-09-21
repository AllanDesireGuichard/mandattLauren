"""
Variante « portefeuille croissance » -> data/allocation_croissance.json

Lancer :  PYTHONPATH=. python3 scripts/optimiser_croissance.py   (quelques minutes)

LA QUESTION. L'étape 4 impose que le portefeuille n'ait JAMAIS perdu plus de
15 % depuis son plus haut sur 2006-2026. C'est la lecture la plus exigeante
de l'énoncé, et elle plafonne le rendement espéré à 6,47 % (calcul libre).

Que se passe-t-il si on remplace ce pire cas par une limite en FRÉQUENCE :
« perdre plus de 15 % sur un an, mais au plus une année sur vingt » ? C'est
la VaR à 95 %, mesurée sur les 228 années glissantes de la période.

CE QUE LE SCRIPT CALCULE. Trois portefeuilles, tous évalués sur les MÊMES
mesures pour qu'ils soient comparables :

    croissance        VaR 95 % >= -15 %, aucune autre règle
    croissance_10me   la même, plus les 10 M€ sécurisés sur l'échelle AAA
    retenu            celui de l'étape 4, repassé sous ces mesures

POURQUOI LES TROIS. Le premier répond à la question posée. Le deuxième
chiffre ce que coûte le seul besoin non négociable du client. Le troisième
sert de point de comparaison : sans lui, les chiffres de risque du
portefeuille croissance n'ont pas d'échelle.

AVERTISSEMENT, à garder à l'esprit en lisant les sorties. La VaR et la CVaR
sont estimées sur les données mêmes qui servent à construire le
portefeuille, et sur des fenêtres de douze mois qui se chevauchent : à forte
part d'actions, vingt ans ne contiennent que sept épisodes de baisse
distincts. Ces quantiles décrivent le passé, ils ne le prolongent pas.
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

SORTIE = allocation.DATA / "allocation_croissance.json"
DEPARTS = 24
NIVEAU = 0.95                  # une année sur vingt
FENETRE = 12                   # mesure sur douze mois glissants


class Mesures:
    """
    Les mesures de risque d'un portefeuille, toutes tirées du même chemin.

    Le chemin (valeur jour par jour, remise aux poids chaque mois) est celui
    de l'étape 4 : `allocation.Chemin`. On y ajoute ce que l'étape 4 ne
    regardait pas, les rendements sur douze mois glissants, d'où sortent la
    VaR et la CVaR.
    """

    def __init__(self, s: pd.DataFrame):
        self.chemin = allocation.Chemin(s)
        self.fins = self.chemin.fins

    def douze_mois(self, w: np.ndarray) -> np.ndarray:
        """Rendements sur douze mois, à chaque fin de mois (en décimal)."""
        m = self.chemin.valeur(w)[self.fins]
        return m[FENETRE:] / m[:-FENETRE] - 1

    def var(self, w: np.ndarray) -> float:
        """Perte dépassée une année sur vingt (négatif)."""
        return float(np.quantile(self.douze_mois(w), 1 - NIVEAU))

    def cvar(self, w: np.ndarray) -> float:
        """Perte MOYENNE de ces années-là : de combien, quand ça dépasse."""
        r = self.douze_mois(w)
        return float(r[r <= np.quantile(r, 1 - NIVEAU)].mean())

    def pire_baisse(self, w: np.ndarray) -> float:
        return self.chemin.pire_baisse(w)


def optimiser(m: Mesures, mu: np.ndarray, bornes: list[tuple[float, float]],
              limite: float) -> np.ndarray:
    """
    Poids qui maximisent le rendement espéré sous « VaR 95 % >= -limite ».

    La VaR n'est pas une fonction lisse des poids : comme dans
    scripts/optimiser.py, on part de plusieurs points tirés au hasard et on
    garde le meilleur résultat qui respecte la limite. Graine fixée : le
    résultat est reproductible.
    """
    n = len(mu)
    contraintes = [
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "ineq", "fun": lambda w: m.var(w) + limite},
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
        if any(w[i] < a - 1e-6 or w[i] > b + 1e-6
               for i, (a, b) in enumerate(bornes)):
            continue
        if m.var(w) < -limite - 5e-4:
            continue
        if meilleur is None or w @ mu > meilleur @ mu:
            meilleur = w
    if meilleur is None:
        raise RuntimeError("aucun portefeuille ne respecte la limite")
    return meilleur


def decrire(nom: str, note: str, cles: list[str], w: np.ndarray,
            mu: np.ndarray, m: Mesures, s: pd.DataFrame) -> dict:
    """Tout ce que l'onglet 6 affiche, calculé une fois pour toutes."""
    poids = {k: float(x) for k, x in zip(cles, w)}
    v = allocation.portefeuille(s, {k: x for k, x in poids.items()
                                    if x > 0.0005})
    dd = allocation.baisse_depuis_plus_haut(v)
    r12 = pd.Series(m.douze_mois(w) * 100)
    ans = (v.index[-1] - v.index[0]).days / 365.25
    return {
        "nom": nom,
        "note": note,
        "poids": {k: round(x, 4) for k, x in poids.items()},
        "rendement_espere": round(float(w @ mu), 3),
        "var95": round(m.var(w) * 100, 2),
        "cvar95": round(m.cvar(w) * 100, 2),
        "pire_baisse": round(float(dd.min() * 100), 2),
        "pire_12m": round(float(r12.min()), 2),
        "annees_en_perte": round(float((r12 < 0).mean() * 100), 1),
        "annees_sous_4": round(float((r12 < 4).mean() * 100), 1),
        "temps_sous_10": round(float((dd <= -0.10).mean() * 100), 1),
        "realise": round(float((v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1)
                         * 100, 2),
        "crises": {c: round(float(dd[a:b].min() * 100), 1)
                   for c, (a, b, _) in allocation.CRISES.items()},
    }


def main() -> int:
    e = allocation.entrees()
    cles = [k for k in allocation.ORDRE if k not in allocation.HORS_CALCUL]
    s = allocation.series()[cles].dropna()
    m = Mesures(s)
    mu = e.loc[cles, "rendement"].to_numpy()
    libre = [(0.0, 1.0)] * len(cles)
    lim = allocation.LIMITE

    portefeuilles, t0 = {}, time.time()

    w = optimiser(m, mu, libre, lim)
    portefeuilles["croissance"] = decrire(
        "Portefeuille croissance", "VaR 95 % à un an ≥ −15 %, aucune autre "
        "règle : le pendant du calcul libre de l'étape 4.",
        cles, w, mu, m, s)
    print("croissance", portefeuilles["croissance"]["rendement_espere"],
          f"{time.time() - t0:.0f} s")

    # Le seul besoin du client qui ne se négocie pas : les 10 M€ à deux ans.
    avec_aaa = list(libre)
    avec_aaa[cles.index("etats_courts")] = (allocation.MIN_AAA, 1.0)
    w = optimiser(m, mu, avec_aaa, lim)
    portefeuilles["croissance_10me"] = decrire(
        "Croissance, 10 M€ sécurisés", "La même, plus l'échelle AAA à "
        f"{allocation.MIN_AAA:.0%} : le besoin de liquidité du client.",
        cles, w, mu, m, s)
    print("croissance_10me",
          portefeuilles["croissance_10me"]["rendement_espere"],
          f"{time.time() - t0:.0f} s")

    # Le portefeuille de l'étape 4, repassé sous les mêmes mesures : sans
    # point de comparaison, les chiffres ci-dessus n'ont pas d'échelle.
    ret = allocation.poids_retenus()
    w = np.array([ret.get(k, 0.0) for k in cles])
    w = w / w.sum()
    portefeuilles["retenu"] = decrire(
        "Portefeuille retenu (étape 4)", "Celui du mandat, mesuré ici sur "
        "la VaR et la CVaR pour être comparable.", cles, w, mu, m, s)
    print("retenu", portefeuilles["retenu"]["rendement_espere"],
          f"{time.time() - t0:.0f} s")

    SORTIE.write_text(json.dumps({
        "date": date.today().isoformat(),
        "limite": lim,
        "niveau": NIVEAU,
        "fenetre": FENETRE,
        "n_fenetres": len(m.douze_mois(w)),
        "debut": s.index[0].date().isoformat(),
        "fin": s.index[-1].date().isoformat(),
        "portefeuilles": portefeuilles,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("->", SORTIE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
