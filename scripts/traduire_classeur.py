"""
Traduit un classeur de risque en anglais — SANS LE RECALCULER.

POURQUOI PASSER PAR LE XML ET NON PAR openpyxl. Le classeur d'Allan a été
ouvert, modifié et enregistré dans un tableur : il porte ses coupes (onglet de
lecture retiré, notes retirées, lignes VaR et CVaR retirées) et les valeurs
déjà calculées. Le relire avec openpyxl pour le réécrire perdrait ces valeurs
en cache — le fichier s'ouvrirait vide jusqu'au premier recalcul. On édite
donc les trois fichiers XML qui portent du texte (chaînes partagées, noms
d'onglets, formules) et on laisse tout le reste octet pour octet.

CE QUE LE PASSAGE CORRIGE AU PASSAGE. Le tableur qui a enregistré le fichier
n'a pas reconnu STDEV.S quand elle est imbriquée dans IFERROR : il l'a marquée
`_xludf.STDEV.S`, c'est-à-dire « fonction définie par l'utilisateur, inconnue ».
Les 23 cellules concernées — tous les Sharpe du classeur — n'ont AUCUNE valeur
en cache et affichent #NOM? à l'ouverture. Elles sont réécrites `_xlfn.STDEV.S`,
qui est la forme qu'Excel attend, et le classeur est marqué « à recalculer à
l'ouverture » pour qu'elles se remplissent seules.

    python3 scripts/traduire_classeur.py outputs/Mandat_Lauren_excel.xlsx
"""
from __future__ import annotations

import html
import re
import shutil
import sys
import zipfile
from pathlib import Path

# Les onglets. Un nom sans espace n'a pas besoin de guillemets dans une
# formule ; un nom qui en contient en garde.
FEUILLES = {
    "Portefeuille": "Portfolio",
    "Covariance": "Covariance",
    "Corrélation": "Correlation",
    "Risque": "Risk",
    "Actions": "Equities",
    "Données": "Data",
    "Données quotidiennes": "Daily data",
    "Données actions": "Equity data",
}

# Les références d'onglet dans les formules, des plus longues aux plus
# courtes : remplacer « Données! » d'abord casserait « Données actions! ».
REFS = [
    ("'Données quotidiennes'!", "'Daily data'!"),
    ("'Données actions'!", "'Equity data'!"),
    ("'Données'!", "Data!"),
    ("Données!", "Data!"),
]

TRAD = {
    # --- en-têtes des blocs de données
    "Date": "Date",
    "Niveaux (données)": "Levels (data)",
    "Niveaux quotidiens (données)": "Daily levels (data)",
    "Variations hebdomadaires": "Weekly returns",
    "Log-variations (pour le rendement annualisé)":
        "Log returns (for the annualised return)",
    "Excès sur le sans-risque": "Excess over the risk-free rate",
    "Écart à l'indice (pour le suivi)": "Active return vs index (for tracking)",
    "Baisse depuis le plus haut": "Drawdown from the peak",
    # --- les supports
    "Portefeuille retenu": "Selected portfolio",
    "Poche actions": "Equity sleeve",
    "États courts AAA": "Short-dated AAA govies",
    "États longs": "Long-dated govies",
    "Obligations indexées": "Inflation-linked bonds",
    "Or": "Gold",
    "Panier équipondéré": "Equal-weighted basket",
    "STOXX Europe 600": "STOXX Europe 600",
    "STOXX Europe 600 (indice)": "STOXX Europe 600 (index)",
    "Sans risque": "Risk-free",
    "Panier, 15 titres à parts égales": "Basket, 15 equally weighted holdings",
    # --- onglet Portefeuille
    "Le portefeuille et ses cinq poches": "The portfolio and its five sleeves",
    "Rendement annualisé %": "Annualised return %",
    "Volatilité annuelle %": "Annual volatility %",
    "Sharpe": "Sharpe ratio",
    "Bêta / poche actions": "Beta vs equity sleeve",
    "Pire baisse depuis le plus haut % (quotidien)":
        "Maximum drawdown % (daily data)",
    "Semaines mesurées": "Weeks measured",
    "VaR 95 % hebdomadaire %": "Weekly 95% VaR %",
    "CVaR 95 % hebdomadaire %": "Weekly 95% CVaR %",
    # --- onglets Covariance et Corrélation
    "Covariance des cinq supports détenus":
        "Covariance of the five holdings",
    "Corrélation des cinq supports détenus":
        "Correlation of the five holdings",
    # --- onglet Risque
    "D'où vient le risque du portefeuille":
        "Where the portfolio's risk comes from",
    "Support": "Holding",
    "Poids": "Weight",
    "Poids %": "Weight %",
    "Volatilité de la ligne %": "Volatility of the holding %",
    "Covariance avec le portefeuille": "Covariance with the portfolio",
    "Contribution marginale %": "Marginal contribution %",
    "Contribution au risque %": "Risk contribution %",
    "Part du risque %": "Share of risk %",
    "Total": "Total",
    "Variance du portefeuille (annuelle)": "Portfolio variance (annual)",
    "Volatilité du portefeuille %": "Portfolio volatility %",
    "À lire": "How to read this",
    "La part du risque se compare à la part du capital (colonne C). L'écart "
    "entre les deux est la concentration du risque.":
        "The share of risk is to be read against the share of capital "
        "(column C). The gap between the two is the concentration of risk.",
    "Deux volatilités, et pourquoi": "Two volatilities, and why",
    "Celle-ci (cellule B12) est DÉDUITE de la matrice de covariance, à poids "
    "constants. L'onglet « Portefeuille » en donne une autre, MESURÉE sur le "
    "chemin réellement suivi, qui est rééquilibré une fois par mois et dérive "
    "entre deux rééquilibrages. L'écart entre les deux — quelques centièmes "
    "de point — est le coût de cette dérive. Les deux sont justes ; c'est la "
    "première qui se décompose ligne à ligne.":
        "This one (cell B12) is IMPLIED by the covariance matrix, at constant "
        "weights. The « Portfolio » tab gives another one, MEASURED "
        "on the path actually followed, which is rebalanced once a month and "
        "drifts in between. The gap between the two — a few hundredths "
        "of a point — is the cost of that drift. Both are right; it is "
        "the first that breaks down holding by holding.",
    # --- onglet Actions
    "Les 15 titres détenus, à parts égales":
        "The 15 holdings, equally weighted",
    "Ticker": "Ticker",
    "Société": "Company",
    "Secteur": "Sector",
    "Pays": "Country",
    "Rendement annualisé % (biaisé)": "Annualised return % (biased)",
    "Bêta / STOXX 600": "Beta vs STOXX 600",
    "Tracking error %": "Tracking error %",
    "Ratio d'information (biaisé)": "Information ratio (biased)",
    "Valorisation": "Valuation",
    "Croissance": "Growth",
    "Dynamique": "Momentum",
    "Qualité": "Quality",
    "Résistance": "Resilience",
    "Note des 5 piliers": "Five-pillar score",
    "Note avenir (analystes)": "Forward score (analysts)",
    "Potentiel vs cible %": "Upside to target price %",
    "Révisions de BPA 30 j %": "EPS revisions, 30 days %",
    "Solde hausses − baisses %": "Net upgrades − downgrades %",
    "Nombre d'analystes": "Number of analysts",
    # --- secteurs
    "Technologie": "Technology",
    "Finance": "Financials",
    "Industrie": "Industrials",
    "Services aux collectivités": "Utilities",
    "Santé": "Health care",
    "Consommation discrétionnaire": "Consumer discretionary",
    "Consommation de base": "Consumer staples",
    "Télécoms et médias": "Telecoms & media",
    "Énergie": "Energy",
    # --- pays
    "Pays-Bas": "Netherlands",
    "Italie": "Italy",
    "Royaume-Uni": "United Kingdom",
    "Espagne": "Spain",
    "Autriche": "Austria",
    "Belgique": "Belgium",
    "Norvège": "Norway",
    "France": "France",
    "Finlande": "Finland",
    # --- titres des onglets de données
    "Données": "Data",
    "Données quotidiennes": "Daily data",
    "Données actions": "Equity data",
    "Données — niveaux hebdomadaires et colonnes calculées":
        "Data — weekly levels and calculated columns",
    "Données actions — niveaux hebdomadaires et colonnes calculées":
        "Equity data — weekly levels and calculated columns",
    "Données quotidiennes — pour la seule pire baisse":
        "Daily data — for the maximum drawdown only",
}

# Ce qui ne se traduit pas : raisons sociales et codes de cotation.
GARDER = re.compile(
    r"^[A-Z0-9][A-Z0-9 .&'\-]*$"          # ASML HOLDING, ANHEUSER-BUSCH…
    r"|^[A-Z0-9]{2,6}\.[A-Z]{2}$"         # ASML.AS, NXT.L…
)


def traduire_chaines(xml: str) -> tuple[str, list[str]]:
    """Réécrit les <t> de xl/sharedStrings.xml. Renvoie les oubliés."""
    oublies: list[str] = []

    def un(m: re.Match) -> str:
        ouvrant, contenu, fermant = m.group(1), m.group(2), m.group(3)
        brut = html.unescape(contenu)
        if brut in TRAD:
            return ouvrant + html.escape(TRAD[brut], quote=False) + fermant
        if not GARDER.match(brut.strip()):
            oublies.append(brut)
        return m.group(0)

    return re.sub(r"(<t(?:\s[^>]*)?>)(.*?)(</t>)", un, xml, flags=re.S), oublies


def traduire_formules(xml: str) -> tuple[str, int]:
    """Renomme les onglets dans les formules et répare les STDEV.S cassées."""
    def une(m: re.Match) -> str:
        f = m.group(2)
        for a, b in REFS:
            f = f.replace(a, b)
        return m.group(1) + f + m.group(3)

    xml = re.sub(r"(<f(?:\s[^>]*)?>)(.*?)(</f>)", une, xml, flags=re.S)
    casses = xml.count("_xludf.")
    return xml.replace("_xludf.", "_xlfn."), casses


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else
               "outputs/Mandat_Lauren_excel.xlsx")
    if not src.exists():
        print(f"introuvable : {src}")
        return 1
    dst = src.with_name(src.stem + "_EN.xlsx")

    zin = zipfile.ZipFile(src)
    oublies: list[str] = []
    reparees = 0
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            nom = item.filename
            if nom == "xl/sharedStrings.xml":
                t, oublies = traduire_chaines(data.decode("utf-8"))
                data = t.encode("utf-8")
            elif nom.startswith("xl/worksheets/sheet"):
                t, c = traduire_formules(data.decode("utf-8"))
                reparees += c
                data = t.encode("utf-8")
            elif nom in ("xl/workbook.xml", "docProps/app.xml"):
                t = data.decode("utf-8")
                for fr, en in sorted(FEUILLES.items(),
                                     key=lambda kv: -len(kv[0])):
                    t = t.replace(f'name="{fr}"', f'name="{en}"')
                    t = t.replace(f"<vt:lpstr>{fr}</vt:lpstr>",
                                  f"<vt:lpstr>{en}</vt:lpstr>")
                # les Sharpe réparées n'ont pas de valeur en cache : sans
                # ceci elles resteraient vides jusqu'à une modification
                t = t.replace("<calcPr calcId=",
                              '<calcPr fullCalcOnLoad="1" calcId=')
                data = t.encode("utf-8")
            zout.writestr(item, data)
    zin.close()

    print(f"écrit : {dst}")
    print(f"formules STDEV.S réparées : {reparees}")
    if oublies:
        print(f"NON TRADUIT ({len(set(oublies))}) :")
        for o in sorted(set(oublies)):
            print(f"   {o!r}")
        return 1
    print("aucune chaîne française oubliée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
