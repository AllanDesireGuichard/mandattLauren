"""
Étape 5 — le portefeuille retenu à l'étape 4, rejoué sur 2006-2026.

AVERTISSEMENT DE MÉTHODE, dit aussi dans l'app : ces données sont celles qui
ont servi à construire le portefeuille (pire baisse visée 14 %). Le rejeu ne
peut donc pas « prouver » que la limite tient ; il mesure ce que l'étape 4
n'a pas regardé : la DURÉE des baisses, et la distribution des résultats
sur un an (VaR, CVaR). Périmètre fixé par Allan le 2026-09-18.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core import allocation


def valeur() -> pd.Series:
    """Valeur des 100 M€ (en euros), rééquilibrés chaque mois."""
    w = {k: x for k, x in allocation.poids_retenus().items() if x > 0}
    # même fenêtre que l'optimisation de l'étape 4
    debut = allocation.resultats()["fenetre"][0]
    v = allocation.portefeuille(allocation.series()[debut:], w)
    return v / 100 * allocation.MONTANT


def episodes(v: pd.Series, seuil: float = 0.05) -> pd.DataFrame:
    """
    Chaque passage sous le plus haut dont la baisse dépasse `seuil` : date
    du sommet, date du creux, perte, date du retour au sommet (ou None si le
    portefeuille n'y est pas encore revenu).
    """
    haut = v.cummax()
    sous = v < haut
    out = []
    debut = None
    for d, s in sous.items():
        if s and debut is None:
            debut = d
        if (not s or d == v.index[-1]) and debut is not None:
            fin = d if not s else None
            morceau = v[debut:d]
            creux = morceau.idxmin()
            sommet = v[:debut].index[-2] if len(v[:debut]) > 1 else debut
            perte = float(v[creux] / haut[creux] - 1)
            if -perte >= seuil:
                out.append({"sommet": sommet, "creux": creux, "perte": perte,
                            "retour": fin})
            debut = None
    return pd.DataFrame(out)


def mois(a: pd.Timestamp, b: pd.Timestamp) -> float:
    return (b - a).days / 30.44


def temps_sous(v: pd.Series) -> dict:
    """Part du temps (en %) à plus de 1 %, 5 % et 10 % sous le plus haut."""
    dd = v / v.cummax() - 1
    return {"sous": float((dd <= -0.01).mean() * 100),
            "5": float((dd <= -0.05).mean() * 100),
            "10": float((dd <= -0.10).mean() * 100),
            "pire": float(dd.min() * 100)}


def un_an(v: pd.Series) -> pd.Series:
    """Rendements sur 12 mois glissants, fin de chaque mois (en %)."""
    m = v.resample("ME").last()
    return (m / m.shift(12) - 1).dropna() * 100


def var_cvar(r: pd.Series, niveau: float = 0.95) -> tuple[float, float]:
    """VaR et CVaR historiques : le seuil des (1-niveau) pires, et leur moyenne."""
    q = float(np.quantile(r, 1 - niveau))
    return q, float(r[r <= q].mean())
