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

ORDRE = ("usa", "japon", "emergents", "indexees", "or", "matieres", "crypto")

# Infrastructure RETIRÉE de l'univers (décision d'Allan, 2026-09-18) : aucun
# fonds ne passe à la fois les exclusions et la taille. Les mesures restent
# dans data/fonds.json pour montrer pourquoi.
RETIREES = ("infrastructure",)


def charger() -> dict:
    return json.loads(FICHIER.read_text(encoding="utf-8"))
