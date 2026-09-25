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
        "Pour les autres classes (des centaines d'actions américaines ou "
        "émergentes, des lingots, des contrats sur matières premières), on "
        "passe par des fonds cotés (ETF). Pour chaque classe, trois ou quatre "
        "fonds cotés à Francfort en euros sont comparés selon une règle "
        "simple : **exclusions conformes au mandat → taille d'au moins "
        "1 Md€ → frais les plus bas**. L'écart de performance avec un fonds "
        "de référence sert de contrôle."
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
    ayem = em["candidats"]["AYEM.DE"]
    rizd = cl["infrastructure"]["candidats"]["RIZD.DE"]
    st.markdown(
        f"**Lecture.**\n"
        f"- Le filtre éloigne peu du marché, **sauf pour les émergents** : le "
        f"seul fonds conforme a fait {_signe(xzem['ecart_moyen'], 'points')} "
        f"par an face au marché sur {viz.fr(xzem['fenetre'], 'ans', 0)}, son "
        f"indice étant bien plus strict que le mandat. Le fonds « Screened » "
        f"colle au marché ({_signe(ayem['ecart_moyen'], 'point')}) mais laisse "
        f"passer l'armement. On garde le conforme, et l'écart sera annoncé au "
        f"client.\n"
        f"- **L'infrastructure est retirée** : le seul fonds filtré ne pèse "
        f"que {_taille(rizd['taille'])}, les gros fonds ne filtrent rien "
        f"(producteurs d'électricité au charbon). Pas d'exception au mandat.\n"
        f"- **Les frais mesurés confirment les frais annoncés** : l'écart de "
        f"frais entre deux fonds se retrouve presque entièrement dans leurs "
        f"performances."
    )


def _pedagogie() -> None:
    st.caption(
        "Trois points de vigilance. Le filtre « Screened » ne retire **pas** "
        "l'armement conventionnel, que nous avons exclu des actions en "
        "direct : on retient donc des indices « SRI », qui l'excluent dès "
        "5 % du chiffre d'affaires. La liquidité d'un ETF n'est pas son "
        "volume de bourse mais sa taille, un teneur de marché créant des "
        "parts à la demande. Et neuf fonds mal identifiés dans l'univers "
        "hérité ont été corrigés, chacun contrôlé sur deux sources par son "
        "ISIN."
    )
