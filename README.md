# Mandat Lauren — gestion privée 100 M€

**Application en ligne : https://mandat-lauren.streamlit.app**
Redéployée automatiquement à chaque `git push` sur `main`.

Cas de pitch private banking. Deux livrables : une **application Streamlit**
en cinq onglets et un **PowerPoint** de 47 slides (`outputs/`).

---

## Le cas

M. Lauren, 60 ans, marié, 2 enfants, résident fiscal français. 100 M€ après
cession d'une startup tech. Besoin de liquidité de 10 M€ sous 2 ans. Objectif :
protéger le reste contre une inflation de 4 %. Contrainte : perte maximum 15 %.
Exclusions tabac / armement / charbon. Le fils veut de la crypto, le père
hésite. Client inquiet sur l'Europe **et** sur les États-Unis.

> **Hypothèses de travail**, énoncées chacune à l'étape où elle intervient :
> le patrimoine est déjà en euros ; la perte de 15 % se mesure depuis le plus
> haut, sur les 100 M€ consolidés ; les 10 M€ sortent en quatre versements de
> 2,5 M€ à 6, 12, 18 et 24 mois ; pas de crypto.

**Hors périmètre** (décision du 2026-09-17) : fiscalité et transmission.
L'exercice porte sur la chaîne d'investissement.

---

## La proposition

```
Rendement espéré brut     5,31 %        Pire baisse 2006-2026    −14,0 %
− frais instruments       0,05 pt       Limite du mandat          −15 %
− frais de mandat         0,40 pt       Réalisé 2006-2026        4,47 % / an
Rendement espéré NET      4,86 %        100 M€ en 2006 ->        239 M€
Inflation à battre        4,00 %
Marge                    +0,86 pt
```

C'est le **net** qui se compare à l'inflation : c'est lui qui reste au client.

```
Actions européennes, 15 titres en direct   12,2 %     12,2 M€
Actions États-Unis            XZMU         10,6 %     10,6 M€
Actions émergentes            XZEM          4,6 %      4,6 M€
Actions Japon                 XZMJ          3,0 %      3,0 M€
                                          ──────
                              actions      30,4 %

Emprunts d'État zone euro 2-10 ans, direct 41,3 %     41,3 M€
Obligations indexées          IBCI         15,0 %     15,0 M€
Échelle AAA 6-24 mois, direct              10,0 %     10,0 M€   les 10 M€
                                          ──────
                              obligataire  66,3 %

Or                            4GLD          3,3 %      3,3 M€
```

Crédit et matières premières restent **à zéro** : le calcul n'en veut pas, et
l'étape 4 dit pourquoi. Infrastructure retirée de l'univers : aucun fonds à la
fois conforme aux exclusions et assez gros.

---

## La chaîne, en cinq étapes

Les cinq onglets sont **séquentiels** : la sortie de chacun est l'entrée du
suivant, et aucun chiffre n'apparaît avant l'étape qui le calcule.

| Étape | Question | Sortie |
|---|---|---|
| 1 · Paramètres | Que demande le client ? | Contraintes, hypothèses, questions ouvertes. **Aucun résultat** |
| 2 · Macro | Où en est l'économie ? | Un rendement espéré par classe d'actifs |
| 3 · Ligne à ligne | Dans quoi investir ? | Un support par classe |
| 4 · Allocation | Combien sur chacun ? | Le portefeuille en M€ |
| 5 · Backtests | Aurait-il tenu ? | Durée des baisses, mauvaise année |

### Étape 3 : l'entonnoir des actions européennes

```
600 valeurs du STOXX Europe 600
− exclusions du mandat (tabac, armement, charbon)
− sociétés d'investissement, non notables
− capitalisations sous 10 Md€
  300 notées sur cinq piliers, chacune face à SON secteur
− vue sectorielle du gérant (quatre métiers écartés, décision assumée)
   30 présélectionnées   premier étage : ce que les sociétés SONT
   15 retenues           second étage : ce que les analystes ATTENDENT
```

Deux étages **séparés**, jamais mélangés : les cinq piliers classent, les
attentes des analystes éliminent. En faire un sixième pilier diluerait le
signal — un avenir dégradé ne pèserait qu'un sixième et serait compensé.

---

## Structure

```
main.py             les cinq onglets, dans l'ordre
tabs/t1_parametres  l'énoncé, ce qu'il veut dire, ce qu'il laisse ouvert
tabs/t2_macro       taux, cycle, crédit, marchés, rendements espérés
tabs/t3_lignes      l'entonnoir, la notation, les emprunts d'État
tabs/t3_fonds       les fonds des autres classes, et leur conformité
tabs/t3_credit      le crédit, et pourquoi il finit à zéro
tabs/t4_allocation  risque, calcul libre, règles, portefeuille en M€
tabs/t5_backtests   le rejeu 2006-2026, durée des baisses, VaR / CVaR
```

| Module | Rôle |
|---|---|
| `core/ips.py` | Le mandat en code : montants, seuils, frais. Aucune variable réglable |
| `core/allocation.py` | Entrées de l'étape 4, séries de risque, **rendement d'un jeu de poids** |
| `core/actions.py` | Univers actions, notation, **rendement espéré du panier détenu** |
| `core/scoring.py` | Les cinq piliers, en écarts-types au sein du secteur |
| `core/outlook.py` | Le second étage : révisions, solde, garde-fous, 30 → 15 |
| `core/exclusions.py` | Tabac / armement / charbon : industrie, puis décisions nommées |
| `core/fonds.py` | Fonds retenus et **contrôle des exclusions** (`non_conformes`) |
| `core/vue_secteurs.py` | La vue du gérant, séparée des exclusions du client, et son coût |
| `core/fiches.py` | Le métier de chaque titre retenu, et pourquoi il est là |
| `core/obligations.py` | Valorisation sur la courbe de Svensson, sensibilité |
| `core/backtests.py` | Épisodes de baisse, temps sous l'eau, VaR / CVaR |
| `core/pedago.py` | Le fil des cinq étapes. `formule()` exige sa traduction |
| `core/viz.py` | Palette validée, mise en page commune |

Deux contrôles, à relancer après toute mise à jour de données :
`scripts/controle.py` (l'app et le deck disent-ils la même chose, et le
portefeuille respecte-t-il le mandat) et `scripts/pitch/controle.py`
(géométrie du deck rendu : chevauchements, débordements).

**Ce que l'application recalcule à l'affichage** : la notation des 600 titres,
la sélection des 30 puis des 15, le rendement espéré du panier, les
obligations sur la courbe, le rendement espéré de chaque jeu de poids, les
pertes en crise, les corrélations, le rejeu. **Ce qu'elle lit** : les poids de
l'optimisation (`data/allocation_optim.json`), qui demandent des minutes de
calcul, et les photos de marché datées (`data/*.json`).

---

## Le rendement suit la sélection

Corrigé le 2026-09-25. La poche d'actions européennes entrait dans
l'allocation avec le rendement espéré de **l'indice** : changer les titres
retenus ne changeait donc rien au rendement annoncé, alors que c'est la seule
poche construite titre par titre.

Elle porte désormais le rendement **mesuré sur les titres détenus**, par la
méthode de l'étape 2 appliquée au panier : moyenne des rendements des
bénéfices (1 / PER) et du dividende augmenté de la croissance réelle des
bénéfices, plus l'inflation de l'énoncé. Résultat au relevé du 18/09/2026 :
**9,23 %**, soit le niveau de l'indice à deux décimales près. Ce n'est pas un
pari de surperformance — c'est la même mesure, faite sur ce qu'on achète.

Et le rendement du portefeuille n'est plus **relu** dans le fichier
d'optimisation : il est recalculé comme la somme des rendements de chaque
ligne, pondérée. `allocation.controle_optimisation()` avertit quand les
rendements espérés ont assez bougé pour que les poids ne soient plus les bons,
et l'onglet 4 affiche l'avertissement.

---

## Pièges à ne pas réapprendre

**Les séries Yahoo mélangent les devises de cotation.** `SPXS.L` chute de 99 %
le 2014-01-02 (passage pence → livres). La capitalisation de Londres est
donnée en livres même quand le cours est en pence (`GBp`). Toujours convertir
explicitement.

**Vérifier les libellés, jamais deviner sur le ticker.** Neuf fonds étaient
mal identifiés dans l'univers hérité — dont un fonds d'actions américaines
présenté comme de la dette émergente. Chacun est désormais contrôlé sur deux
sources par son ISIN.

**Le filtre ESG « Screened » n'exclut pas l'armement conventionnel**, que nous
excluons des actions en direct. Un fonds Screened contredirait la règle
appliquée aux titres : on retient des indices « SRI ». Lire les
méthodologies, ne pas déduire du nom.

**Les champs d'analystes de Yahoo sont incohérents entre eux.** Le solde des
révisions doit être rapporté au NOMBRE DE RÉVISIONS, pas à l'effectif
d'analystes : argenx annonçait 6 hausses et 3 baisses pour un effectif de 3, et
sortait à +100 %. En dessous de trois révisions, le solde est tenu pour neutre.

**Un plafond de volatilité mesuré sur tout l'univers interdit un métier, pas
un titre.** La technologie disparaissait entièrement de la sélection. Le
plafond est mesuré DANS le secteur.

**L'optimisation dégénère si on la laisse partir de n'importe où.** Les
départs doivent respecter les bornes ET la limite de baisse : 3 tirages sur 200
respectaient les bornes, et un seul départ sur seize aboutissait. Le résultat
du dossier tenait à un départ heureux.

**Le calcul libre apprend le passé par cœur** : 87 % sur deux supports, dont le
Japon, gardé non pour son rendement mais pour la tenue du yen dans ces quatre
crises précises. D'où les règles, et leur coût chiffré (−1,16 pt).

---

## Points ouverts

- `data/actions/outlook.csv` a été photographié le 25/09 sur une sélection de
  30 légèrement différente de celle d'aujourd'hui : **Klépierre** n'a pas de
  donnée d'analystes et sort pour cette seule raison. L'application le dit,
  sous « Attentes indisponibles ». À reprendre au prochain relevé.
- Fenêtre de corrélation limitée aux crises de 2008, 2011, 2020 et 2022 : ni
  1994, ni 2000.
- Le crédit avant 2016 est reconstitué depuis les écarts américains : c'est la
  ligne la moins bien mesurée du dossier.
- Les indexées sont flattées avant 2009 (leur remplaçant est un emprunt d'État
  classique, qui a mieux tenu en 2008). D'où la marge d'un point sur la limite.

---

## Lancer

```bash
pip install -r requirements.txt          # l'application
pip install -r requirements-dev.txt      # + la chaîne d'analyse

PYTHONPATH=. streamlit run main.py       # l'application

# rafraîchir les données (réseau)
PYTHONPATH=. python3 scripts/fetch_taux.py
PYTHONPATH=. python3 scripts/fetch_macro.py
PYTHONPATH=. python3 scripts/fetch_marches.py
PYTHONPATH=. python3 scripts/fetch_credit.py
PYTHONPATH=. python3 scripts/fetch_indices.py
PYTHONPATH=. python3 scripts/fetch_actions.py
PYTHONPATH=. python3 scripts/fetch_outlook.py
PYTHONPATH=. python3 scripts/fetch_fonds.py
PYTHONPATH=. python3 scripts/fetch_fonds_credit.py
PYTHONPATH=. python3 scripts/fetch_inflation_longue.py
PYTHONPATH=. python3 scripts/estimer_rendements.py

PYTHONPATH=. python3 scripts/optimiser.py     # l'optimisation (~minutes)

# régénérer le deck
PYTHONPATH=. python3 scripts/pitch/extraire.py
(cd scripts/pitch && npm install && npm run build)
python3 scripts/pitch/controle.py             # géométrie du rendu

PYTHONPATH=. python3 scripts/controle.py      # cohérence app / deck / mandat
# puis comparer les deux .pptx, et recopier le généré sur
# outputs/Mandat_Lauren_pitch.pptx
```

`outputs/Mandat_Lauren_pitch.pptx` est le deck de référence ; le générateur
refuse de l'écrire directement, pour qu'une retouche faite à la main ne soit
jamais écrasée sans qu'on l'ait vue.
