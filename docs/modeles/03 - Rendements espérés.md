---
titre: Rendements espérés par classe d'actifs
source: scripts/estimer_rendements.py -> data/rendements.json
maj: 2026-09-21
---

# Rendements espérés par classe d'actifs

Horizon **10 ans**, **en euros**, dans le monde de l'énoncé : **inflation 4 %**.

> [!important] Le principe qui gouverne tout
> **On ne prévoit rien.** Chaque chiffre est soit un taux lu sur le marché,
> soit une valorisation traduite en rendement, soit une hypothèse étiquetée
> comme telle. Aucun modèle macroéconomique, aucune vue de gérant.

## 1. Obligations à taux fixe — le taux à l'achat, point

Pour une obligation portée jusqu'à l'échéance, **le rendement à maturité
*est* le rendement attendu**. Il n'y a rien à modéliser : voir
[[02 - Valorisation obligataire]].

| Ligne | Rendement | Provenance |
|---|---|---|
| Monétaire | 2,44 % | €STR du jour |
| États AAA 6-24 mois | 3,03 % | Moyenne pondérée de l'échelle |
| États zone euro 2-10 ans | 3,63 % | Moyenne des 5 échéances |

> [!warning] Aucune répercussion d'inflation n'est ajoutée
> Une version antérieure (`core/cma.py`) appliquait à chaque classe un
> « coefficient de répercussion » de l'inflation. Ces coefficients étaient
> **supposés, pas mesurés**. Ils ont été retirés. Une obligation à taux fixe
> ne répercute rien : c'est précisément sa définition, et c'est pourquoi
> aucune ne bat 4 % d'inflation.

## 2. Crédit — le taux moins les défauts

$$r_{\text{crédit}} = y_{\text{fonds}} - \ell_{\text{annuel}}$$

Les pertes viennent de Moody's, *Default and Recovery Rates of Corporate
Bond Issuers 1920-2004*, Exhibit 11 : pertes **cumulées à 5 ans**, en % du
nominal. Il faut les annualiser :

$$\ell_{\text{annuel}} = 1 - (1 - \ell_{5\text{ans}})^{1/5}$$

```python
PERTE_IG = round((1 - (1 - 0.0055) ** (1/5)) * 100, 2)   # 0,55 % -> 0,11 %/an
PERTE_HY = round((1 - (1 - 0.1488) ** (1/5)) * 100, 2)   # 14,88 % -> 3,17 %/an
```

Résultat : crédit euro court **3,50 − 0,11 = 3,39 %**.

C'est ce qui tue le haut rendement : 2,88 % après défauts, **sous les
emprunts d'État**. Le rendement affiché d'un fonds high yield est un
rendement *avant* défauts, donc un plafond, jamais une espérance.

> [!caution] Limite assumée
> Ces statistiques sont **américaines**, transposées à l'euro. Et elles
> couvrent 1982-2004, donc ni 2008 ni 2020. Elles sous-estiment probablement
> la queue.

## 3. Obligations indexées — la seule répercussion mesurée

$$r_{\text{indexées}} = r_{\text{réel}} + \pi = 1{,}43 + 4{,}00 = 5{,}43\ \%$$

Le taux réel est **lu sur le marché** (marché des indexées euro). C'est la
seule classe dont le lien à l'inflation est contractuel et non supposé : le
nominal est indexé, donc la répercussion est de 1 par construction.

## 4. Actions — deux méthodes, puis leur moyenne

C'est le morceau discutable, et il faut savoir le défendre.

### Méthode 1 — rendement des bénéfices

$$r_{\text{réel}}^{(1)} = \frac{1}{PER}$$

À un PER de 20, on achète 5 % de bénéfices par an. Sur longue période, le
rendement réel d'une action converge vers son *earnings yield* — c'est le
résultat empirique qui fonde la méthode (Campbell-Shiller). L'hypothèse
implicite : **pas de ré-expansion ni de compression durable des multiples**.

### Méthode 2 — dividende plus croissance

$$r_{\text{réel}}^{(2)} = \text{div} + g_{\text{réel}}$$

Forme réduite de Gordon-Shapiro. $g$ est la **croissance réelle des
bénéfices par action**, mesurée sur le S&P 500 depuis 1900 (Shiller) :

```python
e10 = (a["E"] / a["CPI"]).rolling(10).mean()     # BPA réel lissé sur 10 ans
g = (e10[fin] / e10[debut]) ** (1 / (fin - debut)) - 1
```

Deux précautions dans ce calcul :
- **déflaté par le CPI** avant tout, donc $g$ est réel ;
- **lissé sur 10 ans** (moyenne mobile), sinon la borne de départ ou
  d'arrivée tombe sur un pic ou un creux de cycle et le résultat bouge de
  plusieurs points.

Valeur retenue : **$g = 2{,}0\ \%$ par an**, la même pour toutes les zones.

### L'assemblage

$$r_{\text{espéré}} = \frac{r^{(1)} + r^{(2)}}{2} + \pi$$

avec $\pi = 4\ \%$ : hypothèse que **les entreprises répercutent l'inflation
dans leurs bénéfices**. C'est une répercussion de 1, discutable, mais
soutenue par le fait que les bénéfices nominaux suivent les prix de vente.

| Zone | PER | Div | $r^{(1)}$ | $r^{(2)}$ | Espéré |
|---|---|---|---|---|---|
| Europe | 18,5 | 3,07 % | 5,41 % | 5,05 % | **9,23 %** |
| États-Unis | 30,0 | 1,06 % | 3,33 % | 3,04 % | **7,19 %** |
| Japon | 19,1 | 3,66 % | 5,24 % | 5,64 % | **9,44 %** |
| Émergents | 20,8 | 2,96 % | 4,81 % | 4,94 % | **8,40 %** |

> [!danger] Les trois attaques prévisibles
> 1. **$g$ identique pour toutes les zones** pénalise les États-Unis, dont
>    le poids technologique justifierait plus. Assumé : mesurer $g$ par zone
>    demanderait un historique long par zone qu'on n'a pas.
> 2. **Le PER dépend de la source.** Avec les PER Yahoo (24,6) au lieu
>    d'iShares (30,0), les États-Unis remontent à ~8,1 %. L'écart avec
>    l'Europe se réduit fortement — **il ne s'inverse pas**.
> 3. **Le Japon sort premier** essentiellement à cause d'un dividende de
>    3,66 %, qui est élevé. Si ce chiffre est faux, toute l'allocation
>    japonaise du calcul libre est fausse. C'est la donnée la plus fragile
>    de l'étape. Voir [[05 - Optimisation sous contrainte de perte]].

## 5. Or et matières premières — une hypothèse, et elle est dite

Aucun flux, donc **aucune méthode d'actualisation n'existe**. On ne peut pas
estimer, on peut seulement poser. Hypothèse : conservation du pouvoir
d'achat, soit $r = \pi = 4{,}00\ \%$, fourchette ±2 points.

Étiqueté `"hypothèse"` dans `rendements.json`, contre `"mesuré"` ou
`"estimé"` pour les autres. **Cette étiquette est dans les données, pas dans
un commentaire** : l'application affiche la nature de chaque chiffre.

## 6. Crypto — zéro

Non estimable pour la même raison que l'or, sans même l'argument du pouvoir
d'achat. Valeur retenue : 0. Elle reste mesurée en risque (−72,9 % en 2020,
−73,8 % en 2022) pour pouvoir montrer *pourquoi* on l'écarte.

## Le contrôle externe

Chaque classe est confrontée à **J.P. Morgan LTCMA 2026** (hypothèses en
euros, p. 84, données au 30/09/2025, **inflation supposée 2 %**).

```python
JPM = {"cash": 2.3, "govt_bonds_eur": 3.4, "credit_ig_eur": 4.0,
       "inflation_linked": 3.6, "equity_developed": 6.3, "us": 6.1,
       "europe": 6.4, "japon": 8.2, "equity_emerging": 7.2, "gold": 4.9}
```

> [!check] Le piège de comparaison, et il est central
> J.P. Morgan suppose **2 %** d'inflation, nous **4 %**. Comparer les deux
> colonnes brutes donne un écart de 2 points qui n'existe pas. Il faut
> **aligner les régimes** avant de conclure. Une fois alignés : même sens,
> écart inférieur à un point.
>
> C'est le même piège, exactement, que celui corrigé dans
> [[06 - Backtest et mesures de risque]] — juger un résultat d'un régime
> avec l'exigence d'un autre.

## Le résultat qui commande tout l'aval

Seules **les actions et les indexées** dépassent 4 %. Aucune obligation à
taux fixe ne protège contre 4 % d'inflation. Chaque euro placé ailleurs
devra donc être compensé par des actions : c'est toute la tension de
[[05 - Optimisation sous contrainte de perte]].

→ Amont : [[02 - Valorisation obligataire]] · Aval : [[05 - Optimisation sous contrainte de perte]]
