---
titre: Rendements espérés par classe d'actifs
source: scripts/estimer_rendements.py -> data/rendements.json
maj: 2026-09-21
---

# Rendements espérés par classe d'actifs

## En une phrase

**Combien chaque grande famille de placements devrait rapporter par an sur
dix ans, en euros, si l'inflation est de 4 % comme le suppose le client.**

> [!important] Le principe qui gouverne tout
> **On ne prévoit rien.** Aucun modèle de croissance, aucune prévision
> d'inflation, aucune vue de gérant sur les taux. Chaque chiffre est soit un
> taux qu'on lit sur le marché, soit un prix qu'on traduit en rendement,
> soit une hypothèse qu'on étiquette comme telle.
>
> C'est un choix défendable en soutenance : « nous n'avons rien prévu, nous
> avons lu ».

## 1. Les obligations à taux fixe : il n'y a rien à modéliser

Si tu achètes une obligation et que tu la gardes jusqu'au bout, **tu sais
déjà ce qu'elle va te rapporter**. C'est écrit dans le contrat : les coupons
sont fixés, la date de remboursement aussi.

> **Pour une obligation portée jusqu'à l'échéance, le taux à l'achat *est*
> le rendement attendu.**

Il n'y a donc aucune estimation à faire. On lit la courbe (voir
[[02 - Valorisation obligataire]]) et c'est terminé.

| Ligne | Rendement | D'où il sort |
|---|---|---|
| Monétaire | 2,44 % | Le taux €STR du jour |
| États AAA 6-24 mois | 3,03 % | Moyenne de l'échelle des 10 M€ |
| États zone euro 2-10 ans | 3,63 % | Moyenne des cinq échéances |

> [!warning] On n'ajoute AUCUNE « répercussion d'inflation »
> Une version antérieure du dossier appliquait à chaque classe un
> coefficient censé dire quelle part d'une hausse d'inflation se retrouvait
> dans son rendement. Ces coefficients étaient **inventés, pas mesurés**.
> Ils ont été retirés.
>
> Et de toute façon, pour une obligation à taux fixe, la réponse est zéro :
> le coupon est fixe, c'est sa définition. **C'est exactement pour ça
> qu'aucune obligation classique ne protège contre 4 % d'inflation** — le
> constat central de l'étape 2.

## 2. Le crédit : le taux affiché est un plafond, pas une espérance

Une obligation d'entreprise paie plus qu'un État. Normal : l'entreprise peut
faire faillite. Donc **une partie de ce supplément n'est pas un gain, c'est
la compensation d'une perte future**.

> **Rendement attendu du crédit = taux affiché − pertes moyennes sur
> défauts.**

Les pertes viennent de Moody's, qui publie des statistiques de défaut
depuis 1920. Elles sont données **en cumulé sur 5 ans**, il faut donc les
ramener à l'année :

- Bien noté : 0,55 % cumulés sur 5 ans → **0,11 % par an**
- Haut rendement : 14,88 % cumulés → **3,17 % par an**

Résultat : crédit euro court à **3,50 − 0,11 = 3,39 %**.

> [!tip] Le chiffre qui tue le haut rendement
> Il affiche 6,05 %, ce qui paraît très attractif. Défauts déduits, il reste
> **2,88 %** — c'est-à-dire **moins qu'un emprunt d'État de la zone euro**.
>
> Le rendement affiché d'un fonds high yield est un rendement *si personne
> ne fait faillite*. C'est un plafond, jamais une espérance. La distinction
> se comprend en une phrase, et beaucoup de concurrents ne la feront pas.

> [!caution] Limite assumée
> Ces statistiques sont **américaines**, transposées à l'euro, et couvrent
> 1982-2004 — donc ni 2008 ni 2020. Elles sous-estiment probablement les
> mauvaises années.

## 3. Les obligations indexées : la seule protection contractuelle

Une obligation indexée verse un taux **plus l'inflation constatée**. Son
lien à l'inflation n'est pas supposé, il est écrit dans le contrat.

> **1,43 % (le taux réel qu'on lit sur le marché) + 4 % (l'inflation de
> l'énoncé) = 5,43 %.**

C'est la seule classe obligataire au-dessus du seuil, et la seule dont on
puisse dire qu'elle protège par construction.

## 4. Les actions : deux façons de raisonner, puis leur moyenne

C'est le morceau discutable. Il faut savoir le défendre.

### Façon 1 — « combien de bénéfices j'achète pour mon argent »

Quand tu achètes une action, tu achètes une part des bénéfices futurs de
l'entreprise. Le PER te dit combien tu paies pour un euro de bénéfice
annuel.

> **À un PER de 20, tu achètes 5 % de bénéfices par an. À un PER de 10, tu
> en achètes 10 %.**

Et sur longue période, ce que rapporte une action au-delà de l'inflation
converge vers ce chiffre-là. **L'hypothèse implicite** : le marché ne se
met pas durablement à payer les bénéfices plus cher (ou moins cher) qu'aujourd'hui.

### Façon 2 — « ce qu'on me verse, plus ce qui grandit »

Autre raisonnement, complètement différent :

> **Ce que rapporte une action = le dividende qu'on te verse + la croissance
> des bénéfices de l'entreprise.**

Le dividende se lit. La croissance, elle, est mesurée sur très longue
période : **2,0 % par an au-delà de l'inflation**, sur le S&P 500 depuis
1900 (données Shiller).

Deux précautions dans ce calcul :
- on **déflate par l'inflation** avant tout, pour obtenir une croissance
  réelle et pas une croissance gonflée par les prix ;
- on **lisse sur dix ans**, sinon la date de départ tombe sur un pic ou un
  creux de cycle et le résultat bouge de plusieurs points.

### L'assemblage

> **Rendement espéré = moyenne des deux façons + 4 % d'inflation.**

Le « + 4 % » suppose que **les entreprises répercutent l'inflation dans
leurs bénéfices** — elles vendent plus cher quand les prix montent.
Hypothèse forte mais raisonnable, et contrairement aux obligations, elle a
un mécanisme derrière.

| Zone | PER | Dividende | Façon 1 | Façon 2 | **Espéré** |
|---|---|---|---|---|---|
| Europe | 18,5 | 3,07 % | 5,41 % | 5,05 % | **9,23 %** |
| États-Unis | 30,0 | 1,06 % | 3,33 % | 3,04 % | **7,19 %** |
| Japon | 19,1 | 3,66 % | 5,24 % | 5,64 % | **9,44 %** |
| Émergents | 20,8 | 2,96 % | 4,81 % | 4,94 % | **8,40 %** |

**L'Europe ressort devant les États-Unis uniquement à cause du prix payé** :
PER de 18,5 contre 30,0. L'action américaine est de meilleure qualité, mais
elle se paie presque deux fois plus cher.

> [!danger] Les trois attaques prévisibles, et les réponses
> **« Vous mettez la même croissance partout. »** Vrai, et ça pénalise les
> États-Unis, dont le poids technologique justifierait plus. Mesurer une
> croissance par zone demanderait un historique long par zone qu'on n'a pas.
> Assumé et dit.
>
> **« Votre PER dépend de la source. »** Vrai aussi. Avec les PER Yahoo
> (24,6) au lieu d'iShares (30,0), les États-Unis remontent à environ 8,1 %.
> L'écart avec l'Europe se réduit fortement — **mais il ne s'inverse pas**.
>
> **« Pourquoi le Japon premier ? »** Parce qu'il cumule un PER raisonnable
> (19,1) et un dividende élevé (3,66 %). **C'est la donnée la plus fragile
> de l'étape** : si ce dividende est faux, toute l'allocation japonaise du
> calcul libre est fausse. Voir [[05 - Optimisation sous contrainte de perte]].

## 5. L'or et les matières premières : une hypothèse, et elle est dite

L'or ne verse rien. Pas de coupon, pas de dividende, pas de loyer. **Il n'y
a donc aucun flux à actualiser, donc aucune méthode d'estimation possible.**

On ne peut pas estimer, on peut seulement poser une hypothèse : l'or
conserve son pouvoir d'achat, donc il suit l'inflation, donc **4,00 %**,
avec une fourchette de deux points de part et d'autre.

> [!note] L'honnêteté est dans les données, pas dans un commentaire
> Dans `rendements.json`, chaque ligne porte une étiquette : `"mesuré"`,
> `"estimé"` ou `"hypothèse"`. L'or est étiqueté `"hypothèse"`, et
> l'application **affiche cette nature** à côté du chiffre. On ne peut donc
> pas faire passer une supposition pour une mesure, même par inadvertance.

## 6. La crypto : zéro

Même raison que l'or, sans même l'argument du pouvoir d'achat. Valeur
retenue : 0.

Elle reste mesurée **en risque** (−72,9 % en 2020, −73,8 % en 2022, en
baissant *avec* les actions) pour pouvoir montrer au fils de M. Lauren
*pourquoi* on l'écarte. Un refus argumenté vaut mieux qu'un refus de
principe.

## Le contrôle externe, et son piège

Chaque chiffre est confronté aux hypothèses long terme de **J.P. Morgan
Asset Management** (LTCMA 2026, en euros).

> [!check] Le piège de comparaison, et il est au cœur du dossier
> **J.P. Morgan suppose 2 % d'inflation. Nous supposons 4 %.**
>
> Comparer les deux colonnes telles quelles fait apparaître un écart de deux
> points qui n'existe pas : ce n'est pas un désaccord sur les actifs, c'est
> un désaccord sur l'inflation. Il faut **ramener les deux au même régime**
> avant de conclure quoi que ce soit.
>
> Une fois alignés : même sens, écart inférieur à un point.
>
> **C'est exactement le même piège** que celui corrigé dans
> [[06 - Backtest et mesures de risque]] : juger un résultat obtenu dans un
> monde avec l'exigence d'un autre monde. Il revient deux fois dans le
> dossier, à deux endroits sans rapport. Il faut le connaître.

## Le résultat qui commande toute la suite

**Seules les actions et les obligations indexées dépassent 4 %.**

Donc chaque euro placé ailleurs — emprunts d'État, crédit, or, monétaire —
devra être compensé par des actions pour tenir l'objectif. C'est toute la
tension du dossier : viser 4 % impose du risque, limiter la perte à 15 % en
interdit trop. Voir [[05 - Optimisation sous contrainte de perte]].

→ Amont : [[02 - Valorisation obligataire]] · Aval : [[05 - Optimisation sous contrainte de perte]]
