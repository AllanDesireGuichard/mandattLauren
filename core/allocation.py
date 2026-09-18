"""
Entrées de l'allocation (étape 4) : un support par classe, son rendement
espéré, et la série longue qui sert à mesurer son risque.

Les rendements viennent de l'étape 2 (data/rendements.json), corrigés par ce
que l'étape 3 a appris en choisissant les supports : les emprunts d'État sont
achetés en direct, donc leur rendement est celui de l'échelle retenue et non
celui du marché entier ; le crédit est un fonds court, qui rapporte moins que
l'indice toutes durées (3,50 % − 0,11 % de défauts, pas 4,04 %).

Les séries longues (data/indices_longs.csv) viennent de
scripts/fetch_indices.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core import obligations, rendements, taux

DATA = Path(__file__).resolve().parents[1] / "data"

# Reprises de l'étape 3 (tabs/t3_lignes.py, tabs/t3_credit.py)
TRANCHES = {0.5: 2.5e6, 1.0: 2.5e6, 1.5: 2.5e6, 2.0: 2.5e6}
ECHELLE_LONGUE = (2, 3, 5, 7, 10)
DEFAUTS_IG = 0.11

ORDRE = ("actions_europe", "usa", "japon", "emergents", "etats_courts",
         "etats_longs", "credit_court", "indexees", "or", "matieres", "crypto")

# Décision d'Allan (2026-09-18) : poche crypto de 1 à 2 %, choix du client,
# posée à côté du calcul et non choisie par lui.
HORS_CALCUL = ("crypto",)


def series() -> pd.DataFrame:
    return pd.read_csv(DATA / "indices_longs.csv", index_col=0,
                       parse_dates=True)


def meta() -> dict:
    return json.loads((DATA / "indices_longs.json").read_text(
        encoding="utf-8"))


def entrees() -> pd.DataFrame:
    """Une ligne par classe : support, rendement espéré et d'où il vient."""
    r = rendements.charger()["classes"]
    sv = taux.charger()["svensson"]
    ech = obligations.echelle(TRANCHES, sv["aaa"])
    courts = sum(x["taux"] * x["cout"] for x in ech) / sum(
        x["cout"] for x in ech)
    longs = sum(obligations.analyse(m, sv["toutes"])["rendement"]
                for m in ECHELLE_LONGUE) / len(ECHELLE_LONGUE)
    cr = json.loads((DATA / "fonds_credit.json").read_text(encoding="utf-8"))
    credit = cr["fonds"][cr["retenu"]]["rendement"] - DEFAUTS_IG

    rdt = {
        "actions_europe": (r["europe"]["central"],
                           "Étape 2, actions européennes"),
        "usa": (r["us"]["central"], "Étape 2, actions américaines"),
        "japon": (r["japon"]["central"], "Étape 2, actions japonaises"),
        "emergents": (r["equity_emerging"]["central"],
                      "Étape 2, actions émergentes"),
        "etats_courts": (courts, "Étape 3, taux garanti de l'échelle AAA"),
        "etats_longs": (longs, "Étape 3, taux de l'échelle 2 à 10 ans"),
        "credit_court": (credit, "Étape 3, taux du fonds moins les défauts"),
        "indexees": (r["inflation_linked"]["central"],
                     "Étape 2, taux réel + 4 % d'inflation"),
        "or": (r["gold"]["central"], "Étape 2, supposé égal à l'inflation"),
        "matieres": (r["alternatives"]["central"],
                     "Étape 2, supposé égal à l'inflation"),
        "crypto": (r["crypto"]["central"], "Étape 2, aucun rendement défendable"),
    }
    m = meta()["classes"]
    lignes = []
    for k in ORDRE:
        c = m[k]
        lignes.append({
            "cle": k, "classe": c["libelle"], "support": c["support"],
            "rendement": rdt[k][0], "origine": rdt[k][1],
            "source": c["source"], "raccord": c.get("raccord"),
            "debut": c["debut"], "controle": c["controle"],
            "hors_calcul": k in HORS_CALCUL,
        })
    return pd.DataFrame(lignes).set_index("cle")
