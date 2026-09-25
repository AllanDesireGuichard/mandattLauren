"""
La vue sectorielle du gérant : des métiers écartés par décision, pas par calcul.

CE QUE CE MODULE N'EST PAS. Ce ne sont pas les exclusions du client, qui
vivent dans core/exclusions.py : celles-là sont des CONTRAINTES du mandat
(tabac, armement, charbon), subies, non négociables, et leur respect se
constate. Ici ce sont des ARBITRAGES DE GESTION, assumés, révisables, et qui
doivent être défendus. Mécaniquement c'est le même filtre ; dans le récit du
dossier ce sont deux choses opposées, et elles sont donc séparées.

POURQUOI UNE VUE DÉCLARÉE PLUTÔT QU'UNE PÉNALITÉ DANS LA NOTE. C'est la
question d'Allan du 2026-09-25 : « la mesure sectorielle doit être faite de
manière discrétionnaire, via les analyses des grandes maisons ». La méthode
est la bonne — un screen quantitatif puis un jugement de gérant est la
pratique courante — mais la forme compte, et la forme « pénalité » ne tient
pas ici, pour trois raisons mesurées.

  1. LE SIGNE DE LA RÈGLE N'EST PAS DÉTERMINÉ. « Les gérants sous-pondèrent
     l'automobile » soutient deux décisions opposées : la pénaliser, c'est
     parier que le consensus a raison ; l'acheter, c'est parier qu'elle est
     devenue bon marché parce qu'elle est détestée. Nos propres piliers
     disent exactement ces deux choses à la fois, sur les six constructeurs
     notés au 2026-09-25 :
         Valorisation  +0,62  contre -0,10 pour l'univers   (+0,72)
         Croissance    +0,30  contre -0,08                  (+0,38)
         Dynamique     -0,58  contre +0,01                  (-0,59)
         Qualité       -0,47  contre -0,07                  (-0,41)
         Résistance    -0,08  contre -0,04                  (-0,04)
     Note finale -0,045 contre +0,008 de médiane : 45e percentile. La note
     ne DÉTECTE pas mal la difficulté du secteur — elle la voit très bien,
     momentum médian -15,9 % contre +15,5 % pour l'univers — elle décide
     qu'elle est DÉJÀ PAYÉE par le prix. Retrancher un malus à la note
     revient à casser cette compensation, c'est-à-dire à déclarer « sur ce
     métier le consensus a raison et le prix n'a pas assez baissé ». C'est
     une position tenable, mais elle doit être DITE, pas glissée dans un
     coefficient.

  2. UNE PÉNALITÉ CHIFFRÉE NE SERAIT PAS RECONSTITUABLE. L'onglet Process
     promet qu'on peut refaire n'importe quel chiffre du dossier de bout en
     bout. Un malus tiré d'une vue de maison n'est ni daté, ni sourçable
     dans l'application, ni reproductible : ce serait le seul maillon non
     vérifiable de la chaîne. Une exclusion déclarée, elle, est binaire,
     datée, motivée, et son coût se mesure (voir `cout`).

  3. LA MAILLE FINE EST TROP CREUSE POUR UNE PÉNALITÉ UNIFORME. Sur les 598
     titres de l'univers, 41 industries en regroupent 414 et 76 autres se
     partagent les 184 restants. Six des quinze titres retenus sont dans une
     industrie de moins de 5 sociétés (Naturgy 4, Aena 4, NEXT 3, IHG 3,
     Vår Energi 2, Publicis 2) : une pénalité calculée par industrie ne
     pourrait pas les atteindre et frapperait les neuf autres, pour une
     raison purement statistique. Une exclusion déclarée n'a pas ce défaut :
     on n'exclut que ce qu'on a décidé d'exclure.

OÙ LE FILTRE AGIT, et pourquoi là. APRÈS la notation, avant la sélection.
  - Après, pour que la note des titres écartés reste calculée et affichable :
    une décision discrétionnaire ne se défend qu'en montrant ce qu'elle a
    coûté. `cout()` le chiffre.
  - Après aussi parce qu'écarter avant de noter déplacerait la moyenne du
    secteur, donc les z-scores de tous ses autres titres : retirer huit
    constructeurs de « Consommation discrétionnaire » changerait les notes
    de NEXT et d'InterContinental pour une raison qui ne les concerne pas.

LA MAILLE EST `industry` (Yahoo, 117 valeurs), et non `secteur` (11 valeurs).
« L'automobile » et « la chimie » n'existent pas dans notre nomenclature à 11
secteurs : les constructeurs sont noyés dans « Consommation discrétionnaire »
avec NEXT et InterContinental, les chimistes dans « Matériaux » avec les
mines. Viser le secteur ferait payer les voisins.
"""
from __future__ import annotations

import pandas as pd

# La vue, telle qu'elle est déclarée. Une entrée par industrie Yahoo :
#     industrie : (depuis, thèse, ce que disent NOS données)
#
# Le troisième champ n'est pas un ornement. Une vue discrétionnaire existe
# précisément pour ce que les mesures n'enregistrent pas encore ; encore
# faut-il dire lesquelles la confirment et lesquelles la contredisent, sinon
# on ne sait plus si l'on anticipe ou si l'on se trompe.
VUE = {
    "Auto Manufacturers": (
        "2026-09-25",
        "Les constructeurs européens font face à une concurrence chinoise "
        "qui produit moins cher sur l'électrique, à une transition qui rend "
        "obsolète l'outil thermique avant d'être rentable, et à des "
        "surcapacités en Europe. Le problème est structurel : il ne se "
        "résout pas par un retour de cycle.",
        "CONFIRMÉE. Momentum médian à 12 mois -15,9 %, le pire des 41 "
        "industries d'au moins cinq titres, contre +15,5 % pour l'univers. "
        "Et le marché vend malgré des bénéfices en hausse de 10,1 % : il "
        "escompte une rupture, pas un creux de cycle.",
    ),
    "Auto Parts": (
        "2026-09-25",
        "Même exposition que les constructeurs, en plus concentrée : un "
        "équipementier ne choisit pas ses volumes et subit la pression sur "
        "les prix de ses donneurs d'ordre.",
        "CONFIRMÉE sur l'activité — bénéfices -2,4 %, ventes -2,6 %, les "
        "deux négatifs, ce qui n'arrive sur aucune autre industrie de la "
        "liste. Le momentum, lui, est positif (+22,1 %) : le marché ne "
        "partage pas encore ce diagnostic.",
    ),
    "Chemicals": (
        "2026-09-25",
        "La chimie de base européenne a perdu son avantage de coût de "
        "l'énergie depuis 2022 : le gaz y reste structurellement plus cher "
        "qu'aux États-Unis, et c'est le premier poste d'un craqueur. "
        "L'écart ne se referme pas par la conjoncture.",
        "NON VÉRIFIABLE sur nos données : l'industrie ne compte que trois "
        "sociétés dans l'univers, une seule notée. Le bénéfice médian y "
        "recule de 34,3 % mais sur trois titres ce chiffre ne veut rien "
        "dire — c'est le même piège que les soldes de révision sur une "
        "seule révision, déjà documenté dans core/outlook.py.",
    ),
    "Specialty Chemicals": (
        "2026-09-25",
        "Même désavantage énergétique, une marche plus haut dans la chaîne. "
        "La spécialité protège les marges plus longtemps que la chimie de "
        "base, mais elle achète les mêmes intrants.",
        "CONTREDITE par nos mesures, et c'est assumé. Sur quinze titres, "
        "l'industrie est au milieu du classement de difficulté : bénéfices "
        "+1,9 %, ventes +1,3 %, momentum +7,5 %. La vue anticipe donc une "
        "dégradation que les chiffres n'enregistrent pas encore. C'EST LE "
        "SEUL CAS DE LA LISTE OÙ NOUS ALLONS CONTRE NOS PROPRES DONNÉES, et "
        "c'est aussi le seul qui coûte un titre (voir `cout`).",
    ),
}

# « Auto & Truck Dealerships » n'est PAS dans la vue, bien qu'elle porte le
# mot « auto » : un distributeur vend la marque qui se vend, il n'est pas
# exposé aux volumes de production européens ni au coût de l'outil thermique.
# La thèse ne s'y applique pas. Aucun de ses trois titres n'est noté, la
# question est sans effet pratique, mais la liste doit rester une liste de
# thèses et non une liste de mots-clés.


def industries() -> list[str]:
    """Les industries écartées par la vue, dans l'ordre de déclaration."""
    return list(VUE)


def ecartees(d: pd.DataFrame) -> pd.Series:
    """Vrai pour les titres que la vue écarte. `d` a une colonne 'industry'."""
    return d["industry"].isin(VUE)


def table() -> pd.DataFrame:
    """La vue, telle qu'elle s'affiche dans l'application et dans le deck."""
    return pd.DataFrame(
        [(i, v[0], v[1], v[2]) for i, v in VUE.items()],
        columns=["Industrie", "Depuis", "Thèse", "Ce que disent nos données"],
    )


def cout(d: pd.DataFrame) -> dict:
    """
    Ce que la vue coûte, mesuré sur l'univers noté `d`.

    Une décision discrétionnaire ne se défend qu'avec son prix affiché : on
    dit ce qu'on s'est interdit, et à quelle note on y renonce.
    """
    e = ecartees(d) & d["note"].notna()
    ec = d[e]
    return {
        "titres_notes": int(e.sum()),
        "meilleure_note": float(ec["note"].max()) if len(ec) else float("nan"),
        "meilleur_titre": (ec.loc[ec["note"].idxmax(), "longName"]
                           if len(ec) else None),
        "par_industrie": ec.groupby("industry")["note"].agg(["size", "max"]),
    }
