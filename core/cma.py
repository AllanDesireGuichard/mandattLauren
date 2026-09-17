"""
Capital Market Assumptions -- hypotheses de marche a 10 ans, en EUR.

PRINCIPE DIRECTEUR : prospectif, pas historique. Une moyenne de rendements
passes n'est pas une prevision -- elle dit surtout d'ou l'on vient en matiere
de valorisation. On part donc de blocs constitutifs : ce que l'actif rapporte
mecaniquement (rendement courant), plus ce qu'on suppose de la croissance et
de la valorisation.

COHERENCE DU REGIME D'INFLATION -- correction d'une incoherence de l'IPS v1.1.
    Le seuil de rendement (4,85 %) est construit sur une inflation de 4 %,
    l'hypothese du client. Mais les rendements attendus, eux, etaient batis
    implicitement sur une inflation proche de 2 %. Comparer les deux revient a
    opposer un monde a 4 % d'inflation a un portefeuille evalue dans un monde
    a 2 % : le mandat paraissait plus difficile qu'il ne l'est.

    Ici, chaque classe d'actifs porte un COEFFICIENT DE REPERCUSSION : la part
    d'une surprise d'inflation qui se retrouve dans son rendement nominal a
    10 ans. Le seuil et les rendements sont alors evalues dans le MEME regime.

    C'est aussi, en soi, la reponse au mandat : le client demande une
    protection contre l'inflation. Un jeu d'hypotheses aveugle au regime
    d'inflation ne peut pas y repondre.

PROVENANCE : chaque entree est etiquetee. On doit pouvoir dire au client,
ligne par ligne, si un chiffre est mesure, lu sur un ecran, ou suppose.
"""
from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------

MESURE = "mesure"          # estime sur nos propres series
MARCHE = "marche"          # lu sur le marche a une date donnee
HYPO = "hypothese"         # choix documente, a defendre

MARKET_DATE = "2026-09-17"

INFLATION_BASE = 0.020     # regime de reference : cible BCE / consensus
INFLATION_CLIENT = 0.040   # hypothese de M. Lauren -- un scenario de stress


@dataclass(frozen=True)
class Assumption:
    real_or_yield: float   # rendement nominal attendu dans le regime de base
    passthrough: float     # part d'une surprise d'inflation repercutee a 10 ans
    provenance: str
    source: str

    def expected(self, inflation: float = INFLATION_BASE) -> float:
        return self.real_or_yield + self.passthrough * (inflation - INFLATION_BASE)


# --------------------------------------------------------------------------
# Hypotheses par classe d'actifs
# --------------------------------------------------------------------------
#
# Coefficients de repercussion, a 10 ans :
#   1.0  l'actif suit integralement l'inflation (indexe, monetaire)
#   0.5  adaptation partielle (obligation a taux fixe : perte en capital
#        d'abord, puis reinvestissement progressif a taux plus eleve)
#   0.8  actions : pouvoir de fixation des prix, mais compression des
#        multiples en regime inflationniste -- la repercussion est reelle
#        mais incomplete
#   0.0  aucun lien mecanique

ASSUMPTIONS: dict[str, Assumption] = {
    "cash": Assumption(
        0.0205, 1.00, MESURE,
        "€STR implicite mesure sur XEON.DE, moyenne 3/6/12 mois au "
        f"{MARKET_DATE}. Le monetaire suit la politique monetaire, donc "
        "repercussion quasi integrale."),

    "govt_bonds_eur_short": Assumption(
        0.0225, 0.90, MARCHE,
        "Rendement actuariel du gisement souverain EUR 1-3 ans. Duration "
        "courte : le reinvestissement a taux plus eleve intervient vite."),

    "govt_bonds_eur": Assumption(
        0.0270, 0.45, MARCHE,
        "Rendement actuariel du gisement souverain zone euro toutes "
        "maturites. Pour un portefeuille a duration constante detenu au-dela "
        "de sa duration, le rendement actuariel d'entree est le meilleur "
        "predicteur du rendement a 10 ans. Repercussion faible : la perte en "
        "capital precede le benefice du reinvestissement."),

    "inflation_linked": Assumption(
        0.0250, 1.00, MARCHE,
        "Rendement reel du gisement indexe zone euro (~0,5 %) plus "
        "l'inflation du regime. Repercussion integrale PAR CONSTRUCTION : "
        "c'est la seule classe qui protege mecaniquement, et c'est ce qui "
        "justifie son poids de 10 % dans un mandat de preservation."),

    "credit_ig_eur": Assumption(
        0.0335, 0.50, MARCHE,
        "Rendement actuariel du credit IG euro, net d'une perte attendue par "
        "defaut de l'ordre de 10 pb. Repercussion voisine du souverain, la "
        "duration etant comparable."),

    "equity_developed": Assumption(
        0.0610, 0.80, HYPO,
        "Blocs constitutifs : rendement du dividende 1,9 % + rachats "
        "d'actions 1,0 % + croissance reelle des BPA 2,0 % + inflation 2,0 % "
        "− derive de valorisation 0,8 % (les multiples americains sont "
        "au-dessus de leur moyenne longue). A recouper avec JPM LTCMA et "
        "BlackRock CMA avant le pitch."),

    "equity_emerging": Assumption(
        0.0730, 0.75, HYPO,
        "Dividende 2,8 % + croissance reelle des BPA 3,0 % + inflation 2,0 % "
        "− derive 0,5 %. Prime par rapport aux developpes justifiee par la "
        "valorisation d'entree, pas par la croissance du PIB (lien "
        "empiriquement faible)."),

    "infrastructure": Assumption(
        0.0580, 0.90, HYPO,
        "Dividende 3,2 % + croissance reelle 1,5 % + inflation 2,0 % "
        "− derive 0,9 %. FORTE repercussion : les revenus d'infrastructure "
        "sont contractuellement indexes. C'est la brique de protection "
        "inflation la plus directe apres les obligations indexees."),

    "gold": Assumption(
        0.0250, 1.00, HYPO,
        "Rendement reel long terme proche de 0,5 %, plus l'inflation. L'or "
        "ne produit aucun flux : sa valeur attendue est la preservation du "
        "pouvoir d'achat, pas la performance. On le detient pour la "
        "decorrelation et contre la defiance monetaire, pas pour son "
        "esperance de rendement."),

    "alternatives": Assumption(
        0.0330, 1.10, HYPO,
        "Matieres premieres diversifiees : collateral (taux monetaire) "
        "+ rendement de portage + spot. Repercussion SUPERIEURE A 1 : les "
        "matieres premieres sont souvent la CAUSE de la surprise "
        "d'inflation, pas seulement sa victime."),

    "crypto": Assumption(
        0.0000, 0.00, HYPO,
        "Esperance comptee a ZERO, deliberement. Non parce qu'elle serait "
        "nulle, mais parce qu'elle n'est pas estimable avec une precision "
        "utile. Porter une esperance positive sur 2 % du portefeuille "
        "reviendrait a financer l'objectif du client avec l'actif le moins "
        "fiable du portefeuille. Toute performance sera un bonus, jamais un "
        "element du plan."),
}


def expected_returns(inflation: float = INFLATION_BASE) -> dict[str, float]:
    return {k: a.expected(inflation) for k, a in ASSUMPTIONS.items()}


def portfolio_return(weights: dict[str, float],
                     inflation: float = INFLATION_BASE) -> float:
    er = expected_returns(inflation)
    return sum(w * er[k] for k, w in weights.items() if k in er)


def provenance_table() -> list[tuple[str, str, str]]:
    return [(k, a.provenance, a.source) for k, a in ASSUMPTIONS.items()]
