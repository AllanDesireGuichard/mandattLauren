"""
Entrées de l'allocation (étape 4) : un support par classe, son rendement
espéré, et la série longue qui sert à mesurer son risque.

Les rendements viennent de l'étape 2 (data/rendements.json), corrigés par ce
que l'étape 3 a appris en choisissant les supports : les emprunts d'État sont
achetés en direct, donc leur rendement est celui de l'échelle retenue et non
celui du marché entier ; le crédit est un fonds court, qui rapporte moins que
l'indice toutes durées (3,50 % − 0,11 % de défauts, pas 4,04 %) ; et depuis le
2026-09-25 les actions européennes portent le rendement MESURÉ SUR LES TITRES
RETENUS, et non celui de l'indice (voir core/actions.rendement_panier).

Les séries longues (data/indices_longs.csv) viennent de
scripts/fetch_indices.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core import actions, obligations, outlook, rendements, taux

DATA = Path(__file__).resolve().parents[1] / "data"

# Reprises de l'étape 3 (tabs/t3_lignes.py, tabs/t3_credit.py)
TRANCHES = {0.5: 2.5e6, 1.0: 2.5e6, 1.5: 2.5e6, 2.0: 2.5e6}
ECHELLE_LONGUE = (2, 3, 5, 7, 10)
DEFAUTS_IG = 0.11

ORDRE = ("actions_europe", "usa", "japon", "emergents", "etats_courts",
         "etats_longs", "credit_court", "indexees", "or", "matieres", "crypto")

# Décision d'Allan (2026-09-18) : pas de crypto. Le bitcoin reste mesuré
# (blocs 1 et 2) pour montrer pourquoi, mais n'entre pas dans le calcul.
HORS_CALCUL = ("crypto",)


def series() -> pd.DataFrame:
    return pd.read_csv(DATA / "indices_longs.csv", index_col=0,
                       parse_dates=True)


def meta() -> dict:
    return json.loads((DATA / "indices_longs.json").read_text(
        encoding="utf-8"))


# Le panier d'actions européennes, retenu une fois par processus. La
# sélection n'est pas réglable dans l'application (aucun déroulant depuis le
# 2026-09-25) : elle ne peut changer qu'avec les données ou le code, donc la
# recalculer à chaque affichage ne ferait que ralentir l'outil. Elle coûte une
# notation de 600 titres, et `entrees()` est appelée cinq fois par rendu de
# l'onglet 4.
_PANIER: dict | None = None


def rendement_panier() -> dict:
    """Rendement espéré des actions européennes, mesuré sur les titres tenus."""
    global _PANIER
    if _PANIER is None:
        _PANIER = actions.rendement_panier(
            outlook.final(actions.selection(actions.univers())))
    return _PANIER


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

    panier = rendement_panier()
    rdt = {
        "actions_europe": (panier["central"],
                           f"Étape 3, mesuré sur les {panier['n']} titres "
                           f"retenus"),
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


# ----------------------------------------------------------------------
# Bloc 2 — le risque

# Répartition FIXE de la poche actions, décision d'Allan (2026-09-18) :
# sans elle, le calcul met toutes les actions sur la zone au rendement espéré
# le plus haut (le Japon, 0,2 pt devant l'Europe, écart dans la marge
# d'erreur). Europe surpondérée : détenue en direct.
MIX_ACTIONS = {"actions_europe": .40, "usa": .35, "japon": .10,
               "emergents": .15}

# Crises définies À L'AVANCE, par leurs dates, et non repérées dans les
# données : les repérer par les baisses du portefeuille biaiserait les
# mesures faites « en crise ». La perte se mesure depuis le plus haut
# atteint AVANT (toute l'histoire), la fenêtre dit seulement où chercher
# le point bas.
CRISES = {
    "2008": ("2007-06-01", "2009-06-30", "Crise financière"),
    "2011": ("2011-04-01", "2012-06-30", "Crise des dettes de la zone euro"),
    "2020": ("2020-02-01", "2020-06-30", "Covid"),
    "2022": ("2022-01-01", "2023-12-31", "Retour de l'inflation"),
}


def portefeuille(s: pd.DataFrame, poids: dict) -> pd.Series:
    """
    Valeur d'un portefeuille remis à ses poids le premier jour de chaque
    mois (base 100). Entre deux rééquilibrages, chaque ligne vit sa vie.
    """
    cles = list(poids)
    p = s[cles].dropna()
    w = pd.Series(poids, dtype=float)
    w = w / w.sum()
    mois = p.index.to_period("M")
    niveau, morceaux = 100.0, []
    for _, bloc in p.groupby(mois):
        if morceaux:
            base = p.loc[:bloc.index[0]].iloc[-2]      # veille du mois
        else:
            base = bloc.iloc[0]
        v = niveau * (bloc / base) @ w
        morceaux.append(v)
        niveau = float(v.iloc[-1])
    return pd.concat(morceaux)


def series_risque() -> pd.DataFrame:
    """Séries du bloc 2 : la poche actions (40/35/10/15) + les autres."""
    s = series()
    out = {"poche_actions": portefeuille(s, MIX_ACTIONS)}
    for k in ORDRE:
        out[k] = s[k]
    return pd.DataFrame(out)


def baisse_depuis_plus_haut(v: pd.Series) -> pd.Series:
    v = v.dropna()
    return v / v.cummax() - 1


def pertes_crises(s: pd.DataFrame) -> pd.DataFrame:
    """Pire baisse depuis le plus haut, dans chaque crise (en %)."""
    out = {}
    for k in s:
        dd = baisse_depuis_plus_haut(s[k])
        out[k] = {c: (float(dd[a:b].min() * 100)
                      if len(dd[a:b]) and dd.index[0] <= pd.Timestamp(a)
                      else float("nan"))
                  for c, (a, b, _) in CRISES.items()}
    return pd.DataFrame(out).T


def volatilite(s: pd.DataFrame) -> pd.Series:
    """Volatilité annuelle, sur les variations hebdomadaires (en %)."""
    r = s.resample("W-FRI").last().pct_change(fill_method=None)
    return r.std() * 52 ** .5 * 100


def pendant_la_baisse(s: pd.DataFrame, ref: str = "poche_actions"
                      ) -> tuple[pd.DataFrame, dict]:
    """
    Pour chaque crise : du sommet au creux de la poche actions DANS la
    fenêtre de crise, ce qu'a fait chaque support sur ces mêmes dates (en %).
    Sommet pris dans la fenêtre, et non sur toute l'histoire : en 2011, les
    actions n'avaient pas retrouvé leur plus haut de 2007, et partir de 2007
    mesurerait quatre ans de marché, pas la crise.
    """
    out, dates = {}, {}
    for c, (a, b, _) in CRISES.items():
        v = s[ref].dropna()
        creux = v[a:b].idxmin()
        debut = pd.Timestamp(a) - pd.DateOffset(months=3)
        sommet = v[debut:creux].idxmax()
        dates[c] = (sommet, creux)
        out[c] = {k: (float(s[k].asof(creux) / s[k].asof(sommet) - 1) * 100
                      if s[k].first_valid_index() <= sommet else float("nan"))
                  for k in s}
    return pd.DataFrame(out), dates


# La poche actions compte pour un seul support : c'est à ce niveau que se
# joue la diversification du portefeuille, les quatre zones étant de toute
# façon tenues ensemble à l'étape 4.
CORR_ORDRE = ("poche_actions", "etats_courts", "etats_longs", "credit_court",
              "indexees", "or", "matieres")


def correlations(s: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Corrélation des variations hebdomadaires entre supports, mesurée
    séparément hors crise et pendant les quatre crises datées.

    Le bitcoin est écarté : il ne commence qu'en 2014 quand tout le reste
    part de 2006, et il n'entre pas dans le portefeuille. Le garder ferait
    cohabiter deux fenêtres dans le même tableau.
    """
    cols = [k for k in CORR_ORDRE if k in s.columns]
    r = s[cols].resample("W-FRI").last().pct_change(fill_method=None)
    en_crise = pd.Series(False, index=r.index)
    for a, b, _ in CRISES.values():
        en_crise[a:b] = True
    hors, pendant = r[~en_crise].dropna(), r[en_crise].dropna()
    return (hors.corr(), pendant.corr(),
            {"hors_crise": len(hors), "en_crise": len(pendant)})


# ----------------------------------------------------------------------
# Blocs 3 et 4 — l'optimisation (calculée par scripts/optimiser.py)

LIMITE = 0.15
# Règles du bloc 4, décisions d'Allan (2026-09-18)
MIN_AAA = 0.10                 # les 10 M€ à décaisser
PLAFONDS = {"indexees": .15, "or": .10, "matieres": .05, "credit_court": .20}
LIMITE_MARGE = 0.14            # marge d'un point sous la limite du mandat
RESULTATS = DATA / "allocation_optim.json"


class Chemin:
    """
    Évaluation rapide d'un portefeuille rééquilibré chaque mois : la même
    règle que portefeuille(), écrite en matrices pour que l'optimiseur
    puisse l'appeler des milliers de fois.
    """

    def __init__(self, s: pd.DataFrame):
        p = s.dropna()
        self.index = p.index
        mois = p.index.to_period("M")
        fin_prec = p.groupby(mois).last().shift(1)
        base = fin_prec.reindex(mois).set_axis(p.index)
        base[mois == mois[0]] = p.iloc[0].values
        self.g = (p / base).to_numpy()
        m = np.asarray(mois.astype(str))
        self.fins = np.r_[np.nonzero(m[1:] != m[:-1])[0], len(m) - 1]

    def valeur(self, w: np.ndarray) -> np.ndarray:
        x = self.g @ w
        v = np.empty_like(x)
        niveau, debut = 100.0, 0
        for f in self.fins:
            v[debut:f + 1] = niveau * x[debut:f + 1]
            niveau, debut = v[f], f + 1
        return v

    def pire_baisse(self, w: np.ndarray) -> float:
        v = self.valeur(w)
        return float((v / np.maximum.accumulate(v) - 1).min())


def resultats() -> dict:
    return json.loads(RESULTATS.read_text(encoding="utf-8"))


def avec_poche_actions(s: pd.DataFrame) -> pd.DataFrame:
    """Les quatre zones d'actions remplacées par la poche 40/35/10/15."""
    autres = [k for k in s if k not in MIX_ACTIONS]
    out = pd.concat([portefeuille(s, MIX_ACTIONS).rename("poche_actions"),
                     s[autres]], axis=1).dropna()
    return out


def rendement_poche(e: pd.DataFrame) -> float:
    return float(sum(p * e.loc[k, "rendement"]
                     for k, p in MIX_ACTIONS.items()))


# ----------------------------------------------------------------------
# Bloc 5 — le portefeuille retenu

MONTANT = 100e6
RETENU = "r4_marge"


def par_ligne(poids: dict) -> dict:
    """
    Poids par support, la poche actions éclatée selon la clé 40/35/10/15.

    Un seul endroit pour cette opération : elle était recopiée dans
    tabs/t4_allocation.py, dans scripts/pitch/extraire.py et ici.
    """
    out = dict(poids)
    poche = out.pop("poche_actions", None)
    if poche is not None:
        for k, m in MIX_ACTIONS.items():
            out[k] = out.get(k, 0.0) + poche * m
    return out


def poids_retenus() -> dict:
    """Poids par support du portefeuille retenu, poche actions éclatée."""
    p = par_ligne(resultats()["scenarios"][RETENU]["poids"])
    return {k: p.get(k, 0.0) for k in ORDRE if k not in HORS_CALCUL}


# ----------------------------------------------------------------------
# Le rendement d'un jeu de poids : RECALCULÉ, jamais relu
#
# POURQUOI. scripts/optimiser.py écrit dans data/allocation_optim.json les
# poids qu'il a trouvés ET le rendement espéré qui allait avec. L'application
# lisait ce second chiffre. Résultat, constaté le 2026-09-25 : le rendement du
# portefeuille ne bougeait pas quand la poche d'actions européennes changeait
# de titres, puisqu'il datait de la dernière optimisation.
#
# Les POIDS, eux, restent ceux de l'optimisation : la retrouver demande des
# minutes de calcul, on ne la relance pas à chaque affichage. Les deux
# décisions se tiennent — les poids sont une décision d'allocation, datée ; le
# rendement est une lecture de marché, qui doit suivre la sélection du jour.
# `controle_optimisation` dit quand l'écart devient assez grand pour qu'il
# faille relancer l'optimisation.

DERIVE_MAX = 0.05          # points de rendement espéré


def rendement(poids: dict, e: pd.DataFrame | None = None) -> float:
    """Rendement espéré d'un jeu de poids, aux rendements espérés du jour."""
    if e is None:
        e = entrees()
    return float(sum(x * e.loc[k, "rendement"]
                     for k, x in par_ligne(poids).items() if k in e.index))


def rendement_retenu(e: pd.DataFrame | None = None) -> float:
    """Rendement espéré brut du portefeuille retenu."""
    return rendement(resultats()["scenarios"][RETENU]["poids"], e)


def controle_optimisation(e: pd.DataFrame | None = None) -> dict:
    """
    Les poids retenus datent-ils d'une optimisation encore valable ?

    Compare le rendement du portefeuille retenu tel qu'on le calcule
    aujourd'hui à celui que l'optimisation avait inscrit. Un écart matériel
    signifie que les rendements espérés ont bougé depuis, et donc que les
    poids optimaux ne sont plus forcément ceux-là.
    """
    res = resultats()
    stocke = res["scenarios"][RETENU]["rendement_espere"]
    vif = rendement_retenu(e)
    return {"date": res["releve"], "stocke": stocke, "vif": vif,
            "derive": vif - stocke, "a_relancer": abs(vif - stocke) > DERIVE_MAX}
