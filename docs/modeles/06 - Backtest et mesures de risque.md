---
titre: Backtest et mesures de risque
source: core/backtests.py, scripts/fetch_inflation_longue.py
maj: 2026-09-21
---

# Backtest et mesures de risque

> [!warning] Ce que ce rejeu ne peut pas prouver
> Les vingt années de données sont **celles qui ont servi à construire le
> portefeuille** : [[05 - Optimisation sous contrainte de perte]] a cherché
> une répartition qui ne perde jamais plus de 14 % sur cette période. Qu'elle
> n'y perde pas plus de 14 % est **acquis d'avance** et ne dit rien de la
> prochaine crise.
>
> Le rejeu mesure ce que l'optimisation **n'a pas regardé** : la durée des
> baisses et la distribution des résultats sur un an.

## 1. La valeur du portefeuille

```python
def valeur():
    w = {k: x for k, x in allocation.poids_retenus().items() if x > 0}
    debut = allocation.resultats()["fenetre"][0]    # MÊME fenêtre que l'optim
    v = allocation.portefeuille(allocation.series()[debut:], w)
    return v / 100 * allocation.MONTANT
```

Le point important est `debut` : la fenêtre est **relue depuis le fichier de
résultats de l'optimisation**, pas redéfinie. Si les deux différaient d'un
mois, les drawdowns ne seraient plus comparables et personne ne le verrait.

## 2. Drawdown

$$DD_t = \frac{V_t}{\max_{s \le t} V_s} - 1$$

```python
dd = v / v.cummax() - 1
```

Le `cummax()` porte sur **toute l'histoire**, pas sur une fenêtre glissante.
Conséquence à connaître : en 2011, la perte se mesure encore depuis le
sommet de 2007, parce que le portefeuille n'y était pas revenu. C'est la
lecture la plus dure, et c'est volontaire.

### Détection des épisodes

`episodes(v, seuil=0.05)` découpe chaque passage sous le plus haut :

```python
haut = v.cummax()
sous = v < haut
for d, s in sous.items():
    if s and debut is None: debut = d
    if (not s or d == v.index[-1]) and debut is not None:
        fin = d if not s else None          # None = pas encore remonté
        creux = v[debut:d].idxmin()
        sommet = v[:debut].index[-2] if len(v[:debut]) > 1 else debut
        perte = float(v[creux] / haut[creux] - 1)
```

Chaque épisode retient : date du sommet, date du creux, perte, **date du
retour au sommet** (ou `None`). C'est cette dernière qui produit le vrai
enseignement du backtest.

| Mesure | Valeur |
|---|---|
| Temps à plus de 1 % sous le plus haut | 53 % |
| Temps à plus de 5 % | 17 % |
| Temps à plus de 10 % | 4 % |
| Plus longue période sous l'eau (2022) | **32 mois** |

> [!important] Le résultat le plus instructif
> **2022 est la crise la plus longue, pas la plus profonde.** 32 mois sous
> l'eau pour une baisse moindre qu'en 2008. La raison : les obligations,
> qui font les deux tiers du portefeuille, **ont baissé avec les actions**.
> C'est le régime que redoute précisément le client, et c'est celui qu'un
> 60/40 classique ne prévoit pas.

## 3. VaR et CVaR historiques

Sur **228 années glissantes**, à chaque fin de mois :

```python
def un_an(v):
    m = v.resample("ME").last()
    return (m / m.shift(12) - 1).dropna() * 100

def var_cvar(r, niveau=0.95):
    q = float(np.quantile(r, 1 - niveau))
    return q, float(r[r <= q].mean())
```

$$\text{VaR}_{95\%} = q_{5\%}(r_{12m}) \qquad
\text{CVaR}_{95\%} = \mathbb{E}\left[r_{12m} \mid r_{12m} \le q_{5\%}\right]$$

**Historiques, pas paramétriques** : pas d'hypothèse gaussienne, pas de
fenêtre pondérée, pas de GARCH. On lit les quantiles empiriques. Le choix
se défend sur un échantillon qui contient 2008 et 2022 — une gaussienne
sous-estimerait la queue d'un facteur 2 ou 3.

| Mesure | Portefeuille retenu |
|---|---|
| VaR 95 % à un an | −6,5 % |
| CVaR 95 % | −8,5 % |
| Pire année | −11,4 % |
| Années en perte | 18 % |

### La lecture à retenir

La **pire année fait −11,4 %** alors que la **pire baisse atteint −14 %**.
L'écart vient des baisses longues : en 2008 comme en 2022, la perte s'est
accumulée sur plus d'un an. C'est exactement pour cela que la limite du
mandat a été mesurée depuis le plus haut et non sur douze mois glissants —
**une limite annuelle aurait laissé passer ces baisses.**

> [!danger] Ce que valent ces quantiles
> Les 228 fenêtres **se chevauchent** : deux années glissantes consécutives
> partagent onze mois sur douze. Le nombre d'observations **indépendantes**
> est de l'ordre de 20, et le nombre d'épisodes de baisse distincts est de
> **sept**. Un quantile à 5 % sur 228 points corrélés n'a pas la précision
> que le chiffre suggère.

## 4. Le régime d'inflation — la correction du 21/09/2026

> [!bug] L'erreur qui a été corrigée
> Le rendement réalisé (4,47 %/an) était comparé au **seuil de 4 % de
> l'énoncé**. Or ce 4 % décrit un monde à 4 % d'inflation, et la période
> rejouée en a vécu un autre. **Juger un résultat d'un régime avec
> l'exigence d'un autre** — c'est le même piège que celui signalé dans
> [[03 - Rendements espérés]] à propos de J.P. Morgan. Et ici il jouait
> **en défaveur** du portefeuille.

### La mesure

Série FRED `CP0000EZCCM086NEST` — IPCH zone euro, mensuel, base 2015 = 100 —
sur la **fenêtre exacte du rejeu**.

$$\pi_{\text{réalisée}} = \left(\frac{I_{\text{fin}}}{I_{\text{début}}}\right)^{1/n} - 1$$

> [!tip] Le piège écarté dans ce calcul
> **On ne fait pas la moyenne des glissements annuels.** Elle surpondère les
> années de forte inflation (2022 à +9,2 %) et ne redonne pas l'érosion
> réelle du pouvoir d'achat. Le **taux composé entre les deux bornes** est
> la seule mesure homogène à un rendement annualisé.

| | Valeur |
|---|---|
| Fenêtre | 10/2006 → 08/2026 (19,8 ans) |
| Inflation cumulée | **53,46 %** |
| Inflation annualisée | **2,18 %** |
| Rendement du portefeuille | 4,47 % |
| **Rendement réel** | **+2,29 %/an** |

L'objectif du client a donc été tenu **largement**, et non de justesse.

### Le sous-produit inattendu

| Fenêtre | Inflation zone euro |
|---|---|
| 20 ans | 2,18 %/an |
| 10 ans | 2,88 %/an |
| **5 ans** | **4,31 %/an** |

L'hypothèse de 4 % du client n'est donc **pas une crainte disproportionnée**
— c'est une extrapolation de ce qu'il vient de vivre. C'est une lecture plus
juste, et plus respectueuse, que « c'est le double de la cible de la BCE ».

## 5. Les années sous l'objectif

Deux mesures, et il faut donner la bonne :

| Seuil | Années glissantes en dessous |
|---|---|
| Inflation constatée (2,18 %) | **29 %** |
| Les 4 % de l'énoncé | 40,8 % |

> [!note] À dire avant qu'on le demande
> Près d'une année glissante sur quatre n'a pas battu l'inflation de son
> époque. C'est normal et il faut l'énoncer : **préserver le pouvoir d'achat
> est un objectif de moyenne longue, pas une garantie annuelle**, et aucun
> portefeuille tenu à 15 % de perte maximum ne peut promettre le contraire.
> Le chiffre est recalculable par n'importe qui à partir des données du
> dossier.

## 6. Les limites de données du backtest

- **Remplaçants avant 2018.** Plusieurs supports n'existaient pas sur toute
  la période et sont représentés par un indice proche. Certains **flattent** :
  les indexées d'avant 2009 sont un emprunt d'État classique, qui a mieux
  tenu en 2008. C'est la raison de la marge de prudence à 14 %.
- **Actions Europe mesurées sur l'indice**, pas sur les 30 titres — pour ne
  pas importer le biais de rétro-sélection de
  [[04 - Notation des actions - 5 piliers]].
- **Crédit reconstitué** avant 2016 à partir des écarts américains,
  corrélation faible : c'est la ligne la moins bien mesurée.
- **Pas de frais de transaction ni de slippage** dans le rejeu. Le
  rééquilibrage mensuel de 100 M€ sur des ETF liquides coûterait quelques
  points de base par an, non déduits.

→ Amont : [[05 - Optimisation sous contrainte de perte]] · Index : [[00 - Index des modèles]]
