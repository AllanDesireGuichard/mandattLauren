---
titre: Notation des actions — cinq piliers
source: core/scoring.py — indicateurs(), _z_secteur(), noter(), selectionner()
maj: 2026-09-21
---

# Notation des actions — cinq piliers

600 titres européens en entrée, **30** en sortie, à parts égales. C'est le
seul endroit du dossier où l'on prétend faire mieux que le marché.

> [!info] Ce n'est PAS un modèle à facteurs
> Ni Fama-French, ni un modèle de risque à la Barra. Aucune régression,
> aucun bêta factoriel estimé, aucune prime de facteur. C'est un **score
> composite normalisé** — la famille des notations quantitatives de type
> *smart beta* / *stock screening*. La différence est importante : un modèle
> à facteurs **explique un rendement** ; ici on **classe des titres**.

## Le pipeline, dans l'ordre

```
19 indicateurs bruts (Yahoo)
   1. orientation       « plus haut = mieux » pour tous
   2. bornes            hors bornes -> NaN (donnée jugée fausse)
   3. exclusion financières sur 3 indicateurs
   4. écrêtage          5e / 95e percentile de l'UNIVERS
   5. score z           AU SEIN DU SECTEUR
   6. pilier            moyenne des z, quorum max(1, n//2)
   7. note              moyenne des 5 piliers, ≥ 4 piliers sur 5
   8. sélection         30 meilleurs sous 3 plafonds
```

## 1. Orientation — « plus haut = mieux »

Un score composite ne peut pas mélanger des indicateurs qui vont dans des
sens opposés. Trois transformations :

| Brut | Transformé | Pourquoi |
|---|---|---|
| PER | $1/PER$ | Rendement des bénéfices : haut = bon marché |
| Price-to-book | $1/PB$ | Idem |
| Dette / fonds propres | $-D/E$ | Moins endetté = mieux |
| Volatilité 3 ans | $-\sigma$ | Moins agité = mieux |
| Bêta | $-\beta$ | Moins exposé = mieux |

L'inversion du PER n'est pas cosmétique : **$1/PER$ est linéaire en
rendement**, le PER ne l'est pas. Passer de 10 à 20 coûte 5 points de
rendement, de 30 à 40 en coûte 0,8. Noter sur le PER brut écraserait
artificiellement les titres chers.

## 2. Bornes de plausibilité

```python
x[k] = x[k].where((x[k] >= lo) & (x[k] <= hi))
```

Hors bornes, la donnée est jugée **fausse** et mise à NaN — pas écrêtée,
supprimée. Exemples de bornes : PER entre 0 et 150, croissance des bénéfices
entre −100 % et +300 %, dividende entre 0 et 15 %.

> [!bug] Le cas qui justifie ce filtre
> Yahoo confond **pence et livres** sur certaines valeurs londoniennes : le
> cours est en GBp mais la capitalisation en GBP. Résultat, des PER
> multipliés par 100. Sans borne, ces titres ressortaient en queue de
> classement avec un score parfaitement calculé sur une donnée absurde.

## 3. Les financières sortent de trois indicateurs

```python
fin = f["secteur"].isin({"Finance", "Immobilier"})
if ignore_fin: x.loc[fin, k] = np.nan
```

Concerne le **flux de trésorerie libre**, la **marge opérationnelle** et
l'**endettement**. Pour une banque, la dette n'est pas un passif de
financement mais sa matière première ; le FCF n'a pas de sens ; la marge
opérationnelle n'est pas définie comme ailleurs. Les noter dessus
reviendrait à les classer sur du bruit comptable.

## 4. Écrêtage puis score z — attention au décalage

```python
def _z_secteur(v, secteur):
    lo, hi = v.quantile(0.05), v.quantile(0.95)   # <- percentiles UNIVERS
    v = v.clip(lo, hi)
    def z(g):
        if g.notna().sum() < 5:
            return (g - v.mean()) / v.std()       # repli univers
        s = g.std()
        return (g - g.mean()) / s if s and s > 0 else g * 0
    return v.groupby(secteur).transform(z)        # <- moments SECTEUR
```

Deux choses différentes se passent ici, et c'est subtil :

- **L'écrêtage** utilise les percentiles de **tout l'univers**.
- **La normalisation** utilise moyenne et écart-type **du secteur**.

$$z_{i} = \frac{\text{clip}(x_i,\ q_{5}^{\text{univers}},\ q_{95}^{\text{univers}}) - \mu_{\text{secteur}}}{\sigma_{\text{secteur}}}$$

> [!question] Est-ce un défaut ?
> C'est défendable : l'écrêtage sert à **neutraliser les valeurs aberrantes**
> (un problème de donnée, global par nature), la normalisation sert à
> **comparer ce qui est comparable** (un problème d'interprétation, sectoriel
> par nature). Mais ce n'est pas neutre : dans un secteur systématiquement
> décalé (la tech sur le PER), l'écrêtage univers rogne plus de titres que
> l'écrêtage sectoriel ne l'aurait fait.

### Pourquoi noter au sein du secteur

Une banque ne se compare pas à un éditeur de logiciels : leurs PER et leurs
marges n'ont pas le même sens. Noter sur l'univers entier reviendrait à
construire un **pari sectoriel déguisé** — on achèterait mécaniquement les
secteurs à PER bas (banques, énergie) et on ne détiendrait jamais de
santé ni de technologie.

### Le repli quand le secteur est trop maigre

Moins de 5 titres valides dans un secteur : on normalise sur les moments de
l'univers. Sans ce repli, un secteur à 2 titres donnerait des $z$ de $\pm 0{,}7$
mécaniquement, quelle que soit la qualité réelle.

## 5. Les cinq piliers

| Pilier | Indicateurs |
|---|---|
| **Valorisation** | rendement des bénéfices, des bénéfices attendus, valeur comptable/cours, FCF/capi, dividende |
| **Croissance** | croissance des bénéfices, du chiffre d'affaires, révision du BPA |
| **Dynamique** | performance 12 mois hors dernier mois, performance 6 mois |
| **Qualité** | ROE, ROA, marge nette, marge opérationnelle, endettement |
| **Résistance** | volatilité 3 ans, perte max 2020, perte max 2022, bêta |

**Poids égaux, 20 % chacun.** Aucun pilier n'a de raison mesurée d'être
privilégié — pondérer demanderait d'estimer des primes de facteur sur
l'univers européen, ce qui est un autre projet.

> [!tip] Le pilier Résistance est spécifique à ce mandat
> Il a été ajouté parce que la contrainte du client est une **perte maximale**.
> Un panier d'actions qui baisse moins en crise permet d'en détenir
> **davantage** pour la même limite de 15 %. C'est le pilier qui relie
> l'étape 3 à [[05 - Optimisation sous contrainte de perte]] : il n'achète
> pas du rendement, il achète du budget de risque.
>
> `mom_12_1` — performance 12 mois **en excluant le dernier mois** — est la
> définition académique standard du momentum : le dernier mois porte un
> effet de retournement à court terme qui pollue le signal.

## 6. Les règles de disponibilité

```python
out[p] = z[cols].mean(axis=1).where(dispo >= max(1, len(cols) // 2))
out["note"] = out[PILIERS].mean(axis=1).where(n >= 4)
```

- Un **pilier** exige `max(1, len(cols) // 2)` indicateurs disponibles.
  Attention à la division entière : pour Valorisation (5 indicateurs) le
  quorum est **2**, pas 3 — donc un peu moins que la moitié. Pour Dynamique
  (2 indicateurs), c'est 1.
- La **note** exige au moins **4 piliers sur 5**.

Sans ces garde-fous, un titre noté sur un seul indicateur chanceux
ressortirait en tête. La moyenne sur les valeurs disponibles est un
**imputation implicite par la moyenne sectorielle** ($z$ manquant ≈ 0 en
espérance) — acceptable tant qu'on exige un quorum, dangereux sinon.

## 7. Sélection — la note ne suffit pas

```python
def selectionner(d, n=30, max_secteur=4, max_pays=6):
    vol_max = plafond_volatilite(d)     # 90e percentile de l'univers noté
```

Trois plafonds appliqués en parcourant le classement par note décroissante :

1. **4 titres par secteur maximum**
2. **6 titres par pays maximum**
3. **volatilité ≤ 90e percentile** de l'univers noté

> [!note] Le plafond de volatilité est MESURÉ, pas fixé
> `d["vol_3a"].quantile(0.90)` : le seuil suit l'agitation des marchés au
> lieu d'être un nombre en dur qui deviendrait absurde en régime de crise.
> Les 10 % de titres les plus agités sont exclus **même très bien notés**.

Les plafonds secteur/pays existent parce qu'une notation **relative au
secteur** peut malgré tout concentrer : si un secteur entier est bien noté,
il rafle la sélection. Ils coûtent de la note et achètent de la
diversification.

## 8. L'exclusion qui n'est pas dans le score

Les **sociétés d'investissement cotées** (Investor, Industrivärden,
Lundbergföretagen, Latour, Aker, Exor, GBL, Sofina, Ackermans, KBC Ancora,
3i) sortent de la notation — pas de l'univers.

Leur bénéfice comptable inclut la **réévaluation de leurs participations**.
PER, rentabilité et croissance n'ont donc pas le sens qu'ils ont pour une
entreprise opérationnelle. Notées comme les autres, elles arrivaient **en
tête du classement pour une raison purement comptable**.

C'est une correction faite à la main, sur une liste nommée. Ce n'est pas
élégant, c'est honnête : aucun filtre automatique ne distingue un holding
d'un conglomérat.

## Résultat et contrôle

30 titres, 10 secteurs, 10 pays, à parts égales.

| | Panier | STOXX Europe 600 |
|---|---|---|
| Volatilité 3 ans | **10,4 %** | 12,8 % |
| Pire baisse 2020 | −34,0 % | −32,1 % |
| Pire baisse 2022 | **−12,8 %** | −18,4 % |

> [!danger] Le biais que ce contrôle ne corrige pas
> Les 30 titres sont choisis **avec les données d'aujourd'hui** puis leur
> passé est mesuré. C'est un biais de survivance et de rétro-sélection : ils
> ont un passé flatteur par construction (+ quelques points par an face à
> l'indice depuis 2019). C'est pourquoi [[05 - Optimisation sous contrainte de perte]]
> mesure le risque de la ligne « actions Europe » **sur l'indice**, pas sur
> le panier.

→ Aval : [[05 - Optimisation sous contrainte de perte]]
