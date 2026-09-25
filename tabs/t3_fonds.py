"""
Onglet 3, bloc 4 — les fonds et ETF des autres classes d'actifs.

Les chiffres viennent de data/fonds.json (scripts/fetch_fonds.py) ; la règle
de choix est appliquée dans le script, l'app ne fait que l'afficher.
Décision d'Allan du 2026-09-18 : actions développées hors Europe en deux
fonds séparés, États-Unis et Japon, plutôt qu'un MSCI World qui aurait
compté l'Europe deux fois.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import fonds, taux, viz


def _taille(m: float | None) -> str:
    if m is None:
        return "—"
    return viz.fr(m / 1000, "Md€", 1) if m >= 1000 else viz.fr(m, "M€", 0)


def _signe(v: float | None, unite: str = "pt") -> str:
    if v is None or pd.isna(v):
        return "—"
    return ("+" if v > 0 else "") + viz.fr(v, unite, 2)


def bloc() -> None:
    d = fonds.charger()
    cl = d["classes"]

    st.markdown("#### Les fonds pour les autres classes d'actifs")
    st.markdown(
        "Pour les autres classes, on passe par des fonds indiciels : filtre "
        "ESG conforme au mandat, frais bas, taille suffisante."
    )
    st.markdown(
        "Les actions hors Europe sont prises en deux fonds, **États-Unis** et "
        "**Japon**, plutôt qu'un fonds « Monde » qui contient environ 15 % "
        "d'actions européennes, déjà détenues en direct."
    )
    _lectures(cl)
    _pedagogie()
    st.caption(f"Frais, taille et indice : justETF ; prix : Yahoo. Relevé du "
               f"{taux.date_fr(d['releve'])}.")


def _lectures(cl: dict) -> None:
    em = cl["emergents"]
    xzem = em["candidats"][em["retenu"]]
    rizd = cl["infrastructure"]["candidats"]["RIZD.DE"]
    st.markdown(
        f"- Le filtre éloigne peu du marché, **sauf pour les émergents** : "
        f"le seul fonds conforme a fait "
        f"{_signe(xzem['ecart_moyen'], 'points')} par an face au marché sur "
        f"{viz.fr(xzem['fenetre'], 'ans', 0)}. On le garde, et l'écart est "
        f"annoncé au client.\n"
        f"- **L'infrastructure est retirée** : le seul fonds filtré ne pèse "
        f"que {_taille(rizd['taille'])}, et les gros fonds ne filtrent rien."
    )


def _pedagogie() -> None:
    st.caption(
        "Le filtre « Screened » ne retire pas l'armement conventionnel, que "
        "nous avons exclu des actions en direct : on retient donc des "
        "indices « SRI ». Neuf fonds mal identifiés dans l'univers hérité "
        "ont été corrigés, chacun contrôlé sur deux sources par son ISIN."
    )
