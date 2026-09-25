"""
Fonds et ETF retenus pour les classes non investies en direct.

Lit data/fonds.json, produit par scripts/fetch_fonds.py (photo datée : frais,
taille et indice relevés sur justETF, prix et volumes sur Yahoo).

Deux constats vérifiés le 2026-09-18 et consignés ici parce qu'ils fondent
les verdicts de l'onglet :

1. EXCLUSIONS, lues dans les méthodologies MSCI (et non déduites du nom) :
   - « ESG Screened » exclut les armes controversées, nucléaires et civiles,
     le tabac et le charbon, mais PAS l'armement conventionnel. Or les
     actions en direct excluent tout le secteur aéronautique et défense :
     un fonds Screened contredirait la règle appliquée aux titres.
   - « SRI » exclut l'armement conventionnel dès 5 % du chiffre d'affaires,
     le tabac (producteurs) et le charbon (5 %).
   - « Low Carbon SRI Selection » (fonds Xtrackers « ESG ») reprend les
     critères SRI, y ajoute pétrole et gaz (5 %) et nucléaire (30 %), et ne
     garde que la moitié la mieux notée de chaque secteur : plus strict que
     le mandat, d'où un écart au marché plus grand.

2. L'UNIVERS HÉRITÉ CONTENAIT NEUF LIBELLÉS FAUX (CORRECTIONS ci-dessous).
   Les séries de prix étaient bien celles des vrais produits : c'est le nom
   qu'on leur avait donné qui était faux, ce qui explique qu'aucun contrôle
   de volatilité ne les ait repérés.
"""
from __future__ import annotations

import json
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "data" / "fonds.json"

# ticker, ce qu'on avait noté, ce que c'est vraiment (nom Yahoo du 2026-09-18)
CORRECTIONS = (
    ("JREU.L", "Obligations émergentes en euros (fonds principal)",
     "Actions américaines (JPMorgan US Research Enhanced)"),
    ("EUNH.DE", "Haut rendement en euros (fonds principal)",
     "Emprunts d'État de la zone euro"),
    ("EXH3.DE", "Services aux collectivités européens",
     "Agroalimentaire européen"),
    ("STHE.L", "Obligations indexées sur l'inflation en euros",
     "Haut rendement américain court, couvert en euros (PIMCO)"),
    ("SPXS.L", "Actions américaines avec filtre ESG",
     "Actions américaines sans aucun filtre"),
    ("XZWE.DE", "Actions européennes avec filtre ESG",
     "Actions mondiales avec filtre ESG, couvertes en euros"),
    ("EUNA.DE", "Emprunts d'État de la zone euro",
     "Obligations mondiales, couvertes en euros"),
    ("IEAG.L", "Obligations mondiales", "Obligations en euros avec filtre ESG"),
    ("AIGC.L", "Fonds UCITS de matières premières",
     "Titre de créance (ETC) de matières premières, hors cadre UCITS"),
)

# Les classes présentées comme investissables, dans l'ordre d'affichage.
# LE BITCOIN N'Y EST PAS, et c'est une correction du 2026-09-25 : la décision
# d'Allan du 2026-09-18 est « pas de crypto ». Le laisser dans cet ordre faisait
# annoncer à la conclusion de l'étape 3 un ETP Bitcoin parmi les supports
# retenus, quand l'étape 4 n'en détient pas un euro. Les mesures restent dans
# data/fonds.json — l'étape 4 dit pourquoi on n'en prend pas — mais le fonds
# n'est plus proposé.
ORDRE = ("usa", "japon", "emergents", "indexees", "or", "matieres")
HORS_UNIVERS = ("crypto",)

# Infrastructure RETIRÉE de l'univers (décision d'Allan, 2026-09-18) : aucun
# fonds ne passe à la fois les exclusions et la taille. Les mesures restent
# dans data/fonds.json pour montrer pourquoi.
RETIREES = ("infrastructure",)


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Contrôle des exclusions du mandat
# --------------------------------------------------------------------------
# Chaque candidat de data/fonds.json porte un champ `exclusions`, posé à la
# main dans scripts/fetch_fonds.py après lecture des méthodologies d'indices :
#
#   conforme      le filtre couvre les trois exclusions du mandat (tabac,
#                 armement, charbon), au moins aussi strictement que lui ;
#   sans objet    le fonds ne détient aucune action d'entreprise — emprunts
#                 d'État, or physique, contrats à terme de matières premières.
#                 Il n'y a rien à exclure, pas « rien n'a été vérifié » ;
#   non conforme  un filtre existe mais laisse passer une exclusion du mandat.
#                 C'est le cas des indices « Screened », qui ne retirent pas
#                 l'armement conventionnel — que nous excluons des actions en
#                 direct ;
#   non filtré    aucun filtre d'exclusion ;
#   à vérifier    filtre non standard dont la méthodologie n'a pas été lue.
#
# SEULS « conforme » ET « sans objet » SONT ACHETABLES. Le contrôle ci-dessous
# le vérifie à l'exécution, sur les fonds réellement retenus, plutôt que de
# s'en remettre à la règle écrite dans le script qui les a choisis.

ACHETABLES = ("conforme", "sans objet")


def exclusions(classes: dict | None = None) -> list[dict]:
    """Une ligne par classe investissable : le fonds retenu et son statut."""
    cl = (classes if classes is not None else charger()["classes"])
    out = []
    for k in ORDRE:
        c = cl.get(k)
        if c is None or not c.get("retenu"):
            continue
        r = c["candidats"][c["retenu"]]
        out.append({
            "cle": k, "libelle": c["libelle"], "ticker": c["retenu"],
            "nom": r["nom"], "isin": r["isin"], "filtre": r["filtre"],
            "statut": r["exclusions"], "indice": r["indice"],
            "frais": r["frais"], "taille": r["taille"],
            "replication": r["replication"], "domicile": r["domicile"],
            "conforme": r["exclusions"] in ACHETABLES,
        })
    return out


def non_conformes(classes: dict | None = None) -> list[dict]:
    """Les fonds retenus qui ne passent pas les exclusions du mandat. Vide."""
    return [x for x in exclusions(classes) if not x["conforme"]]
