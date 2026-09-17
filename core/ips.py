"""
Parametres du mandat. Source unique de verite.

PERIMETRE, revu le 2026-09-17. Ce module ne decrit plus qu'un PROCESSUS
D'INVESTISSEMENT. Tout ce qui relevait de la fiscalite, de la transmission et
de la structuration d'enveloppe a ete retire (code dans archive/core/).

Consequence a ne pas passer sous silence : le resultat le plus puissant du
dossier precedent disparait avec lui. La structuration valait +50 M EUR de
patrimoine net transmis, contre +5,5 M EUR pour toute l'optimisation
d'allocation -- un facteur neuf. Ce n'est pas une perte de qualite, c'est un
changement d'objet : on ne construit plus un mandat de gestion privee, on
construit et on documente une chaine d'investissement.

Deuxieme consequence, mecanique : le seuil de rendement requis etait calcule
net des frais de mandat (0,40 %) et de la friction d'enveloppe (0,25 %). Sans
eux, il tombe de 4,80 % a 4,15 % et la marge s'elargit d'autant. Ce n'est PAS
une amelioration du portefeuille -- c'est le meme portefeuille juge sur un
seuil plus bas. Dit autrement : la marge affichee ici est une marge AVANT
frais de gestion. Voir `SEUIL_REFERENCE_AVEC_FRAIS` pour le point de
comparaison, qui reste affiche mais n'est plus un parametre.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# 1. Le mandat. Aucune de ces valeurs n'est reglable dans l'application :
#    ce sont des donnees du probleme, pas des variables de decision.
# --------------------------------------------------------------------------

TOTAL_ASSETS = 100_000_000.0      # EUR, produit de cession deja converti
LIQUIDITY_NEED = 10_000_000.0     # EUR, a decaisser sous 24 mois
BASE_CURRENCY = "EUR"
HORIZON_YEARS = 10                # horizon de reference des hypotheses

INFLATION_TARGET = 0.0400         # HYPOTHESE CLIENT, figee. Voir onglet 2 :
                                  # le point d'inflation anticipe par le
                                  # marche est mesure, pas suppose, et il est
                                  # nettement plus bas.

INSTRUMENT_TER = 0.0015           # TER moyen pondere des supports retenus.
                                  # Conserve parce que c'est une propriete
                                  # MESURABLE des instruments (onglet 3), pas
                                  # un parametre commercial.

ANNUAL_COST = INSTRUMENT_TER      # seul cout porte par le processus

# Point de comparaison, affiche et jamais reglable : ce que deviendrait le
# seuil avec des frais de gestion de marche sur un encours de cette taille.
FRAIS_GESTION_REFERENCE = 0.0040
SEUIL_REFERENCE_AVEC_FRAIS = INFLATION_TARGET + ANNUAL_COST + FRAIS_GESTION_REFERENCE


def required_gross_return(inflation: float | None = None) -> float:
    """
    Rendement brut annuel requis pour preserver le pouvoir d'achat.

    Inflation + cout des supports. Rien d'autre : ni frais de gestion, ni
    fiscalite, par decision de perimetre.
    """
    infl = INFLATION_TARGET if inflation is None else inflation
    return infl + ANNUAL_COST


TARGET_GROSS_RETURN = round(required_gross_return(), 4)

# --------------------------------------------------------------------------
# 2. La contrainte de risque. C'est elle qui pilote tout le dimensionnement.
# --------------------------------------------------------------------------

MAX_DRAWDOWN = 0.15               # pic a creux, 12 mois glissants, en EUR
DD_BREACH_PROBABILITY = 0.10      # tolerance de depassement

# MESURE, pas postule. scripts/estimate_dd_ratio.py, 21,8 ans de donnees
# quotidiennes en EUR (2004-2026 : 2008, 2011, 2020, 2022).
# La valeur "regle empirique" de 1,9 etait fausse et trop conservatrice : elle
# sous-allouait le risque d'environ dix points d'actions. Le ratio n'est pas
# constant -- 1,81 a 20 % d'actions, 1,33 a 80 % -- parce que la
# diversification obligataire agit plus sur le drawdown que sur la volatilite.
DD_TO_VOL_RATIO = 1.35

TARGET_VOL = 0.096                # lu sur la SAA testee, pas deduit du ratio
EXPECTED_DD_P90 = 0.138           # data/saa_risk.csv
DD_BREACH_MEASURED = 0.091        # P(perte 12m > 15 %), tolerance 10 %
TARGET_VOL_RISKY = TARGET_VOL / 0.90

# LE CHIFFRE A NE JAMAIS OMETTRE. Le pire drawdown de la periode n'est pas
# 13,8 % (P90) mais 26 % (2008). La contrainte de 15 % est tenue "moins d'une
# annee sur dix", pas "jamais". Les deux chiffres vont ensemble ou pas du tout.
WORST_OBSERVED_DD = 0.256
DD_2022 = 0.138

# Crises nommees, mesurees sur la SAA (scripts/stress_tests.py).
# La duree compte autant que la profondeur : 2022 est moins profond que 2020
# mais trois fois plus long a recuperer.
CRISES = {
    "Lehman 2008":        {"drawdown": 0.256, "recuperation_mois": 12},
    "COVID 2020":         {"drawdown": 0.175, "recuperation_mois": 5},
    "Taux 2022":          {"drawdown": 0.138, "recuperation_mois": 17},
    "Dette EUR 2011":     {"drawdown": 0.068, "recuperation_mois": 3},
}

# --------------------------------------------------------------------------
# 3. Contraintes d'investissement
# --------------------------------------------------------------------------

# Les trois exclusions visent des EMETTEURS D'ENTREPRISE. Il n'y a rien a
# filtrer dans un Bund ou dans un lingot : core/esg.py distingue
# "exige" / "sans objet" / "sous condition".
ESG_EXCLUSIONS = {
    "tabac":          {"production": 0.00, "distribution": 0.05},
    "armement":       {"controverse": 0.00, "conventionnel": 0.05},
    "charbon":        {"extraction": 0.05, "production_electrique": 0.05},
}

UCITS_ONLY = True                 # resident francais retail, contrainte PRIIPs

CONCENTRATION_LIMITS = {
    "single_line": 0.10,
    "single_asset_class": 0.40,
    "growth_assets": 0.60,
    "crypto": 0.02,
    "single_issuer": 0.05,        # hors dette souveraine core
}

MIN_DAILY_LIQUIDITY = 0.80

FX_HEDGE_RATIO = {
    "bonds_international": 1.00,      # vol FX (8-10 %) > vol actif (4-5 %)
    "equity_developed_ex_emu": 0.40,  # USD = couverture naturelle en stress
    "equity_emerging": 0.00,          # devise = moteur de performance
    "gold": 0.00,                     # couvrir annulerait la reserve de valeur
    "alternatives": 0.50,
}

# --------------------------------------------------------------------------
# 4. Poche de liquidite
# --------------------------------------------------------------------------
# L'architecture en quatre poches est retiree avec la transmission : trois des
# quatre n'avaient de sens que par leur enveloppe fiscale. La poche de
# liquidite reste, parce qu'elle repond a un fait du mandat -- 10 M EUR a
# decaisser sous deux ans -- et non a un choix de structuration.
#
# Elle est une decision de POLITIQUE, jamais un arbitrage d'optimisation.
# L'exclure du calcul : voir core/optimizer.py, ou l'inclure faisait degenerer
# la parite de risque vers un fonds monetaire a 82 %.

LIQUIDITY_SLEEVE = ("cash", "govt_bonds_eur_short")
LIQUIDITY_WEIGHT = LIQUIDITY_NEED / TOTAL_ASSETS      # 10 %

# --------------------------------------------------------------------------
# 5. Allocation strategique en vigueur
# --------------------------------------------------------------------------
# Issue de scripts/optimize_saa.py puis DE-RISQUEE apres stress tests :
# croissance 50 % -> 45 %, par rotation vers l'obligataire et l'or, jamais
# vers le monetaire (gonfler la poche de liquidite confondrait deux
# decisions distinctes). Cout 19 pb de rendement, gain 1,5 pt de marge sur
# le drawdown.
#
# A RECALIBRER A L'ETAPE 2. Les hypotheses de rendement sous-jacentes
# (core/cma.py) s'ancrent sur un taux monetaire EUR mesure a 2,05 %. Le taux
# de depot BCE est a 2,50 % et le 10 ans EUR a 3,53 % (16/09/2026). La
# calibration doit etre reprise sur les courbes vivantes.

SAA_INDICATIVE = {
    "equity_developed":      0.23,
    "equity_emerging":       0.11,
    "infrastructure":        0.09,
    "crypto":                0.02,
    "inflation_linked":      0.15,
    "govt_bonds_eur":        0.10,
    "credit_ig_eur":         0.09,
    "gold":                  0.07,
    "alternatives":          0.04,
    "govt_bonds_eur_short":  0.05,
    "cash":                  0.05,
}


GROWTH_ASSETS = ("equity_developed", "equity_emerging", "infrastructure", "crypto")
REAL_ASSETS = ("gold", "infrastructure", "inflation_linked")
BOND_ASSETS = ("inflation_linked", "govt_bonds_eur", "credit_ig_eur",
               "govt_bonds_eur_short")

# Quatre familles, pas onze : au-dela de huit teintes aucune palette
# categorielle ne tient, et onze categories ne se distinguent pas a l'oeil.
# core/viz.py consomme ce dictionnaire -- une seule definition des familles.
FAMILIES = {
    "Croissance":   GROWTH_ASSETS,
    "Obligataire":  ("inflation_linked", "govt_bonds_eur", "credit_ig_eur"),
    "Actifs reels": ("gold", "alternatives"),
    "Liquidite":    LIQUIDITY_SLEEVE,
}

# --------------------------------------------------------------------------
# 6. Gouvernance
# --------------------------------------------------------------------------

REBALANCING_BAND = 0.03           # +/- 3 points autour de la cible
REVIEW_TRIGGER_DD = 0.10          # 2/3 du budget de risque -> revue

TACTICAL_BANDS = {
    "growth":  (0.40, 0.45, 0.55),   # (min, cible, max)
    "bonds":   (0.28, 0.34, 0.40),
    "real":    (0.08, 0.11, 0.16),
    "cash":    (0.05, 0.10, 0.15),
}

# --------------------------------------------------------------------------
# 7. Faisabilite
# --------------------------------------------------------------------------


def expected_gross_return(inflation: float | None = None) -> float:
    from core.cma import INFLATION_CLIENT, portfolio_return
    return portfolio_return(SAA_INDICATIVE,
                            INFLATION_CLIENT if inflation is None else inflation)


def feasibility() -> list[tuple[str, float, float, float]]:
    """
    (libelle, rendement attendu, seuil requis, marge) par regime d'inflation.

    Les deux nombres sont evalues DANS LE MEME REGIME. C'est la correction la
    plus importante du projet : les versions initiales comparaient un seuil
    bati sur 4 % d'inflation a des rendements attendus batis implicitement sur
    2 %. Un portefeuille evalue dans un monde, juge dans un autre.
    """
    from core.cma import INFLATION_BASE, INFLATION_CLIENT

    out = []
    for label, infl in [("Hypothese client", INFLATION_CLIENT),
                        ("Consensus BCE", INFLATION_BASE)]:
        er = expected_gross_return(infl)
        seuil = required_gross_return(inflation=infl)
        out.append((f"{label} (inflation {infl:.0%})", er, seuil, er - seuil))
    return out


def summary() -> dict[str, str]:
    er = expected_gross_return()
    seuil = required_gross_return()
    return {
        "Actifs sous mandat":        f"{TOTAL_ASSETS/1e6:,.0f} M EUR".replace(",", " "),
        "Besoin de liquidite":       f"{LIQUIDITY_NEED/1e6:,.0f} M EUR sous 24 mois",
        "Devise de reference":       BASE_CURRENCY,
        "Hypothese d'inflation":     f"{INFLATION_TARGET:.2%} (figee)",
        "Seuil de rendement requis": f"{seuil:.2%}",
        "Rendement brut attendu":    f"{er:.2%}",
        "Marge":                     f"{er - seuil:+.2%}",
        "Volatilite cible":          f"{TARGET_VOL:.2%}",
        "Contrainte de perte":       f"{MAX_DRAWDOWN:.0%} sur 12 mois, "
                                     f"depassement < {DD_BREACH_PROBABILITY:.0%}",
        "Drawdown P90 mesure":       f"{EXPECTED_DD_P90:.1%}",
        "Probabilite mesuree":       f"{DD_BREACH_MEASURED:.1%}",
        "Pire cas observe (2008)":   f"{WORST_OBSERVED_DD:.1%}",
    }


# --------------------------------------------------------------------------
# Controles de coherence. Executes a l'import : un parametre incoherent doit
# casser au chargement, pas produire un portefeuille silencieusement faux.
# --------------------------------------------------------------------------

def _controles() -> None:
    poids = sum(SAA_INDICATIVE.values())
    assert abs(poids - 1.0) < 1e-9, f"la SAA somme a {poids}"

    croissance = sum(SAA_INDICATIVE[k] for k in GROWTH_ASSETS)
    assert croissance <= CONCENTRATION_LIMITS["growth_assets"], \
        f"croissance {croissance:.0%} au-dela du plafond"

    sleeve = sum(SAA_INDICATIVE[k] for k in LIQUIDITY_SLEEVE)
    assert abs(sleeve - LIQUIDITY_WEIGHT) < 1e-9, \
        f"poche de liquidite {sleeve:.0%} vs besoin {LIQUIDITY_WEIGHT:.0%}"

    couvertes = {c for fam in FAMILIES.values() for c in fam}
    assert couvertes == set(SAA_INDICATIVE), \
        f"classes non rattachees a une famille : {set(SAA_INDICATIVE) - couvertes}"

    assert DD_BREACH_MEASURED <= DD_BREACH_PROBABILITY, \
        "la SAA viole sa propre contrainte de depassement"


_controles()


if __name__ == "__main__":
    for k, v in summary().items():
        print(f"{k:<28} {v}")
    print()
    print("FAISABILITE")
    for label, er, seuil, marge in feasibility():
        print(f"  {label:<28} attendu {er:.2%}  requis {seuil:.2%}  "
              f"marge {marge:+.2%}")
    print()
    print(f"Pour memoire, seuil avec des frais de gestion de "
          f"{FRAIS_GESTION_REFERENCE:.2%} : {SEUIL_REFERENCE_AVEC_FRAIS:.2%} "
          f"-> marge {expected_gross_return() - SEUIL_REFERENCE_AVEC_FRAIS:+.2%}")
    print()
    print("Controles de coherence : OK")
