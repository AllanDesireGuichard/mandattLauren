"""
IPS — parametres du mandat Lauren.

Source unique de verite. Le document docs/02_ips.md est la version redigee de
ce module ; toute modification ici doit y etre repercutee.
"""
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Client et actifs
# --------------------------------------------------------------------------

TOTAL_ASSETS = 100_000_000.0      # EUR — hypothese : produit de cession deja converti
LIQUIDITY_NEED = 10_000_000.0     # EUR — a decaisser sous 24 mois
CLIENT_AGE = 60
N_CHILDREN = 2
BASE_CURRENCY = "EUR"

# --------------------------------------------------------------------------
# Objectif de rendement  (cf. docs/02_ips.md §3)
# --------------------------------------------------------------------------

INFLATION_TARGET = 0.0400         # objectif de preservation du pouvoir d'achat
MANDATE_FEE = 0.0040              # frais de mandat negocies
INSTRUMENT_TER = 0.0015           # TER moyen pondere, gestion indicielle

# Friction fiscale ANNUELLE. Chiffres revus a la baisse apres reexamen :
# l'ancienne comparaison (0,35 % contre 1,20 %) opposait une structure
# optimisee a un CTO garni de fonds DISTRIBUANTS -- un homme de paille, que
# personne de competent ne mettrait en place. La vraie comparaison est
# ci-dessous, et l'ecart annuel est bien plus mince qu'annonce.
TAX_DRAG_STRUCTURED = 0.0030      # AV LUX + ETF capitalisants + domicile irlandais
TAX_DRAG_CTO_COMPETENT = 0.0045   # CTO bien gere, ETF capitalisants
TAX_DRAG_CTO_NAIF = 0.0090        # CTO, supports distribuants
TAX_DRAG_UNSTRUCTURED = TAX_DRAG_CTO_COMPETENT

TOTAL_FEES = MANDATE_FEE + INSTRUMENT_TER


def required_gross_return(drag: float = TAX_DRAG_STRUCTURED,
                          inflation: float | None = None) -> float:
    """Rendement brut annuel requis pour preserver le pouvoir d'achat."""
    infl = INFLATION_TARGET if inflation is None else inflation
    return infl + TOTAL_FEES + drag


TARGET_GROSS_RETURN = round(required_gross_return(), 4)

# --------------------------------------------------------------------------
# Contrainte de risque  (cf. docs/02_ips.md §4)
# --------------------------------------------------------------------------

MAX_DRAWDOWN = 0.15               # pic a creux, 12 mois glissants, consolide EUR
DD_BREACH_PROBABILITY = 0.10      # tolerance de depassement

# ESTIME, PAS ASSUME.  scripts/estimate_dd_ratio.py + validate_saa_risk.py,
# 21,8 ans de donnees quotidiennes en EUR (2004-2026 : GFC, 2011, 2020, 2022).
#
# Valeur precedente : 1.9, posee comme "regle empirique". FAUSSE et trop
# conservatrice -- elle sous-allouait le risque d'environ 10 points d'actions.
#
# Le ratio n'est PAS constant : il decroit avec le poids d'actions
# (1,81 a 20 % d'actions -> 1,33 a 80 %) parce que la diversification
# obligataire agit davantage sur le drawdown que sur la volatilite.
# Pour un portefeuille multi-actifs diversifie comme le notre : 1,33-1,36.
DD_TO_VOL_RATIO = 1.35

# Budget de risque retenu : PAS derive du ratio, mais lu directement sur la
# SAA testee (data/saa_risk.csv). Marge deliberee sous les 15 %, parce que
# l'estimation elle-meme porte une erreur.
TARGET_VOL = 0.099                # SAA a 47 % d'actifs de croissance
EXPECTED_DD_P90 = 0.133           # mesure -> 1,7 pt de marge sous la contrainte
TARGET_VOL_RISKY = TARGET_VOL / 0.90

# CE QUE LE CLIENT DOIT SAVOIR, ET QUE LE P90 MASQUE.
# Le pire drawdown observe sur la periode n'est pas 13 % mais 26 % (2008).
# La contrainte de 15 % est tenue "moins d'une annee sur dix", pas "jamais".
WORST_OBSERVED_DD = 0.263         # SAA au niveau de risque retenu, 2008
DD_2022 = 0.133

# --------------------------------------------------------------------------
# Architecture en poches  (cf. docs/02_ips.md §6.1)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Bucket:
    code: str
    name: str
    amount: float
    horizon_years: tuple[int, int]
    target_vol: float
    wrapper: str
    rationale: str

    @property
    def weight(self) -> float:
        return self.amount / TOTAL_ASSETS


BUCKETS: tuple[Bucket, ...] = (
    Bucket(
        "A", "Liquidite", 10_000_000, (0, 2), 0.010,
        "Compte-titres / depots",
        "Engagement date et certain : preservation nominale, aucune prise de risque.",
    ),
    Bucket(
        "B", "Coeur patrimonial", 58_000_000, (10, 20), 0.070,
        "Assurance-vie luxembourgeoise",
        "Niveau de vie du client, protege de l'inflation. Risque modere.",
    ),
    Bucket(
        "C", "Transmission", 30_000_000, (25, 30), 0.120,
        "AV LUX + donation demembree",
        "Horizon superieur a l'esperance de vie du client : le risque est "
        "remunere par le temps et dilue par les poches A et B.",
    ),
    Bucket(
        "D", "Satellite", 2_000_000, (10, 30), 0.500,
        "Compartiment dedie",
        "Convictions plafonnees, dont crypto. Loge dans la poche longue.",
    ),
)

# --------------------------------------------------------------------------
# Contraintes  (cf. docs/02_ips.md §5)
# --------------------------------------------------------------------------

ESG_EXCLUSIONS = {
    "tobacco":       {"production": 0.00, "distribution": 0.05},
    "weapons":       {"controversial": 0.00, "conventional": 0.05},
    "thermal_coal":  {"extraction": 0.05, "power_generation": 0.05},
}

UCITS_ONLY = True                 # resident francais retail, contrainte PRIIPs

CONCENTRATION_LIMITS = {
    "single_line": 0.10,
    "single_asset_class": 0.40,
    "growth_assets": 0.60,
    "crypto": 0.02,
    "single_issuer": 0.05,        # hors dette souveraine core
    "illiquid": 0.15,             # poche C uniquement
}

MIN_DAILY_LIQUIDITY = 0.80        # poches B et C

# --------------------------------------------------------------------------
# Couverture de change  (cf. docs/02_ips.md §6.4)
# --------------------------------------------------------------------------

FX_HEDGE_RATIO = {
    "bonds_international": 1.00,   # vol FX (8-10 %) > vol actif (4-5 %)
    "equity_developed_ex_emu": 0.40,  # USD = couverture naturelle en stress
    "equity_emerging": 0.00,       # devise = moteur de performance
    "gold": 0.00,                  # couvrir annulerait la reserve de valeur
    "alternatives": 0.50,
}

# --------------------------------------------------------------------------
# Allocation strategique indicative  (a confirmer par optimisation)
# --------------------------------------------------------------------------

# SAA corrigee apres validation empirique (scripts/validate_saa_risk.py).
# Correction 1 : le poids d'actions passe de 52 % a 47 % -- non pas par
#   prudence, mais parce que l'ancien chiffre etait incoherent avec la
#   volatilite cible annoncee (52 % d'actions ne font pas 7,9 % de vol,
#   ils en font ~10,8 %).
# Correction 2 : la poche A pesait 10 % des actifs mais la SAA n'affichait
#   que 5 % de cash. Les 5 % manquants sont desormais explicites en
#   souverain court, qui est bien ce que decrit l'IPS §6.2.
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
    "govt_bonds_eur_short":  0.05,   # poche A
    "cash":                  0.05,   # poche A
}

# Issue de scripts/optimize_saa.py (second passage), puis DE-RISQUEE apres les
# stress tests de l'etape 4.
#
# L'allocation issue de l'optimisation (croissance 50 %) ressortait a 14,1 %
# de drawdown P90 et 9,2 % de probabilite de depassement -- soit juste sous
# les seuils de 15 % et 10 %. Elle satisfaisait la contrainte, sans marge.
#
# Or l'estimation elle-meme porte une erreur : un seul bug d'echelle avait
# deja deplace ce chiffre de 12,0 % a 14,1 %. Construire a la limite d'une
# mesure aussi sensible n'est pas defendable.
#
# De-risquage par ROTATION vers l'obligataire et l'or, PAS vers le monetaire :
# la poche A est dimensionnee sur le besoin de liquidite de 10 M EUR, la
# gonfler reviendrait a confondre deux decisions distinctes.
#   croissance   50 % -> 45 %
#   obligataire  30 % -> 34 %
#   actifs reels 10 % -> 11 %
# Cout : 19 pb de rendement. Gain : 1,5 pt de marge sur le drawdown.
#
# PARTAGE DE LA POCHE A -- decision hors optimisation.
#   L'optimiseur place les 10 % integralement en monetaire : a rendement
#   voisin, 0,4 % de volatilite domine 1,6 %. Economiquement juste, mais il
#   raisonne en risque, pas en ADOSSEMENT. La poche A finance un decaissement
#   date : on echelonne 5 % de monetaire et 5 % de souverain court sur le
#   calendrier de depense (IPS §6.2).
#   A soulever avec le client : si les dates de depense sont incertaines, le
#   tout-monetaire est preferable ; si elles sont connues, l'echelonnement
#   rapporte ~20 pb de plus.

# Poche A = liquidites + souverain court. 10 % des actifs, coherent avec
# BUCKETS et avec le diviseur de TARGET_VOL_RISKY.
LIQUIDITY_SLEEVE = ("cash", "govt_bonds_eur_short")

# Hypotheses de rendement : voir core/cma.py, qui porte le detail des blocs
# constitutifs, la provenance de chaque entree, et surtout la COHERENCE DU
# REGIME D'INFLATION -- le seuil et les rendements attendus sont desormais
# evalues dans le meme regime.


def expected_gross_return(inflation: float | None = None) -> float:
    from core.cma import INFLATION_CLIENT, portfolio_return
    return portfolio_return(SAA_INDICATIVE,
                            INFLATION_CLIENT if inflation is None else inflation)


GROWTH_ASSETS = ("equity_developed", "equity_emerging", "infrastructure", "crypto")
REAL_ASSETS = ("gold", "infrastructure", "inflation_linked")

# --------------------------------------------------------------------------
# Gouvernance  (cf. docs/02_ips.md §9)
# --------------------------------------------------------------------------

REBALANCING_BAND = 0.03           # +/- 3 points autour de la cible
REVIEW_TRIGGER_DD = 0.10          # 2/3 du budget de risque -> revue exceptionnelle

TACTICAL_BANDS = {
    "growth":  (0.40, 0.50, 0.60),   # (min, cible, max)
    "bonds":   (0.22, 0.30, 0.38),
    "real":    (0.10, 0.15, 0.20),
    "cash":    (0.02, 0.05, 0.15),
}

# --------------------------------------------------------------------------
# Fiscalite et transmission  (cf. docs/02_ips.md §7)
# --------------------------------------------------------------------------

PFU_RATE = 0.30                   # flat tax : 12.8 % IR + 17.2 % PS
CORPORATE_TAX_RATE = 0.25         # IS, si holding patrimoniale

# Bareme art. 669 CGI — valeur de l'usufruit par tranche d'age du donateur.
# Le passage 60 -> 61 ans fait chuter l'usufruit de 50 % a 40 %, donc monte
# la nue-propriete taxable de 50 % a 60 %. Point de calendrier critique.
USUFRUCT_SCALE = {
    (0, 20): 0.90, (21, 30): 0.80, (31, 40): 0.70, (41, 50): 0.60,
    (51, 60): 0.50, (61, 70): 0.40, (71, 80): 0.30, (81, 90): 0.20,
    (91, 120): 0.10,
}


def bare_ownership_value(age: int) -> float:
    """Valeur taxable de la nue-propriete donnee, selon l'age du donateur."""
    for (lo, hi), usufruct in USUFRUCT_SCALE.items():
        if lo <= age <= hi:
            return 1.0 - usufruct
    raise ValueError(f"age hors bareme : {age}")


DONATION_ALLOWANCE = 100_000.0    # par parent, par enfant, tous les 15 ans
DONATION_ALLOWANCE_PERIOD = 15

# Assurance-vie, primes versees avant 70 ans (art. 990 I CGI)
AV_ALLOWANCE_PER_BENEFICIARY = 152_500.0
AV_RATE_LOW = 0.20                # jusqu'a 700 k€ au-dela de l'abattement
AV_RATE_HIGH = 0.3125             # au-dela
AV_THRESHOLD = 700_000.0
AV_AGE_LIMIT = 70                 # fenetre fermant aux 70 ans du client

# Bareme des droits de succession en ligne directe (art. 777 CGI)
SUCCESSION_ALLOWANCE = 100_000.0  # par parent, par enfant
SUCCESSION_SCALE = (
    (8_072,     0.05), (12_109,    0.10), (15_932,    0.15),
    (552_324,   0.20), (902_838,   0.30), (1_805_677, 0.40),
    (float("inf"), 0.45),
)

WITHHOLDING_TAX = {               # retenue a la source sur dividendes US
    "ireland_domiciled": 0.15,    # convention fiscale Irlande - Etats-Unis
    "luxembourg_domiciled": 0.30,
}

# --------------------------------------------------------------------------

def feasibility() -> list[tuple[str, float, str]]:
    """
    Ecart entre rendement attendu et rendement requis, dans les deux regimes
    d'inflation.

    CORRECTION MAJEURE (v1.2). La v1.1 annoncait une marge de -0,09 %. Elle
    comparait un seuil bati sur 4 % d'inflation a des rendements attendus
    batis implicitement sur 2 %. Une fois le regime rendu coherent
    (cf. core/cma.py), la marge est POSITIVE dans les deux cas.
    """
    from core.cma import INFLATION_BASE, INFLATION_CLIENT

    out = []
    for label, infl in [("Consensus BCE (inflation 2 %)", INFLATION_BASE),
                        ("Hypothese client (inflation 4 %)", INFLATION_CLIENT)]:
        gap = expected_gross_return(infl) - required_gross_return(inflation=infl)
        out.append((label, gap, "regime coherent seuil / rendements"))

    exp = expected_gross_return()
    out.append(("  frais de mandat 0,40 % -> 0,25 %",
                exp - (INFLATION_TARGET + 0.0025 + INSTRUMENT_TER
                       + TAX_DRAG_STRUCTURED),
                "negociable sur 100 M EUR"))
    out.append(("  sans structuration fiscale",
                exp - required_gross_return(TAX_DRAG_CTO_COMPETENT),
                "l'ecart annuel reste modeste : 15 bps"))
    out.append(("  sans structuration du tout",
                exp - required_gross_return(TAX_DRAG_CTO_NAIF),
                "60 bps : c'est la que l'erreur coute"))
    return out


def summary() -> dict:
    """Parametres cles, pour affichage Streamlit et controle de coherence."""
    return {
        "Actifs":                    f"{TOTAL_ASSETS:,.0f} EUR",
        "Besoin de liquidite":       f"{LIQUIDITY_NEED:,.0f} EUR",
        "Inflation cible":           f"{INFLATION_TARGET:.2%}",
        "Rendement brut requis":     f"{required_gross_return():.2%}",
        "  sans structuration":      f"{required_gross_return(TAX_DRAG_CTO_COMPETENT):.2%}",
        "Rendement brut attendu":    f"{expected_gross_return():.2%}",
        "  marge":                   f"{expected_gross_return()-required_gross_return():+.2%}",
        "  (inflation 2 %)":         f"{expected_gross_return(0.02):.2%}"
                                     f" vs {required_gross_return(inflation=0.02):.2%}",
        "Volatilite cible":          f"{TARGET_VOL:.2%}",
        "Drawdown maximum":          f"{MAX_DRAWDOWN:.0%} (12m, P<{DD_BREACH_PROBABILITY:.0%})",
        "  P90 mesure":              f"{EXPECTED_DD_P90:.1%}",
        "  pire cas observe (2008)": f"{WORST_OBSERVED_DD:.1%}",
        "Nue-propriete a 60 ans":    f"{bare_ownership_value(60):.0%}",
        "Nue-propriete a 61 ans":    f"{bare_ownership_value(61):.0%}",
    }


if __name__ == "__main__":
    for k, v in summary().items():
        print(f"{k:<28} {v}")
    print()
    total = sum(b.amount for b in BUCKETS)
    assert abs(total - TOTAL_ASSETS) < 1, f"poches = {total:,.0f}"
    w = sum(SAA_INDICATIVE.values())
    assert abs(w - 1.0) < 1e-9, f"SAA = {w}"
    growth = sum(SAA_INDICATIVE[k] for k in GROWTH_ASSETS)
    assert growth <= CONCENTRATION_LIMITS["growth_assets"], f"growth = {growth}"
    print(f"Poches          {total:,.0f} EUR  OK")
    print(f"SAA             {w:.0%}  OK")
    print(f"Actifs croissance {growth:.0%}  (plafond {CONCENTRATION_LIMITS['growth_assets']:.0%})  OK")
    sleeve = sum(SAA_INDICATIVE[k] for k in LIQUIDITY_SLEEVE)
    a = [b for b in BUCKETS if b.code == "A"][0]
    assert abs(sleeve - a.weight) < 1e-9, f"poche A {a.weight} vs SAA {sleeve}"
    print(f"Poche A vs SAA  {sleeve:.0%} = {a.weight:.0%}  OK")
    print()
    print("FAISABILITE  (ecart rendement attendu - requis)")
    for label, gap, note in feasibility():
        print(f"  {gap:+.2%}  {label}")
        print(f"           {note}")
