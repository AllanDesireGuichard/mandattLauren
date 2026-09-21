---
titre: Courbe de taux — modèle de Svensson
source: core/obligations.py, fonction taux_zero()
donnees: data/taux_marche.json, clé "svensson"
maj: 2026-09-21
---

# Courbe de taux — Svensson (1994)

## Le problème qu'il résout

La BCE publie chaque jour une courbe zéro-coupon de la zone euro. Elle ne la
publie pas comme une liste de taux, mais comme **six paramètres** : c'est une
fonction continue $r(m)$ qui donne le taux pour n'importe quelle échéance,
y compris celles où aucune obligation n'existe.

C'est ce qui rend l'obligataire souverain **constructible en direct** dans ce
dossier : on n'a pas besoin d'une cotation d'une ligne nommée (introuvable
sans source payante), on price l'obligation sur la courbe. C'est exactement
ce que fait un gérant obligataire pour juger si un titre est cher.

## La formule

Svensson étend Nelson-Siegel (1987) en ajoutant une seconde bosse.

$$
r(m) = \beta_0
+ \beta_1 \underbrace{\frac{1 - e^{-m/\tau_1}}{m/\tau_1}}_{f_1}
+ \beta_2 \underbrace{\left[\frac{1 - e^{-m/\tau_1}}{m/\tau_1} - e^{-m/\tau_1}\right]}_{f_2}
+ \beta_3 \underbrace{\left[\frac{1 - e^{-m/\tau_2}}{m/\tau_2} - e^{-m/\tau_2}\right]}_{f_3}
$$

Taux en pourcentage, **capitalisation continue**, $m$ en années.

```python
def taux_zero(m, p):
    m = max(m, 1e-6)                      # évite la division par zéro en m=0
    a, b = m / p["tau1"], m / p["tau2"]
    f1 = (1 - math.exp(-a)) / a
    f2 = f1 - math.exp(-a)
    f3 = (1 - math.exp(-b)) / b - math.exp(-b)
    return p["beta0"] + p["beta1"]*f1 + p["beta2"]*f2 + p["beta3"]*f3
```

## Ce que fait chaque terme

| Terme | Comportement en $m \to 0$ | en $m \to \infty$ | Interprétation |
|---|---|---|---|
| $\beta_0$ | 1 | 1 | **Niveau long.** L'asymptote : le taux vers lequel la courbe tend. |
| $\beta_1 f_1$ | $\to \beta_1$ | $\to 0$ | **Pente.** $r(0) = \beta_0 + \beta_1$, donc $-\beta_1$ est l'écart court-long. |
| $\beta_2 f_2$ | $\to 0$ | $\to 0$ | **Première bosse**, centrée autour de $\tau_1$. |
| $\beta_3 f_3$ | $\to 0$ | $\to 0$ | **Seconde bosse**, centrée autour de $\tau_2$. |

Les deux facteurs de bosse sont nuls aux deux extrémités : ils ne déforment
la courbe qu'au milieu. C'est toute l'astuce — quatre paramètres de niveau
et deux d'emplacement suffisent à reproduire les formes réelles d'une courbe
(croissante, plate, inversée, en bosse, en S).

> [!tip] La lecture de gérant
> $\beta_0$ te dit où le marché voit les taux à très long terme.
> $\beta_0 + \beta_1$ te dit le taux au jour le jour.
> Leur différence, c'est la pente — le signal de cycle le plus regardé.
> $\beta_2, \beta_3$ te disent où la courbe est déformée, donc où il y a
> potentiellement de la valeur relative.

## Pourquoi ce modèle et pas une interpolation

Une interpolation (spline, linéaire) passe par tous les points observés,
y compris le bruit. Svensson **impose une forme** : quatre facteurs
seulement, donc la courbe ne peut pas osciller librement. Trois
conséquences pratiques :

1. **Elle extrapole proprement.** Demander $r(0{,}5)$ ou $r(37)$ a un sens
   même si aucune obligation n'y cote.
2. **Elle lisse le bruit de cotation.** Deux obligations de même échéance qui
   cotent différemment (liquidité, ancienneté) ne créent pas de pic.
3. **Elle est comparable dans le temps.** Les six paramètres d'hier et
   d'aujourd'hui se comparent terme à terme.

Le prix à payer : la courbe ne repasse pas exactement par chaque prix
observé. Pour de la valeur relative ligne à ligne, c'est un défaut ; pour
construire une allocation, c'est ce qu'on veut.

## Contrôle effectué

> [!check] Vérifié le 2026-09-18
> La formule ré-implémentée ici redonne les taux publiés par la BCE à
> **0,0005 point près**. Le contrôle est indispensable : une erreur de
> convention (continue vs actuarielle, ou $\tau$ en mois au lieu d'années)
> produit une courbe qui a l'air plausible et qui est fausse de 30 à 50 pb.

## Le piège de convention

Svensson donne des taux en **capitalisation continue**. L'actualisation
s'écrit donc en exponentielle :

$$DF(m) = e^{-\frac{r(m) + c}{100} \cdot m}$$

où $c$ est un choc de taux en points de pourcentage (0 en temps normal).

```python
def actualisation(m, p, choc=0.0):
    return math.exp(-(taux_zero(m, p) + choc) / 100 * m)
```

Mais le **rendement actuariel** renvoyé par [[02 - Valorisation obligataire]]
est en capitalisation annuelle, $(1+y)^{-t}$. Les deux conventions coexistent
dans le même fichier. Mélanger les deux fait une erreur d'environ
$y^2/2$ — soit ~6 pb à 3,5 %, ce qui est invisible à l'œil et faux.

## Deux usages dans le dossier

1. **L'échelle AAA des 10 M€** — quatre zéro-coupon à 6, 12, 18, 24 mois.
   Pour recevoir $M$ à l'échéance $t$, on investit $M \cdot DF(t)$
   aujourd'hui. Taux garanti $= DF(t)^{-1/t} - 1$.
2. **L'échelle 2-3-5-7-10 ans** — cinq obligations émises au pair, dont on
   calcule le rendement moyen et la sensibilité.

## Sources

- Svensson, L. (1994), *Estimating and Interpreting Forward Interest Rates:
  Sweden 1992-1994*, NBER WP 4871.
- Nelson & Siegel (1987), *Parsimonious Modeling of Yield Curves*, J. Business.
- Données : BCE, `data-api.ecb.europa.eu`, clé `YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{m}Y`
  — **sans clé API**, c'est une des rares sources de qualité totalement libres.

→ Suite : [[02 - Valorisation obligataire]]
