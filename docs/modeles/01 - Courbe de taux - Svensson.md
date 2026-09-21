---
titre: Courbe de taux — modèle de Svensson
source: core/obligations.py, fonction taux_zero()
donnees: data/taux_marche.json, clé "svensson"
maj: 2026-09-21
---

# Courbe de taux — Svensson

## En une phrase

**Une machine qui donne le taux d'intérêt pour n'importe quelle durée, à
partir de six nombres publiés chaque jour par la BCE.**

## Le problème

Prêter de l'argent à l'État allemand pour 3 mois, ce n'est pas le même taux
que pour 10 ans. Il y a donc un taux par durée — c'est ce qu'on appelle la
courbe des taux.

Le problème pratique : les obligations qui existent ont des échéances en
désordre. Il y en a une à 4 ans et 2 mois, une à 7 ans et 9 mois, rien à
6 ans. Si j'ai besoin du taux à 6 ans exactement, personne ne me le donne.

Deux solutions possibles :

1. **Relier les points** entre les obligations existantes. Simple, mais on
   recopie le bruit : si une obligation cote un peu de travers ce jour-là
   (peu échangée, mal cotée), la courbe fait une bosse qui n'existe pas.
2. **Décrire la forme de la courbe** par quelques nombres, et accepter de
   ne pas passer exactement par chaque point. C'est Svensson.

## L'idée : une courbe de taux a toujours la même allure

Regarde n'importe quelle courbe de taux, de n'importe quel pays, de
n'importe quelle époque. Elle se décrit toujours avec trois ingrédients :

**1. Un niveau général.** La courbe est globalement haute ou globalement
basse. En 2021 elle était vers 0 %, aujourd'hui vers 3 %.

**2. Une pente.** Soit le court terme rapporte moins que le long terme
(courbe montante, situation normale : on exige plus pour prêter longtemps),
soit l'inverse (courbe inversée, signal de récession classique).

**3. Une ou deux bosses au milieu.** La courbe n'est presque jamais une
ligne droite. Il y a souvent un renflement vers 2-3 ans, parfois un second
vers 10-15 ans, parce que les banques centrales agissent sur le court terme
et les assureurs achètent le très long.

> [!tip] L'analogie
> C'est comme décrire un visage. Tu peux lister la couleur de chaque pixel
> (l'interpolation), ou tu peux dire « ovale, yeux écartés, nez droit »
> (Svensson). La seconde description est plus courte, plus robuste au bruit,
> et elle permet de dessiner les parties qu'on n'a pas vues.

## Les six nombres

| Nom | Ce qu'il règle | Comment le lire |
|---|---|---|
| **β₀** | Le niveau du très long terme | Le taux vers lequel la courbe tend quand on va très loin. Aujourd'hui ≈ 3,3 % |
| **β₁** | La pente | Le taux au jour le jour vaut **β₀ + β₁**. Si β₁ est négatif, le court terme est sous le long : courbe montante |
| **β₂** | La taille de la première bosse | Positif = renflement, négatif = creux |
| **β₃** | La taille de la seconde bosse | Idem, plus loin sur la courbe |
| **τ₁** | Où se situe la première bosse | En années. Typiquement 1 à 3 ans |
| **τ₂** | Où se situe la seconde | Typiquement 10 à 20 ans |

**Quatre boutons de taille, deux boutons de position.** C'est tout.

> [!note] Les deux lectures immédiates d'un gérant
> - **β₀ + β₁** = le taux court d'aujourd'hui.
> - **−β₁** = l'écart court-long, c'est-à-dire la pente. C'est le signal de
>   cycle le plus regardé au monde : une pente qui s'inverse a précédé la
>   plupart des récessions.

## La formule, pour mémoire

$$
r(m) = \beta_0
+ \beta_1 f_1(m)
+ \beta_2 f_2(m)
+ \beta_3 f_3(m)
$$

**Ce que ça dit en français :** le taux pour une durée *m* est un niveau de
base, plus une contribution de pente, plus deux contributions de bosse.
Chaque *f* est une forme fixe, et les β disent avec quelle intensité on
applique chaque forme.

Les trois formes ont des comportements qui font tout le travail :

- **f₁ (la pente)** vaut 1 pour les durées très courtes et s'efface
  progressivement vers 0 pour les longues. Donc β₁ agit sur le court terme
  et plus du tout sur le long.
- **f₂ et f₃ (les bosses)** valent 0 aux deux extrémités et sont maximales
  au milieu, autour de τ₁ et τ₂. Donc elles déforment le ventre de la courbe
  sans toucher ni le court ni le long.

C'est cette propriété — *chaque forme agit sur une zone et une seule* — qui
rend le modèle lisible. Si tu changes β₂, seul le ventre bouge.

```python
def taux_zero(m, p):
    m = max(m, 1e-6)                      # évite la division par zéro
    a, b = m / p["tau1"], m / p["tau2"]
    f1 = (1 - math.exp(-a)) / a
    f2 = f1 - math.exp(-a)
    f3 = (1 - math.exp(-b)) / b - math.exp(-b)
    return p["beta0"] + p["beta1"]*f1 + p["beta2"]*f2 + p["beta3"]*f3
```

## Ce que ça permet dans le dossier

**Les emprunts d'État sont achetés en direct**, pas via un fonds. Pour cela
il faut pouvoir dire ce que vaut une obligation qui n'existe pas encore —
par exemple « une obligation à 18 mois pour couvrir le décaissement de
M. Lauren ». Sans Svensson, il faudrait une source de cotations payante.
Avec, un fichier de six nombres suffit.

C'est aussi ce qui permet de construire l'échelle AAA de 6 à 24 mois pour
les 10 M€ : aucune des quatre échéances n'a besoin d'exister sur le marché.

## Le contrôle qu'il fallait faire

> [!check] Vérifié le 18/09/2026
> La formule réimplémentée redonne les taux publiés par la BCE **à 0,0005
> point près**. Ce contrôle n'est pas une formalité : une erreur de
> convention produit une courbe parfaitement plausible et complètement
> fausse, de 30 à 50 points de base.

## Le piège à connaître : deux façons de compter les intérêts

Il existe deux conventions pour dire « 3 % par an » :

- **Capitalisation annuelle** : 100 € deviennent 103 € au bout d'un an.
  C'est celle du quotidien.
- **Capitalisation continue** : les intérêts sont réinvestis en permanence,
  à chaque instant. 100 € deviennent 103,05 €.

**La BCE publie en capitalisation continue.** Le rendement actuariel des
obligations, lui, est en capitalisation annuelle. Les deux conventions
cohabitent donc dans le même fichier.

L'écart est faible — de l'ordre de 6 points de base pour un taux de 3,5 % —
mais c'est exactement le genre d'erreur invisible : le résultat reste
plausible, personne ne le remarque, et tous les chiffres aval sont décalés.

## Limites

- La courbe **ne repasse pas exactement** par chaque obligation cotée. Pour
  faire de la valeur relative ligne à ligne (« cette obligation est-elle
  chère face à sa voisine ? »), c'est un défaut. Pour construire une
  allocation, c'est ce qu'on veut.
- Elle décrit la **qualité de crédit moyenne** de son périmètre. La courbe
  AAA et la courbe « toutes zone euro » sont deux objets différents ; leur
  écart est le spread souverain moyen, qui n'est pas modélisé émetteur par
  émetteur.

## Sources

- Svensson, L. (1994), NBER WP 4871. Extension de Nelson & Siegel (1987).
- BCE, `data-api.ecb.europa.eu` — **sans clé API**, une des rares sources de
  qualité totalement libres.

→ Suite : [[02 - Valorisation obligataire]]
