---
titre: Backtest et mesures de risque
source: core/backtests.py, scripts/fetch_inflation_longue.py
maj: 2026-09-21
---

# Backtest et mesures de risque

## En une phrase

**On rejoue le portefeuille retenu jour par jour de 2006 à aujourd'hui, pour
voir non pas s'il a gagné, mais combien de temps il est resté dans le
rouge.**

## L'avertissement à dire en premier

> [!warning] Ce rejeu ne prouve pas que la limite tient
> Les vingt années de données sont **exactement celles qui ont servi à
> construire le portefeuille** : l'étape 4 a cherché une répartition qui ne
> perde jamais plus de 14 % **sur cette période**.
>
> Qu'elle n'y perde pas plus de 14 % n'est donc pas un résultat, c'est une
> conséquence mécanique de la façon dont on l'a construite. Ça ne dit rien
> de la prochaine crise.
>
> **Alors à quoi sert le rejeu ?** À mesurer ce que l'optimisation n'a pas
> regardé : la **durée** des baisses, et la fréquence des mauvaises années.
> Ces deux choses-là ne sont contraintes nulle part, donc elles sont
> informatives.

C'est le genre de phrase qu'il vaut mieux dire soi-même. Si le jury la
trouve avant toi, tu passes pour quelqu'un qui n'a pas vu le problème.

## 1. La mesure de base : la baisse depuis le plus haut

À chaque instant, on compare la valeur du portefeuille à son **meilleur
niveau atteint depuis le début**. L'écart, c'est ce que le client verrait
sur son relevé s'il comparait à son meilleur souvenir.

> [!note] Le « meilleur niveau » porte sur toute l'histoire, pas sur une fenêtre
> Conséquence concrète : en 2011, la perte se mesure encore depuis le sommet
> de **2007**, parce que le portefeuille n'y était pas revenu entre-temps.
>
> C'est la lecture la plus dure possible, et c'est volontaire. Une mesure
> glissante ferait disparaître les crises longues.

## 2. Le vrai enseignement : la durée, pas la profondeur

Pour chaque baisse de plus de 5 %, on note quatre choses : la date du
sommet, la date du point bas, la perte, et **la date du retour au sommet**.

C'est la dernière qui est instructive, parce que c'est elle que vit le
client.

| Mesure | Valeur |
|---|---|
| Temps passé à plus de 1 % sous son plus haut | **53 %** |
| Temps passé à plus de 5 % | 17 % |
| Temps passé à plus de 10 % | 4 % |
| Plus longue période sous l'eau | **32 mois** (2022) |

**Comment le dire au client :** la plupart du temps, votre patrimoine est un
peu en dessous de son meilleur niveau — c'est normal, c'est la vie d'un
portefeuille investi. Une fois sur six environ, il en est à plus de 5 %. Les
pertes proches de la limite sont rares et brèves.

> [!important] 2022 est la crise la plus instructive du lot
> **32 mois sous l'eau, pour une baisse pourtant moins profonde qu'en 2008.**
>
> Pourquoi ? Parce que les obligations, qui font les deux tiers du
> portefeuille, **ont baissé en même temps que les actions**. Dans une
> récession classique (2008, 2011), les obligations montent quand les
> actions chutent : c'est ce qui amortit. Dans un choc d'inflation, les deux
> baissent ensemble et rien n'amortit.
>
> C'est exactement le régime que redoute M. Lauren. Et c'est l'argument qui
> disqualifie un 60/40 classique pour ce mandat : le protéger avec un 60/40
> reviendrait à le laisser sans protection dans le seul scénario qu'il
> craint.

## 3. À quoi ressemble une mauvaise année

On regarde les rendements sur douze mois glissants, à chaque fin de mois —
228 « années » au total.

Deux chiffres, et il faut bien comprendre la différence :

- **« La perte dépassée une année sur vingt »** : on classe les 228 années
  de la pire à la meilleure, on regarde la 12ᵉ. En dessous, on est dans les
  5 % les plus mauvaises. **−6,5 %.**
- **« La perte moyenne de ces années-là »** : quand on est dans ces 5 %,
  combien perd-on en moyenne ? **−8,5 %.**

> [!tip] Pourquoi les deux, et pas seulement le premier
> Le premier dit **à partir de quand** on est dans les mauvaises années. Il
> ne dit rien de ce qui se passe une fois qu'on y est. Le second dit
> **de combien** ça tombe.
>
> C'est toute la différence entre VaR et CVaR, et c'est ce qui disqualifie
> la variante « croissance » de [[05 - Optimisation sous contrainte de perte]] :
> elle respectait le premier chiffre et catastrophait le second.

| Mesure | Valeur |
|---|---|
| Perte dépassée une année sur vingt | −6,5 % |
| Perte moyenne ces années-là | −8,5 % |
| Pire année | −11,4 % |
| Part des années en perte | 18 % |

**Le point de lecture.** La pire *année* fait −11,4 %, alors que la pire
*baisse* atteint −14 %. L'écart vient des baisses longues : en 2008 comme en
2022, la perte s'est accumulée sur plus d'un an. **C'est précisément pour
cela que la limite du mandat a été mesurée depuis le plus haut et non sur
douze mois** : une limite annuelle aurait laissé passer ces baisses.

> [!danger] Ce que valent vraiment ces chiffres
> Les 228 années glissantes **se recouvrent** : deux années qui commencent à
> un mois d'écart partagent onze mois sur douze. Ce ne sont donc pas 228
> observations indépendantes — il y en a de l'ordre de vingt, et seulement
> **sept épisodes de baisse distincts**.
>
> Un seuil « une année sur vingt » calculé là-dessus repose sur une poignée
> d'observations. Les chiffres sont descriptifs, pas prédictifs.

## 4. La correction du 21/09/2026 : juger dans le bon monde

> [!bug] L'erreur qu'il y avait
> Le rendement réalisé (4,47 % par an) était comparé au **seuil de 4 % de
> l'énoncé**. Sauf que ce 4 % décrit un monde où l'inflation est de 4 % — et
> la période rejouée n'a pas vécu ça du tout.
>
> C'est le même piège que celui de J.P. Morgan dans
> [[03 - Rendements espérés]] : **juger un résultat obtenu dans un monde
> avec l'exigence d'un autre monde.** Et ici il jouait **contre** le
> portefeuille.

### Ce qu'on a mesuré

On a pris l'indice des prix de la zone euro (FRED, IPCH) sur la **fenêtre
exacte du rejeu**, et on a calculé de combien les prix ont monté.

> [!tip] Le piège évité dans ce calcul
> On ne fait **pas** la moyenne des inflations annuelles. Elle surpondère les
> années extrêmes — 2022 à +9,2 % — et ne redonne pas l'érosion réelle du
> pouvoir d'achat.
>
> On calcule le **taux composé entre le début et la fin** : de combien les
> prix ont-ils monté au total, et quel taux annuel régulier donnerait le
> même résultat. C'est la seule mesure homogène à un rendement annualisé.

| | Valeur |
|---|---|
| Fenêtre | octobre 2006 → août 2026 (19,8 ans) |
| Hausse totale des prix | **53,5 %** |
| Soit par an | **2,18 %** |
| Rendement du portefeuille | 4,47 % |
| **Gain de pouvoir d'achat** | **+2,29 % par an** |

**L'objectif du client a donc été tenu largement**, et non de justesse comme
le laissait croire la comparaison au seuil de 4 %.

### Le sous-produit inattendu, et il est bon à prendre

| Sur les… | Inflation zone euro |
|---|---|
| 20 dernières années | 2,18 % par an |
| 10 dernières années | 2,88 % par an |
| **5 dernières années** | **4,31 % par an** |

L'hypothèse de 4 % de M. Lauren n'est donc **pas une crainte
disproportionnée** : c'est presque exactement ce que la zone euro vient de
vivre. **Il n'extrapole pas une peur, il extrapole son vécu.**

C'est une façon nettement plus juste — et plus respectueuse — de présenter
son hypothèse que « c'est le double de la cible de la BCE ».

## 5. Les années qui n'atteignent pas l'objectif

Deux mesures, et il faut donner la bonne :

| Seuil de comparaison | Années glissantes en dessous |
|---|---|
| L'inflation réellement constatée (2,18 %) | **29 %** |
| Les 4 % de l'énoncé | 40,8 % |

> [!note] Le chiffre qu'il vaut mieux donner soi-même
> Près d'une année sur quatre n'a pas battu l'inflation de son époque.
>
> C'est normal, et il faut le formuler ainsi : **préserver le pouvoir
> d'achat est un objectif de moyenne longue, pas une garantie annuelle.**
> Aucun portefeuille tenu à 15 % de perte maximum ne peut promettre le
> contraire — et n'importe qui peut recalculer ce chiffre à partir des
> données du dossier.

## 6. Ce que le rejeu ne sait pas faire

- **Les remplaçants d'avant 2018.** Plusieurs supports n'existaient pas sur
  toute la période et sont représentés par un indice proche. Certains
  **flattent** : les indexées d'avant 2009 sont représentées par un emprunt
  d'État classique, qui a mieux tenu en 2008. C'est la raison d'être de la
  marge de prudence à 14 %.
- **Les actions européennes sont mesurées sur l'indice**, pas sur les 30
  titres, pour ne pas importer le passé flatteur de
  [[04 - Notation des actions - 5 piliers]].
- **Le crédit est reconstitué** avant 2016 à partir des écarts américains,
  avec une corrélation faible : c'est la ligne la moins bien mesurée.
- **Aucun frais de transaction.** Rééquilibrer 100 M€ tous les mois coûterait
  quelques points de base par an, non déduits du rejeu.

→ Amont : [[05 - Optimisation sous contrainte de perte]] · Index : [[00 - Index des modèles]]
