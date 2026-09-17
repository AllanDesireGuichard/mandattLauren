"""
Acces aux sources de donnees externes.

Une seule regle ici : AUCUNE cle en dur. Le depot est public -- c'est la
condition du niveau gratuit de Streamlit Community Cloud, qui ne lit pas les
depots prives. Une cle commitee dans ce depot est une cle publiee.

Ordre de resolution : st.secrets (local via .streamlit/secrets.toml, en ligne
via le panneau Secrets du tableau de bord) puis variable d'environnement,
pour que les scripts hors Streamlit fonctionnent aussi.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------------------
# Catalogue des sources. Toutes verifiees le 2026-09-17.
# --------------------------------------------------------------------------

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Courbe zero-coupon AAA de la zone euro, quotidienne, SANS CLE.
# C'est elle qui rend l'obligataire souverain constructible en direct :
# on y price une obligation bullet plutot que de chercher une cotation.
ECB_YC_BASE = "https://data-api.ecb.europa.eu/service/data/YC/"
ECB_YC_KEY = "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{maturity}Y"


class CleManquante(RuntimeError):
    """Levee avec le mode d'emploi, jamais un simple KeyError."""


def fred_key() -> str:
    """
    Cle API FRED. Gratuite, obtenue sur
    https://fred.stlouisfed.org/docs/api/api_key.html
    """
    try:                                    # import tardif : les scripts
        import streamlit as st              # hors Streamlit n'en ont pas besoin
        if "FRED_API_KEY" in st.secrets:
            cle = str(st.secrets["FRED_API_KEY"]).strip()
            if cle:
                return cle
    except Exception:                       # pas de contexte Streamlit, ou
        pass                                # pas de fichier secrets : on passe

    cle = (os.environ.get("FRED_API_KEY") or "").strip()
    if cle:
        return cle

    raise CleManquante(
        "Cle FRED absente.\n"
        "  En local  : copier .streamlit/secrets.toml.example en "
        "secrets.toml et y mettre la cle.\n"
        "  En ligne  : Streamlit Cloud > Manage app > Settings > Secrets.\n"
        "  En script : export FRED_API_KEY=...\n"
        "La cle est gratuite : "
        "https://fred.stlouisfed.org/docs/api/api_key.html"
    )


def fred_disponible() -> bool:
    """Pour qu'un onglet degrade proprement au lieu de lever une exception."""
    try:
        fred_key()
        return True
    except CleManquante:
        return False
