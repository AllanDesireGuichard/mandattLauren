---
titre: Valorisation obligataire
source: core/obligations.py — prix(), coupon_au_pair(), rendement(), analyse(), echelle()
maj: 2026-09-21
---

# Valorisation obligataire

Tout part de la courbe de [[01 - Courbe de taux - Svensson]]. Conventions du
code : **coupon annuel, nominal 100, obligation bullet** (tout le capital à
l'échéance), **pas de coupon couru** — on suppose une émission du jour.

## 1. Prix

$$P = \sum_{t \in T} \left[c + 100 \cdot \mathbb{1}_{t = T_{\max}}\right] \cdot DF(t)$$

Les dates de coupon sont construites **à rebours depuis l'échéance**, ce qui
gère proprement les maturités non entières :

```python
def _dates(maturite):
    n = math.ceil(maturite - 1e-9)
    return [maturite - k for k in range(n)][::-1]
```

Pour $T = 2{,}5$ ans : dates $\{0{,}5 ; 1{,}5 ; 2{,}5\}$. Une construction
naïve en partant de 1 an aurait donné $\{1 ; 2\}$ et oublié un flux.

## 2. Coupon au pair

On ne cherche pas une obligation existante : on se demande **quel coupon
ferait coter 100 aujourd'hui**. C'est l'émission théorique du jour.

$$c^\ast = 100 \cdot \frac{1 - DF(T)}{\sum_{t \in T} DF(t)}$$

Démonstration en une ligne : poser $P = 100$ dans la formule du prix et
isoler $c$. Le numérateur est ce qu'il reste à financer une fois le
remboursement actualisé ; le dénominateur est l'annuité actualisée.

> [!note] Pourquoi au pair
> Une obligation au pair a un rendement actuariel égal à son coupon et
> n'introduit ni prime ni décote. C'est la référence neutre : elle isole
> l'effet de la courbe de l'effet du prix d'achat.

## 3. Rendement actuariel — par dichotomie

$$P = \sum_{t} \frac{F_t}{(1 + y)^t}$$

Pas de solution analytique : la fonction est un polynôme de degré $T$ en
$1/(1+y)$. Le code fait **100 itérations de dichotomie** sur $[-5\% ; +30\%]$ :

```python
lo, hi = -0.05, 0.30
for _ in range(100):
    mid = (lo + hi) / 2
    if pv(mid) > prix_: lo = mid
    else:               hi = mid
```

100 itérations sur un intervalle de 35 points donnent une précision de
$35/2^{100}$, soit largement en-deçà de la précision machine. C'est
volontairement grossier et incassable : Newton-Raphson serait plus rapide
mais peut diverger sur une obligation à coupon nul ou à taux négatif.

La borne basse à $-5\%$ n'est pas décorative : la zone euro a connu des
rendements souverains négatifs de 2015 à 2022.

## 4. Les mesures de risque et de rendement

Toutes dans `analyse(maturite, p)`, sur une obligation émise au pair.

### Duration de Macaulay
$$D = \frac{1}{P}\sum_t t \cdot \frac{F_t}{(1+y)^t}$$
La durée de vie moyenne des flux, pondérée par leur valeur actuelle. En
années.

### Sensibilité (duration modifiée)
$$D_m = \frac{D}{1+y} \approx -\frac{1}{P}\frac{\partial P}{\partial y}$$
La baisse de prix, en %, pour **+1 point** de taux. C'est le chiffre qu'on
cite : « l'échelle 2-10 ans perd 4,7 % si les taux montent d'un point ».

### Convexité
$$C = \frac{1}{P(1+y)^2}\sum_t t(t+1)\frac{F_t}{(1+y)^t}$$

Le terme d'ordre 2 du développement :
$$\frac{\Delta P}{P} \approx -D_m \Delta y + \tfrac{1}{2} C (\Delta y)^2$$

La convexité est **positive** pour une obligation classique : les pertes
accélèrent moins vite que les gains. C'est un actif pour le détenteur, et
c'est ce qui rend la sensibilité seule trop pessimiste sur les fortes hausses.

> [!warning] Le code calcule les deux chocs en dur, pas par approximation
> `choc_plus_1` et `choc_moins_1` repricent réellement l'obligation avec
> la courbe décalée d'un point, au lieu d'utiliser $-D_m + \frac{1}{2}C$.
> C'est plus juste, et ça évite de se faire piéger sur les longues
> maturités où le terme d'ordre 2 ne suffit plus.

### Portage et glissement — la décomposition du rendement à un an

$$\text{portage} = \frac{c}{P} \qquad
\text{glissement} = \frac{P_{T-1} - P_T}{P_T} \qquad
r_{1\text{an}} = \text{portage} + \text{glissement}$$

- Le **portage** (*carry*) : le coupon encaissé.
- Le **glissement** (*roll-down*) : le gain de prix obtenu **sans que la
  courbe bouge**, simplement parce que l'obligation vieillit et se retrouve
  valorisée sur un point de courbe plus court, où le taux est plus bas
  (si la courbe est croissante).

C'est la décomposition qui permet de dire *pourquoi* une échéance rapporte :
une courbe très pentue paie surtout en glissement, une courbe plate surtout
en portage.

## 5. L'échelle — l'adossement des 10 M€

```python
def echelle(montants, p):
    for t, montant in sorted(montants.items()):
        df = actualisation(t, p)
        cout = montant * df
        taux = (1 / df) ** (1 / t) * 100 - 100
```

Pour chaque besoin de trésorerie $(t, M)$, on achète un zéro-coupon qui rend
exactement $M$ en $t$. Coût $M \cdot DF(t)$, taux garanti $DF(t)^{-1/t} - 1$
(en capitalisation annuelle, converti depuis la continue).

**Le point de méthode.** L'adossement supprime le risque de taux, il ne le
réduit pas. Si les taux montent, l'obligation perd de la valeur de marché —
mais on ne la vend pas, on la porte jusqu'à l'échéance, et elle rend le
montant prévu. C'est la différence entre risque de prix et risque de flux :
pour un besoin daté, seul le second compte.

Résultat dans le dossier : 9,63 M€ investis aujourd'hui rendent les 10 M€
échelonnés sur 6-12-18-24 mois, soit **78 k€ de mieux que le monétaire**.

## Limites

- **Pas de spread émetteur.** La courbe « toutes zone euro » mélange des
  qualités de crédit ; la courbe AAA est utilisée pour les 10 M€, la courbe
  générale pour la poche longue. L'écart entre les deux est le spread
  souverain moyen, il n'est pas modélisé ligne à ligne.
- **Pas de coupon couru, pas de conventions de décompte** (ACT/ACT, 30/360).
  Sur une émission du jour, c'est sans effet ; sur une ligne réelle achetée
  en cours de vie, il y aurait un décalage de quelques dizaines de pb.
- **Pas de risque de réinvestissement des coupons.** Le rendement actuariel
  suppose que chaque coupon est réinvesti à $y$, ce qui est faux.

→ Amont : [[01 - Courbe de taux - Svensson]] · Aval : [[03 - Rendements espérés]]
