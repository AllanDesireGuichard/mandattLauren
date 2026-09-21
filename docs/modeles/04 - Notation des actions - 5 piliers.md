---
titre: Notation des actions — cinq piliers
source: core/scoring.py — indicateurs(), _z_secteur(), noter(), selectionner()
maj: 2026-09-21
---

# Notation des actions — cinq piliers

## En une phrase

**On donne une note à chacune des 600 actions européennes, on garde les 30
meilleures.** La note est la moyenne de cinq jugements : est-elle bon marché,
grandit-elle, monte-t-elle, est-elle bien gérée, et encaisse-t-elle les
crises.

## Ce que ce n'est pas

> [!warning] Ce n'est pas un modèle à facteurs
> Pas de Fama-French, pas de Barra. Aucune régression, aucun bêta estimé,
> aucune prime de facteur calculée.
>
> Un modèle à facteurs **explique un rendement** : « cette action a rapporté
> 8 % parce qu'elle est exposée au facteur value à hauteur de 0,7 ».
> Ici on fait autre chose, de plus modeste : on **classe des titres** les uns
> par rapport aux autres. C'est une notation quantitative, la famille du
> *stock screening*. Elle ne prétend pas prédire un rendement.

## Le problème à résoudre avant de noter

On veut mélanger des choses qui n'ont rien à voir : un PER, une marge, une
volatilité, une croissance. Trois obstacles :

1. **Les unités sont différentes.** Un PER de 18 et une marge de 12 %, on ne
   peut pas en faire la moyenne.
2. **Les sens sont opposés.** Un PER bas est bon, une marge haute est bonne.
3. **Les niveaux normaux dépendent du secteur.** Une banque à PER 9 est
   normale, un éditeur de logiciels à PER 9 est en détresse.

Le pipeline règle ces trois problèmes dans l'ordre.

## Étape 1 — Tout mettre dans le sens « plus haut = mieux »

| On a | On utilise | Pourquoi |
|---|---|---|
| PER | **1 ÷ PER** | Devient le « rendement des bénéfices » : haut = bon marché |
| Cours / valeur comptable | **son inverse** | Idem |
| Dette / fonds propres | **son opposé** | Moins endetté = mieux noté |
| Volatilité | **son opposé** | Moins agitée = mieux notée |
| Bêta | **son opposé** | Moins sensible au marché = mieux notée |

> [!tip] L'inversion du PER n'est pas cosmétique
> **1 ÷ PER est directement un rendement.** À un PER de 20, tu achètes 5 %
> de bénéfices par an ; à un PER de 10, tu en achètes 10 %.
>
> Et surtout, l'échelle devient honnête. Passer d'un PER de 10 à 20 te coûte
> 5 points de rendement. Passer de 30 à 40 ne t'en coûte que 0,8. Sur le PER
> brut, les deux écarts valent « 10 » et seraient traités pareil — ce qui
> écraserait artificiellement tout le haut du classement.

## Étape 2 — Jeter les données manifestement fausses

Chaque indicateur a des bornes de plausibilité. **Hors bornes, la donnée
n'est pas écrêtée : elle est supprimée.** PER hors de [0 ; 150], croissance
des bénéfices hors de [−100 % ; +300 %], dividende hors de [0 ; 15 %].

> [!bug] Le cas réel qui justifie ce filtre
> Yahoo confond **pence et livres** sur certaines valeurs de Londres : le
> cours est en pence, la capitalisation en livres. Résultat, des PER
> multipliés par cent. Sans borne, ces titres arrivaient en fin de classement
> avec une note parfaitement calculée sur une donnée absurde — et rien ne
> signalait le problème.

## Étape 3 — Retirer trois indicateurs aux banques et à l'immobilier

Le flux de trésorerie libre, la marge opérationnelle et l'endettement sont
mis à « non disponible » pour le secteur Finance et Immobilier.

**Pourquoi.** Pour une banque, la dette n'est pas un fardeau de financement,
c'est sa matière première : elle emprunte pour prêter. La juger endettée,
c'est la juger sur son métier. Le flux de trésorerie libre n'a pas de sens
pour elle, et sa marge opérationnelle ne se définit pas comme ailleurs.

Les noter là-dessus reviendrait à classer les banques sur du bruit
comptable.

## Étape 4 — Ramener tout le monde sur la même échelle

C'est le cœur technique, et c'est simple une fois dit en français.

> **Pour chaque indicateur, on remplace la valeur brute par : « de combien
> cette action s'écarte de la moyenne de son secteur, mesuré en nombre
> d'écarts-types ».**

C'est le *score z*. Une action à +1 est meilleure que 84 % de son secteur.
À 0 elle est dans la moyenne. À −2 elle est dans les 2 % les plus mauvais.

**Ce que ça règle :** tout devient comparable. Un z de +1 sur le PER et un z
de +1 sur la marge veulent dire la même chose — « nettement au-dessus de ses
pairs » — et on peut enfin en faire la moyenne.

### Pourquoi « de son secteur » et pas « de tout le marché »

Si on notait contre l'univers entier, les secteurs structurellement bon
marché (banques, énergie) rafleraient toutes les bonnes notes de
valorisation, et la santé ou la technologie n'en auraient jamais.

> **On construirait un pari sectoriel déguisé en sélection de titres.**

En notant au sein du secteur, on cherche la meilleure banque parmi les
banques et le meilleur éditeur parmi les éditeurs.

### Deux détails du code qui méritent d'être connus

**Le rabotage des valeurs extrêmes se fait sur l'univers entier**, alors que
la comparaison se fait par secteur. Avant de calculer les écarts, on ramène
les 5 % de valeurs les plus hautes et les 5 % les plus basses aux seuils
correspondants — mais ces seuils sont calculés sur les 600 titres, pas
secteur par secteur.

C'est défendable : une valeur aberrante est un problème de *donnée*, qui est
global, alors que la comparaison est un problème d'*interprétation*, qui est
sectoriel. Mais ce n'est pas neutre, et ce n'était documenté nulle part.

*Le cas qui l'a motivé : Sanofi, dont la croissance des bénéfices ressortait
à −91 % à cause d'éléments exceptionnels. Sans rabotage, ce seul chiffre
plombait tout le pilier Croissance du secteur santé.*

**Si un secteur compte moins de 5 titres exploitables**, on le compare à
l'univers entier. Sans ce repli, un secteur à deux titres donnerait
mécaniquement un « bon » et un « mauvais » à ±0,7, quelle que soit leur
qualité réelle.

## Étape 5 — Les cinq piliers, indicateur par indicateur

**Poids égaux : 20 % chacun.** Aucun pilier n'a de raison *mesurée* d'être
privilégié — pondérer demanderait d'estimer des primes de facteur sur
l'univers européen, ce qui est un autre projet.

### Pilier 1 — Valorisation : « est-ce que je la paie cher ? »

| Indicateur | Ce qu'il mesure concrètement |
|---|---|
| Rendement des bénéfices | Les bénéfices annuels rapportés au prix payé. À PER 20, tu achètes 5 % par an |
| Rendement des bénéfices attendus | Pareil, sur les bénéfices que les analystes prévoient l'an prochain |
| Valeur comptable / cours | Ce que vaudrait l'entreprise si on la liquidait, rapporté à son prix |
| Flux de trésorerie libre / capitalisation | Le **cash réellement dégagé** rapporté au prix. Plus dur à maquiller que le bénéfice comptable |
| Rendement du dividende | Ce qui est effectivement versé à l'actionnaire |

*Note haute = tu paies peu cher ce que l'entreprise produit.*

### Pilier 2 — Croissance : « est-ce que ça grandit ? »

| Indicateur | Ce qu'il mesure concrètement |
|---|---|
| Croissance des bénéfices sur un an | Le bénéfice a-t-il augmenté |
| Croissance du chiffre d'affaires sur un an | Les ventes ont-elles augmenté. Moins manipulable que le bénéfice |
| Révision du bénéfice par action | Le bénéfice **attendu** rapporté au bénéfice **passé** : les analystes révisent-ils en hausse ? |

*Le troisième est le plus intéressant : il capte le changement d'opinion du
marché, pas seulement le passé.*

### Pilier 3 — Dynamique : « est-ce que ça monte ? »

| Indicateur | Ce qu'il mesure concrètement |
|---|---|
| Performance 12 mois **hors dernier mois** | La tendance de fond sur un an |
| Performance 6 mois | La tendance récente |

> [!tip] Pourquoi exclure le dernier mois
> C'est la définition académique standard du momentum. Le dernier mois porte
> un effet de **retournement à court terme** : une action qui vient de
> beaucoup monter a tendance à refluer juste après. L'inclure ajoute du
> bruit qui va à l'encontre du signal qu'on cherche.

### Pilier 4 — Qualité : « est-ce que c'est bien géré ? »

| Indicateur | Ce qu'il mesure concrètement |
|---|---|
| Rentabilité des fonds propres (ROE) | Ce que l'entreprise gagne avec l'argent des actionnaires |
| Rentabilité des actifs (ROA) | Ce qu'elle gagne avec tout ce qu'elle possède. Moins flatté par la dette que le ROE |
| Marge nette | Ce qui reste en bas du compte de résultat, pour 100 € de ventes |
| Marge opérationnelle | Ce qui reste **avant** frais financiers et impôts : la rentabilité du métier lui-même |
| Endettement (inversé) | Dette rapportée aux fonds propres |

*ROE et ROA sont mis ensemble volontairement : un ROE élevé obtenu par
beaucoup de dette se trahit par un ROA médiocre.*

### Pilier 5 — Résistance : « est-ce que ça tient en crise ? »

| Indicateur | Ce qu'il mesure concrètement |
|---|---|
| Volatilité 3 ans (inversée) | À quel point le cours bouge au quotidien |
| Perte maximale en 2020 | Ce que le titre a perdu pendant le Covid |
| Perte maximale en 2022 | Ce qu'il a perdu pendant le choc d'inflation |
| Bêta (inversé) | De combien il amplifie les mouvements du marché |

> [!important] Ce pilier a été ajouté pour CE mandat, et voici le raisonnement
> La contrainte du client est une **perte maximale de 15 %**. Cette limite se
> tient au niveau du portefeuille entier. Or plus la poche actions encaisse
> bien les crises, **plus on peut en détenir** pour la même limite.
>
> Ce pilier n'achète donc pas du rendement : **il achète du budget de
> risque**, qui sera ensuite dépensé en actions dans
> [[05 - Optimisation sous contrainte de perte]]. C'est le pilier qui relie
> l'étape 3 à l'étape 4.
>
> Les deux crises retenues sont complémentaires : 2020 est un krach brutal
> et bref, 2022 une érosion longue par l'inflation. Bien tenir dans l'une ne
> dit rien de l'autre.

## Étape 6 — Les garde-fous de calcul

- **Un pilier n'est calculé que si assez d'indicateurs sont disponibles.**
  Précisément : `max(1, nombre ÷ 2)` en division entière. Pour Valorisation
  (5 indicateurs) le seuil est **2** — donc un peu moins que la moitié.
- **La note finale exige au moins 4 piliers sur 5.**

Sans ces quorums, un titre noté sur un seul indicateur chanceux ressortirait
en tête du classement. Faire la moyenne sur les seuls indicateurs
disponibles revient à supposer que les manquants sont dans la moyenne — ce
qui est acceptable si on en exige assez, et dangereux sinon.

## Étape 7 — La sélection : la note ne suffit pas

On descend le classement du meilleur au moins bon, et on prend, sous trois
plafonds :

1. **4 titres maximum par secteur**
2. **6 titres maximum par pays**
3. **volatilité inférieure au 90ᵉ percentile** de l'univers noté

> [!note] Le plafond de volatilité est mesuré, pas décidé
> C'est le 90ᵉ percentile de l'univers noté, recalculé à chaque fois. Le
> seuil suit donc l'agitation des marchés, au lieu d'être un nombre en dur
> qui deviendrait absurde en régime de crise. **Les 10 % de titres les plus
> agités sont écartés même très bien notés** — demande explicite d'Allan.

Les plafonds secteur et pays existent parce qu'une notation relative au
secteur **peut quand même concentrer** : si tout un secteur est bien noté,
il rafle la sélection. Ils coûtent de la note et achètent de la
diversification.

## L'exclusion qui n'est pas dans la note

Onze **sociétés d'investissement cotées** (Investor, Industrivärden, Exor,
Sofina, 3i, Aker…) sortent de la notation — mais restent dans l'univers.

**Pourquoi.** Leur bénéfice comptable inclut la réévaluation de leurs
participations. Si leurs participations montent de 30 %, leur « bénéfice »
explose sans qu'elles aient rien produit. PER, rentabilité et croissance
n'ont donc pas le sens qu'ils ont pour une entreprise opérationnelle.

Notées comme les autres, **elles arrivaient en tête du classement pour une
raison purement comptable**.

C'est une correction faite à la main, sur une liste nommée. Ce n'est pas
élégant, et c'est honnête : aucun filtre automatique ne distingue un holding
d'un conglomérat industriel.

## Le résultat, et son contrôle

30 titres, 10 secteurs, 10 pays, à parts égales.

| | Le panier | STOXX Europe 600 |
|---|---|---|
| Volatilité 3 ans | **10,4 %** | 12,8 % |
| Pire baisse 2020 | −34,0 % | −32,1 % |
| Pire baisse 2022 | **−12,8 %** | −18,4 % |

Moins agité au quotidien, nettement mieux tenu en 2022, à égalité en 2020.
**Mais en crise il perd bien plus que 15 %** : c'est le dosage avec les
obligations et l'or, à l'étape 4, qui tiendra la limite.

> [!danger] Le biais que ce contrôle ne corrige pas
> Les 30 titres sont choisis **avec les données d'aujourd'hui**, puis on
> regarde leur passé. Ils ont donc un passé flatteur par construction : ils
> battent l'indice de plusieurs points par an depuis 2019, ce qui ne prouve
> rien du tout.
>
> C'est pourquoi [[05 - Optimisation sous contrainte de perte]] mesure le
> risque de la ligne « actions Europe » **sur l'indice**, pas sur le panier.
> On refuse d'importer un avantage qu'on sait faux.

→ Aval : [[05 - Optimisation sous contrainte de perte]]
