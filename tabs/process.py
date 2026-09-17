"""
Onglet Process -- methodologie redigee.

Ecrit comme un chapitre de methode : d'ou viennent les donnees, ce qu'on leur
a fait subir, pourquoi, et ce que chaque arbitrage a ecarte. Objectif : qu'un
lecteur puisse reconstituer n'importe quel chiffre du dossier.
"""
from __future__ import annotations

import streamlit as st


def partie_1() -> None:
    st.markdown("""
## I. Les données : nature, provenance, limites

### I.1 Le principe de séparation des usages

Une erreur fréquente consiste à utiliser le même jeu de données pour toutes
les questions. Or **sélectionner un instrument** et **calibrer un risque** ne
demandent ni la même profondeur ni la même nature de données.

Sélectionner un instrument, c'est comparer des supports **entre eux** sur une
fenêtre commune : dix ans suffisent, et l'important est que la fenêtre soit
identique pour tous les candidats.

Calibrer un risque, c'est estimer un comportement en crise : il faut alors
**contenir des crises**. Une fenêtre qui exclut 2008 et 2011 sous-estime
systématiquement le risque, quel que soit le soin apporté au calcul.

Nous avons donc constitué deux jeux distincts, et nous refusons de les mélanger.

### I.2 Les six sources

#### Source 1 — Le référentiel d'instruments d'equitydb2
`~/projets/equitydb2/state/etf_universe.csv`

643 ETF référencés manuellement, dont 266 domiciliés en Europe. Fournit le
code, le libellé, la catégorie, la région et la domiciliation.

**Limite identifiée et assumée.** La colonne `expense_ratio` mélange les
conventions décimale et pourcentage : `IBGS.L` y figure à 0,2 — soit 20 % de
frais, ce qui est absurde — quand d'autres lignes sont correctement exprimées
en décimal. Cette colonne n'a **pas** été réutilisée ; les frais ont été
resaisis à la main pour les seuls supports retenus.

#### Source 2 — Le cache de prix d'equitydb2
`~/projets/equitydb2/state/cache/etf/*.parquet`

731 séries quotidiennes de cours ajustés. Sert à la **sélection**
d'instruments, jamais à la calibration.

**Deux limites.** La profondeur est plafonnée à dix ans — 483 séries atteignent
ce plafond, aucune ne le dépasse. Et le cache contient des séries corrompues,
traitées en partie II.

#### Source 3 — Les proxys longs, via yfinance
`data/prices/` — SPY, EFA, EEM, IEF, TIP, LQD, GLD, VNQ

Huit séries de 21,8 ans (novembre 2004 à septembre 2026), couvrant la crise
financière de 2008, la crise de la dette souveraine de 2011, le choc COVID de
2020 et le choc d'inflation de 2022. Servent à la **calibration du risque**, aux
stress tests et au backtest.

**Limite assumée.** Ce sont des indices **larges, non filtrés ESG**. Ce choix
est délibéré et justifié en partie IV.

#### Source 4 — L'extension ciblée
`data/universe_candidates.csv`

88 candidats ajoutés à la main pour combler les classes d'actifs sans support :
crédit euro filtré, infrastructure, alternatifs, monétaire euro, obligations
vertes, or non couvert. 53 ont pu être récupérés.

**Limite.** Les 35 échecs correspondent à des codes inexistants ou à des
produits délistés. Trois codes se sont révélés désigner **autre chose** que ce
que nous supposions — voir partie II.

#### Source 5 — Le change
`EURUSD=X`, depuis 2003

Sert à convertir les séries libellées en dollars et à appliquer les ratios de
couverture définis dans la politique de change.

#### Source 6 — Les barèmes fiscaux
`core/ips.py` — articles 669, 777 et 990 I du Code général des impôts

Barème de l'usufruit par tranche d'âge, barème progressif des mutations à titre
gratuit en ligne directe, abattements, régime de l'assurance-vie.

**Limite majeure.** Ces barèmes sont exacts à notre connaissance au
17 septembre 2026, mais trois éléments ne sont **délibérément pas modélisés** :
le régime matrimonial, les droits du conjoint survivant, et la réserve
héréditaire. Ils modifient les montants, non la hiérarchie des leviers. Une
validation notariale est indispensable avant mise en œuvre.

### I.3 Ce que l'application lit réellement

Une distinction utile pour comprendre l'architecture : **l'application ne lit
que des fichiers CSV**. Les séries de prix, les calculs d'optimisation et les
simulations sont exécutés hors ligne par les scripts, et leurs résultats sont
déposés dans `data/`.

Ce découpage est volontaire. L'optimisation demande une dizaine de minutes ; la
relancer à chaque interaction rendrait l'outil inutilisable. Seuls deux onglets
recalculent en direct — Faisabilité et Transmission — parce qu'ils reposent sur
des formules fermées, donc instantanées, et parce que ce sont les deux
questions qu'un client pose en séance.
""")


def partie_2() -> None:
    st.markdown("""
## II. Le nettoyage des données : le travail invisible

### II.1 Le constat initial

En appliquant les premiers calculs de risque au cache d'equitydb2, un résultat
impossible est apparu : un ETF d'obligations d'État de la zone euro à maturité
1-3 ans affichait **29 % de volatilité annuelle et 99 % de perte maximale**.

Un tel instrument présente en réalité une volatilité de l'ordre de 1,5 %.
L'écart n'était pas une imprécision : c'était une corruption de la série.

### II.2 Le diagnostic

L'examen des séries incriminées a révélé trois pathologies distinctes.

#### Pathologie 1 — La rupture d'échelle

Certaines séries présentent un saut unique d'un facteur exactement 100 :

```
SPXS.L    2014-01-02    303,05  →  3,02      soit ÷100
IBGS.L    2009-01-02    12 517  →  120,35    soit ÷100
```

L'explication tient à la place de cotation. Les valeurs londoniennes sont
souvent cotées en **pence** puis redénominées en **livres**, ou l'inverse. Le
fournisseur de données n'a pas répercuté le changement d'unité sur
l'historique antérieur.

Cette pathologie est **réparable** : il suffit de remettre le segment antérieur
à l'échelle du segment récent.

#### Pathologie 2 — L'oscillation entre deux lignes de cotation

D'autres séries alternent entre deux cotations différentes du même produit :

```
SGLN.L    avril 2011    −39 %, +64 %, −38 %, +62 %
IBGS.L    mai 2008      −22 %, +28 %
```

Le fournisseur mélange ici deux lignes — typiquement une cotation en dollars et
une en livres du même ETC. Un jour sur deux provient d'une série différente.

Cette pathologie n'est **pas réparable** : rien ne permet de savoir quel point
appartient à quelle série. Les séries concernées sont rejetées.

#### Pathologie 3 — La contamination diffuse

Le cas le plus dangereux. Certaines séries ne présentent aucun saut
spectaculaire, mais restent contaminées de façon diffuse — typiquement parce
que la ligne de cotation est libellée dans une devise différente de celle du
fonds. La série porte alors du risque de change qui n'a rien à y faire.

`ECRP.L`, fonds de crédit euro coté à Londres en pence, ressortait ainsi à
9,8 % de volatilité contre environ 5 % pour le même sous-jacent coté à
Francfort.

Aucun saut ne permet de la détecter. Il faut un autre garde-fou.

### II.3 Le traitement en trois étages

Le module `core/quality.py` applique successivement :

**Étage 1 — Réparation des ruptures d'échelle.** On détecte les variations
quotidiennes supérieures à 35 %, on vérifie si le rapport avant/après est
proche de 100, 1000 ou de leur inverse, et on remet le segment antérieur à
l'échelle. Plusieurs ruptures successives sont traitées.

**Étage 2 — Rejet des oscillations.** Après réparation, on cherche les
variations extrêmes restantes. Si deux d'entre elles, de signes opposés,
apparaissent à moins de dix jours d'intervalle, la série est déclarée
oscillante et rejetée.

**Étage 3 — Contrôle de plausibilité par classe d'actifs.** C'est le garde-fou
décisif, le seul qui attrape la contamination diffuse. Chaque classe d'actifs
se voit assigner une fourchette de volatilité annuelle plausible :

| Classe d'actifs | Fourchette admise |
|---|---|
| Monétaire | 0,05 % – 2,0 % |
| Souverain euro court | 0,05 % – 3,0 % |
| Souverain euro | 1,5 % – 7,5 % |
| Crédit IG euro | 1,5 % – 7,5 % |
| Actions développées | 8 % – 30 % |
| Actions émergentes | 10 % – 35 % |
| Or | 10 % – 30 % |
| Crypto | 30 % – 120 % |

Toute série sortant de sa fourchette est rejetée, **quelle que soit la cause**.
Le raisonnement est simple : un ETF souverain 1-3 ans à 8 % de volatilité est
faux, qu'on sache expliquer pourquoi ou non.

### II.4 Pourquoi un contrôle automatique et non une relecture

Sur 182 séries, une inspection manuelle est impraticable — et surtout, elle ne
détecterait pas la contamination diffuse, qui ne se voit pas à l'œil sur un
graphique.

L'enjeu justifie l'effort. Une erreur de données ne produit pas un message
d'erreur : elle produit un résultat **d'apparence normale mais faux**. Un
optimiseur nourri de séries corrompues rend un portefeuille corrompu, sans
qu'aucun contrôle ne s'allume.

### II.5 Le piège des codes trompeurs

Trois codes ajoutés à l'extension ciblée se sont révélés désigner des produits
entièrement différents de ce que nous supposions :

| Code | Ce que nous supposions | Ce que c'est réellement |
|---|---|---|
| `CTA.L` | Un fonds de suivi de tendance | **CT Automotive Group plc**, équipementier automobile |
| `XZEC.DE` | Du crédit corporate euro filtré | Xtrackers Stoxx European Market Leaders, un fonds d'**actions** |
| `EEDS.L` | Du crédit filtré | iShares MSCI USA CTB, un fonds d'**actions** américaines |

Leur volatilité les a trahis — 55 %, 19 % et 17 %, incompatibles avec du
crédit. Le traitement retenu consiste à récupérer systématiquement les
libellés réels avant tout classement.

### II.6 Le mode de défaillance dominant

Rétrospectivement, **la devise de cotation** a causé plus d'erreurs que toute
autre source. Trois occurrences, dont une commise en corrigeant la précédente :

1. `ECRP.L`, fonds euro coté en pence — volatilité gonflée de moitié
2. `XZW0.DE` (euros) comparé à `URTH` (dollars) — écart de suivi apparent de
   19 %, qui n'était que de la volatilité de change
3. `SAWD.L` et `SUSW.L`, cotés en **dollars malgré le suffixe `.L`** — la
   conversion appliquée à un seul côté de la comparaison

**Le suffixe de place ne détermine pas la devise.** C'est la leçon la plus
coûteuse de l'étude.
""")


def partie_3() -> None:
    st.markdown("""
## III. La chaîne de construction, étape par étape

### III.1 Vue d'ensemble

```
  equitydb2                yfinance                  barèmes CGI
  643 ETF référencés       proxys longs 21,8 ans     art. 669 · 777 · 990 I
  731 séries ≤ 10 ans      extension 88 candidats
        │                        │                          │
        └────────────┬───────────┘                          │
                     ▼                                      │
         core/data.py  —  retry, replis, cache              │
                     ▼                                      │
         core/quality.py  —  réparation, rejet,             │
                            plausibilité par classe         │
                     ▼                                      │
         core/metrics.py  —  filtres durs + score           │
                     ▼                                      │
         226 candidats → 182 séries → 48 supports           │
                     ▼                                      │
         core/cma.py  —  blocs constitutifs,                │
                        répercussion de l'inflation         │
                     ▼                                      │
         core/optimizer.py  —  BL + resampling              │
                     ▼                                      │
         contraintes de second niveau                       │
                     ▼                                      ▼
         ALLOCATION  ──────────────────────►  core/succession.py
                     │                               core/tax.py
                     ▼                                      ▼
         stress_tests · backtest · benchmark        transmission
```

### III.2 Étape 1 — Récupération robuste

`core/data.py`

Le service yfinance présente des échecs **intermittents par code** : un
identifiant qui répond à un instant donné peut échouer quelques minutes plus
tard. Nous l'avons constaté sur `SGLN.L`, `SPY` et `AAPL`, tous trois en échec
puis fonctionnels sans modification du code.

Le chargeur applique donc : une tentative à la fois, un délai croissant entre
les essais, une liste de codes de repli par classe d'actifs, et un cache
incrémental afin de ne jamais reperdre ce qui a déjà été téléchargé.

L'appel groupé `yf.download()` sur une liste est proscrit : un échec partiel y
est silencieux.

### III.3 Étape 2 — Constitution de l'univers

`scripts/build_universe.py`

Les 266 codes européens d'equitydb2 sont classés dans les onze classes
d'actifs de l'allocation par règles explicites appliquées au libellé, avec
dérogations manuelles. S'y ajoutent les 88 candidats de l'extension ciblée.

L'application du filtre ESG mérite une précision. Les trois exclusions du
mandat — tabac, armement, charbon thermique — visent des **émetteurs
d'entreprise**. Les appliquer à une obligation d'État allemande ou à de l'or
physique est une erreur de catégorie : il n'y a aucun émetteur à exclure.

L'univers est donc découpé en trois régimes :

| Régime | Classes concernées |
|---|---|
| Filtre **exigé** | Actions développées, actions émergentes, infrastructure, crédit, immobilier |
| Filtre **sans objet** | Souverain, obligations indexées, or, matières premières, monétaire, crypto |
| Filtre **sous condition** | Alternatifs, agrégat global, obligations vertes — dépend du sous-jacent |

Règle complémentaire : lorsque le filtre est exigé, c'est le support
**principal** qui doit le porter. Se contenter d'un suppléant filtré viderait
le mandat de son sens.

### III.4 Étape 3 — Sélection des instruments

`core/metrics.py` et `scripts/select_instruments.py`

La sélection distingue deux natures de critères, et c'est une distinction
importante.

**Les filtres durs** portent sur ce qui est **mesurablement faux** :
historique d'au moins trois ans, série propre au sens de la partie II,
volatilité dans la fourchette plausible de la classe.

**Les préférences souples** portent sur ce qui est seulement **préférable**,
et sont agrégées en un score :

| Critère | Poids |
|---|---|
| Historique suffisant | 16 |
| Série propre | 8 |
| Filtre ESG présent | 4 |
| Couverture de change conforme à la politique | 4 |
| Cohérence devise / place de cotation | 3 |
| Support capitalisant | 2 |
| Fiabilité de la place de cotation | 1 |

Cette distinction résulte d'une correction. Notre première règle excluait
purement et simplement les cotations londoniennes pour les classes libellées
en euros. Elle rejetait `SUOE.L` — 5,4 % de volatilité, parfaitement plausible
— en même temps qu'`ECRP.L` — 9,8 %, contaminé. Le principe retenu est
désormais : **filtre dur sur ce qui est mesurable, préférence souple sur le
reste**. Une intuition sur la place de cotation ne vaut pas une mesure.

### III.5 Étape 4 — Hypothèses de marché

`core/cma.py`

Chaque entrée porte une étiquette de provenance :

- **mesuré** — estimé sur nos propres séries. Le taux monétaire euro à 2,05 %
  est lu sur la série de `XEON.DE`, qui réplique l'€STR
- **marché** — lu sur un prix observable à une date donnée. Les rendements
  actuariels obligataires
- **hypothèse** — un choix documenté, décomposé en blocs constitutifs

S'y ajoute le coefficient de répercussion de l'inflation, propre à ce mandat.

### III.6 Étape 5 — Optimisation

`core/optimizer.py` et `scripts/optimize_saa.py`

Cinq étapes enchaînées : ancrage neutre en parité de risque sur les actifs
risqués, rendements d'équilibre, Black-Litterman avec quatre vues assorties
d'une confiance explicite, frontière resamplée sur 120 tirages, puis
contraintes de second niveau.

Un ajustement mérite d'être signalé. Les **corrélations** proviennent de la
fenêtre instruments, de 6,2 ans : elles sont nettement plus stables dans le
temps que les volatilités. Les **volatilités**, elles, sont remises à l'échelle
de la référence longue de 21,8 ans. Sans cet ajustement, on optimiserait sur un
risque sous-estimé, faute de 2008 et 2011 dans la fenêtre.

C'est une approximation de premier ordre, et elle est imparfaite : 2008 a
frappé le crédit et les actions bien plus durement que l'or, alors que
l'ajustement est uniforme.

### III.7 Étape 6 — Validation du risque

`scripts/stress_tests.py`

Les fenêtres glissantes de 252 jours sont calculées sur l'ensemble des 21,8
ans, soit 5 438 observations.

Les crises sont définies **a priori** — Lehman, dette souveraine 2011, COVID,
inflation 2022 — et jamais par sélection sur les données. Ce point est
méthodologiquement important et fait l'objet de la partie V.
""")


def partie_4() -> None:
    st.markdown("""
## IV. Les arbitrages : ce qui a été écarté, et pourquoi

Un choix dont on ne sait pas nommer l'alternative écartée n'est pas un choix.
Huit décisions structurantes, chacune avec ce qu'elle exclut.

### IV.1 La définition de la contrainte de risque

**Retenu** — drawdown sur 12 mois glissants, consolidé en euros, probabilité de
dépassement inférieure à 10 %.

**Écarté** — la VaR à 95 %, et le plafond absolu « jamais ».

**Raison** — le drawdown est la seule des trois mesures qui décrive ce que le
client vit : l'écart entre son meilleur relevé et le pire. C'est aussi la plus
contraignante, donc le choix conservateur. Quant au plafond absolu, aucun
gérant ne peut le garantir sur un portefeuille investi ; le promettre serait
malhonnête.

### IV.2 La famille d'indices ESG

**Retenu** — MSCI ESG Screened.

**Écarté** — MSCI SRI, qui procède par sélection des meilleurs de chaque
secteur, et les indices alignés Paris.

**Raison** — le mandat demande trois exclusions précises, pas une démarche ESG
large. ESG Screened exclut exactement ces trois secteurs et rien de plus :
l'univers reste à environ 95 % de l'indice parent, et l'écart de suivi
demeure sous 1 %. Le SRI, qui ne retient qu'environ un quart de l'univers,
irait bien au-delà de la demande et introduirait des biais sectoriels marqués
qu'il faudrait alors assumer et expliquer.

**Ce choix reste une question posée au client**, pas une décision prise à sa
place.

### IV.3 La portée du filtre ESG

**Retenu** — filtre exigé sur les seules classes à émetteurs d'entreprise.

**Écarté** — un filtre uniforme sur l'ensemble du portefeuille.

**Raison** — développée en III.3. Exiger un label sur de la dette souveraine ou
de l'or reviendrait soit à payer une surcouche sans contenu, soit à écarter
des instruments parfaitement conformes.

### IV.4 L'ancrage de Black-Litterman

**Retenu** — les hypothèses de marché comme prior, les vues appliquées en
écarts.

**Écarté** — l'optimisation inverse depuis un portefeuille neutre en parité de
risque.

**Raison** — l'optimisation inverse suppose que le portefeuille de référence
est optimal. Or nos hypothèses affirment le contraire : à 4 % d'inflation, le
souverain rapporte moins que le monétaire. La parité de risque étant
obligataire à 53 %, l'aversion au risque déduite tombait à 1,76 et la prime des
actions ressortait à 1,49 % au lieu de 3,65 %. Un prior qui contredit ses
propres hypothèses n'est pas un prior.

### IV.5 La méthode de backtest

**Retenu** — indices larges non filtrés sur 21,8 ans, effet du filtre ESG
mesuré séparément sur la période où il existe.

**Écarté** — le backtest sur les ETF eux-mêmes, et le backtest sur les séries
d'indices ESG reconstituées.

**Raison** — les ETF filtrés datent de 2016 à 2020 et ne couvrent aucune crise
majeure. Quant aux séries d'indices ESG antérieures à 2017, elles sont
**rétro-calculées** : la méthodologie a été appliquée après coup. Or un indice
n'est lancé qu'une fois qu'il a montré qu'il fonctionnait — backtester dessus
flatte donc systématiquement l'approche ESG.

La formulation retenue devant le client : *« nous vous montrons le comportement
de la stratégie sur vingt ans, reconstitué à partir d'indices larges. L'effet du
filtre éthique, nous le mesurons séparément sur la période où il existe
réellement. Nous ne vous présentons pas un historique 2008 d'un filtre qui
n'existait pas en 2008. »*

### IV.6 Le niveau de risque

**Retenu** — 45 % d'actifs de croissance.

**Écarté** — 50 %, sortie directe de l'optimisation.

**Raison** — à 50 %, le drawdown au 90ᵉ centile ressortait à 14,1 % et la
probabilité de dépassement à 9,2 %, soit juste sous les seuils de 15 % et 10 %.
Or l'estimation elle-même venait de bouger de deux points à la suite d'une
correction. Construire à la limite d'une mesure aussi sensible n'était pas
défendable.

Coût du dé-risquage : 19 points de base de rendement annuel.

**Constat annexe, et il est instructif.** Le dé-risquage a été opéré par
rotation des actions vers l'obligataire et l'or. Son effet sur la queue de
distribution s'est révélé **faible** : le drawadown P90 passe de 14,1 % à 13,8 %.
Un transfert équivalent vers le monétaire l'aurait ramené à 12,3 %.

Autrement dit : **dans les crises qui comptent, les obligations ne sont pas un
substitut sans risque.** Seul le monétaire réduit réellement la queue. C'est la
confirmation chiffrée, sur le portefeuille lui-même, de l'argument développé
contre le 60/40.

### IV.7 Le partage de la poche de liquidité

**Retenu** — 5 % de monétaire et 5 % de souverain court, échelonnés sur le
calendrier de décaissement.

**Écarté** — 100 % de monétaire, sortie directe de l'optimisation.

**Raison** — l'optimiseur a raison dans son cadre : à rendement voisin, 0,4 %
de volatilité domine 1,6 %. Mais il raisonne en **risque**, pas en
**adossement**. La poche de liquidité finance un décaissement daté ;
l'échelonner sur les échéances est un choix d'appariement, pas d'optimisation.

Point à soulever avec le client : si les dates de dépense sont incertaines, le
tout-monétaire redevient préférable.

### IV.8 La stratégie de transmission

**Retenu** — 30 % en assurance-vie, 40 % en nue-propriété donnée, 30 % en
compte-titres.

**Écarté** — la variante 30 / 60 / 10, qui transmet 15 M€ de plus.

**Raison** — elle donne la nue-propriété de 60 % du patrimoine dès aujourd'hui.
Le client conserve les revenus, mais perd le contrôle : il ne peut plus
arbitrer librement ce capital, ni le nantir, ni changer d'avis. À soixante ans,
avec deux enfants dont la maturité patrimoniale reste à observer, le gain
fiscal seul ne justifie pas une décision irréversible.

**À poser comme question au client, pas à trancher à sa place.**
""")


def partie_5() -> None:
    st.markdown("""
## V. Les erreurs trouvées, et ce qu'elles enseignent

Cette partie figure dans le dossier parce qu'elle explique pourquoi certains
paramètres valent ce qu'ils valent — et parce qu'un travail qui ne présente
aucune correction n'a, en pratique, pas été vérifié.

Neuf erreurs ont été identifiées et corrigées. Elles se répartissent en trois
familles, et chaque famille enseigne quelque chose de différent.

### V.1 Famille 1 — Postuler au lieu de mesurer

#### Le ratio drawdown / volatilité

**Avant** — 1,9, posé comme « règle empirique ».
**Après** — 1,35, mesuré sur 21,8 ans.

C'est le paramètre le plus porteur de tout le dossier : il traduit la contrainte
client en budget de risque, dont découle l'allocation entière. L'erreur
sous-allouait le risque d'environ dix points d'actions.

#### L'écart fiscal annuel

**Avant** — 85 points de base, puis 15.
**Après** — 38 points de base, dérivés d'un modèle explicite.

Le premier chiffre opposait une structure optimisée à un compte-titres garni de
fonds distribuants : un homme de paille, puisque personne de compétent ne
procède ainsi. Le deuxième, en corrigeant, sous-estimait la friction de
rebalancement. Seul le calcul dérivé tranche.

**Leçon** — un paramètre porteur doit pointer vers le script qui l'a mesuré.

### V.2 Famille 2 — Comparer des choses non comparables

#### Le régime d'inflation

**Avant** — un seuil bâti sur 4 % d'inflation comparé à des rendements attendus
bâtis implicitement sur 2 %.
**Après** — coefficients de répercussion par classe, et même régime des deux
côtés.

C'est la correction la plus importante de l'étude. La marge du mandat passe de
**−0,09 % à +0,99 %**. On évaluait un portefeuille dans un monde et on le
jugeait avec une exigence formulée dans un autre.

#### L'échelle des pondérations

**Avant** — des poids déjà nets de la poche de liquidité, multipliés une
seconde fois par le même facteur.
**Après** — une échelle unique.

Le portefeuille testé était à 72 % de risqué au lieu de 84 %. Le drawdown
annoncé à 12,0 % valait en réalité 14,1 %.

#### Les fenêtres d'observation

**Avant** — deux séries de longueurs différentes comparées directement, dont
l'une démarrait après le krach COVID.
**Après** — vérification systématique des dates de départ.

La série « avec crypto » paraissait moins risquée que la série « sans crypto ».
Ce n'était pas un effet de la crypto : c'était un effet de fenêtre.

**Leçon** — une erreur d'échelle ou de fenêtre ne se voit pas dans le résultat.
Elle le déplace silencieusement.

### V.3 Famille 3 — Les sorties dégénérées

Trois fois dans la même étude, un calcul d'optimisation a produit un résultat
mathématiquement correct et pratiquement inutilisable.

| Calcul | Sortie libre | Ce que le modèle ne voyait pas |
|---|---|---|
| Parité de risque | **82 % de monétaire**, neutre à 0,99 % de volatilité | Pour égaliser les contributions au risque, un actif à 0,4 % de volatilité doit peser énormément. La poche de liquidité est une décision de politique |
| Optimisation d'allocation | **28 % d'infrastructure**, 0,8 % d'or, 0 % de souverain | Concentration sectorielle, comportement en stress, scénario de récession, capacité d'exécution |
| Localisation des actifs | **100 % en assurance-vie** | Purge des plus-values au décès, liquidité, concentration sur un assureur, flexibilité |

**Leçon** — il faut lancer le calcul **libre d'abord**, précisément parce que
c'est lui qui révèle ce que le modèle ignore. Les contraintes ajoutées ensuite
ne sont pas de la prudence : elles encodent des risques absents de la matrice
d'entrée.

### V.4 Une erreur de statistique

**Avant** — les corrélations de stress estimées sur le décile des jours où la
moyenne des actifs était la plus basse.
**Après** — des périodes de crise définies a priori.

Conditionner sur une **somme** biaise mécaniquement à la baisse les
corrélations entre ses composantes. Le tableau produit montrait des
corrélations qui *diminuent* en crise — l'inverse du phénomène connu.

Une fois corrigé, le résultat est conforme à l'intuition : en 2022, la
corrélation du crédit aux actions passe de 0,27 à 0,37, celle de
l'infrastructure de 0,43 à 0,57. Et **l'or passe de 0,07 à −0,07** : seule
brique dont la diversification s'améliore sous stress. C'est l'argument chiffré
de sa présence à 7 %.

### V.5 Une prétention non vérifiée

**Avant** — le block bootstrap présenté comme donnant des estimations de perte
plus prudentes qu'un tirage naïf.
**Après** — mesuré, il tombe entre 0 et 0,6 point **en dessous** du 90ᵉ centile
historique, pour des longueurs de blocs allant de 21 à 252 jours.

Il recoupe le relevé historique, il ne le durcit pas. La formulation a été
corrigée dans tous les documents.

### V.6 Ce qu'on refuse de chiffrer

Une mesure a été tentée puis **abandonnée** : le coût du filtre ESG.

Cinq supports censés suivre des indices monde très proches donnent des écarts
allant de **−2,16 % à +1,03 %** par an. Une dispersion de cette ampleur entre
produits équivalents n'est pas un signal, c'est du bruit de mesure. Trois causes
identifiées : devises de cotation hétérogènes, clôtures non synchrones entre
Londres et New York, et traitement des dividendes non garanti homogène.

**Conclusion retenue : ne présenter aucun chiffre de coût ESG** tant qu'il n'a
pas été repris des fiches officielles des indices. C'est une donnée publique
que n'importe qui peut recouper ; une erreur y serait relevée immédiatement.

Savoir renoncer à un chiffre fait partie de la méthode.
""")


PARTIES = [
    ("I. Les données", partie_1),
    ("II. Le nettoyage", partie_2),
    ("III. La chaîne de construction", partie_3),
    ("IV. Les arbitrages", partie_4),
    ("V. Les erreurs et ce qu'elles enseignent", partie_5),
]


def render() -> None:
    st.header("Process — d'où vient chaque chiffre")
    st.caption("Méthodologie complète : sources et leurs limites, traitements "
               "appliqués, arbitrages avec l'alternative écartée, et les "
               "corrections faites en cours de route.")

    st.markdown("""
---
#### Plan

**I. Les données** — le principe de séparation des usages · les six sources,
leur nature et leurs limites · ce que l'application lit réellement

**II. Le nettoyage** — le constat initial · trois pathologies diagnostiquées ·
le traitement en trois étages · le piège des codes trompeurs · le mode de
défaillance dominant

**III. La chaîne de construction** — récupération robuste · constitution de
l'univers · sélection des instruments · hypothèses de marché · optimisation ·
validation du risque

**IV. Les arbitrages** — huit décisions structurantes, chacune avec ce qu'elle
écarte et pourquoi

**V. Les erreurs** — postuler au lieu de mesurer · comparer des choses non
comparables · les sorties dégénérées · et ce qu'on refuse de chiffrer

---
""")

    for titre, fn in PARTIES:
        with st.expander(titre, expanded=(titre.startswith("I."))):
            fn()
