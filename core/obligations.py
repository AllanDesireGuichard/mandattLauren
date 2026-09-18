"""
Obligations d'État en direct, évaluées sur la courbe de la BCE.

On ne cherche pas une cotation (les lignes obligataires nommées ne sont pas
accessibles de façon fiable sans source payante, voir core/sources.py) : on
PRICE une obligation à partir de la courbe zéro-coupon publiée par la BCE.
C'est exactement ce que fait un gérant obligataire pour juger si un titre
est cher ou bon marché.

La courbe est donnée par les six paramètres du modèle de Svensson, publiés
chaque jour par la BCE (data/taux_marche.json, clé « svensson »). Les taux
sont à capitalisation continue ; la formule redonne les taux publiés à
0,0005 point près (vérifié le 2026-09-18).

Conventions : coupon annuel, nominal 100, obligation « bullet » (tout le
capital remboursé à l'échéance), pas de coupon couru (émission du jour).
"""
from __future__ import annotations

import math


def taux_zero(m: float, p: dict) -> float:
    """Taux zéro-coupon (en %, capitalisation continue) à l'échéance m ans."""
    m = max(m, 1e-6)
    a, b = m / p["tau1"], m / p["tau2"]
    f1 = (1 - math.exp(-a)) / a
    f2 = f1 - math.exp(-a)
    f3 = (1 - math.exp(-b)) / b - math.exp(-b)
    return p["beta0"] + p["beta1"] * f1 + p["beta2"] * f2 + p["beta3"] * f3


def actualisation(m: float, p: dict, choc: float = 0.0) -> float:
    """Valeur aujourd'hui d'un euro reçu dans m ans. `choc` en points de %."""
    return math.exp(-(taux_zero(m, p) + choc) / 100 * m)


def _dates(maturite: float) -> list[float]:
    """Dates de coupon annuelles, en partant de l'échéance."""
    n = math.ceil(maturite - 1e-9)
    return [maturite - k for k in range(n)][::-1]


def prix(coupon: float, maturite: float, p: dict, choc: float = 0.0) -> float:
    return sum((coupon + (100 if t == maturite else 0))
               * actualisation(t, p, choc) for t in _dates(maturite))


def coupon_au_pair(maturite: float, p: dict) -> float:
    """Le coupon qui fait coter l'obligation exactement 100 aujourd'hui."""
    ts = _dates(maturite)
    return 100 * (1 - actualisation(maturite, p)) / sum(
        actualisation(t, p) for t in ts)


def rendement(coupon: float, maturite: float, prix_: float) -> float:
    """Rendement actuariel (en %, capitalisation annuelle), par dichotomie."""
    ts = _dates(maturite)

    def pv(y):
        return sum((coupon + (100 if t == maturite else 0)) / (1 + y) ** t
                   for t in ts)

    lo, hi = -0.05, 0.30
    for _ in range(100):
        mid = (lo + hi) / 2
        if pv(mid) > prix_:
            lo = mid
        else:
            hi = mid
    return mid * 100


def analyse(maturite: float, p: dict) -> dict:
    """
    Tout ce qu'un gérant regarde sur une obligation émise au pair.
      duration  : durée de vie moyenne des flux, pondérée par leur valeur ;
      sensibilité : baisse de prix pour +1 point de taux (duration modifiée) ;
      convexité : la courbure — les pertes accélèrent moins que les gains ;
      portage   : le coupon encaissé sur un an, rapporté au prix ;
      glissement : le gain de prix en un an si la courbe ne bouge pas,
                   parce que l'obligation « vieillit » vers des échéances
                   où les taux sont plus bas ;
      choc +1 pt : la perte de prix si tous les taux montent d'un point.
    """
    c = coupon_au_pair(maturite, p)
    p0 = prix(c, maturite, p)
    y = rendement(c, maturite, p0) / 100
    ts = _dates(maturite)
    flux = [(t, c + (100 if t == maturite else 0)) for t in ts]
    pv = [(t, f / (1 + y) ** t) for t, f in flux]
    duration = sum(t * v for t, v in pv) / p0
    sensibilite = duration / (1 + y)
    convexite = sum(t * (t + 1) * v for t, v in pv) / (p0 * (1 + y) ** 2)
    if maturite > 1:
        p1 = prix(c, maturite - 1, p)
        glissement = (p1 - p0) / p0 * 100
    else:
        glissement = (100 - p0) / p0 * 100
    portage = c / p0 * 100
    return {
        "maturite": maturite, "coupon": c, "prix": p0, "rendement": y * 100,
        "duration": duration, "sensibilite": sensibilite,
        "convexite": convexite, "portage": portage, "glissement": glissement,
        "rendement_1an": portage + glissement,
        "choc_plus_1": (prix(c, maturite, p, choc=1.0) - p0) / p0 * 100,
        "choc_moins_1": (prix(c, maturite, p, choc=-1.0) - p0) / p0 * 100,
    }


def echelle(montants: dict[float, float], p: dict) -> list[dict]:
    """
    Échelle d'obligations zéro-coupon : pour recevoir `montant` à chaque
    échéance `t` (en années), combien faut-il investir aujourd'hui ?
    C'est l'adossement : chaque besoin de trésorerie est couvert par une
    obligation qui arrive à échéance au bon moment.
    """
    out = []
    for t, montant in sorted(montants.items()):
        df = actualisation(t, p)
        out.append({"echeance": t, "montant": montant, "cout": montant * df,
                    "taux": (1 / df) ** (1 / t) * 100 - 100})
    return out
