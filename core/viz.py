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
  - une seule serie -> pas de legende, le titre la nomme
  - le texte porte des jetons de texte, jamais la couleur de serie
"""
from __future__ import annotations

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CATEGORICAL_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500"]

# Paire divergente (polarite : de quel cote de zero). Les deux premieres
# couleurs categorielles servent de poles -- froid a gauche, chaud a droite --
# et le milieu est un gris neutre, jamais une teinte : au centre, le lecteur
# doit lire "rien". Bras interpoles en OKLab, quatre pas chacun, luminosite
# monotone verifiee. A n'employer que sur une echelle centree sur zero.
DIVERGENT = ["#2a78d6", "#6097de", "#90b5e4", "#c0d2e9", "#f0efec",
             "#f3cfc0", "#f3af95", "#f18d68", "#eb6834"]
DIVERGENT_MID = "#f0efec"


def echelle_divergente() -> list[list]:
    """La paire divergente au format d'echelle continue de Plotly."""
    n = len(DIVERGENT) - 1
    return [[i / n, c] for i, c in enumerate(DIVERGENT)]


INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"

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


def fr(value: float, unit: str = "", dec: int = 1) -> str:
    """Nombre au format francais : virgule decimale, espace pour les milliers."""
    s = f"{value:,.{dec}f}".replace(",", " ").replace(".", ",")
    return f"{s} {unit}".strip()
