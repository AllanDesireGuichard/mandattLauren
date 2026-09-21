---
titre: Valorisation obligataire
source: core/obligations.py — prix(), coupon_au_pair(), rendement(), analyse(), echelle()
maj: 2026-09-21
---

# Valorisation obligataire

## En une phrase

**Une obligation, c'est une liste de versements futurs. La valoriser, c'est
dire ce que valent ces versements aujourd'hui.**

Tout part de la courbe de [[01 - Courbe de taux - Svensson]], qui donne le
taux pour chaque durée.

## 1. Le prix : ramener le futur à aujourd'hui

Une obligation à 5 ans qui verse 3 € par an, c'est six versements : 3 € dans
un an, 3 € dans deux ans… et 103 € dans cinq ans (le dernier coupon plus le
remboursement du capital).

**Un euro dans 5 ans vaut moins qu'un euro aujourd'hui**, parce qu'un euro
d'aujourd'hui pourrait être placé pendant 5 ans. La courbe des taux dit
exactement combien moins : c'est le *facteur d'actualisation*.

> **Le prix de l'obligation = la somme de tous ses versements, chacun ramené
> à sa valeur d'aujourd'hui.**

C'est toute la valorisation obligataire. Il n'y a rien d'autre.

### Un détail qui compte : les dates de versement

Le code construit les dates **en partant de l'échéance et en remontant** :

```python
def _dates(maturite):
    n = math.ceil(maturite - 1e-9)
    return [maturite - k for k in range(n)][::-1]
```

Pour une obligation à 2 ans et 6 mois, ça donne : 6 mois, 1 an et 6 mois,
2 ans et 6 mois. Si on partait de 1 an en avançant, on obtiendrait 1 an et
2 ans — et on oublierait un versement. Sur une maturité non entière, c'est
une erreur de plusieurs pourcents sur le prix.

## 2. Le coupon au pair : une obligation de référence

On ne prend pas une obligation existante. On se pose la question inverse :

> **Quel coupon faudrait-il verser pour que cette obligation vaille
> exactement 100 aujourd'hui ?**

C'est l'obligation qu'un État émettrait aujourd'hui s'il empruntait
maintenant. On l'appelle « au pair » parce que son prix égale son nominal.

**Pourquoi cette référence.** Une obligation au pair n'a ni prime ni décote :
son coupon *est* son rendement. Elle isole donc l'effet de la courbe de
l'effet du prix d'achat. Comparer une obligation à 10 ans achetée 118 et une
à 2 ans achetée 97 mélange deux choses ; comparer deux obligations au pair
ne compare que les durées.

## 3. Le rendement actuariel : le taux unique équivalent

Le prix vient d'une courbe entière — un taux différent pour chaque échéance.
Mais on veut pouvoir dire « cette obligation rapporte 3,4 % ». D'où :

> **Le rendement actuariel est le taux unique qui, appliqué à tous les
> versements, redonnerait exactement le prix observé.**

C'est une moyenne, pondérée par la taille et la date des versements.

**Comment le code le trouve.** Il n'y a pas de formule directe : on cherche
par tâtonnement, en coupant l'intervalle en deux à chaque fois. On sait que
le taux est entre −5 % et +30 %. On teste 12,5 % : le prix calculé est trop
bas, donc le vrai taux est plus bas. On teste 3,75 %. Et ainsi de suite,
100 fois. La précision devient absurdement fine bien avant la fin.

> [!note] Pourquoi cette méthode plutôt qu'une méthode rapide
> Newton-Raphson converge en 4 ou 5 itérations au lieu de 100, mais peut
> partir en vrille sur une obligation à coupon nul ou à taux négatif. La
> dichotomie est lente et **incassable** : tant que la solution est dans
> l'intervalle, elle la trouve. Sur un dossier qu'on doit pouvoir défendre,
> c'est le bon arbitrage.
>
> La borne basse à −5 % n'est pas décorative : la zone euro a connu des
> rendements souverains négatifs de 2015 à 2022.

## 4. Les mesures de risque, en français

### La duration : dans combien de temps je récupère mon argent

Une obligation à 10 ans ne te rend pas tout ton argent dans 10 ans : elle
verse des coupons avant. La duration, c'est **le délai moyen de
récupération**, en pondérant chaque versement par ce qu'il pèse.

Une obligation à 10 ans avec de gros coupons a une duration de 8 ans. Un
zéro-coupon à 10 ans a une duration de 10 ans pile, puisque tout arrive à la
fin.

### La sensibilité : combien je perds si les taux montent

C'est **la duration, corrigée d'un petit facteur**. Et son interprétation est
directe :

> **Sensibilité de 4,7 ⟹ si tous les taux montent d'un point, l'obligation
> perd environ 4,7 % de sa valeur.**

C'est le chiffre qu'on cite dans le dossier : « l'échelle 2-10 ans perd
4,7 % si les taux montent d'un point ».

**L'intuition :** si tu détiens une obligation qui paie 3 % et que le marché
se met à payer 4 %, personne ne veut de la tienne à son prix actuel. Son
prix baisse jusqu'à ce qu'elle redevienne compétitive. Plus elle est longue,
plus il faut baisser — d'où le lien avec la duration.

### La convexité : la bonne nouvelle

La sensibilité suppose une relation en ligne droite entre taux et prix. En
réalité la relation est courbe, et **courbée dans le bon sens pour le
détenteur** :

> **Quand les taux montent, on perd un peu moins que prévu. Quand ils
> baissent, on gagne un peu plus que prévu.**

La convexité mesure cet écart favorable. Elle est positive pour toute
obligation classique. C'est un actif gratuit, et elle explique pourquoi la
sensibilité seule est trop pessimiste sur les grosses variations.

> [!tip] Ce que fait le code, et c'est mieux que la moyenne
> Au lieu d'approcher la perte par « sensibilité + convexité », le code
> **revalorise réellement l'obligation** avec la courbe décalée d'un point
> (`choc_plus_1`). C'est exact au lieu d'être approché, et ça évite de se
> faire piéger sur les longues maturités où l'approximation décroche.

### Portage et glissement : d'où vient le rendement d'une année

Si je garde cette obligation un an et que la courbe ne bouge pas du tout,
je gagne de l'argent par deux canaux :

- **Le portage** *(carry)* : j'encaisse le coupon. Évident.
- **Le glissement** *(roll-down)* : moins évident, et c'est le joli. Mon
  obligation à 10 ans devient une obligation à 9 ans. Or sur une courbe
  montante, le taux à 9 ans est plus bas que celui à 10 ans. Mon obligation
  est donc valorisée avec un taux plus bas, **donc son prix monte**. J'ai
  gagné de l'argent sans que rien ne bouge, juste parce que le temps a passé.

> **Rendement sur un an, courbe inchangée = portage + glissement.**

Cette décomposition dit *pourquoi* une échéance paie : une courbe très
pentue paie surtout en glissement, une courbe plate surtout en portage.

## 5. L'échelle : adosser les 10 M€

M. Lauren a besoin de 10 M€ étalés sur deux ans. La réponse n'est pas de
placer 10 M€ quelque part et d'espérer, c'est de **faire coïncider chaque
besoin avec un remboursement**.

| Échéance | Montant voulu | Taux garanti |
|---|---|---|
| 6 mois | 2,5 M€ | 2,75 % |
| 12 mois | 2,5 M€ | 3,01 % |
| 18 mois | 2,5 M€ | 3,15 % |
| 24 mois | 2,5 M€ | 3,22 % |

Coût aujourd'hui : **9,63 M€** pour récupérer 10 M€ aux bonnes dates.
Soit **78 k€ de mieux que de laisser l'argent au monétaire.**

> [!important] La distinction qui fait tout : risque de prix ≠ risque de flux
> Si les taux montent, ces obligations perdent de la valeur de marché. Et
> alors ? On ne les vend pas. On les garde jusqu'à l'échéance, et elles
> rendent le montant prévu, à la date prévue.
>
> **L'adossement ne réduit pas le risque de taux : il le rend sans objet.**
> Pour un besoin daté, seul le flux compte, pas le prix intermédiaire.
> C'est l'argument central pour justifier l'achat en direct plutôt qu'un
> fonds obligataire, qui n'a pas d'échéance et subit donc le prix.

## Limites

- **Pas de coupon couru, pas de conventions de décompte** (ACT/ACT, 30/360).
  Sans effet sur une émission du jour ; décalage de quelques dizaines de
  points de base sur une ligne réelle achetée en cours de vie.
- **Le rendement actuariel suppose que les coupons sont réinvestis au même
  taux**, ce qui est faux. Sur une obligation à fort coupon, c'est une
  hypothèse optimiste.
- **Pas de spread émetteur ligne à ligne** : deux courbes (AAA et zone euro
  globale), pas une par pays.

→ Amont : [[01 - Courbe de taux - Svensson]] · Aval : [[03 - Rendements espérés]]
