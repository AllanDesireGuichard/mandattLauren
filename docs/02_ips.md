# Investment Policy Statement — Famille Lauren
**Version 1.3 — 17 septembre 2026**

> Révisée après passe de validation empirique. Les corrections de la v1.0
> sont signalées en encadré à chaque endroit concerné.

Document de cadrage contractuel. Fige les objectifs, contraintes et le budget
de risque **avant** toute optimisation. Toute modification requiert l'accord
formel du client.

---

## 1. Identification et situation

| | |
|---|---|
| Client | M. Lauren, 60 ans, marié, 2 enfants |
| Résidence fiscale | France |
| Devise de référence | EUR |
| Origine des fonds | Cession d'une société technologique |
| Actifs investissables | **100 000 000 €** |
| Expérience d'investissement | Entrepreneur — familier du risque, non familier des marchés cotés |

> **Hypothèse retenue** : le produit de cession est déjà converti en euros.
> Le risque de conversion du notionnel est hors périmètre. La couverture de
> change des actifs étrangers acquis reste une décision d'allocation (§6.4).

---

## 2. Objectifs

### 2.1 Objectif de liquidité — prioritaire
**10 000 000 €** disponibles sur un horizon de 0 à 24 mois.
Contrainte de préservation nominale : cette poche n'a pas vocation à performer.

### 2.2 Objectif de rendement
Préservation du pouvoir d'achat des 90 M€ restants face à une inflation
anticipée de **4,0 % par an**, **nette de frais et nette de fiscalité**.

### 2.3 Objectif de transmission
Transmission progressive et fiscalement optimisée aux deux enfants.
**L'indicateur de succès est le patrimoine net transmis, non le patrimoine brut.**

---

## 3. Décomposition de l'objectif de rendement

| Composante | Taux | Commentaire |
|---|---|---|
| Inflation à couvrir | 4,00 % | Hypothèse client |
| Frais de mandat | 0,40 % | Négocié sur la taille d'actifs |
| Frais des instruments (TER moyen) | 0,15 % | Gestion indicielle majoritaire |
| Friction fiscale annuelle | 0,30 % | Structure §7 |
| **Rendement brut requis** | **4,85 %** | |

### Ce que coûte réellement l'absence de structuration

> **Correction d'une version antérieure de ce document.** La v1.0 opposait une
> structure optimisée (0,35 %) à un compte-titres garni de supports
> **distribuants** (1,20 %), et en concluait un écart de 0,85 %. Cette
> comparaison était un homme de paille : personne de compétent ne loge des
> fonds distribuants dans un compte-titres. Chiffres révisés :

| Scénario | Friction annuelle | Rendement brut requis |
|---|---|---|
| Structure optimisée (AV LUX + ETF capitalisants + domicile irlandais) | 0,30 % | **4,85 %** |
| Compte-titres bien géré, ETF capitalisants | 0,45 % | 5,00 % |
| Compte-titres, supports distribuants | 0,90 % | 5,45 % |

**Conséquence sur l'argumentaire.** L'écart annuel entre une structure
optimisée et un compte-titres correctement géré est de **15 points de base**,
pas 85. C'est réel, ce n'est pas décisif.

> **La valeur du contrat luxembourgeois n'est donc pas dans la friction
> annuelle. Elle est à la transmission** — 20 % contre 45 % en ligne directe —
> **et dans l'accès** (univers élargi, multi-devises, super-privilège). C'est
> sur ce terrain qu'il faut construire l'argument, où les chiffres sont
> massifs, et non sur un différentiel de rendement annuel qui ne tient pas
> l'examen.

Ce qui coûte vraiment cher, en revanche, c'est l'absence totale de soin :
60 points de base par an entre un compte-titres bien géré et un compte-titres
négligent. Cet argument-là est solide, et il est gratuit à mettre en œuvre.

## 4. Contrainte de risque

### 4.1 Définition retenue

> Perte maximale de pic à creux *(maximum drawdown)* sur toute fenêtre de
> **12 mois glissants**, mesurée au niveau **consolidé**, en **euros**,
> avec une probabilité de dépassement **inférieure à 10 %**.

Justification des trois choix :

| Choix | Justification |
|---|---|
| Drawdown plutôt que VaR | C'est la mesure vécue par le client (écart entre le meilleur et le pire relevé). C'est aussi la plus contraignante — le choix conservateur. |
| Niveau consolidé | Appliquer la contrainte ligne à ligne interdirait toute exposition actions. |
| Probabilité < 10 % | Aucun plafond absolu n'est garantissable. Un seuil probabilisé est vérifiable et honnête. |

### 4.2 Traduction en budget de risque — **mesurée, non postulée**

> **Correction majeure.** La v1.0 posait un ratio drawdown/volatilité de 1,9
> comme « règle empirique », sans l'estimer. Il a été mesuré sur **21,8 ans de
> données quotidiennes en euros** (2004-2026, incluant 2008, 2011, 2020, 2022)
> — `scripts/estimate_dd_ratio.py`.

Le ratio réel est de **1,33 à 1,36** pour un portefeuille multi-actifs
diversifié. Il n'est pas constant : il décroît avec le poids d'actions
(1,81 à 20 % d'actions, 1,33 à 80 %), parce que la diversification
obligataire agit davantage sur le drawdown que sur la volatilité.

**Le 1,9 était trop conservateur : il sous-allouait le risque d'environ dix
points d'actions.**

Allocation testée directement contre la contrainte — `scripts/validate_saa_risk.py` :

| Actifs de croissance | Volatilité | DD P90 | Pire observé | 2008 | 2022 |
|---|---|---|---|---|---|
| 38 % | 8,1 % | 10,7 % | 20,7 % | 21,3 % | 10,7 % |
| 42 % | 9,0 % | 12,0 % | 23,0 % | 23,8 % | 12,0 % |
| **47 %** | **9,9 %** | **13,3 %** | 25,3 % | 26,3 % | 13,3 % |
| 51 % | 10,8 % | 14,6 % | 27,6 % | 28,7 % | 14,6 % |

> **Budget retenu : 47 % d'actifs de croissance, volatilité 9,9 %, DD P90 de
> 13,3 %.** Soit 1,7 point de marge sous la contrainte — marge délibérée,
> parce que l'estimation elle-même porte une erreur.

### 4.2 bis Ce que le P90 masque — à dire au client

Le pire drawdown observé sur la période n'est pas 13 % mais **26 %, en 2008**.
La contrainte de 15 % est tenue « moins d'une année sur dix », pas « jamais ».

Présenter le P90 sans le pire cas serait exactement le type d'omission qui
détruit la confiance le jour où elle se matérialise. Les deux chiffres doivent
figurer sur la même slide.

### 4.3 Résolution de la tension « dynamique » / 15 %

Le profil déclaré est *dynamique* (≈ 13 % de volatilité par convention de place,
soit un drawdown attendu de 25-35 %). Il est **incompatible** avec le plafond
de 15 %.

> **Arbitrage retenu : la contrainte chiffrée prime sur l'adjectif.**
>
> Le qualificatif « dynamique » est interprété comme une description du
> **comportement** du client (tolérance psychologique à la volatilité, absence
> de risque de vente panique) et non comme une cible de volatilité. Il est
> honoré par la **localisation** du risque — concentré dans la poche
> transmission à 30 ans — et non par son niveau global.

### 4.4 Test de cohérence — **le mandat est atteignable**

> **Correction v1.2 — la plus importante à ce jour.** Les versions
> précédentes comparaient un seuil de rendement bâti sur **4 % d'inflation**
> à des rendements attendus bâtis implicitement sur **2 %**. C'est-à-dire
> qu'on jugeait un portefeuille évalué dans un monde à 2 % d'inflation contre
> une exigence formulée dans un monde à 4 %. Le mandat paraissait plus
> difficile qu'il ne l'est.
>
> Chaque classe d'actifs porte désormais un **coefficient de répercussion**
> (`core/cma.py`) : la part d'une surprise d'inflation qui se retrouve dans son
> rendement nominal à dix ans. Seuil et rendements sont évalués dans le même
> régime.

| Régime d'inflation | Rendement attendu | Seuil requis | Marge |
|---|---|---|---|
| **2 %** — consensus, cible BCE | 4,25 % | 2,85 % | **+1,40 %** |
| **4 %** — hypothèse du client | 5,84 % | 4,85 % | **+0,99 %** |

**L'objectif est atteint dans les deux régimes**, avec environ un point de
marge annuelle.

### Le point de pitch que cela ouvre

> « Monsieur Lauren, votre hypothèse d'inflation à 4 % est nettement au-dessus
> du consensus, qui table plutôt sur 2 %. Nous ne l'avons pas corrigée : nous
> avons construit votre portefeuille pour qu'il tienne **dans votre scénario**,
> pas dans le nôtre.
>
> Le résultat est que si l'inflation se révèle conforme au consensus, votre
> marge est plus large — environ 1,4 point par an au lieu de 1. Vous êtes
> couvert dans les deux cas, et vous ne dépendez pas du fait que nous ayons
> raison sur l'inflation. »

### Les leviers, à titre de sensibilité

| Levier | Marge résultante |
|---|---|
| Point de départ (inflation 4 %) | +0,99 % |
| Frais de mandat 0,40 % → 0,25 % | +1,14 % |
| Sans structuration fiscale | +0,84 % |
| Sans structuration du tout | +0,39 % |

> La structuration fiscale n'est donc **pas** la condition de faisabilité du
> mandat, contrairement à ce qu'affirmaient les v1.0 et v1.1. Le mandat tient
> sans elle. Ce qu'elle apporte est ailleurs — à la transmission — et c'est là
> qu'il faut la défendre.

## 5. Contraintes

### 5.1 Horizon

| Poche | Horizon |
|---|---|
| A — Liquidité | 0 – 2 ans |
| B — Cœur patrimonial | 10 – 20 ans |
| C — Transmission | 25 – 30 ans+ |
| D — Satellite | 10 ans+ |

> L'horizon de la poche C excède l'espérance de vie du client : l'actif est
> destiné à être conservé et réinvesti par les héritiers. C'est ce qui autorise
> son budget de risque élevé.

### 5.2 Contraintes ESG — exclusions sectorielles

| Secteur exclu | Seuil de chiffre d'affaires | Périmètre |
|---|---|---|
| Tabac | Production : 0 % — Distribution : 5 % | Toutes poches |
| Armement | Armes controversées : 0 % — Armement conventionnel : 5 % | Toutes poches |
| Charbon thermique | Extraction et production d'électricité : 5 % | Toutes poches |

**Implication :** l'univers investissable **et le benchmark** sont restreints
aux indices filtrés (séries SRI / ESG Screened). Un benchmark non filtré
contredirait le mandat et rendrait la mesure de performance non pertinente.

### 5.3 Contraintes réglementaires
- Résident français retail → **univers UCITS exclusivement** en détention directe
  (règlement PRIIPs : les fonds domiciliés aux États-Unis sont inaccessibles)
- Exception : le fonds d'assurance spécialisé logé dans un contrat luxembourgeois
  élargit l'univers éligible (§7)

### 5.4 Contraintes de liquidité
- Poche A : liquidité quotidienne obligatoire
- Poches B et C : minimum 80 % en actifs à liquidité quotidienne
- Actifs illiquides (private assets) : plafond 15 % du total, poche C uniquement

### 5.5 Contraintes de concentration

| Règle | Plafond |
|---|---|
| Ligne individuelle | 10 % |
| Classe d'actifs unique | 40 % |
| Actifs de croissance (actions + assimilés) | 60 % |
| Crypto-actifs | **2 %** |
| Émetteur unique (hors dette souveraine core) | 5 % |

---

## 6. Politique d'investissement

### 6.1 Architecture en poches

| Poche | Montant | % | Horizon | Vol. cible | Enveloppe |
|---|---|---|---|---|---|
| A — Liquidité | 10 M€ | 10 % | 0-2 ans | < 1 % | Compte-titres / dépôts |
| B — Cœur patrimonial | 58 M€ | 58 % | 10-20 ans | ~7 % | Assurance-vie LUX |
| C — Transmission | 30 M€ | 30 % | 25-30 ans | ~12 % | AV LUX + démembrement |
| D — Satellite | 2 M€ | 2 % | 10 ans+ | ~50 % | Compartiment dédié |

### 6.2 Poche A — spécification détaillée

| Paramètre | Décision | Justification |
|---|---|---|
| Devise | **EUR 100 %** | Devise de la dépense. Le risque de change sur un engagement daté et certain n'est pas rémunéré. |
| Duration | **6 – 12 mois** | Adossement au calendrier de décaissement |
| Support | Fonds monétaires haute qualité + dette souveraine européenne courte, échelonnée | Liquidité quotidienne, risque de crédit minimal |
| Rendement attendu | ~2,2 % | Proche du taux €STR |

> Si une fraction du besoin de liquidité est libellée en devise étrangère,
> la poche est ventilée à l'identique. **Règle : la devise de la poche de
> liquidité est celle de la dépense, jamais celle de l'opportunité.**

### 6.3 Allocation stratégique

*Issue de l'optimisation — `scripts/optimize_saa.py`, validée sur 21,8 ans.*

| Classe d'actifs | Poids | Écart vs indicatif | Rôle |
|---|---|---|---|
| Actions développées | 26 % | −4 pts | Moteur de performance |
| Actions émergentes | 12 % | +4 pts | Valorisation d'entrée — **plafonné** |
| Infrastructure cotée | 10 % | +3 pts | Revenus indexés — **plafonné** |
| Crypto | 2 % | — | Satellite figé |
| **Actifs de croissance** | **50 %** | | |
| Obligations indexées | 14 % | +4 pts | Seule classe à répercussion intégrale |
| Souverain EUR | 8 % | −2 pts | Couverture récession — **plancher** |
| Crédit IG EUR | 8 % | — | Portage |
| **Obligataire** | **30 %** | | |
| Or | 6 % | −3 pts | Décorrélation — **plancher** |
| Alternatifs | 4 % | −2 pts | Matières premières diversifiées |
| **Actifs réels** | **10 %** | | |
| Monétaire + souverain court | 10 % | — | Poche A |

**Résultats :** rendement attendu **5,98 %**, volatilité **9,86 %**,
marge **+1,13 %**, drawdown P90 **12,0 %** (validé par simulation sur 21,8 ans).

### 6.3 bis Ce que l'optimisation a produit, et pourquoi nous ne l'avons pas suivie

L'optimisation libre donne une allocation mathématiquement optimale et
pratiquement inutilisable :

| Classe | Libre | Retenu |
|---|---|---|
| Infrastructure | **27,8 %** | 10 % |
| Actions émergentes | 20,9 % | 12 % |
| Actions développées | **7,1 %** | 26 % |
| Or | **0,8 %** | 6 % |
| Souverain EUR | **0,0 %** | 8 % |

Chacune de ces décisions est correcte **au regard des données fournies**, et
fausse au regard du mandat. Les contraintes de second niveau encodent des
risques que la matrice de covariance ne peut pas voir :

| Contrainte | Ce qu'elle achète |
|---|---|
| Infrastructure ≤ 10 % | Un seul secteur ; le support filtré ESG a 3,1 ans et une capacité limitée. Risque de concentration **et** d'exécution. |
| Or ≥ 6 % | Seule brique dont la corrélation aux actions **baisse** sous stress (0,07 → −0,07 en 2022). Une covariance pleine période efface ce comportement. |
| Souverain EUR ≥ 8 % | Nos hypothèses sont calées sur **un seul régime**. Elles ne tarifient pas la récession — seul scénario où le souverain protège. Le plancher achète une assurance que le modèle ne sait pas valoriser. |
| Actions développées ≥ 20 % | Liquidité et capacité pour un mandat de 100 M€. |
| Crypto = 2 % | Décision de **gouvernance** client, pas une sortie d'optimisation. |

> **À dire au client :** « L'optimiseur nous a dit où nos hypothèses poussent.
> Notre travail était de décider ce que nos hypothèses ne pouvaient pas voir. »

Effet mesurable des contraintes : l'instabilité moyenne des poids entre
tirages passe de **3,8 % à 2,3 %**. Le portefeuille contraint est non
seulement plus prudent, il est plus **reproductible**.

### 6.4 Politique de couverture de change

| Classe d'actifs | Ratio de couverture | Justification |
|---|---|---|
| Obligations internationales | **100 %** | La volatilité de change (8-10 %) excède celle de l'actif (4-5 %) : non couvert, l'actif défensif devient un actif risqué |
| Actions développées hors zone euro | **30 – 50 %** | Le dollar s'apprécie en régime de stress : l'exposition résiduelle amortit les drawdowns |
| Actions émergentes | **0 %** | Couverture coûteuse ; la devise participe au moteur de performance |
| Or | **0 %** | Couvrir annulerait sa fonction de réserve de valeur |

> **Réponse à l'inquiétude simultanée euro / dollar du client :** la stratégie
> n'est pas d'arbitrer une devise contre l'autre, mais de réduire la dépendance
> aux deux — exposition résiduelle CHF et JPY, or, actifs réels.

---

## 7. Structuration fiscale et patrimoniale

### 7.1 Enveloppes retenues

| Enveloppe | Montant indicatif | Rôle |
|---|---|---|
| Assurance-vie luxembourgeoise | ~70 M€ | Report d'imposition, régime de transmission, super-privilège, multi-devises, univers élargi (FAS) |
| Compte-titres ordinaire | ~28 M€ | Poche de liquidité, ETF capitalisants faible rotation |
| PEA (×2, couple) | 0,3 M€ | Marginal mais sans coût |
| Contrat de capitalisation | à l'étude | Support de donation démembrée |

### 7.2 Règle d'asset location

```
→  Assurance-vie :   obligations à coupon élevé, haut rendement, alternatifs,
                     stratégies à forte rotation, supports distribuants
                     (fiscalement coûteux ailleurs, neutralisés ici)

→  Compte-titres :   ETF actions capitalisants, faible rotation
                     (aucun fait générateur avant cession)
```

### 7.3 Règles au niveau de l'instrument
- **Supports capitalisants exclusivement** hors assurance-vie
- **Domiciliation irlandaise** pour toute exposition actions américaines
  (retenue à la source ramenée de 30 % à 15 % par convention fiscale : ~22 bps/an)
- Éviter les structures à étages générant une retenue à la source non récupérable

### 7.4 Calendrier de transmission indicatif

| Échéance | Opération | Objet |
|---|---|---|
| **T0 — avant le 61e anniversaire** | Donation-partage en nue-propriété | Barème art. 669 CGI à **50 %** au lieu de 60 % après 61 ans |
| T0 | Versements en assurance-vie | Régime art. 990 I — fenêtre ouverte jusqu'à 70 ans |
| T0 | Abattements 100 k€ × 2 parents × 2 enfants | Démarrage du compteur de 15 ans |
| T + 15 ans | Renouvellement des abattements | Second cycle |
| Revue annuelle | Ajustement | Selon valorisation et situation familiale |

> **Point de calendrier critique.** Le passage de la tranche d'âge à 61 ans
> fait passer la valeur taxable de la nue-propriété de 50 % à 60 %. Toute
> donation démembrée doit être réalisée **avant le prochain anniversaire**.

> **Réserve.** L'ensemble du volet fiscal et successoral doit être validé par
> un notaire et un avocat fiscaliste avant mise en œuvre. Le présent document
> définit la stratégie patrimoniale ; il ne se substitue pas à un conseil
> juridique. Le régime matrimonial et les droits du conjoint survivant
> nécessitent un traitement dédié non couvert ici.

---

## 8. Benchmark

Benchmark hybride composite, dérivé de l'allocation stratégique.
**Spécification complète : document 03.**

Critères de validité :
1. Investissable — chaque composant réplicable par ETF
2. Réplicable — pondérations publiques, règles de rebalancement écrites
3. Cohérent en devise — libellé EUR, politique de couverture identique
4. Cohérent en ESG — indices filtrés

Double référence retenue :
- **Relative** — le benchmark composite (mesure la valeur ajoutée de gestion)
- **Absolue** — inflation + 0 % net (mesure l'atteinte de l'objectif client)

---

## 9. Gouvernance

### 9.1 Rebalancement
Par **bandes de tolérance de ± 3 points** autour des poids cibles.
Pas de rebalancement calendaire systématique — réduit les frais et la
matérialisation d'impôt, et impose une discipline contracyclique.

### 9.2 Bandes d'allocation tactique

| Classe d'actifs | Cible | Min | Max |
|---|---|---|---|
| Actifs de croissance | 50 % | 40 % | 60 % |
| Obligations | 30 % | 22 % | 38 % |
| Actifs réels (or, infra) | 15 % | 10 % | 20 % |
| Liquidités | 5 % | 2 % | 15 % |

### 9.3 Calendrier de revue

| Fréquence | Objet |
|---|---|
| Mensuelle | Reporting — performance, risque, suivi du drawdown vs 15 % |
| Trimestrielle | Revue tactique, respect des bandes |
| Annuelle | Révision de l'IPS, hypothèses de marché, calendrier de transmission |
| **Déclenchée** | **Drawdown ≥ 10 %** (2/3 du budget de risque) — revue exceptionnelle avec plan d'action |

---

## 10. Synthèse des paramètres

```
Actifs                        100 000 000 €
Besoin de liquidité            10 000 000 €   (0-2 ans, EUR)
Inflation cible                       4,00 %
Rendement brut requis                 4,85 %   (inflation client 4 %)
Rendement brut attendu                5,84 %   marge  +0,99 %
  en regime consensus (2 %)           4,25 %   seuil 2,85 %, marge +1,40 %
Volatilité cible                      9,9 %
Drawdown maximum                     15,0 %   (12 mois, P < 10 %)
  P90 mesuré                         13,3 %   1,7 pt de marge
  pire cas observé (2008)            26,3 %   à dire au client
Actifs de croissance                    47 %
Poche liquidité                         10 %   (5 % monétaire + 5 % souverain court)
Plafond crypto                           2 %   coût mesuré : +0,7 pt de drawdown
Horizon poche longue                30 ans
Rebalancement                    bandes ± 3 pts
```

---

## 11. Journal de révision

**v1.2 — hypothèses de marché.** Construction des Capital Market Assumptions
(`core/cma.py`, `scripts/estimate_cma.py`). Trois apports et deux corrections :

*Apports.*
1. Rendements attendus par blocs constitutifs, chaque entrée étiquetée
   **mesurée / marché / hypothèse**. Le taux monétaire EUR (2,05 %) est mesuré
   sur XEON.DE, pas supposé.
2. Volatilités et corrélations estimées sur les séries nettoyées.
3. Coefficients de répercussion de l'inflation par classe d'actifs — ce qui
   rend le jeu d'hypothèses capable de répondre au mandat, qui est un mandat
   de protection contre l'inflation.

*Corrections.*
4. **Incohérence de régime d'inflation** — voir §4.4. La marge passe de
   −0,09 % à **+0,99 %**.
5. **Erreur statistique sur les corrélations de stress.** La première version
   les estimait sur le décile des jours où la moyenne des actifs était la plus
   basse. Or conditionner sur une **somme** biaise mécaniquement à la baisse
   les corrélations entre ses composantes : le tableau montrait des
   corrélations qui *diminuent* en crise, l'inverse du phénomène connu.
   Remplacé par des **périodes de crise définies a priori**. Le résultat est
   alors conforme : en 2022, le crédit passe de 0,27 à 0,37 face aux actions,
   l'infrastructure de 0,43 à 0,57 — et **l'or de 0,07 à −0,07**, seule brique
   dont la diversification s'améliore sous stress.

*Limite assumée.* La fenêtre commune aux instruments retenus est de 6,2 ans :
elle couvre 2022 mais ni 2008 ni 2011. La volatilité mesurée dessus (7,8 %)
**sous-estime** le risque ; la référence retenue pour le budget de risque reste
l'estimation sur 21,8 ans (9,9 %).



**v1.1 — 17 septembre 2026.** Passe de validation empirique. Quatre corrections :

1. **Ratio drawdown/volatilité** — 1,9 postulé → 1,35 mesuré sur 21,8 ans.
   L'ancienne valeur sous-allouait le risque d'environ dix points d'actions.
2. **Cohérence poche A / SAA** — les 5 points manquants sont explicités en
   souverain court. Assertion de contrôle ajoutée dans `core/ips.py`.
3. **Écart fiscal annuel** — 0,85 % → 0,15 % contre un compte-titres bien géré.
   L'argument fiscal est déplacé sur la transmission, où il est solide.
4. **Marge du mandat** — +0,10 % → −0,09 %. Le mandat est au bord de la
   faisabilité ; l'écart se referme par la négociation des frais.

**Méthode de backtest — décision.** Les ETF filtrés ESG datent de 2016-2020 et
ne couvrent pas 2008. Deux options écartées, une retenue :

| Option | Écartée / retenue |
|---|---|
| Backtester sur les ETF | Écartée — 8 ans d'historique, ne couvre aucune crise majeure |
| Backtester sur les séries d'indices ESG reconstituées | **Écartée** — ces séries sont rétro-calculées : la méthodologie a été appliquée après coup, et un indice n'est lancé qu'une fois qu'il a montré qu'il fonctionnait. Le biais flatte systématiquement l'ESG |
| Backtester sur indices larges non filtrés, et mesurer séparément l'écart de suivi ESG sur 2017-2026 | **Retenue** — c'est la seule option sans biais de sélection rétrospective |

Formulation à retenir devant le client : *« Nous vous montrons le comportement
de la stratégie sur vingt ans, reconstitué à partir d'indices larges. L'effet
du filtre éthique, nous le mesurons séparément sur la période où il existe
réellement — depuis 2017. Nous ne vous présentons pas un historique 2008 d'un
filtre qui n'existait pas en 2008. »*
