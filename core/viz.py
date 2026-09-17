"""
Palette et helpers graphiques.

Palette validee par scripts/validate_palette.js du referentiel dataviz :
  clair  #2a78d6,#eb6834,#1baf7a,#eda100  -- tous les controles passent,
         avec un AVERTISSEMENT de contraste sur l'aqua et le jaune. La regle
         d'appoint s'applique : chaque graphique porte des etiquettes
         visibles ET une vue tableau.
  sombre #3987e5,#d95926,#199e70,#c98500  -- tous les controles passent.

Regles suivies :
  - couleurs categorielles assignees dans un ORDRE FIXE, jamais cyclees
  - les 11 classes d'actifs sont repliees en 4 GROUPES : au-dela de 8 teintes
    aucune palette ne tient, et 11 categories ne se distinguent pas a l'oeil
  - une seule serie -> pas de legende, le titre la nomme
  - correlations -> palette divergente, gris neutre au point median
  - le texte porte des jetons de texte, jamais la couleur de serie
"""
from __future__ import annotations

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CATEGORICAL_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500"]

INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"

STATUS = {"good": "#008300", "warning": "#eda100", "critical": "#e34948"}

# Regroupement des 11 classes de la SAA en 4 familles lisibles.
# Les familles sont definies UNE SEULE FOIS, dans core/ips.py : elles sont
# une propriete de l'allocation, pas un choix graphique. Ici on ne fait
# que leur attacher une couleur et un libelle accentue.
from core.ips import FAMILIES  # noqa: E402

FAMILY_LABEL = {"Croissance": "Croissance", "Obligataire": "Obligataire",
                "Actifs reels": "Actifs réels", "Liquidite": "Liquidité"}
GROUPS = {FAMILY_LABEL[f]: list(c) for f, c in FAMILIES.items()}
GROUP_COLOR = dict(zip(GROUPS, CATEGORICAL))

LABEL = {
    "equity_developed": "Actions développées",
    "equity_emerging": "Actions émergentes",
    "infrastructure": "Infrastructure cotée",
    "crypto": "Crypto",
    "inflation_linked": "Obligations indexées",
    "govt_bonds_eur": "Souverain EUR",
    "credit_ig_eur": "Crédit IG EUR",
    "gold": "Or",
    "alternatives": "Alternatifs",
    "govt_bonds_eur_short": "Souverain EUR court",
    "cash": "Monétaire",
}


def group_of(cls: str) -> str:
    for g, members in GROUPS.items():
        if cls in members:
            return g
    return "Autre"


def color_of(cls: str) -> str:
    return GROUP_COLOR.get(group_of(cls), INK_2)


def layout(title: str = "", height: int = 380, **kw) -> dict:
    """Mise en page commune : grille discrete, axes recessifs, pas de fioriture."""
    base = {
        "title": {"text": title, "font": {"size": 15, "color": INK}, "x": 0},
        "height": height,
        "margin": {"l": 10, "r": 10, "t": 46 if title else 16, "b": 10},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": INK_2, "size": 12},
        "xaxis": {"gridcolor": GRID, "zerolinecolor": GRID,
                  "linecolor": GRID, "tickfont": {"color": INK_2}},
        "yaxis": {"gridcolor": GRID, "zerolinecolor": GRID,
                  "linecolor": GRID, "tickfont": {"color": INK_2}},
        "legend": {"orientation": "h", "y": -0.16, "x": 0,
                   "font": {"color": INK_2}},
        "hoverlabel": {"font": {"size": 12}},
    }
    base.update(kw)
    return base


def diverging(value: float) -> str:
    """Palette divergente pour les correlations : deux teintes, gris median."""
    if value > 0.05:
        return f"rgba(42,120,214,{min(abs(value), 1.0):.2f})"
    if value < -0.05:
        return f"rgba(235,104,52,{min(abs(value), 1.0):.2f})"
    return "rgba(140,138,132,0.25)"


DIVERGING_SCALE = [
    [0.0, "#eb6834"], [0.35, "#f6bda5"], [0.5, "#e6e5e1"],
    [0.65, "#a8c7ec"], [1.0, "#2a78d6"],
]
SEQUENTIAL_SCALE = [[0.0, "#e8f0fb"], [0.5, "#6ba3e3"], [1.0, "#1b4f91"]]


def fr(value: float, unit: str = "", dec: int = 1) -> str:
    """Nombre au format francais : virgule decimale, espace pour les milliers."""
    s = f"{value:,.{dec}f}".replace(",", " ").replace(".", ",")
    return f"{s} {unit}".strip()
