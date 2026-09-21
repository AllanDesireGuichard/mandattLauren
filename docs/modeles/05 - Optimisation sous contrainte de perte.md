---
titre: Optimisation sous contrainte de perte maximale
source: core/allocation.py (classe Chemin), scripts/optimiser.py
maj: 2026-09-21
---

# Optimisation sous contrainte de perte maximale

## Le programme

$$
\max_{w}\ w^{\top}\mu
\quad \text{s.c.} \quad
\underbrace{\min_{t}\left[\frac{V_t(w)}{\max_{s \le t} V_s(w)} - 1\right] \ge -0{,}15}_{\text{pire baisse depuis le plus haut}},
\quad \sum_i w_i = 1, \quad w \ge 0
$$

où $V_t(w)$ est la valeur du portefeuille **rééquilibré chaque mois** sur les
séries d'octobre 2006 à septembre 2026, et $\mu$ le vecteur des rendements
espérés de [[03 - Rendements espérés]].

L'objectif est **linéaire**. Toute la difficulté est dans la contrainte.

## Pourquoi pas Markowitz — le point de méthode central

> [!important] La question sera posée en soutenance
> La contrainte du client n'est pas une volatilité, c'est une **perte
> maximale depuis le plus haut**. Ce sont deux objets mathématiquement
> différents.

$$\sigma_p^2 = w^{\top}\Sigma w \qquad \text{vs} \qquad MDD(w) = \min_t \left[\frac{V_t}{\max_{s\le t}V_s} - 1\right]$$

- La **variance** est une forme quadratique : elle ne dépend que des moments
  d'ordre 2, donc **elle ignore l'ordre d'arrivée des rendements**. Permuter
  chronologiquement les rendements ne change pas $\sigma$.
- Le **drawdown maximal** est un maximum le long d'un chemin : permuter les
  rendements le change complètement. Il dépend de l'**autocorrélation** et
  de la **structure de dépendance dans les queues**, que $\Sigma$ ne capture
  pas.

Il n'existe pas de fonction $f$ telle que $MDD = f(\Sigma, \mu)$ sans
hypothèse distributionnelle forte (typiquement : rendements i.i.d. gaussiens,
pour lesquels on a des résultats asymptotiques à la Magdon-Ismail). Sur des
données réelles avec 2008 et 2022 dedans, cette hypothèse est fausse dans la
direction qui compte.

**Optimiser la variance en espérant que le drawdown suive aurait été un
raccourci non vérifié.** On optimise donc directement sur le chemin.

### Le prix de ce choix, qui est réel

La contrainte est évaluée sur **une seule trajectoire historique**. Le
calcul ne trouve pas le portefeuille robuste, il trouve **le portefeuille
qui aurait le mieux marché sur ces vingt années**. C'est du surapprentissage
caractérisé.

C'est pourquoi le résultat brut est **rejeté** et corrigé par des règles,
dont le coût est chiffré ligne à ligne (voir plus bas).

### Black-Litterman

Écarté pour une autre raison : BL sert à mélanger un équilibre de marché
avec des vues subjectives. Ici, **les vues sont déjà dans $\mu$** — les
rendements espérés viennent des valorisations, qui *sont* la vue. Les
réinjecter par BL les compterait deux fois.

## Le calcul du chemin — la classe `Chemin`

L'optimiseur appelle la contrainte des milliers de fois. Un rééquilibrage
mensuel naïf (boucle Python sur 240 mois × 16 départs × 400 itérations) est
inutilisable. D'où une formulation matricielle, pré-calculée une fois :

```python
class Chemin:
    def __init__(self, s):
        p = s.dropna()
        mois = p.index.to_period("M")
        fin_prec = p.groupby(mois).last().shift(1)   # dernier cours du mois -1
        base = fin_prec.reindex(mois).set_axis(p.index)
        base[mois == mois[0]] = p.iloc[0].values     # amorçage
        self.g = (p / base).to_numpy()               # gain depuis le rééq.
        m = np.asarray(mois.astype(str))
        self.fins = np.r_[np.nonzero(m[1:] != m[:-1])[0], len(m) - 1]
```

`self.g[t, i]` = performance de l'actif $i$ **depuis le dernier
rééquilibrage** jusqu'à $t$. Le portefeuille vaut alors :

```python
def valeur(self, w):
    x = self.g @ w                 # produit matrice-vecteur : tout le chemin
    v = np.empty_like(x)
    niveau, debut = 100.0, 0
    for f in self.fins:            # une itération par MOIS, pas par jour
        v[debut:f+1] = niveau * x[debut:f+1]
        niveau, debut = v[f], f+1
    return v
```

Le cœur — `self.g @ w` — est **un seul produit matriciel** pour les 5 209
jours. La boucle qui reste ne fait que chaîner les 240 mois entre eux
(capitalisation du niveau). C'est ce qui rend l'optimisation faisable.

> [!note] Ce que « rééquilibré chaque mois » veut dire ici
> Le premier jour de chaque mois, les poids sont remis à $w$. Entre deux
> rééquilibrages, chaque ligne vit sa vie et les poids dérivent. C'est la
> convention d'un mandat réel, et elle est **conservatrice** : le
> rééquilibrage vend ce qui monte et achète ce qui baisse, ce qui amortit
> les drawdowns.

## La résolution

```python
DEPARTS = 16
contraintes = [
    {"type": "eq",   "fun": lambda w: w.sum() - 1},
    {"type": "ineq", "fun": lambda w: limite + chemin.pire_baisse(w)},
]
rng = np.random.default_rng(0)
for _ in range(DEPARTS):
    w0 = rng.dirichlet(np.ones(n))
    r = minimize(lambda w: -w @ mu, w0, method="SLSQP", bounds=bornes,
                 constraints=contraintes, options={"maxiter": 400, "ftol": 1e-9})
```

### Pourquoi plusieurs départs

$MDD(w)$ n'est **ni lisse ni convexe**. Le $\min_t$ et le $\max_{s\le t}$
créent des points anguleux : quand le creux se déplace d'une date à une
autre, le gradient saute. SLSQP, qui approche le gradient par différences
finies, peut s'arrêter sur un point anguleux qui n'est pas un optimum.

**16 tirages de Dirichlet($\mathbf{1}$)** — la loi uniforme sur le simplexe,
donc des répartitions initiales uniformément réparties parmi tous les
portefeuilles admissibles. On garde le meilleur résultat qui respecte la
limite. **Graine fixée à 0** : le résultat est reproductible, ce qui est
non négociable pour un dossier qu'on doit pouvoir refaire.

### La vérification a posteriori

```python
if chemin.pire_baisse(w) < -limite - 5e-4:
    continue
```

SLSQP peut rendre une solution qui viole légèrement la contrainte. On la
**revérifie** et on la jette si elle dépasse, avec une tolérance de 5 pb.
Ne jamais faire confiance au solveur sur une contrainte non lisse.

## Le calcul libre, et pourquoi il est inutilisable

Résultat sans aucune règle : **6,47 %** espérés, pire baisse −15,0 %.

| Ligne | Poids |
|---|---|
| Obligations indexées | 55 % |
| Japon | 32 % |
| États longs | 9 % |

> [!danger] Ce que le calcul a appris par cœur
> - **Le Japon** est retenu pour deux raisons : c'est le $\mu$ le plus élevé
>   (9,44 %, tiré par un dividende de 3,66 % — la donnée la plus fragile de
>   [[03 - Rendements espérés]]), et c'est l'action qui a le mieux tenu en
>   2008 : **−49,1 % en euros contre −59,0 % pour l'Europe**. L'avantage est
>   réel mais ne fait que 10 points, **sur une seule crise**.
> - **Les indexées** sont les seules obligations au-dessus de 4 %, et leur
>   2008 est **flatté par un remplaçant** (avant 2009, la série est un
>   emprunt d'État classique, qui a mieux tenu que les vraies indexées).
>
> Deux lignes font 87 % du portefeuille. Si l'une se comporte autrement
> qu'en 2006-2026, rien ne compense.

## Les quatre règles et leur coût

On relance le calcul en ajoutant une règle à la fois, chacune gardant les
précédentes. **C'est le tableau le plus important du dossier** : il chiffre
le prix de chaque précaution.

| Règle | Rdt | Coût | Répartition obtenue |
|---|---|---|---|
| Seule la limite de 15 % | 6,47 % | — | indexées 55, Japon 32, États longs 9 |
| + 10 % échelle AAA | 6,46 % | −0,01 | indexées 58, Japon 32, AAA 10 |
| + clé actions 40/35/10/15 | 5,78 % | −0,68 | indexées 70, actions 20, AAA 10 |
| + plafonds par ligne | 5,40 % | −0,38 | États longs 37, actions 32, indexées 15 |
| + marge à 14 % | **5,31 %** | −0,09 | États longs 41, actions 30, indexées 15 |

### Lecture de chaque ligne

**−0,01 pt pour les 10 M€.** Le résultat le plus contre-intuitif. Le calcul
paie l'échelle AAA (3,03 %) en vendant les États longs (3,63 %) et le crédit
(3,39 %) : il troque une obligation médiocre contre une autre. **Sécuriser
la liquidité du client ne coûte rien.**

**−0,68 pt pour la clé actions.** La plus chère. On fixe
$w_{\text{actions}} \cdot (0{,}40 ; 0{,}35 ; 0{,}10 ; 0{,}15)$ et le calcul
ne décide plus que de $w_{\text{actions}}$, pas de sa composition. Cela
oblige à acheter 35 % d'américain à 7,19 % là où il concentrait sur du
japonais à 9,44 %. **Ces 0,68 pt achètent l'absence de pari géographique.**
Le portefeuille retenu ne contient plus que 3 % de Japon.

**−0,38 pt pour les plafonds** (indexées ≤ 15 %, or ≤ 10 %, matières ≤ 5 %,
crédit ≤ 20 %). La ligne précédente mettait 70 % sur un seul support. Effet
de bord notable : le portefeuille devient **plus diversifié et plus
actions** (20 → 32 %), parce que plafonner les indexées ne laisse que les
actions pour tenir le rendement.

**−0,09 pt pour la marge à 14 %.** La seule règle qui ne vienne pas du
client. Elle laisse un point de jeu pour l'erreur de mesure des remplaçants
d'avant 2018. L'assurance la moins chère du tableau.

> [!tip] La colonne que personne ne regarde
> La pire baisse affiche **−15,0 % sur les quatre premières lignes**. Ce
> n'est pas une coïncidence : le calcul maximise le rendement, donc il
> s'écrase systématiquement contre la limite. **La contrainte est toujours
> saturante.** À chaque étape, ce qui l'arrête c'est le risque, jamais les
> règles — celles-ci ne font que changer la façon dont il dépense un budget
> de risque constant.

## La variante testée et écartée

Si l'objectif était 4 % **au-dessus** de l'inflation (8 % nominal), il est
hors d'atteinte sous cette contrainte (plafond 6,47 %). En remplaçant le
pire cas par une limite en fréquence :

| Contrainte | Rdt max | VaR 95 % | CVaR 95 % | Pire baisse |
|---|---|---|---|---|
| Pire baisse ≥ −15 % | 6,47 % | −6,9 % | −8,9 % | −15,0 % |
| VaR 95 % ≥ −15 % | 8,42 % | −15,0 % | **−29,5 %** | **−51,5 %** |
| CVaR 95 % ≥ −15 % | 7,77 % | −13,5 % | −15,0 % | −32,3 % |
| Aucune | 9,44 % | −25,2 % | −27,0 % | −52,7 % |

**Trois raisons de refuser.** En CVaR — la mesure qui dit *de combien* on
dépasse — on plafonne sous la cible. En VaR la cible passe, mais la
contrainte ne contraint plus rien : les années de dépassement coûtent
29,5 % en moyenne. Et ces quantiles reposent sur **sept épisodes de baisse
distincts** en vingt ans, avec des fenêtres qui se chevauchent.

→ Amont : [[03 - Rendements espérés]], [[04 - Notation des actions - 5 piliers]]
· Aval : [[06 - Backtest et mesures de risque]]
