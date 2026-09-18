"""
Exclusions tabac, armement et charbon appliquées aux actions en direct.

Le mandat fixe des seuils de chiffre d'affaires (0 % ou 5 % selon l'activité,
voir core/ips.py). Les mesurer exige une base payante (MSCI ESG, Sustainalytics).
Décision validée avec Allan le 2026-09-18 : on s'en approche en deux niveaux,
et la limite est dite dans l'application.

  1. EXCLUSION AUTOMATIQUE par industrie (classification Yahoo) : les
     sociétés dont c'est le cœur de métier.
  2. DÉTECTION PAR MOTS-CLÉS dans la description d'activité : elle signale
     les groupes diversifiés qui ont une activité concernée sans en faire leur
     industrie principale. Chaque titre signalé est tranché À LA MAIN dans
     DECISIONS, avec sa raison. Un titre signalé et non tranché est EXCLU
     par prudence et apparaît comme « à trancher ».

Limite assumée : la distribution de tabac (seuil 5 %), typiquement la grande
distribution alimentaire, n'est ni classée ni décrite comme telle. Elle n'est
pas filtrée.
"""
from __future__ import annotations

import re

import pandas as pd

INDUSTRIES = {
    "Tobacco": "tabac",
    "Aerospace & Defense": "armement",
    "Thermal Coal": "charbon",
    "Coking Coal": "charbon",
}

MOTS = {
    "tabac": r"\b(tobacco|cigarettes?|cigars?|nicotine)\b",
    "armement": r"\b(defen[cs]e|military|weapons?|munitions?|ammunition|"
                r"missiles?|armou?red|warships?|submarines?)\b",
    "charbon": r"\b(coal|lignite)\b",
}

# Titres signalés par les mots-clés, tranchés à la main et validés avec Allan
# le 2026-09-18. ticker : (décision « exclu » / « conservé », raison).
# « À confirmer » : la part réelle de l'activité mériterait d'être vérifiée
# dans le rapport annuel de la société.
A_CONFIRMER = " (à confirmer sur le rapport annuel)"
DECISIONS: dict[str, tuple[str, str]] = {
    # exclus
    "GLEN.L": ("exclu", "Extraction de charbon thermique, bien au-delà de 5 %"),
    "RWE.DE": ("exclu", "Production d'électricité au lignite, au-delà de 5 %"),
    "MRO.L": ("exclu", "GKN Aerospace : composants d'avions militaires, part "
                       "importante du chiffre d'affaires"),
    "IDR.MC": ("exclu", "Systèmes militaires : radars, guerre électronique"),
    "BAB.L": ("exclu", "Soutien aux sous-marins et systèmes d'armes"),
    "TKA.DE": ("exclu", "Détient la majorité de TKMS (sous-marins), environ "
                        "6 % du chiffre d'affaires" + A_CONFIRMER),
    "ZAB.WA": ("exclu", "Supérettes : le tabac pèse lourd dans les ventes"
                        + A_CONFIRMER),
    "AVOL.SW": ("exclu", "Boutiques hors taxes : le tabac est une catégorie "
                         "majeure" + A_CONFIRMER),
    # conservés : services ou logiciels, sans fabrication d'armes
    "CAP.PA": ("conservé", "Services informatiques, clients défense minoritaires"),
    "SOP.PA": ("conservé", "Services informatiques, activité défense et sécurité "
                           "minoritaire" + A_CONFIRMER),
    "DSY.PA": ("conservé", "Logiciels de conception, sans fabrication d'armes"),
    "NOKIA.HE": ("conservé", "Équipements télécoms, activité défense marginale"),
    "SRP.L": ("conservé", "Services aux administrations, dont la défense, sans "
                          "fabrication d'armes"),
    "MTO.L": ("conservé", "Gestion d'installations, sans fabrication d'armes"),
    "CPG.L": ("conservé", "Restauration collective, dont bases militaires : un "
                          "service, pas une arme"),
    "BVI.PA": ("conservé", "Inspection et certification"),
    "DSV.CO": ("conservé", "Logistique, activité défense marginale"),
    "SKA-B.ST": ("conservé", "Construction, clients défense minoritaires"),
    "ACP.WA": ("conservé", "Logiciels, clients défense minoritaires"),
    "ADDT-B.ST": ("conservé", "Distribution industrielle diversifiée"),
    # conservés : industriels à activité militaire marginale
    "PRY.MI": ("conservé", "Câbles, usages militaires marginaux"),
    "ASSA-B.ST": ("conservé", "Serrures et contrôle d'accès, pas des armes"),
    "SMIN.L": ("conservé", "Détection et équipements industriels, part militaire "
                           "limitée" + A_CONFIRMER),
    "HUBN.SW": ("conservé", "Connectique, usages militaires marginaux"),
    "HIAB.HE": ("conservé", "Grues de manutention, usages militaires marginaux"),
    "MYCR.ST": ("conservé", "Équipements électroniques, usages militaires "
                            "marginaux"),
    "RAA.DE": ("conservé", "Équipements de cuisine professionnelle"),
    "EL.PA": ("conservé", "Optique et lunetterie, mention défense marginale"),
    "EXO.AS": ("conservé", "Holding diversifiée, sans activité d'armement "
                           "significative"),
    # conservés : charbon hors champ, tabac minoritaire
    "AAL.L": ("conservé", "Sorti du charbon thermique en 2021 ; le charbon "
                          "métallurgique n'est pas visé" + A_CONFIRMER),
    "MT.AS": ("conservé", "Consomme du charbon pour l'acier : ni extraction de "
                          "charbon thermique, ni production électrique"),
    "EDP.LS": ("conservé", "Sortie du charbon annoncée, part résiduelle"
                           + A_CONFIRMER),
    "AD.AS": ("conservé", "Tabac minoritaire dans un assortiment alimentaire"
                          + A_CONFIRMER),
    "DNP.WA": ("conservé", "Tabac minoritaire dans un assortiment alimentaire"
                           + A_CONFIRMER),
}


def classer(f: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute trois colonnes : 'exclusion' (motif ou vide), 'niveau'
    (« industrie », « décision », « à trancher » ou vide) et 'raison'.
    """
    out = pd.DataFrame(index=f.index,
                       columns=["exclusion", "niveau", "raison", "signal"])
    for i, r in f.iterrows():
        ind = r.get("industry") or ""
        if ind in INDUSTRIES:
            out.loc[i, ["exclusion", "niveau", "raison"]] = (
                INDUSTRIES[ind], "industrie", f"Industrie Yahoo : {ind}")
            continue
        texte = str(r.get("longBusinessSummary") or "")
        signaux = [m for m, pat in MOTS.items()
                   if re.search(pat, texte, flags=re.I)]
        if not signaux:
            continue
        out.loc[i, "signal"] = ", ".join(signaux)
        d = DECISIONS.get(r["ticker"])
        if d is None:
            out.loc[i, ["exclusion", "niveau", "raison"]] = (
                signaux[0], "à trancher",
                "Signalé par la description d'activité, non encore examiné")
        elif d[0] == "exclu":
            out.loc[i, ["exclusion", "niveau", "raison"]] = (
                signaux[0], "décision", d[1])
        else:
            out.loc[i, ["niveau", "raison"]] = ("conservé", d[1])
    return out
