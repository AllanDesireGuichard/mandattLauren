---
titre: Optimisation sous contrainte de perte maximale
source: core/allocation.py (classe Chemin), scripts/optimiser.py
maj: 2026-09-21
---

# Optimisation sous contrainte de perte maximale

## En une phrase

**Trouver combien mettre sur chaque support pour que le portefeuille rapporte
le plus possible, sans jamais avoir perdu plus de 15 % sur les vingt
dernières années.**

## Le problème, écrit en français

- **Ce qu'on cherche à maximiser** : le rendement espéré du portefeuille.
  C'est la moyenne des rendements de chaque ligne (étape 2), pondérée par ce
  qu'on y met.
- **La contrainte** : on rejoue le portefeuille jour par jour de 2006 à
  aujourd'hui, rééquilibré chaque mois. À chaque instant on regarde de
  combien il est descendu sous son meilleur niveau passé. **Ce creux ne doit
  jamais dépasser 15 %.**
- **Les évidences** : les poids sont positifs (pas de vente à découvert) et
  font 100 %.

L'objectif est facile. **Toute la difficulté est dans la contrainte.**

## Pourquoi pas Markowitz — la question qui sera posée

La théorie classique dit : calcule la matrice de covariance, minimise la
variance à rendement donné, tu obtiens la frontière efficiente. Pourquoi ne
pas l'avoir fait ?

> [!important] Parce que la contrainte du client n'est pas une volatilité
> M. Lauren n'a pas dit « je veux une volatilité de 6 % ». Il a dit **« je ne
> veux jamais perdre plus de 15 % »**. Ce sont deux objets différents.

Prends un portefeuille et note ses rendements mensuels sur vingt ans.
Maintenant **mélange les mois au hasard**, comme un paquet de cartes.

- **La volatilité ne change pas d'un iota.** Elle ne regarde que la
  dispersion des rendements, pas leur ordre d'arrivée.
- **La pire baisse change complètement.** Si tous les mauvais mois se
  suivent, tu creuses un trou de 40 %. S'ils sont éparpillés entre de bons
  mois, tu ne descends jamais à plus de 10 %.

> **La volatilité ignore l'ordre. Le drawdown ne dépend que de l'ordre.**

Autrement dit : on ne peut pas calculer la pire baisse à partir de la
matrice de covariance. Il n'existe pas de formule qui relie les deux — sauf
en supposant que les rendements sont indépendants et gaussiens, ce qui est
précisément faux dans les crises, c'est-à-dire là où ça compte.

**Optimiser la variance en espérant que la perte maximale suive aurait été
un raccourci non vérifié.** On mesure donc directement sur le chemin
historique.

### Le prix de ce choix, et il est réel

La contrainte est évaluée sur **une seule trajectoire**, celle qui a eu lieu.
Le calcul ne cherche donc pas le portefeuille robuste : il cherche **le
portefeuille qui aurait le mieux marché sur ces vingt années précises**.
C'est du surapprentissage, au sens plein du terme.

C'est pour ça que le résultat brut est **rejeté**, puis corrigé par des
règles dont on chiffre le coût une par une (plus bas).

### Et Black-Litterman ?

Écarté pour une autre raison. Black-Litterman sert à mélanger un équilibre
de marché avec des opinions personnelles. Or ici, **les opinions sont déjà
dans les rendements espérés** : ils viennent des valorisations, et dire
« l'Europe est moins chère donc rapportera plus » *est* l'opinion. Les
réinjecter par Black-Litterman reviendrait à les compter deux fois.

## Comment on calcule vite le chemin

L'optimiseur teste des milliers de répartitions. Pour chacune, il faut
rejouer vingt ans de bourse avec un rééquilibrage mensuel. Fait naïvement,
c'est inutilisable.

L'astuce : **pré-calculer une fois pour toutes, pour chaque jour et chaque
actif, sa performance depuis le dernier rééquilibrage**. Une fois cette
table construite, la valeur du portefeuille pour n'importe quelle
répartition s'obtient par une seule multiplication de tableaux, d'un coup
pour les 5 209 jours. Il ne reste qu'à enchaîner les 240 mois entre eux.

```python
self.g = (p / base).to_numpy()   # performance depuis le dernier rééquilibrage
...
x = self.g @ w                   # tout le chemin, en une opération
```

> [!note] Ce que « rééquilibré chaque mois » veut dire
> Le premier jour de chaque mois, on remet les poids à leur cible. Entre
> deux, chaque ligne vit sa vie et les poids dérivent.
>
> C'est la convention d'un mandat réel, et elle est **prudente** : le
> rééquilibrage vend mécaniquement ce qui a monté et achète ce qui a baissé,
> ce qui amortit les creux.

## Comment on résout

La pire baisse n'est pas une fonction « lisse » des poids. Quand on déplace
un peu les poids, le creux le plus profond peut sauter brutalement d'une
date à une autre — et le calcul fait un angle. Les solveurs classiques
peuvent s'arrêter sur un de ces angles en croyant avoir trouvé le sommet.

La parade :

> **On part de seize répartitions tirées au hasard, on optimise depuis
> chacune, et on garde la meilleure qui respecte la limite.**

Le tirage est fait avec une graine fixée : **le résultat est reproductible**,
ce qui n'est pas négociable pour un dossier qu'on doit pouvoir refaire
devant quelqu'un.

Et surtout, **on revérifie la contrainte à la sortie** :

```python
if chemin.pire_baisse(w) < -limite - 5e-4:
    continue          # le solveur a triché, on jette
```

Un solveur peut rendre une solution qui viole légèrement la contrainte. On
ne lui fait pas confiance.

## Le calcul libre, et pourquoi il est inutilisable

Sans aucune règle autre que la limite de 15 %, le calcul répond :

| Ligne | Poids |
|---|---|
| Obligations indexées | 55 % |
| Japon | 32 % |
| États longs | 9 % |

**6,47 % de rendement espéré.** C'est un plafond utile — rien ne fera mieux
sous cette limite — mais ce n'est pas une proposition.

> [!danger] Ce que le calcul a appris par cœur
> **Le Japon** est choisi pour deux raisons. D'abord c'est le rendement
> espéré le plus élevé (9,44 %), tiré par un dividende de 3,66 % qui est la
> donnée la plus fragile de [[03 - Rendements espérés]]. Ensuite c'est
> l'action qui a le mieux tenu en 2008 : **−49,1 % en euros contre −59,0 %
> pour l'Europe**. L'avantage est réel, mais il ne fait que dix points, et
> il repose sur **une seule crise**.
>
> **Les indexées** sont les seules obligations au-dessus de 4 %, et leur
> 2008 est **flatté par un remplaçant** : avant 2009 la série utilisée est
> un emprunt d'État classique, qui a mieux tenu que les vraies indexées.
>
> Deux lignes font 87 % du portefeuille. Si l'une se comporte autrement
> qu'en 2006-2026, rien ne compense.

## Les quatre règles, et ce que chacune coûte

On relance le calcul en ajoutant une règle à la fois, chacune gardant les
précédentes. **C'est le tableau le plus important du dossier** : il met un
prix sur chaque précaution.

| Règle ajoutée | Rendement | Coût | Ce que le calcul répond |
|---|---|---|---|
| Seule la limite de 15 % | 6,47 % | — | indexées 55, Japon 32, États longs 9 |
| + 10 % sur l'échelle AAA | 6,46 % | −0,01 | indexées 58, Japon 32, AAA 10 |
| + clé actions 40/35/10/15 | 5,78 % | −0,68 | indexées 70, actions 20, AAA 10 |
| + plafonds par ligne | 5,40 % | −0,38 | États longs 37, actions 32, indexées 15 |
| + marge à 14 % | **5,31 %** | −0,09 | États longs 41, actions 30, indexées 15 |

### Ligne par ligne

**−0,01 point pour les 10 M€.** Le résultat le plus contre-intuitif, et ton
meilleur argument client. Regarde d'où vient l'argent : les États longs
passent de 9 % à 0 et le crédit de 2 % à 0. Le calcul a payé l'échelle AAA
(3,03 %) en vendant des obligations qui rapportaient à peu près pareil —
3,63 % et 3,39 %. Il a troqué une obligation médiocre contre une autre.
**Sécuriser la liquidité du client ne coûte rien.**

**−0,68 point pour la clé actions. La plus chère du tableau.** On fige la
composition de la poche actions — 40 % Europe, 35 % États-Unis, 10 % Japon,
15 % émergents — et le calcul ne décide plus que de sa **taille**. Ça coûte
cher parce que ça oblige à acheter 35 % d'américain à 7,19 % là où il se
concentrait sur du japonais à 9,44 %. **Ces 0,68 point achètent l'absence
de pari géographique.** Le portefeuille final ne contient plus que 3 % de
Japon.

**−0,38 point pour les plafonds.** La ligne d'avant mettait 70 % sur un seul
support, ce qui est inacceptable quel que soit le rendement. On plafonne :
indexées 15 %, or 10 %, matières premières 5 %, crédit 20 %. Effet de bord
intéressant : le portefeuille devient **plus diversifié ET plus actions**
(20 → 32 %), parce que priver le calcul des indexées ne lui laisse que les
actions pour tenir le rendement.

**−0,09 point pour la marge à 14 %.** La seule règle qui ne vienne pas du
client mais de nous. Elle laisse un point de jeu pour les erreurs de mesure
des remplaçants d'avant 2018. **L'assurance la moins chère du tableau.**

> [!tip] La colonne que personne ne regarde
> La pire baisse affiche **−15,0 % sur les quatre premières lignes**. Ce
> n'est pas un hasard : le calcul maximise le rendement, donc il va
> systématiquement s'écraser contre la limite.
>
> **À chaque étape, ce qui l'arrête c'est le risque, jamais les règles.**
> Les règles ne réduisent pas le budget de risque, elles changent seulement
> la façon dont il est dépensé. C'est la phrase à avoir en tête si on te
> demande pourquoi le rendement baisse à chaque ligne.

## La variante testée et écartée

Si l'objectif était 4 % **au-dessus** de l'inflation (8 % nominal), il serait
hors d'atteinte ici : le plafond est à 6,47 %. En remplaçant « jamais plus
de 15 % » par « plus de 15 % au plus une année sur vingt », la cible devient
atteignable — mais à un prix qui la disqualifie.

| Contrainte de risque | Rdt max | Perte dépassée 1 an/20 | Perte **moyenne** ces années-là | Pire baisse |
|---|---|---|---|---|
| Pire baisse ≥ −15 % (retenue) | 6,47 % | −6,9 % | −8,9 % | −15,0 % |
| « 1 année sur 20 » | 8,42 % | −15,0 % | **−29,5 %** | **−51,5 %** |
| Version plus exigeante | 7,77 % | −13,5 % | −15,0 % | −32,3 % |
| Aucune | 9,44 % | −25,2 % | −27,0 % | −52,7 % |

**Trois raisons de refuser.** La règle « une année sur vingt » dit à partir
de quand on dépasse, mais **pas de combien** — et la réponse est −29,5 % en
moyenne, −51,5 % au pire. La version qui borne aussi l'ampleur n'atteint pas
la cible. Et ces seuils reposent sur **sept épisodes de baisse distincts**
en vingt ans : on mesurerait la queue de la distribution avec une poignée
d'observations.

→ Amont : [[03 - Rendements espérés]], [[04 - Notation des actions - 5 piliers]]
· Aval : [[06 - Backtest et mesures de risque]]
