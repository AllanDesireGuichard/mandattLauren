"""
Friction fiscale annuelle et localisation des actifs.

Les constantes TAX_DRAG_* de core/ips.py etaient POSTULEES. Ce module les
derive, pour qu'on puisse dire au client d'ou vient chaque point de base.

TROIS REGIMES, et ce qui les separe reellement :

  CTO capitalisant   Un ETF capitalisant loge dans un compte-titres ne
                     declenche AUCUN impot tant qu'on ne vend pas. La seule
                     friction vient des plus-values realisees au
                     rebalancement. C'est peu connu, et c'est gratuit.

  CTO distribuant    Les dividendes verses sont taxes chaque annee au PFU de
                     30 %, puis doivent etre reinvestis. Meme actif, meme
                     performance brute : l'ecart est pur gaspillage.

  Assurance-vie      Capitalisation : zero impot tant qu'il n'y a pas de
                     rachat. En contrepartie, des frais de contrat.

La retenue a la source sur dividendes etrangers ne depend PAS de l'enveloppe
mais de la DOMICILIATION DU FONDS -- 15 % pour un fonds irlandais contre 30 %
ailleurs sur les dividendes americains. Elle est donc traitee a part.
"""
from __future__ import annotations

from core.ips import PFU_RATE, SAA_INDICATIVE

# Rendement courant distribue par classe d'actifs (dividendes ou coupons).
# Sert de base a l'imposition annuelle en cas de support distribuant.
YIELD = {
    "equity_developed": 0.019, "equity_emerging": 0.028,
    "infrastructure": 0.032,   "crypto": 0.000,
    "inflation_linked": 0.012, "govt_bonds_eur": 0.027,
    "credit_ig_eur": 0.033,    "gold": 0.000,
    "alternatives": 0.000,     "govt_bonds_eur_short": 0.022,
    "cash": 0.021,
}

# Rotation annuelle induite par le rebalancement par bandes de +/- 3 points.
# Plus une classe est volatile, plus elle derive vite hors de sa bande.
TURNOVER = {
    "equity_developed": 0.12, "equity_emerging": 0.15, "infrastructure": 0.13,
    "crypto": 0.35,           "inflation_linked": 0.07, "govt_bonds_eur": 0.07,
    "credit_ig_eur": 0.07,    "gold": 0.12,             "alternatives": 0.14,
    "govt_bonds_eur_short": 0.05, "cash": 0.05,
}

EMBEDDED_GAIN = 0.20          # plus-value latente moyenne au moment de vendre
FRAIS_CONTRAT_AV = 0.0025     # contrat luxembourgeois, negocie sur 30 M EUR+


def drag_cto_accumulating(cls: str) -> float:
    """Aucun impot sur les revenus : seules les plus-values realisees comptent."""
    return TURNOVER[cls] * EMBEDDED_GAIN * PFU_RATE


def drag_cto_distributing(cls: str) -> float:
    return YIELD[cls] * PFU_RATE + drag_cto_accumulating(cls)


def drag_av(cls: str) -> float:
    """Zero impot pendant la vie du contrat ; restent les frais."""
    return FRAIS_CONTRAT_AV


def portfolio_drag(mode: str) -> float:
    f = {"cto_acc": drag_cto_accumulating,
         "cto_dist": drag_cto_distributing,
         "av": drag_av}[mode]
    return sum(w * f(c) for c, w in SAA_INDICATIVE.items())


def asset_location() -> list[tuple[str, float, str, float, float]]:
    """
    Quelle enveloppe pour quelle classe d'actifs.

    Regle : loger dans l'assurance-vie ce qui coute cher ailleurs. Un actif
    dont le rendement courant est nul (or, matieres premieres) n'a rien a
    gagner a la capitalisation et paierait les frais de contrat pour rien.

    Retourne (classe, poids, enveloppe retenue, friction retenue, economie).
    """
    out = []
    for c, w in sorted(SAA_INDICATIVE.items(), key=lambda kv: -kv[1]):
        acc, av = drag_cto_accumulating(c), drag_av(c)
        env, best = ("CTO capitalisant", acc) if acc <= av else ("Assurance-vie", av)
        out.append((c, w, env, best, abs(acc - av)))
    return out


# --------------------------------------------------------------------------
# Reserves sur la localisation des actifs
# --------------------------------------------------------------------------
#
# Applique brut, le calcul ci-dessus conclut "tout en assurance-vie" : ses
# 0,25 % de frais battent les 0,63 % de friction du compte-titres sur CHAQUE
# classe. C'est le meme type de sortie degeneree que l'optimiseur d'allocation
# -- correcte au regard des donnees fournies, fausse au regard du mandat.
#
# Quatre elements que le calcul ne voit pas :

LOCATION_CONSTRAINTS = {
    "purge des plus-values au deces": (
        "Au deces, les plus-values latentes d'un compte-titres sont PURGEES : "
        "elles ne sont jamais imposees. Le modele ci-dessus taxe les plus-"
        "values de rebalancement, mais pas celles conservees jusqu'au bout. "
        "Pour la part destinee a etre detenue jusqu'au deces, la friction "
        "reelle du CTO est donc INFERIEURE a 0,63 %."),
    "liquidite de la poche A": (
        "Les 10 M EUR a decaisser sous deux ans doivent etre directement "
        "accessibles. Un rachat en assurance-vie prend des jours et peut "
        "declencher une imposition. La poche A reste au compte-titres, quel "
        "que soit le calcul."),
    "concentration sur un assureur": (
        "Loger 90 M EUR chez un seul assureur cree un risque de contrepartie "
        "que le super-privilege luxembourgeois attenue sans l'annuler. "
        "Repartir sur deux compagnies, ou conserver une part en direct."),
    "flexibilite et controle": (
        "Le compte-titres permet de nantir, de donner des titres en direct, "
        "de piloter finement la fiscalite des cessions. L'assurance-vie est "
        "plus rigide. Une partie du patrimoine doit rester manoeuvrable."),
}

# Repartition retenue, une fois ces reserves appliquees.
RECOMMENDED_LOCATION = {
    "Assurance-vie LUX":  0.65,
    "Compte-titres":      0.35,
}
