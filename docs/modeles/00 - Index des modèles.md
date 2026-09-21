---
titre: Modèles du mandat Lauren
projet: mandattLauren
maj: 2026-09-21
---

# Modèles du mandat Lauren

Les six modèles qui produisent un chiffre dans le dossier. Pour chacun :
**ce qu'il fait et pourquoi**, expliqué en français, puis ce qu'il ne sait
pas faire.

> [!info] Comment ces notes sont écrites
> **L'idée d'abord, la formule seulement si elle apprend quelque chose.**
> Il n'en reste qu'une sur les six notes, celle de Svensson, et chacun de
> ses symboles y est nommé.
>
> C'est la règle que le code s'impose déjà à lui-même : `pedago.formule()`
> lève une exception si la traduction en français manque — « une formule
> sans traduction n'a rien à faire dans cette application ».
>
> Chaque note commence par un **« En une phrase »**, indique son fichier
> source, et finit par ses limites. Quand le code s'écarte de la version
> canonique du modèle, c'est signalé.

## La carte

| # | Modèle | Produit | Fichier |
|---|---|---|---|
| 1 | [[01 - Courbe de taux - Svensson]] | La courbe zéro-coupon euro | `core/obligations.py` |
| 2 | [[02 - Valorisation obligataire]] | Prix, duration, convexité, portage | `core/obligations.py` |
| 3 | [[03 - Rendements espérés]] | 10 rendements de classes d'actifs | `scripts/estimer_rendements.py` |
| 4 | [[04 - Notation des actions - 5 piliers]] | 30 titres sur 600 | `core/scoring.py` |
| 5 | [[05 - Optimisation sous contrainte de perte]] | Les poids du portefeuille | `core/allocation.py` |
| 6 | [[06 - Backtest et mesures de risque]] | Drawdown, durée, VaR, CVaR | `core/backtests.py` |

## L'enchaînement

```
BCE (6 paramètres)
    └─> [1] Svensson : le taux pour n'importe quelle durée
            └─> [2] Prix, duration, rendement d'une obligation
                    └─> [3] Rendement espéré obligataire ─┐
iShares / Yahoo / Shiller                                 │
    └─> [3] Rendement espéré actions ──────────────────────┤
                                                           │
Yahoo (600 titres)                                         │
    └─> [4] Notation, 30 titres retenus ───┐               │
                                            │               │
Séries longues 2006-2026 ───────────────────┴───> [5] Optimisation
                                                           │
                                                           v
                                                   [6] Backtest
```

Chaque flèche est une dépendance dure : changer un modèle amont change tout
l'aval. C'est pour cela que la chaîne est séquentielle et que chaque étape
publie son résultat dans un fichier daté (`data/*.json`).

## Ce qu'aucun de ces modèles ne fait

- **Aucune prévision macroéconomique.** Pas de modèle de croissance, pas de
  modèle d'inflation, pas de vue de taux. Les rendements attendus sont soit
  des taux lus sur le marché, soit des valorisations traduites en rendement.
- **Aucune matrice de covariance.** Voir [[05 - Optimisation sous contrainte de perte]]
  pour la raison, qui est le point de méthode le plus contestable du dossier.
- **Aucune simulation.** Pas de Monte-Carlo, pas de bootstrap. Le risque est
  mesuré sur le chemin historique réalisé, avec les limites que cela implique.
