"""
Le second étage de la sélection actions : ce que les analystes attendent.

La notation de core/scoring.py mesure ce que les sociétés SONT — bilan,
marges, valorisation, comportement en crise. Tout y est constaté. Ce module
pose la question suivante : où vont-elles ? Il ne reclasse rien, il resserre
les 30 titres retenus en 14 à 16.

DÉCISIONS D'ALLAN, 2026-09-24 :
  - on part des 30 déjà retenus, on ne relance pas le tri sur tout l'univers :
    l'entonnoir garde deux étapes lisibles, 600 -> 30 sur le constaté, puis
    30 -> 15 sur l'attendu ;
  - l'avenir est un ÉTAGE SÉPARÉ, pas un sixième pilier : les cinq piliers
    classent, l'avenir élimine. Mélanger les deux diluerait le signal (un
    avenir dégradé ne pèserait qu'un sixième et serait compensé) et ferait
    perdre le récit.

POURQUOI CES QUATRE INDICATEURS, et pas l'avis « acheter / conserver / vendre »
  Le niveau du consensus est un mauvais discriminant : le biais acheteur est
  structurel, et l'objectif de cours monte mécaniquement quand un titre baisse
  (la cible bouge plus lentement que le cours), si bien qu'un fort potentiel
  signale souvent une chute récente plutôt qu'un bon dossier. À quoi s'ajoute
  un fait mesuré le 2026-09-24 : `recommendationMean` manque sur 7 des 30,
  dont des sociétés suivies par 14 à 16 analystes. En faire un critère
  écarterait 7 titres pour une raison technique. Il est affiché, jamais noté.

  Ce qui est retenu à la place — tout à 30/30 de couverture :
    revision      la variation du bénéfice attendu sur 90 jours. Le sens dans
                  lequel le consensus bouge, qui vaut mieux que son niveau ;
    solde         la part des révisions du dernier mois qui vont dans le bon
                  sens, entre -100 et +100. Rapportée au NOMBRE DE RÉVISIONS
                  et non à l'effectif d'analystes, et tenue pour neutre en
                  dessous de trois révisions (voir `indicateurs`) ;
    potentiel     objectif de cours consensus rapporté au cours. Sert en
                  GARDE-FOU, pas en score : la valeur exacte du potentiel n'est
                  pas un signal, mais un cours au-dessus de la cible ET des
                  bénéfices qui ne suivent pas en est un (voir plus bas) ;
    dispersion    écart entre l'estimation la plus haute et la plus basse,
                  rapporté à la moyenne. Mesure à quel point l'avenir de la
                  société est lisible. Sert aussi en garde-fou : elle est
                  structurellement sectorielle (une pétrolière dépend d'un
                  prix que personne ne prévoit), donc la noter reviendrait à
                  noter le secteur.

POURQUOI LE GARDE-FOU DU POTENTIEL EST CONDITIONNEL, révision d'Allan du
2026-09-24. Il excluait tout titre cotant au-dessus de son objectif. Il
disait donc l'inverse de ce que ce module explique deux paragraphes plus
haut : si la cible bouge plus lentement que le cours — c'est l'argument qui
sert à écarter le potentiel du score — alors un potentiel NÉGATIF signale
d'abord une hausse récente, et une cible qui n'a pas rattrapé son retard.

MESURÉ SUR LE RELEVÉ DU 2026-09-24, et c'est sans appel : les HUIT titres
cotant au-dessus de leur objectif ont TOUS un bénéfice attendu révisé à la
HAUSSE. Endesa +1,8 %, EMS-Chemie +3,0 %, Evolution +2,0 %, OMV +10,8 %,
Equinor +4,0 %, Orion +6,4 %, Sabadell +2,7 %, Vår Energi +7,3 %. OMV a la
deuxième meilleure révision des trente et sortait pour un objectif périmé.
L'ordre est celui qu'on attend d'un consensus : l'analyste relève son BPA
d'abord, son objectif de cours suit avec du retard. La règle ne sanctionnait
donc pas la cherté, elle sanctionnait la bonne dynamique bénéficiaire.

LA RÈGLE RETENUE. Un objectif dépassé n'est un avertissement que si les
bénéfices ne suivent pas : `potentiel < 0` ET `revision <= 0`. Le garde-fou
reste — une société chère dont le consensus stagne doit sortir — mais il ne
mord plus sur le cas inverse. Sur le relevé du 2026-09-24 il n'écarte AUCUN
titre, et ce zéro est le résultat : il n'y a pas, aujourd'hui, de société
au-dessus de sa cible sans bénéfices pour la justifier.

CE QUE LE CHANGEMENT A COÛTÉ ET RAPPORTÉ, mesuré sur le panier à 15 :
  règle d'avant  vol 11,72 %  2020 -37,3 %  2022 -13,4 %   8 secteurs, 6 pays
  règle retenue  vol 11,49 %  2020 -37,8 %  2022 -12,5 %   9 secteurs, 8 pays
Entrent Endesa, Orion et Vår Energi ; sortent Carrefour, Iberdrola et Ipsen.
Les deux seuils intermédiaires essayés (tolérer 5 % puis 10 % de dépassement)
faisaient à peu près aussi bien, mais leur seuil ne répond à aucune question :
celui-ci en pose une.

DEVISES : les quatre sont des ratios, la devise s'annule dans chacun. Aucun
ne mélange un montant publié (« financialCurrency », le dollar pour argenx et
Airtel Africa) avec un cours de cotation.

POURQUOI PAS DE NOTE AU SEIN DU SECTEUR, contrairement à scoring.py : la
notation compare des PER et des marges, qui n'ont pas le même sens d'un
secteur à l'autre, sur un univers de plusieurs centaines de titres. Ici on
compare 30 titres déjà tous jugés bons, sur des variations en pourcentage qui
se comparent d'un secteur à l'autre. Découper en secteurs donnerait des
groupes de 1 à 4 titres : un écart-type n'y veut rien dire.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FICHIER = Path(__file__).resolve().parents[1] / "data" / "actions" / "outlook.csv"

# Plafonds resserrés pour le second étage. Ceux du premier (4 par secteur,
# 6 par pays) tiennent sur 30 titres ; sur 15 ils laisseraient 6 espagnols
# faire 40 % du panier. Resserrer la sélection oblige à resserrer les
# plafonds, sinon on troque une sélection contre un pari géographique.
#
# LE PLAFOND SECTORIEL EST LE PLUS SERRÉ DES DEUX, à dessein : les pays
# européens sont très corrélés entre eux, bien plus que les secteurs. Deux
# sociétés françaises de deux métiers différents diversifient mieux que deux
# banques de deux pays. C'est donc le secteur qu'il faut contenir en premier.
#
# COMBIEN ILS LAISSENT PASSER, mesuré sur le relevé du 2026-09-24 (20 titres
# franchissent les garde-fous, on en demande 16) :
#     2 par secteur, 3 par pays -> 13 titres   trop peu
#     2 par secteur, 4 par pays -> 15 titres   retenu
#     3 par secteur, 4 par pays -> 16 titres   laisse revenir un 3e financier
MAX_SECTEUR = 2
MAX_PAYS = 4

# Au-delà de ce percentile de dispersion, l'avenir de la société est jugé
# illisible. Seuil MESURÉ sur les titres retenus, pas fixé à la main : il
# suit l'état du marché, comme scoring.plafond_volatilite.
DISPERSION_QUANTILE_MAX = 0.90

# Plancher de révision : on n'achète pas une société dont les analystes
# viennent de couper le bénéfice attendu de plus de 5 % en trois mois.
#
# POURQUOI UN SEUIL ABSOLU ICI, alors que la dispersion et la volatilité ont
# des seuils en percentile : un percentile écarte toujours 10 % des titres,
# y compris quand aucun ne va mal. Pour un plancher de qualité, c'est le
# mauvais comportement — on veut qu'il ne morde que s'il y a une raison.
# L'alternative écartée était le 10e percentile des révisions, qui vaut
# -2,3 % sur le relevé du 2026-09-24 et aurait aussi écarté United Utilities,
# dont le consensus ne recule que de 2 %.
#
# SANS CE PLANCHER, Norsk Hydro était retenue avec une révision de -17,3 % et
# la pire note d'avenir des trente : la sélection descendait la liste jusqu'à
# remplir son quota, et raclait le fond dès qu'un secteur se vidait.
REVISION_MIN = -5.0

# Nombre de révisions en dessous duquel le solde n'est pas interprété.
# Sur une seule révision il ne peut valoir que -100 ou +100 : c'est du bruit
# présenté comme une unanimité.
REVISIONS_MIN = 3

AVIS_FR = {
    "strong_buy": "Achat fort", "buy": "Achat", "hold": "Conserver",
    "underperform": "Sous-performance", "sell": "Vente", "none": "—",
}


def releve() -> str:
    return str(pd.read_csv(FICHIER)["date_releve"].iloc[0])


def indicateurs() -> pd.DataFrame:
    """Les quatre mesures d'avenir, une ligne par titre, indexées par ticker."""
    o = pd.read_csv(FICHIER).set_index("ticker")
    x = pd.DataFrame(index=o.index)

    cible = pd.to_numeric(o["targetMeanPrice"], errors="coerce")
    cours = pd.to_numeric(o["currentPrice"], errors="coerce")
    x["potentiel"] = (cible / cours - 1).where(cours > 0) * 100

    avant = pd.to_numeric(o["bpa_90daysAgo"], errors="coerce")
    apres = pd.to_numeric(o["bpa_current"], errors="coerce")
    # un bénéfice attendu négatif rendrait le rapport ininterprétable
    x["revision"] = (apres / avant - 1).where(avant > 0) * 100

    # Part des révisions du mois qui vont dans le bon sens, entre -100 et +100.
    # Le dénominateur est le NOMBRE DE RÉVISIONS, pas l'effectif d'analystes :
    # les deux champs de Yahoo sont incohérents entre eux (argenx, relevé du
    # 2026-09-24 : 6 hausses et 3 baisses pour un effectif annoncé de 3). Le
    # rapport au nombre d'analystes sortait à +100 % et plaçait argenx en tête
    # du classement d'avenir pour cette seule raison.
    hausses = pd.to_numeric(o["rev_hausse_30j"], errors="coerce").fillna(0)
    baisses = pd.to_numeric(o["rev_baisse_30j"], errors="coerce").fillna(0)
    total = hausses + baisses
    # En dessous de REVISIONS_MIN, le solde est tenu pour neutre plutôt que
    # calculé : sur une ou deux révisions il ne peut valoir que -100, 0 ou
    # +100, et ces extrêmes ne veulent rien dire. Airtel Africa sortait à
    # -100 % parce qu'un analyste et un seul avait abaissé, BAWAG à +100 %
    # pour la raison inverse. Neutre et non pas absent : le silence des
    # analystes n'est pas un reproche à faire à la société.
    x["revisions_30j"] = total
    brut = ((hausses - baisses) / total.where(total > 0)).fillna(0) * 100
    x["solde"] = brut.where(total >= REVISIONS_MIN, 0.0)

    haut = pd.to_numeric(o["bpa_haut"], errors="coerce")
    bas = pd.to_numeric(o["bpa_bas"], errors="coerce")
    moyen = pd.to_numeric(o["bpa_moyen"], errors="coerce")
    x["dispersion"] = ((haut - bas) / moyen.abs()).where(moyen != 0) * 100

    x["analystes"] = pd.to_numeric(o["numberOfAnalystOpinions"], errors="coerce")
    x["avis"] = o["recommendationKey"].map(AVIS_FR).fillna("—")
    x["cours"] = cours
    x["cible"] = cible
    x["cible_haute"] = pd.to_numeric(o["targetHighPrice"], errors="coerce")
    x["cible_basse"] = pd.to_numeric(o["targetLowPrice"], errors="coerce")
    x["devise_cours"] = o["currency"]          # devise de COTATION : celle du
                                               # cours et de la cible, jamais
                                               # celle des bénéfices publiés
    return x


def plafond_dispersion(x: pd.DataFrame) -> float:
    """Dispersion maximale tolérée : mesurée sur les titres notés, pas fixée."""
    return float(x["dispersion"].quantile(DISPERSION_QUANTILE_MAX))


def noter(x: pd.DataFrame) -> pd.DataFrame:
    """
    Note d'avenir : moyenne des écarts-types de `revision` et `solde`.

    Le potentiel et la dispersion n'entrent pas dans la note — ils agissent en
    garde-fous (voir `juger`). La note ne dit donc qu'une chose, mais elle la
    dit proprement : le consensus se redresse-t-il ou se dégrade-t-il ?
    """
    out = pd.DataFrame(index=x.index)
    for c in ("revision", "solde"):
        v = x[c]
        lo, hi = v.quantile(0.05), v.quantile(0.95)     # comme scoring.py : un
        v = v.clip(lo, hi)                              # extrême ne fait pas la note
        s = v.std()
        out["z_" + c] = (v - v.mean()) / s if s and s > 0 else v * 0
    out["note_avenir"] = out[["z_revision", "z_solde"]].mean(axis=1)
    return out


def juger(sel: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    """
    Les 30 titres, augmentés des mesures d'avenir et du motif d'exclusion.

    `sel` : la sélection de core/actions.py (une ligne par titre, colonne
    'ticker'). Renvoie le même tableau, indexé comme lui.
    """
    d = sel.set_index("ticker").join(x).join(noter(x))
    seuil = plafond_dispersion(x)

    # Tous les motifs qui s'appliquent, pas seulement le premier : Rio Tinto
    # cumule un consensus en recul et une dispersion de 68 %, et n'afficher
    # que l'un des deux donnerait une raison plus faible que la réalité.
    # Conditionnel, et non plus `potentiel < 0` seul : un objectif dépassé
    # n'est un avertissement que si le bénéfice attendu ne suit pas. Voir le
    # docstring du module — les huit titres concernés au 2026-09-24 étaient
    # tous révisés à la hausse, la règle d'avant écartait la bonne dynamique.
    griefs = {
        "Cours au-dessus de la cible sans relais des bénéfices":
            (d["potentiel"] < 0) & (d["revision"] <= 0),
        "Prévisions en net recul": d["revision"] < REVISION_MIN,
        "Avenir illisible": d["dispersion"] > seuil,
        "Attentes indisponibles": d["revision"].isna() | d["potentiel"].isna(),
    }
    d["motif"] = [" · ".join(m for m, v in griefs.items() if v.loc[i]) or pd.NA
                  for i in d.index]
    return d.reset_index()


def selectionner(d: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """
    Les n titres retenus au second étage, parmi ceux qu'aucun garde-fou
    n'écarte, classés par note d'avenir et sous les plafonds resserrés.

    `d` : la sortie de `juger`.
    """
    retenus, par_secteur, par_pays = [], {}, {}
    candidats = d[d["motif"].isna()].sort_values("note_avenir", ascending=False)
    for i, r in candidats.iterrows():
        if par_secteur.get(r["secteur"], 0) >= MAX_SECTEUR:
            continue
        if par_pays.get(r["pays"], 0) >= MAX_PAYS:
            continue
        retenus.append(i)
        par_secteur[r["secteur"]] = par_secteur.get(r["secteur"], 0) + 1
        par_pays[r["pays"]] = par_pays.get(r["pays"], 0) + 1
        if len(retenus) == n:
            break
    return d.loc[retenus]


def final(sel: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Chaîne complète : les 30 jugés, puis les n retenus."""
    return selectionner(juger(sel, indicateurs()), n=n)
