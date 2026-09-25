"""
Onglet 3, bloc 5 — le crédit : prêter aux entreprises.

Chiffres : data/fonds_credit.json (scripts/fetch_fonds_credit.py) pour les
fonds, data/rendements.json pour les rendements espérés de l'étape 2, courbe
de la BCE (ensemble de la zone euro) pour l'État de même échéance.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import streamlit as st

from core import obligations, rendements, taux, viz

FICHIER = Path(__file__).resolve().parents[1] / "data" / "fonds_credit.json"
DEFAUTS_IG = 0.11      # perte moyenne annuelle sur défauts, Moody's (étape 2)


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


def _etat(maturite: float, zone: dict) -> float:
    """Taux de l'État zone euro à la même échéance, en taux annuel."""
    return (math.exp(obligations.taux_zero(maturite, zone) / 100) - 1) * 100


def bloc() -> None:
    d = json.loads(FICHIER.read_text(encoding="utf-8"))
    f, ret, rep = d["fonds"], d["retenu"], d["repere_etat"]
    r = rendements.charger()["classes"]
    zone = taux.charger()["svensson"]["toutes"]
    c = f[ret]

    st.markdown("#### Le crédit : prêter aux entreprises")
    st.markdown(
        "Une obligation d'entreprise paie un peu plus qu'un État, parce que "
        "l'entreprise peut faire défaut. L'étape 2 a montré que ce "
        "supplément, la prime, est aujourd'hui parmi les plus faibles depuis "
        "quarante ans."
    )
    longs = [x for x in f.values() if x["duree"] > 4]
    p_court = c["rendement"] - _etat(c["maturite"], zone)
    net = c["rendement"] - DEFAUTS_IG
    echelle = [obligations.analyse(m, zone)["rendement"] for m in (2, 3, 5, 7, 10)]
    ech = sum(echelle) / len(echelle)
    st.markdown(
        f"- **Quel crédit ?** Bien noté seulement. Défauts déduits, le haut "
        f"rendement rapporte {_pct(r['hy_euro']['central'])}, **moins que "
        f"les États** ({_pct(r['govt_bonds_eur']['central'])}).\n"
        f"- **Quelle durée ?** Courte : allonger fait passer la prime de "
        f"{viz.fr(p_court, 'point', 2)} à "
        f"{viz.fr(max(x['rendement'] - _etat(x['maturite'], zone) for x in longs), 'point', 2)}, "
        f"mais la perte de 2022 de "
        f"{viz.fr(-c['pires_baisses']['2022'], '%', 1)} à "
        f"{viz.fr(-min(x['pires_baisses']['2022'] for x in longs), '%', 1)}.\n"
        f"- **Quel fonds ?** **{ret.split('.')[0]}** ({c['nom']}), durée "
        f"{viz.fr(c['duree'], 'ans', 1)}, frais {_pct(c['frais'])}, "
        f"{viz.fr(c['taille'] / 1000, 'Md€', 1)}."
    )
    st.warning(
        f"**Le crédit court rapporte à peine plus que l'État** : "
        f"{viz.fr(p_court, 'point', 2)} de plus à échéance égale, "
        f"{viz.fr(p_court - DEFAUTS_IG, 'point', 2)} défauts déduits. Et il a "
        f"perdu {viz.fr(-c['pires_baisses']['2020'], '%', 1)} en 2020, contre "
        f"{viz.fr(-rep['pires_baisses']['2020'], '%', 1)} pour les États de "
        f"même durée. Pour l'étape 4, on retient donc **{_pct(net)}** (et non "
        f"les {_pct(r['credit_ig_eur']['central'])} de l'indice toutes "
        f"durées) : moins que l'échelle d'États 2-10 ans ({_pct(ech)}).",
        icon=":material/warning:",
    )
    st.caption(
        "La prime rémunère le défaut et la hausse de la prime elle-même. En "
        "2020 les défauts sont restés rares mais la prime s'est envolée : le "
        "fonds court a perdu trois fois plus que les États de même durée."
    )
