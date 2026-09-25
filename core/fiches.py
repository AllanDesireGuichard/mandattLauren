"""
Une ligne par titre retenu : ce que fait la société, et pourquoi elle est là.

Demande d'Allan du 2026-09-25 : l'application doit être factuelle et rapide,
« avec descriptions de chaque titre retenu », et la description doit dire
« le métier et pourquoi ce titre est dans le portefeuille ».

DEUX MOITIÉS, ET ELLES N'ONT PAS LE MÊME STATUT.

  LE MÉTIER est rédigé à la main, à partir de la description d'activité de
  Yahoo (`longBusinessSummary`), qui est en anglais, de longueur très
  inégale, et souvent noyée dans une liste de segments comptables. Elle est
  donc résumée en une phrase française. C'est du texte, il est daté, et il
  doit être relu quand la sélection change.

  LE POURQUOI est rédigé à la main pour la partie qualitative, mais SES
  CHIFFRES SONT CALCULÉS. Le pilier le plus fort de la société, sa valeur,
  et la révision de son bénéfice attendu ne sont pas recopiés ici : ils sont
  lus dans la sélection à l'affichage. C'est délibéré — une raison écrite en
  dur se périme au premier relevé suivant, et personne ne s'en aperçoit.

CE QUI SE PASSE SI LA SÉLECTION CHANGE. Un titre qui entre sans avoir de
fiche n'est pas une erreur : `table()` le montre avec sa mention « fiche à
rédiger » plutôt que de le cacher ou de planter. L'application dit alors
elle-même ce qu'il lui manque.
"""
from __future__ import annotations

import pandas as pd

from core import scoring, viz

A_REDIGER = "— fiche à rédiger —"

# ticker : (le métier, la raison qualitative[, le pilier à citer])
#
# La raison ne répète JAMAIS un chiffre : il est ajouté par `table()`. Le
# TROISIÈME champ, facultatif, force le pilier affiché quand la raison en
# nomme un qui n'est pas le plus fort de la société — sans lui, la ligne
# d'InterContinental parlait de résistance et le chiffre montrait la
# dynamique. Une raison et son chiffre qui se contredisent valent moins que
# pas de raison du tout.
FICHES = {
    "ASML.AS": (
        "Fabrique les machines de lithographie qui gravent les puces, et "
        "reste le seul fournisseur au monde des machines à ultraviolets "
        "extrêmes.",
        "Le meilleur dossier des trente sur l'avenir",
    ),
    "UNI.MI": (
        "Assureur italien, dommages et vie, adossé à des participations "
        "bancaires.",
        "Consensus en redressement franc et unanime",
    ),
    "DPLM.L": (
        "Distribue des produits techniques de spécialité — joints, "
        "instruments de contrôle, consommables de laboratoire — au "
        "Royaume-Uni et en Amérique du Nord.",
        "Croissance et dynamique parmi les meilleures du panier",
    ),
    "ELE.MC": (
        "Produit, distribue et vend de l'électricité en Espagne et au "
        "Portugal.",
        "Défensive régulée, la plus forte dynamique de marché des quinze",
    ),
    "BG.VI": (
        "Banque autrichienne de détail et d'entreprise, également présente "
        "en Allemagne, en Irlande et aux Pays-Bas.",
        "La deuxième meilleure révision de bénéfice du panier",
    ),
    "NTGY.MC": (
        "Transporte, stocke, distribue et vend du gaz en Espagne et à "
        "l'international.",
        "La moins chère des quinze face à son secteur",
    ),
    "ARGX.BR": (
        "Biotechnologie belge, traitements des maladies auto-immunes ; son "
        "produit principal traite la myasthénie.",
        "La meilleure note des trente sur les cinq piliers",
    ),
    "NXT.L": (
        "Distribue vêtements, maison et beauté au Royaume-Uni, en magasin "
        "et en ligne, et loue sa plateforme logistique à d'autres marques.",
        "Qualité et dynamique équilibrées, sans point faible",
    ),
    "VAR.OL": (
        "Produit du pétrole et du gaz sur le plateau continental norvégien.",
        "La seule énergie du panier, et son consensus se relève",
    ),
    "IHG.L": (
        "Exploite et franchise des hôtels — Holiday Inn, Crowne Plaza, "
        "InterContinental — dans une centaine de pays.",
        "La meilleure tenue en crise des quinze : un franchiseur "
        "n'immobilise pas les murs",
        "Résistance",
    ),
    "PUB.PA": (
        "Publicité, communication et transformation numérique, pour des "
        "annonceurs mondiaux.",
        "Forte dynamique de marché et révisions majoritairement en hausse",
    ),
    "ABI.BR": (
        "Premier brasseur mondial, présent sur tous les continents.",
        "Croissance rare pour une défensive de cette taille — deuxième du "
        "panier derrière Airtel",
    ),
    "ORNBV.HE": (
        "Laboratoire finlandais, médicaments humains et vétérinaires ; "
        "traitements du cancer de la prostate et de la maladie de "
        "Parkinson.",
        "La qualité de bilan la plus élevée des quinze",
    ),
    "AAF.L": (
        "Téléphonie mobile et paiement par mobile au Nigeria, en Afrique de "
        "l'Est et en Afrique francophone.",
        "La croissance la plus forte du panier, sur un marché peu équipé",
    ),
    "AENA.MC": (
        "Exploite les aéroports espagnols, et des concessions au Brésil, au "
        "Mexique et au Royaume-Uni.",
        "Qualité élevée et bonne tenue en crise, sur une activité "
        "concédée",
    ),
}


def _chiffre(r: pd.Series, pilier: str | None = None) -> str:
    """Le fait mesuré qui appuie la raison. Lu dans la sélection, pas écrit."""
    piliers = {p: r[p] for p in scoring.PILIERS if pd.notna(r.get(p))}
    bouts = []
    if pilier and pilier in piliers:
        bouts.append(f"{pilier.lower()} {viz.fr(piliers[pilier], '', 2)}")
    elif piliers:
        nom, val = max(piliers.items(), key=lambda kv: kv[1])
        bouts.append(f"{nom.lower()} {viz.fr(val, '', 2)}")
    if pd.notna(r.get("revision")):
        bouts.append(f"bénéfice attendu {viz.fr(r['revision'], '%', 1)} "
                     f"sur 90 jours")
    return " · ".join(bouts)


def table(fin: pd.DataFrame) -> pd.DataFrame:
    """
    Une ligne par titre retenu : société, métier, pourquoi elle est là.

    `fin` : la sélection finale (sortie de core.outlook), qui porte les notes
    par pilier et les mesures d'avenir.
    """
    lignes = []
    for _, r in fin.iterrows():
        fiche = FICHES.get(r["ticker"])
        if fiche is None:
            metier = pourquoi = A_REDIGER
        else:
            metier, raison, *reste = fiche
            pourquoi = f"{raison} ({_chiffre(r, reste[0] if reste else None)})"
        lignes.append((r["longName"], r["secteur"], metier, pourquoi))
    return pd.DataFrame(lignes, columns=["Société", "Secteur", "Métier",
                                         "Pourquoi elle est là"])


def manquantes(fin: pd.DataFrame) -> list[str]:
    """Les titres retenus sans fiche, à rédiger. Vide en temps normal."""
    return [r["longName"] for _, r in fin.iterrows()
            if r["ticker"] not in FICHES]
