"""
Filtre ESG du mandat Lauren.

Trois exclusions sectorielles (IPS §5.2), avec seuils de chiffre d'affaires.
Le filtre s'applique a l'univers investissable ET au benchmark : un indice
non filtre rendrait la mesure de performance non pertinente.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Exclusion:
    sector: str
    label: str
    thresholds: dict[str, float]   # activite -> % de CA maximum tolere
    rationale: str


EXCLUSIONS: tuple[Exclusion, ...] = (
    Exclusion(
        "tobacco", "Tabac",
        {"production": 0.00, "distribution": 0.05},
        "Tolerance zero sur la production. Seuil de 5 % sur la distribution "
        "pour ne pas exclure mecaniquement la grande distribution.",
    ),
    Exclusion(
        "weapons", "Armement",
        {"controversial": 0.00, "conventional": 0.05},
        "Armes controversees (mines, bombes a sous-munitions, biologiques, "
        "chimiques, nucleaires hors TNP) : exclusion absolue, deja imposee par "
        "la loi belge et les conventions d'Oslo/Ottawa. Armement conventionnel "
        "a 5 % pour ne pas exclure les conglomerats industriels diversifies.",
    ),
    Exclusion(
        "thermal_coal", "Charbon thermique",
        {"extraction": 0.05, "power_generation": 0.05},
        "Extraction et production d'electricite. Seuil de 5 %, aligne sur la "
        "pratique des indices MSCI ESG Screened.",
    ),
)

# --------------------------------------------------------------------------
# Correspondance avec les familles d'indices disponibles
# --------------------------------------------------------------------------

INDEX_FAMILIES = {
    "MSCI SRI": {
        "strictness": "haute",
        "coverage": "~25 % de l'indice parent (best-in-class)",
        "covers_mandate": True,
        "note": "Exclut les trois secteurs demandes, plus alcool, jeu, OGM, "
                "nucleaire, divertissement pour adultes. Va au-dela du mandat : "
                "tracking error elevee vs indice parent (3-5 %).",
    },
    "MSCI ESG Screened": {
        "strictness": "moderee",
        "coverage": "~95 % de l'indice parent",
        "covers_mandate": True,
        "note": "Exclut exactement armes controversees, tabac, charbon "
                "thermique et sables bitumineux. CORRESPONDANCE LA PLUS "
                "PRECISE avec le mandat, tracking error faible (<1 %).",
    },
    "MSCI ESG Enhanced Focus / Paris-Aligned": {
        "strictness": "climat",
        "coverage": "variable",
        "covers_mandate": False,
        "note": "Optimise sur l'intensite carbone, pas sur des exclusions "
                "sectorielles explicites. Ne garantit pas le mandat tabac/armes.",
    },
}

# --------------------------------------------------------------------------

RECOMMENDED_FAMILY = "MSCI ESG Screened"

RECOMMENDATION_RATIONALE = """\
Le mandat demande TROIS exclusions precises, pas une demarche ESG globale.

- MSCI ESG Screened exclut exactement ces trois secteurs, et rien de plus.
  L'univers reste a ~95 % de l'indice parent : la tracking error vs le marche
  est inferieure a 1 %, donc le cout d'opportunite du filtre est negligeable.

- MSCI SRI irait bien au-dela de la demande du client (best-in-class, ~25 %
  de l'univers). C'est defendable si le client veut une demarche ESG large,
  mais cela introduit 3 a 5 % de tracking error et des biais sectoriels
  marques (sous-ponderation energie, sur-ponderation technologie) qu'il
  faudrait alors assumer et expliquer.

ARBITRAGE RETENU : ESG Screened en coeur de portefeuille, SRI possible en
satellite si le client exprime une preference ESG plus large. A poser comme
question ouverte en rendez-vous plutot que comme decision prise a sa place.
"""


def check_coverage(index_family: str) -> bool:
    """L'indice couvre-t-il les exclusions du mandat ?"""
    fam = INDEX_FAMILIES.get(index_family)
    return bool(fam and fam["covers_mandate"])


if __name__ == "__main__":
    for e in EXCLUSIONS:
        print(f"\n{e.label.upper()}")
        for act, th in e.thresholds.items():
            print(f"  {act:<18} seuil CA  {th:.0%}")
        print(f"  -> {e.rationale}")
    print("\n" + "=" * 70)
    print(f"FAMILLE RETENUE : {RECOMMENDED_FAMILY}\n")
    print(RECOMMENDATION_RATIONALE)


# --------------------------------------------------------------------------
# Perimetre d'application du filtre
# --------------------------------------------------------------------------
#
# Point de rigueur souvent manque : les trois exclusions du mandat (tabac,
# armement, charbon thermique) sont des exclusions d'EMETTEURS D'ENTREPRISE.
# Les appliquer a une obligation d'Etat allemande ou a de l'or physique est
# une erreur de categorie -- il n'y a rien a filtrer.
#
# Exiger un "label ESG" sur ces classes reviendrait a payer une surcouche
# marketing sans contenu, ou a ecarter des instruments parfaitement conformes
# au mandat. On applique donc le filtre la ou il y a quelque chose a filtrer.

ESG_APPLICABLE = {
    "equity_developed", "equity_emerging", "infrastructure", "real_estate",
    "credit_ig_eur", "credit_ig_global", "credit_hy",
}

ESG_NOT_APPLICABLE = {
    "gold":                 "or physique, aucun emetteur",
    "cash":                 "monetaire et dette souveraine court terme",
    "govt_bonds_eur":       "dette souveraine de la zone euro",
    "govt_bonds_eur_short": "dette souveraine de la zone euro",
    "govt_bonds_global":    "dette souveraine",
    "inflation_linked":     "dette souveraine indexee",
    "bonds_em":             "dette souveraine emergente",
    "crypto":               "aucun emetteur",
}

# Classes ou la reponse depend de ce que l'instrument detient reellement :
# un indice de matieres premieres n'a pas d'emetteur, un ETF de mines d'or si.
# Exige une analyse en transparence avant validation.
ESG_CONDITIONAL = {
    "alternatives":      "selon le sous-jacent : indice de matieres premieres "
                         "(aucun emetteur) vs actions minieres (emetteurs a filtrer)",
    "global_agg_hedged": "melange souverain et credit : verifier la part credit",
    "green_bonds":       "vert par construction, mais verifier l'emetteur",
}


def esg_required(saa_class: str) -> bool:
    """Le filtre ESG doit-il etre exige sur cette classe d'actifs ?"""
    return saa_class in ESG_APPLICABLE


def esg_status(saa_class: str) -> str:
    if saa_class in ESG_APPLICABLE:
        return "exige"
    if saa_class in ESG_NOT_APPLICABLE:
        return "sans objet"
    if saa_class in ESG_CONDITIONAL:
        return "sous condition"
    return "non classe"
