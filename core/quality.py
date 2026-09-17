"""
Controle qualite des series de prix.

Probleme constate : les series Yahoo des lignes londoniennes (.L) melangent
les devises de cotation. Deux symptomes distincts :

  1. RUPTURE D'ECHELLE -- un saut unique d'un facteur 100 (pence <-> livres),
     par exemple SPXS.L le 2014-01-02 : 303,05 -> 3,02.
     Reparable : on remet le segment anterieur a l'echelle du segment recent.

  2. OSCILLATION -- la serie alterne entre deux lignes de cotation,
     par exemple SGLN.L en avril 2011 : -39 %, +64 %, -38 %, +62 %.
     Non reparable : on ne sait pas quel point appartient a quelle serie.
     La serie est rejetee.

Sans ce filtre, l'optimiseur tournerait sur des volatilites de 29 % pour un
ETF d'obligations d'Etat 1-3 ans. Les chiffres seraient faux et invisibles.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

JUMP_THRESHOLD = 0.35          # variation quotidienne suspecte
SCALE_FACTORS = (100.0, 1000.0)
SCALE_TOL = 0.08               # tolerance relative sur le facteur
OSCILLATION_WINDOW = 10        # jours : un saut suivi d'un saut inverse


def _suspects(s: pd.Series, threshold: float = JUMP_THRESHOLD) -> pd.Series:
    r = s.pct_change()
    return r[r.abs() > threshold]


def _is_scale_break(ratio: float) -> float | None:
    """Le rapport avant/apres correspond-il a un changement d'unite ?"""
    for f in SCALE_FACTORS:
        for cand in (f, 1.0 / f):
            if abs(ratio / cand - 1.0) < SCALE_TOL:
                return cand
    return None


def repair(s: pd.Series, threshold: float = JUMP_THRESHOLD
           ) -> tuple[pd.Series, list[str]]:
    """
    Repare les ruptures d'echelle. Retourne (serie reparee, journal).
    Les oscillations ne sont pas reparees -- elles seront detectees par audit().
    """
    s = s.copy()
    log: list[str] = []
    for _ in range(6):                       # plusieurs ruptures possibles
        sus = _suspects(s, threshold)
        fixed = False
        for d in sus.index:
            i = s.index.get_loc(d)
            if i == 0:
                continue
            ratio = s.iloc[i] / s.iloc[i - 1]
            f = _is_scale_break(ratio)
            if f is None:
                continue
            s.iloc[:i] = s.iloc[:i] * f      # segment anterieur remis a l'echelle
            log.append(f"{d.date()} rupture d'echelle x{f:g} corrigee")
            fixed = True
            break
        if not fixed:
            break
    return s, log


def audit(s: pd.Series, allow_volatile: bool = False) -> dict:
    """
    Verdict sur une serie, apres tentative de reparation.

    allow_volatile : pour la crypto et les matieres premieres, ou des
    variations quotidiennes superieures a 35 % sont plausibles.
    """
    thr = 0.60 if allow_volatile else JUMP_THRESHOLD
    fixed, log = repair(s, thr)
    sus = _suspects(fixed, thr)

    oscillating = False
    if len(sus) >= 2:
        idx = [fixed.index.get_loc(d) for d in sus.index]
        vals = sus.to_numpy()
        for a in range(len(idx) - 1):
            if (idx[a + 1] - idx[a] <= OSCILLATION_WINDOW
                    and np.sign(vals[a]) != np.sign(vals[a + 1])):
                oscillating = True
                break

    if oscillating:
        verdict = "REJET oscillation de devise"
    elif len(sus) > 0:
        verdict = f"REJET {len(sus)} saut(s) inexplique(s)"
    else:
        verdict = "OK"

    return {"series": fixed, "repairs": log, "n_suspects": int(len(sus)),
            "oscillating": oscillating, "verdict": verdict,
            "clean": verdict == "OK"}


# Places de cotation, par fiabilite decroissante des donnees Yahoo.
# Les lignes londoniennes sont penalisees a cause du probleme pence/livres.
VENUE_SCORE = {".DE": 3, ".PA": 3, ".AS": 3, ".MI": 3, ".SW": 2, ".L": 1}


def venue_score(ticker: str) -> int:
    for suf, sc in VENUE_SCORE.items():
        if ticker.endswith(suf):
            return sc
    return 2


# --------------------------------------------------------------------------
# Controle de plausibilite par classe d'actifs
# --------------------------------------------------------------------------
#
# Les reparations ci-dessus attrapent les ruptures franches, mais pas les
# contaminations diffuses (series melangeant deux lignes de cotation avec des
# ecarts moderes). Sur 182 series, une verification manuelle est impossible.
#
# D'ou ce garde-fou : une fourchette de volatilite annuelle plausible par
# classe d'actifs. Un ETF d'obligations d'Etat 1-3 ans a 8 % de volatilite est
# faux, quelle qu'en soit la cause. Mieux vaut rejeter un instrument valide
# que faire tourner l'optimiseur sur une serie fausse -- une erreur de donnees
# ne se voit pas dans le resultat, elle le deplace silencieusement.

PLAUSIBLE_VOL = {
    "cash":                 (0.0005, 0.020),
    "govt_bonds_eur_short": (0.0005, 0.030),
    "govt_bonds_eur":       (0.015,  0.075),
    "govt_bonds_global":    (0.015,  0.120),
    "inflation_linked":     (0.015,  0.080),
    "credit_ig_eur":        (0.015,  0.075),
    "credit_ig_global":     (0.020,  0.120),
    "credit_hy":            (0.030,  0.180),
    "bonds_em":             (0.030,  0.180),
    "global_agg_hedged":    (0.015,  0.100),
    "green_bonds":          (0.015,  0.075),
    "equity_developed":     (0.080,  0.300),
    "equity_emerging":      (0.100,  0.350),
    "infrastructure":       (0.080,  0.350),
    "real_estate":          (0.100,  0.400),
    "gold":                 (0.100,  0.300),
    "alternatives":         (0.050,  0.450),
    "crypto":               (0.300,  1.200),
}

VOLATILE_CLASSES = {"crypto", "alternatives", "gold"}


def plausible_vol(vol: float, saa_class: str) -> tuple[bool, str]:
    rng = PLAUSIBLE_VOL.get(saa_class)
    if rng is None or vol is None or not np.isfinite(vol):
        return True, ""
    lo, hi = rng
    if vol < lo:
        return False, f"vol {vol:.1%} < {lo:.1%} attendu"
    if vol > hi:
        return False, f"vol {vol:.1%} > {hi:.1%} attendu"
    return True, ""


# --------------------------------------------------------------------------
# Coherence devise / place de cotation
# --------------------------------------------------------------------------
#
# Un fonds libelle en euros mais cote a Londres est servi par Yahoo dans sa
# ligne en pence : la serie porte alors du GBP/EUR qui n'a rien a y faire.
# Symptome observe : ECRP.L (Amundi EUR Corporate Bond ESG) affiche 9,8 % de
# volatilite, contre ~5 % pour le meme sous-jacent cote a Francfort.
#
# Sur les classes libellees en euros, on exige donc une cotation en zone euro.
# Ce n'est pas un jugement sur l'instrument -- c'est un refus de faire entrer
# du bruit de change dans l'estimation du risque.

EUR_DENOMINATED = {
    "govt_bonds_eur", "govt_bonds_eur_short", "inflation_linked",
    "credit_ig_eur", "cash", "green_bonds",
}
EUROZONE_VENUES = (".DE", ".PA", ".AS", ".MI", ".F", ".BR", ".MC")


def venue_matches_currency(ticker: str, saa_class: str) -> bool:
    if saa_class not in EUR_DENOMINATED:
        return True
    return ticker.endswith(EUROZONE_VENUES)
