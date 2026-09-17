"""
Onglet Concepts -- cours structure sur la construction du portefeuille.

Ecrit comme un chapitre de cours : parties, sous-parties, modeles explicites,
raisonnement redige. Chaque notion est amenee par le probleme qu'elle resout,
pas par sa definition.
"""
from __future__ import annotations

import streamlit as st

ARTIFACT = "https://claude.ai/code/artifact/108496cb-e142-4cde-9ad5-d44bbba44d2a"


def _say(text: str, label: str = "Formulation pour le client") -> None:
    st.markdown(
        f"<div style='background:#1b2530;color:#e8ebee;padding:20px 24px;"
        f"border-radius:3px;font-family:Georgia,serif;font-size:1.02rem;"
        f"line-height:1.65;margin:14px 0'>"
        f"<div style='font-family:sans-serif;font-size:.7rem;letter-spacing:.12em;"
        f"color:#9fb0bd;text-transform:uppercase;margin-bottom:12px;"
        f"padding-bottom:9px;border-bottom:1px solid #4e6c82'>{label}</div>"
        f"{text}</div>", unsafe_allow_html=True)


# ==========================================================================

def partie_1() -> None:
    st.markdown("""
## I. Le cadre : d'un besoin à un problème d'optimisation

### I.1 Ce qu'un mandat de gestion doit traduire

Un client n'exprime jamais un problème mathématique. Il exprime des besoins,
des craintes et des contraintes, formulés en langage courant et souvent
partiellement contradictoires. Le premier travail du gérant n'est pas de
calculer : il est de **traduire**, et de faire apparaître les contradictions
avant qu'elles ne se manifestent dans le portefeuille.

Dans notre cas, la demande initiale tient en six énoncés :

1. Cent millions d'euros à investir, dont dix à dépenser sous deux ans
2. Protéger le pouvoir d'achat contre une inflation de 4 % par an
3. Ne pas perdre plus de 15 %
4. Un profil de risque qualifié de « dynamique »
5. Trois exclusions sectorielles — tabac, armement, charbon thermique
6. Transmettre progressivement aux enfants

Ces six énoncés ne sont pas de même nature. Les deux premiers sont des
**objectifs**, le troisième une **contrainte**, le quatrième une
**préférence déclarée**, le cinquième une **restriction d'univers**, le
sixième un **changement de fonction objectif**. Les confondre conduit à des
erreurs de construction.

### I.2 La distinction objectif / contrainte

Un objectif se maximise ; une contrainte se respecte. La différence est
opérationnelle : on accepte de sous-performer son objectif, jamais de violer
sa contrainte.

Ici, l'objectif de rendement (couvrir l'inflation) et la contrainte de perte
(15 %) tirent en sens opposé. La question n'est donc pas « quel portefeuille
est le meilleur », mais **« quel est le rendement maximal atteignable sous
la contrainte de perte »**. C'est un problème d'optimisation sous contrainte,
et sa réponse est unique une fois les paramètres fixés.

### I.3 Pourquoi un objectif de rendement s'exprime toujours en net

L'erreur la plus fréquente consiste à viser en brut ce qui est exprimé en net.
Le client demande de préserver son pouvoir d'achat : c'est une exigence sur ce
qui **reste dans sa poche**, après frais de gestion, frais d'instruments et
fiscalité.

Le rendement brut requis s'écrit :
""")
    st.latex(r"r_{\text{requis}} = \pi + f_{\text{mandat}} + f_{\text{instruments}} + \tau")
    st.markdown("""
où $\\pi$ est l'inflation à couvrir, $f$ les couches de frais, et $\\tau$ la
friction fiscale annuelle. Avec $\\pi = 4{,}00\\,\\%$, des frais totaux de
$0{,}55\\,\\%$ et une friction de $0{,}25\\,\\%$ en assurance-vie, le seuil
s'établit à **4,80 %**.

Le même portefeuille logé dans un compte-titres garni de supports distribuants
porte une friction de $1{,}23\\,\\%$ et exige alors **5,78 %**. Près d'un point
de rendement supplémentaire pour un portefeuille identique : c'est la mesure de
ce que coûte une enveloppe mal choisie.

### I.4 L'architecture par objectifs

Un patrimoine sert plusieurs objectifs, d'horizons différents. Les traiter dans
un portefeuille unique revient à leur appliquer à tous le même budget de
risque — donc à servir mal chacun d'eux.

L'approche retenue, dite *goal-based investing*, consiste à découper le
patrimoine en poches, chacune adossée à un objectif daté :

| Poche | Montant | Horizon | Rôle | Volatilité cible |
|---|---|---|---|---|
| A — Liquidité | 10 M€ | 0-2 ans | Financer une dépense certaine | < 1 % |
| B — Cœur patrimonial | 58 M€ | 10-20 ans | Préserver le niveau de vie | ~7 % |
| C — Transmission | 30 M€ | 25-30 ans | Capital destiné aux enfants | ~12 % |
| D — Satellite | 2 M€ | 10 ans + | Convictions plafonnées | ~50 % |

Le bénéfice n'est pas cosmétique. La contrainte de 15 % porte sur le
**consolidé** : une poche à horizon long peut donc porter un risque très
supérieur à 15 % dès lors qu'elle est diluée par les poches courtes. Sans ce
découpage, le rendement requis n'est pas atteignable.

### I.5 L'horizon d'investissement n'est pas l'âge du client

L'usage veut qu'on réduise le risque avec l'âge. Ce réflexe repose sur une
hypothèse implicite : que le patrimoine sera consommé par son détenteur.

Lorsqu'une partie du patrimoine est destinée à être transmise, elle ne sera pas
liquidée au décès — elle continuera d'être investie par les héritiers.
L'horizon pertinent est alors la somme des deux espérances de vie, soit trente
ans et plus. Appliquer un profil prudent à cette poche revient à lui interdire
le rendement que son horizon justifie.
""")
    _say("Beaucoup vous diraient : vous avez soixante ans, donc horizon vingt ans, "
         "donc portefeuille prudent. Je crois que c'est une erreur d'analyse. "
         "Cet argent ne sera pas consommé à votre décès : il continuera d'être "
         "investi par vos enfants. L'horizon réel, c'est votre espérance de vie "
         "<b>plus</b> la leur. Et c'est une bonne nouvelle : le temps est le seul "
         "ingrédient qui transforme le risque en rendement.")


def partie_2() -> None:
    st.markdown("""
## II. La mesure du risque : quelle grandeur, et pourquoi

### II.1 Trois mesures concurrentes

Dire « je ne veux pas perdre plus de 15 % » ne suffit pas à définir une
contrainte. Trois grandeurs peuvent porter ce chiffre, et elles ne décrivent
pas la même chose.

**La volatilité** est l'écart-type des rendements. Elle mesure l'amplitude
moyenne des variations :
""")
    st.latex(r"\sigma = \sqrt{\frac{1}{T-1}\sum_{t=1}^{T}(r_t - \bar{r})^2} \times \sqrt{252}")
    st.markdown("""
Sa limite est décisive : elle est **symétrique**. Une hausse de 5 % et une
baisse de 5 % y contribuent identiquement, alors que le client ne les vit pas
de la même façon.

**La Value at Risk (VaR)** est le quantile de la distribution des pertes. À
95 % et sur un an, c'est la perte dépassée une année sur vingt. Elle est
asymétrique, ce qui corrige le défaut précédent, mais elle décrit une perte
**de fin de période** : elle ignore ce qui s'est passé entre-temps.

**Le drawdown** est la perte maximale de pic à creux sur une fenêtre :
""")
    st.latex(r"DD_{[t_0,t_1]} = \max_{t \in [t_0,t_1]}\left(1 - \frac{V_t}{\max_{s \le t} V_s}\right)")
    st.markdown("""
C'est la seule des trois qui décrive ce que le client **vit réellement** :
l'écart entre le meilleur relevé qu'il a reçu et le pire. C'est aussi la plus
contraignante des trois, ce qui en fait le choix conservateur.

### II.2 La définition retenue, et ses trois composantes

> **Perte maximale de pic à creux sur toute fenêtre de douze mois glissants,
> mesurée au niveau consolidé, en euros, avec une probabilité de dépassement
> inférieure à 10 %.**

Chacun des trois qualificatifs répond à une objection :

**« Douze mois glissants »** — et non « depuis le début du mandat ». Une mesure
ancrée sur une date de départ dépend du hasard de cette date. Une fenêtre
glissante teste toutes les dates d'entrée possibles.

**« Au niveau consolidé »** — et non ligne à ligne. Appliquer 15 % à chaque
ligne interdirait toute exposition actions, puisque aucune classe d'actifs
risquée ne respecte seule cette contrainte.

**« Probabilité de dépassement inférieure à 10 % »** — et non « jamais ».
Aucun gérant ne peut garantir un plafond absolu sur un portefeuille investi.
Promettre l'absolu serait malhonnête ; annoncer une fréquence est vérifiable.

### II.3 Du seuil de perte au budget de volatilité

La contrainte porte sur un drawdown, mais l'optimisation travaille sur une
volatilité. Il faut donc un lien entre les deux.

Ce lien existe empiriquement. Pour un portefeuille multi-actifs diversifié, le
drawdown au 90ᵉ centile sur douze mois est approximativement proportionnel à
la volatilité annuelle :
""")
    st.latex(r"DD_{P90} \approx k \times \sigma")
    st.markdown("""
La valeur de $k$ ne se postule pas : elle se mesure. Estimée sur 21,8 ans de
données quotidiennes en euros, incluant 2008, 2011, 2020 et 2022, elle
s'établit à **1,35** pour un portefeuille diversifié.

Ce coefficient n'est pas constant : il vaut 1,81 pour un portefeuille à 20 %
d'actions et décroît jusqu'à 1,33 à 80 %. La raison est que la diversification
obligataire agit davantage sur l'enchaînement des pertes que sur leur
amplitude moyenne.

### II.4 Volatilité et drawdown ne mesurent pas la même chose

La distinction mérite d'être comprise, car elle explique pourquoi une
optimisation moyenne-variance ne suffit pas.

La volatilité est une propriété de la **distribution** des rendements. Le
drawdown est une propriété de leur **trajectoire**. Deux séries peuvent
partager exactement la même volatilité et présenter des drawdowns radicalement
différents selon l'ordre dans lequel les rendements se présentent.

Douze mois consécutifs à $-1\\,\\%$ produisent un drawdown de 11,4 %. Les mêmes
rendements alternés avec des mois à $+1\\,\\%$ produisent un drawdown de 1 %.
Même moyenne, même écart-type, même ensemble de valeurs.

C'est pourquoi la contrainte ne peut pas être vérifiée analytiquement : elle
exige une **simulation de trajectoires**.
""")
    _say("Je ne vais pas vous promettre que vous ne perdrez jamais 15 %. Personne "
         "ne peut le promettre, et si on vous le promet, méfiez-vous. Ce que je "
         "vous dis, c'est que nous construisons le portefeuille pour que cela "
         "arrive moins d'une année sur dix — et nous vous montrerons les "
         "simulations qui le démontrent.")


def partie_3() -> None:
    st.markdown("""
## III. Les hypothèses de marché : d'où vient un rendement attendu

### III.1 Pourquoi l'historique ne fait pas une prévision

La tentation naturelle consiste à estimer le rendement attendu d'une classe
d'actifs par sa moyenne historique. C'est une erreur de raisonnement.

Une moyenne historique mesure ce qui s'est produit, et ce qui s'est produit
dépend massivement de l'évolution des **valorisations** sur la période. Un
marché actions dont le multiple de bénéfices est passé de 10 à 20 affiche une
performance passée flatteuse — et c'est précisément la raison pour laquelle sa
performance future sera plus faible. La moyenne historique est donc, au mieux,
neutre ; au pire, un indicateur à contresens.

L'approche correcte est celle des **blocs constitutifs** : décomposer le
rendement attendu en ses composantes économiques, et estimer chacune.

### III.2 Le modèle actions

Pour une action, le rendement total se décompose en :
""")
    st.latex(r"E[r] = \underbrace{d + b}_{\text{flux rendus}} + \underbrace{g_{\text{réel}} + \pi}_{\text{croissance des bénéfices}} + \underbrace{\Delta v}_{\text{dérive de valorisation}}")
    st.markdown("""
où $d$ est le rendement du dividende, $b$ le rendement des rachats d'actions,
$g_{\\text{réel}}$ la croissance réelle des bénéfices par action, $\\pi$
l'inflation, et $\\Delta v$ la variation annualisée du multiple de valorisation.

Pour les actions développées, notre estimation :

| Composante | Valeur | Justification |
|---|---|---|
| Rendement du dividende | +1,9 % | Observable sur l'indice |
| Rachats d'actions | +1,0 % | Moyenne des dix dernières années, en baisse tendancielle |
| Croissance réelle des BPA | +2,0 % | Proche de la croissance du PIB réel des économies développées |
| Inflation | +2,0 % | Régime de référence |
| Dérive de valorisation | **−0,8 %** | Les multiples américains sont au-dessus de leur moyenne longue : retour partiel supposé sur dix ans |
| **Total** | **6,1 %** | |

Le terme de dérive est le seul réellement discutable, et il est aussi le plus
influent. Le rendre explicite permet au client de contester **ce point précis**
plutôt que le chiffre global.

### III.3 Le modèle obligataire

Pour un portefeuille obligataire détenu à duration constante sur une période
au moins égale à sa duration, le meilleur prédicteur du rendement est le
**rendement actuariel d'entrée**. La démonstration est intuitive : les pertes
en capital dues à la hausse des taux sont compensées par le réinvestissement
des coupons à des taux plus élevés, et inversement.

Pour le crédit, il faut retrancher la perte attendue par défaut :
""")
    st.latex(r"E[r_{\text{crédit}}] = y - PD \times LGD")
    st.markdown("""
où $y$ est le rendement actuariel, $PD$ la probabilité de défaut annuelle et
$LGD$ la perte en cas de défaut. Pour du crédit *investment grade* euro, ce
terme est de l'ordre de dix points de base.

### III.4 La répercussion de l'inflation — le modèle central de ce mandat

Un mandat dont l'objectif est la protection contre l'inflation ne peut pas se
contenter d'hypothèses établies dans un seul régime d'inflation. Il faut
modéliser **comment chaque classe d'actifs réagit à une surprise
d'inflation**.

Nous introduisons pour cela un coefficient de répercussion $\\beta_\\pi$ :
""")
    st.latex(r"E[r_i \mid \pi] = E[r_i \mid \pi_0] + \beta_{\pi,i} \times (\pi - \pi_0)")
    st.markdown("""
où $\\pi_0$ est le régime de référence (2 %) et $\\beta_{\\pi,i}$ la part de la
surprise d'inflation qui se retrouve dans le rendement nominal à dix ans.

| Classe d'actifs | $\\beta_\\pi$ | Mécanisme |
|---|---|---|
| Monétaire | 1,00 | Les taux directeurs suivent l'inflation |
| Obligations indexées | 1,00 | Protection mécanique — c'est leur définition |
| Or | 1,00 | Réserve de valeur, aucun flux nominal à actualiser |
| Matières premières | 1,10 | Souvent la **cause** de la surprise, pas seulement sa victime |
| Infrastructure cotée | 0,90 | Revenus contractuellement indexés |
| Actions | 0,80 | Pouvoir de fixation des prix, mais compression des multiples |
| Crédit IG | 0,50 | Duration intermédiaire |
| **Souverain à taux fixe** | **0,45** | Perte en capital d'abord, réinvestissement ensuite |

Ce tableau explique pourquoi une allocation obligataire classique échoue dans
le scénario que craint le client. À 4 % d'inflation, le souverain euro rapporte
**3,60 %** quand le monétaire rapporte **4,05 %** : l'actif réputé défensif
rapporte moins que le sans-risque.

### III.5 La conséquence méthodologique

Si les rendements attendus dépendent du régime d'inflation, alors le **seuil
requis** en dépend aussi — puisqu'il contient $\\pi$. Les deux termes doivent
donc être évalués dans le **même régime**, sans quoi la comparaison n'a aucun
sens.

| Régime | Rendement attendu | Seuil requis | Marge |
|---|---|---|---|
| Inflation 2 % (consensus BCE) | 4,25 % | 2,85 % | **+1,40 %** |
| Inflation 4 % (hypothèse client) | 5,84 % | 4,85 % | **+0,99 %** |

L'objectif est atteint dans les deux cas. Ce résultat a une valeur commerciale
directe : il signifie que **le client ne dépend pas de la justesse de notre
prévision d'inflation**.
""")
    _say("Votre hypothèse d'inflation à 4 % est nettement au-dessus du consensus, "
         "qui table plutôt sur 2 %. <b>Nous ne l'avons pas corrigée.</b> Nous avons "
         "construit votre portefeuille pour qu'il tienne dans votre scénario, pas "
         "dans le nôtre.<br><br>Et si l'inflation se révèle conforme au consensus, "
         "votre marge est plus large encore. Vous êtes couvert dans les deux cas — "
         "vous ne dépendez pas du fait que nous ayons raison.")


def partie_4() -> None:
    st.markdown("""
## IV. L'optimisation : construire, puis refuser le résultat

### IV.1 Le problème de Markowitz et ses deux faiblesses

L'optimisation moyenne-variance résout :
""")
    st.latex(r"\min_w \; w^\top \Sigma w \quad \text{s.c.} \quad \mu^\top w = r^*, \;\; \mathbf{1}^\top w = 1, \;\; w \ge 0")
    st.markdown("""
où $w$ est le vecteur des poids, $\\Sigma$ la matrice de covariance et $\\mu$
les rendements attendus. Le résultat est la frontière efficiente.

Ce cadre souffre de deux faiblesses bien documentées.

**L'instabilité.** La solution est extrêmement sensible aux rendements
attendus. Déplacer une estimation de vingt points de base suffit à faire
basculer l'allocation. Or les rendements attendus sont précisément les
paramètres les plus mal estimés : leur erreur-type est de l'ordre de
$\\sigma/\\sqrt{T}$, soit plusieurs points de pourcentage même sur vingt ans
de données.

**La concentration.** L'optimiseur ne connaît que ce qu'on lui donne. Il
concentre sur l'actif présentant le meilleur couple estimé, sans percevoir ni
le risque de concentration sectorielle, ni la capacité d'exécution, ni les
régimes que la matrice de covariance ne contient pas.

### IV.2 Black-Litterman : régulariser par un point d'ancrage

Le modèle de Black-Litterman corrige l'instabilité en partant d'un point
neutre et en ne s'en écartant qu'à proportion de la confiance accordée à
chaque vue.

Le rendement postérieur s'écrit :
""")
    st.latex(r"\mu_{BL} = \left[(\tau\Sigma)^{-1} + P^\top \Omega^{-1} P\right]^{-1}\left[(\tau\Sigma)^{-1}\pi + P^\top \Omega^{-1} Q\right]")
    st.markdown("""
où $\\pi$ est le prior, $P$ la matrice des vues (une ligne par vue, $+1$ et
$-1$ sur les actifs concernés), $Q$ l'ampleur de chaque vue, $\\Omega$
l'incertitude qui leur est associée, et $\\tau$ l'incertitude sur le prior.

Cette formule est une **moyenne pondérée par les précisions** : plus une vue
est certaine (donc $\\Omega$ petit), plus elle tire le postérieur vers elle.

**Le choix du prior est décisif.** L'usage recommande l'optimisation inverse
depuis les poids de marché : $\\pi = \\delta\\,\\Sigma\\,w_{\\text{mkt}}$. Cette
méthode suppose que le portefeuille de référence est **optimal**.

Nous l'avons écartée, pour une raison de cohérence interne. Faute de
capitalisation boursière comparable pour l'or ou le monétaire, nous avions
retenu un neutre en parité de risque — donc obligataire à 53 %. Or nos propres
hypothèses disent qu'à 4 % d'inflation le souverain rapporte moins que le
monétaire : ce portefeuille n'est pas optimal selon nos hypothèses.
L'aversion au risque déduite tombait alors à 1,76, et la prime des actions
ressortait à **1,49 %** au lieu des 3,65 % de nos hypothèses.

**Un prior qui contredit ses propres hypothèses n'est pas un prior.** Nous
avons donc retenu les hypothèses de marché comme point de départ, et appliqué
les vues en écarts.

### IV.3 Le resampling de Michaud

Pour traiter l'instabilité, on perturbe les rendements attendus selon leur
erreur d'estimation, on réoptimise, et on moyenne les allocations obtenues :
""")
    st.latex(r"\hat{w} = \frac{1}{N}\sum_{n=1}^{N} w^*\!\left(\mu + \varepsilon_n\right), \qquad \varepsilon_n \sim \mathcal{N}\!\left(0, \frac{\text{diag}(\Sigma)}{T}\right)")
    st.markdown("""
Le portefeuille moyen est plus diversifié et beaucoup plus stable que
l'optimum unique. L'écart-type des poids entre tirages fournit en prime une
**mesure de fragilité par ligne** : une classe dont le poids varie de ±12 %
d'un tirage à l'autre n'est pas une conviction, c'est un artefact.

### IV.4 Ce que l'optimisation libre produit, et pourquoi on la refuse

Appliqué sans contraintes de second niveau, le processus donne :

| Classe | Optimisation libre | Retenu |
|---|---|---|
| Infrastructure cotée | **27,8 %** | 9 % |
| Actions émergentes | 20,9 % | 11 % |
| Actions développées | **7,1 %** | 23 % |
| Or | **0,8 %** | 7 % |
| Souverain euro | **0,0 %** | 10 % |

Chacune de ces décisions est **correcte au regard des données fournies et
fausse au regard du mandat**. Les contraintes ajoutées n'expriment pas de la
prudence : elles encodent des risques absents de la matrice d'entrée.

| Contrainte | Risque encodé |
|---|---|
| Infrastructure ≤ 10 % | Concentration sectorielle et capacité d'exécution — le support filtré ESG a 3,1 ans d'historique |
| Or ≥ 6 % | Comportement en régime de stress : c'est la seule brique dont la corrélation aux actions **baisse** en crise (0,07 → −0,07 en 2022). Une covariance pleine période moyenne ce comportement et l'efface |
| Souverain euro ≥ 8 % | Scénario de récession, non tarifé par des hypothèses mono-régime |
| Actions développées ≥ 20 % | Liquidité et capacité pour un mandat de 100 M€ |
| Crypto = 2 % | Décision de gouvernance, pas une sortie de calcul |

L'effet est mesurable : l'instabilité moyenne des poids passe de **3,8 % à
2,3 %**. Le portefeuille contraint est à la fois plus prudent et plus
reproductible.

### IV.5 La validation par simulation

La contrainte de drawdown étant dépendante de la trajectoire (§II.4), elle ne
peut être vérifiée que par simulation. Deux méthodes sont employées
conjointement.

**Les fenêtres historiques glissantes** : on calcule le drawdown maximal sur
chacune des 5 438 fenêtres de 252 jours disponibles, et on lit le 90ᵉ centile.

**Le block bootstrap** : on rééchantillonne l'historique par blocs de plusieurs
mois consécutifs, afin de préserver l'autocorrélation et les enchaînements de
crise qu'un tirage indépendant détruirait.

Un constat mérite d'être signalé, car il contredit l'intuition courante : sur
nos données, le block bootstrap donne des drawdowns **inférieurs de zéro à
0,6 point** au relevé historique, pour des longueurs de blocs allant de 21 à
252 jours. Il recoupe le relevé historique, il ne le durcit pas. Le chiffre
sur lequel nous nous engageons reste celui que le marché a réellement produit.
""")
    _say("Nous n'optimisons pas une fois. Nous proposons une allocation, nous la "
         "passons dans des milliers de scénarios, nous regardons combien de fois "
         "elle dépasse vos 15 %, et nous corrigeons jusqu'à ce que la réponse soit "
         "satisfaisante. Ce n'est pas un calcul, c'est une boucle de validation."
         "<br><br>Et au bout, l'optimiseur nous a dit où nos hypothèses poussent. "
         "Notre travail était de décider ce que nos hypothèses ne pouvaient pas voir.")


def partie_5() -> None:
    st.markdown("""
## V. Fiscalité et transmission : le changement de fonction objectif

### V.1 Pourquoi le patrimoine brut est le mauvais indicateur

Toute la construction précédente maximise une richesse terminale. Or le client
ne cherche pas à maximiser sa fortune : il cherche à maximiser **ce qui arrive
à ses enfants**. Ce n'est pas le même problème.

La fonction objectif devient :
""")
    st.latex(r"\max_{\;\text{allocation},\,\text{structure}} \; \mathbb{E}\!\left[W_T \times \left(1 - \theta(\text{structure})\right)\right]")
    st.markdown("""
où $\\theta$ est le taux effectif de transmission, qui dépend non pas de
l'allocation mais de la **structure juridique** des enveloppes.

L'ordre de grandeur de $\\theta$ va de 14 % à 45 % selon la structure. Aucune
décision d'allocation ne produit un écart de cette ampleur.

### V.2 Les trois régimes de transmission

**Le barème de droit commun (art. 777 CGI).** En ligne directe, après un
abattement de 100 000 € par parent et par enfant, le barème est progressif
jusqu'à 45 % au-delà de 1 805 677 €. Sur les montants qui nous occupent, le
taux effectif approche 44,5 %.

**L'assurance-vie, primes versées avant 70 ans (art. 990 I CGI).** Abattement
de 152 500 € par bénéficiaire, puis 20 % jusqu'à 700 000 € et 31,25 % au-delà.
Sur 100 M€ transmis à deux bénéficiaires, le taux effectif ressort à **31,0 %**
contre 44,4 % au barème de droit commun.

Le client a soixante ans : cette fenêtre lui est ouverte pour dix ans encore,
puis se ferme. C'est un argument de calendrier, pas seulement d'optimisation.

**La donation en nue-propriété (art. 669 CGI).** C'est le levier le plus
puissant, et il repose sur deux effets distincts.

*Premier effet — la base taxable est réduite.* La pleine propriété se
décompose en usufruit (le droit aux revenus) et nue-propriété (la propriété à
terme). Le barème légal fixe la valeur de l'usufruit selon l'âge du donateur :
""")
    st.latex(r"\text{valeur de la nue-propriété} = 1 - u(\text{âge})")
    st.markdown("""
| Âge du donateur | Usufruit | Nue-propriété taxable |
|---|---|---|
| 51 à 60 ans | 50 % | **50 %** |
| 61 à 70 ans | 40 % | **60 %** |
| 71 à 80 ans | 30 % | 70 % |

Transmettre la nue-propriété d'un actif de 10 M€ à soixante ans revient donc à
acquitter des droits sur 5 M€.

*Second effet — l'appréciation future échappe à l'impôt.* Les enfants étant
déjà nus-propriétaires, toute la plus-value ultérieure leur revient sans droit
supplémentaire. Et au décès du donateur, **l'usufruit s'éteint sans aucune
taxation** : les nus-propriétaires deviennent pleins propriétaires.

### V.3 Le point de calendrier

La bascule entre tranches d'âge est un effet de seuil, pas une progression
continue. Pour une donation de 36 M€ :

| Date de la donation | Nue-propriété taxable | Droits dus |
|---|---|---|
| Avant 61 ans | 50 % | **7,4 M€** |
| Après 61 ans | 60 % | **9,1 M€** |

**1,6 M€ d'écart pour un anniversaire franchi.** Sur la totalité du patrimoine,
l'écart atteint 4,5 M€. C'est l'élément le plus concret du dossier, et il a une
date limite.

### V.4 La friction fiscale annuelle

Distincte de la transmission, elle mesure ce que l'enveloppe coûte chaque
année. Le modèle :
""")
    st.latex(r"\tau_i = \underbrace{y_i \times t_{\text{revenus}}}_{\text{revenus distribués}} + \underbrace{\rho_i \times g \times t_{\text{PV}}}_{\text{plus-values de rebalancement}}")
    st.markdown("""
où $y_i$ est le rendement courant distribué, $\\rho_i$ la rotation annuelle
induite par le rebalancement, $g$ la plus-value latente moyenne, et $t$ les
taux applicables.

Ce modèle fait apparaître un point mal connu : **un ETF capitalisant logé dans
un compte-titres ne déclenche aucun impôt tant qu'on ne vend pas.** Le premier
terme s'annule. Seule subsiste la friction de rebalancement.

| Régime | Friction annuelle | Seuil requis |
|---|---|---|
| Assurance-vie luxembourgeoise | 0,25 % | 4,80 % |
| Compte-titres, supports capitalisants | 0,63 % | 5,18 % |
| Compte-titres, supports distribuants | 1,23 % | 5,78 % |

L'écart entre une structure optimisée et un compte-titres correctement géré
est de **38 points de base**. C'est réel, ce n'est pas spectaculaire. L'écart
entre un compte-titres correctement géré et un compte-titres négligent est de
**60 points de base** — et il est gratuit à corriger.

### V.5 La hiérarchie des leviers

En projetant le patrimoine net transmis sur vingt-cinq ans, on peut chiffrer
ce que rapporte chaque décision :

| Décision | Gain pour les enfants |
|---|---|
| Optimisation de l'allocation (+0,14 %/an) | +5,5 M€ |
| Dé-risquage après stress tests (−0,19 %/an) | −7,4 M€ |
| **Structuration de la transmission** | **+50 M€** |

**La structuration pèse neuf fois le gain de toute l'optimisation
d'allocation.** C'est la conclusion la plus importante de l'étude, et elle
inverse l'ordre d'importance habituel d'un mandat de gestion.

### V.6 Une limite de l'optimisation, à nouveau

Appliqué mécaniquement, le calcul de localisation des actifs conclut « tout en
assurance-vie » : ses 0,25 % de frais battent les 0,63 % du compte-titres sur
chaque classe. C'est la troisième sortie dégénérée rencontrée dans cette étude,
après la parité de risque et l'optimisation d'allocation.

Quatre éléments lui échappent :

**La purge des plus-values au décès.** Les plus-values latentes d'un
compte-titres ne sont jamais imposées au décès. Pour la part destinée à être
conservée jusqu'au bout, la friction réelle est donc inférieure à 0,63 %.

**La liquidité.** Un rachat en assurance-vie prend plusieurs jours. Les 10 M€ à
décaisser doivent rester directement accessibles.

**La concentration sur un assureur.** Le super-privilège luxembourgeois atténue
le risque de contrepartie sans l'annuler.

**La flexibilité.** Le compte-titres permet de nantir, de donner des titres en
direct, de piloter finement la fiscalité des cessions.

Répartition retenue : **65 % assurance-vie, 35 % compte-titres.**
""")
    _say("Nous mesurons la mauvaise chose si nous regardons la valeur de votre "
         "portefeuille. Ce qui compte, c'est ce qui arrivera à vos enfants après "
         "droits. Entre les deux, il peut y avoir quarante-cinq points d'écart — "
         "et aucune décision d'allocation ne produira jamais un gain de cette "
         "ampleur.<br><br>Regardez les deux patrimoines <b>bruts</b> : 290 millions "
         "sans structuration, 264 avec. Le scénario structuré est plus pauvre, "
         "parce que les droits de donation sont payés dès le départ. Et pourtant "
         "il transmet cinquante millions de plus.")

    st.markdown("""
> **Réserve.** Ce module applique des règles fiscales exactes à notre
> connaissance, mais ne modélise ni le régime matrimonial, ni les droits du
> conjoint survivant, ni la réserve héréditaire. Ces trois éléments changent
> les montants, non la hiérarchie des leviers. Une validation par un notaire
> est indispensable avant toute mise en œuvre.
""")


PARTIES = [
    ("I. Le cadre", partie_1),
    ("II. La mesure du risque", partie_2),
    ("III. Les hypothèses de marché", partie_3),
    ("IV. L'optimisation", partie_4),
    ("V. Fiscalité et transmission", partie_5),
]


def render() -> None:
    st.header("Concepts — la construction du portefeuille, expliquée")
    st.caption("Cinq parties. Chaque notion est amenée par le problème qu'elle "
               "résout, avec le modèle qui la formalise et la formulation à "
               "employer devant le client.")

    st.link_button("Argumentaire oral complet — 14 concepts, mode répétition",
                   ARTIFACT, width="content")

    st.markdown("""
---
#### Plan

**I. Le cadre** — traduire un besoin en problème d'optimisation · objectif
contre contrainte · pourquoi un objectif s'exprime en net · l'architecture par
poches · l'horizon réel

**II. La mesure du risque** — volatilité, VaR et drawdown · la définition
retenue et ses trois composantes · du seuil de perte au budget de volatilité ·
pourquoi trajectoire et distribution diffèrent

**III. Les hypothèses de marché** — pourquoi l'historique ne prévoit rien · le
modèle actions par blocs · le modèle obligataire · la répercussion de
l'inflation · la cohérence de régime

**IV. L'optimisation** — Markowitz et ses deux faiblesses · Black-Litterman et
le choix du prior · le resampling de Michaud · pourquoi refuser le résultat
libre · la validation par simulation

**V. Fiscalité et transmission** — le changement de fonction objectif · les
trois régimes · le point de calendrier · la friction annuelle · la hiérarchie
des leviers

---
""")

    for titre, fn in PARTIES:
        with st.expander(titre, expanded=(titre.startswith("I."))):
            fn()
