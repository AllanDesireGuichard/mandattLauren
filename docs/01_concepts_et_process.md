# Concepts & process — support de préparation orale
**Dossier Lauren — mandat de gestion privée** · v1.1

> **Révision du 17 septembre 2026.** Quatre arguments de la v1.0 se sont
> révélés faux à la validation empirique et sont corrigés ci-dessous :
> le ratio drawdown/volatilité (§5), l'écart fiscal annuel (§4), la marge du
> mandat (§5) et l'apport du block bootstrap (§6). Chiffres de référence à
> jour dans `core/ips.py` ; version rédigée et publiée dans
> `outputs/argumentaire.html`.

> Ce document a un seul but : pouvoir défendre chaque décision du portefeuille
> à l'oral, devant le client, sans notes. Chaque concept suit le même format :
>
> - **L'idée** — la formulation en une phrase
> - **Au client** — ce que je dis réellement en rendez-vous
> - **Si on me challenge** — la réponse à l'objection attendue
>
> Règle de langage : aucun jargon sans traduction immédiate. Un client qui a
> vendu une startup tech est intelligent mais n'est pas gérant d'actifs.

---

## Hypothèse de travail

Le patrimoine est **déjà en euros** : 100 M€, dont 10 M€ de besoin de liquidité.
La décision de conversion du produit de cession est donc hors périmètre.

Ce qui reste vivant, et qui est une décision d'allocation à part entière :
**la couverture de change des actifs étrangers** que nous achetons (actions
américaines, obligations internationales). Voir §10.

---

# PARTIE I — LES FONDATIONS

## 1. Pourquoi nous ne construisons pas UN portefeuille, mais quatre

**L'idée.** Un patrimoine n'a pas un objectif, il en a plusieurs, avec des
horizons différents. Un seul portefeuille moyenne ces objectifs et les sert
tous mal.

**Au client.**
> « Monsieur Lauren, vos 100 millions ne servent pas tous la même chose.
> 10 millions doivent être disponibles dans deux ans : cet argent n'a pas le
> droit de baisser, point. À l'inverse, la part qui ira à vos enfants sera
> investie pendant trente ans : lui interdire de prendre du risque, ce serait
> lui interdire de performer.
>
> Si je mélange les deux dans un portefeuille unique, j'obtiens un compromis
> qui ne convient à aucun des deux : trop risqué pour vos deux ans, trop timide
> pour vos trente ans. Donc nous séparons. Quatre poches, quatre horizons,
> quatre budgets de risque. »

| Poche | Montant | Horizon | Rôle | Risque |
|---|---|---|---|---|
| **A — Liquidité** | 10 M€ | 0-2 ans | Le projet financé | Quasi nul |
| **B — Cœur patrimonial** | ~58 M€ | 10-20 ans | Votre niveau de vie, protégé de l'inflation | Modéré |
| **C — Transmission** | ~30 M€ | 25-30 ans | Ce qui ira aux enfants | Élevé, assumé |
| **D — Satellite** | ~2 M€ | 10 ans+ | Convictions, dont crypto | Très élevé, plafonné |

**Si on me challenge** — *« C'est de la complexité pour faire joli. »*
> Non, c'est ce qui rend l'objectif atteignable. La contrainte de 15 % s'applique
> au total. La poche C peut donc porter beaucoup plus de risque qu'elle n'en
> porterait seule, parce qu'elle est diluée par les poches A et B. C'est
> précisément cette respiration qui nous permet d'aller chercher le rendement
> dont vous avez besoin. Sans découpage, nous n'y arrivons pas.

> **Nom technique** (à ne pas prononcer devant le client) : *goal-based investing*,
> ou allocation par objectifs. C'est aussi la logique de l'*Asset-Liability
> Management* des institutionnels : on adosse des actifs à des engagements datés.

---

## 2. L'horizon d'investissement n'est pas l'âge du client

**L'idée.** M. Lauren a 60 ans. Son portefeuille, lui, a 30 ans — parce que
l'argent ne s'arrête pas à lui.

**Au client.**
> « Beaucoup de banquiers vous diraient : vous avez 60 ans, donc horizon
> 20 ans, donc portefeuille prudent. Je crois que c'est une erreur d'analyse.
>
> Vous nous avez dit vouloir transmettre progressivement à vos enfants. Cet
> argent-là ne sera pas consommé à votre décès : il continuera d'être investi
> par eux. L'horizon réel de cette poche, c'est votre espérance de vie **plus**
> la leur. Trente ans, au bas mot.
>
> Et c'est une très bonne nouvelle : le temps est le seul ingrédient qui
> transforme le risque en rendement. Nous avons le droit d'en prendre. »

**Si on me challenge** — *« Mais si j'ai besoin de tout d'un coup ? »*
> C'est exactement le rôle de la poche A. Elle est dimensionnée pour cela, et
> nous pouvons la redimensionner à tout moment. Le long terme de la poche C
> n'est pas un enfermement : c'est une décision que nous prenons ensemble et
> que nous pouvons réviser chaque année.

---

## 3. La tension centrale du dossier : « dynamique » vs « perte maximum 15 % »

**C'est le point le plus important du pitch. Le traiter en premier, frontalement.
Ne jamais laisser le client le découvrir seul.**

**L'idée.** Le client demande deux choses qui se contredisent partiellement.
Notre valeur ajoutée est de le dire, puis de résoudre.

**Au client.**
> « Vous nous avez dit deux choses. Un : votre profil de risque est dynamique.
> Deux : vous ne voulez pas perdre plus de 15 %.
>
> Je dois vous dire honnêtement que ces deux phrases ne sont pas tout à fait
> compatibles. Un portefeuille dynamique standard, dans notre industrie, c'est
> environ 13 % de volatilité annuelle. Et un portefeuille à 13 % de volatilité,
> en 2008, a perdu 35 %. En 2022, 20 %. Si nous vous vendions un profil
> dynamique classique, nous vous exposerions à des pertes de plus du double de
> ce que vous acceptez.
>
> Donc voilà notre lecture : entre les deux, **c'est la contrainte de 15 % qui
> commande**. Le mot "dynamique" décrit votre état d'esprit — vous n'êtes pas
> un client obligataire, vous acceptez la volatilité, vous ne paniquerez pas.
> Nous en tenons compte. Mais c'est le chiffre qui pilote l'allocation, pas
> l'adjectif. »

**Si on me challenge** — *« Alors vous me classez prudent ? Je ne suis pas un
retraité. »*
> Non. Un profil prudent, c'est 3 à 4 % de volatilité et un rendement qui ne
> couvre pas l'inflation. Nous vous positionnons à environ 8 %, soit le haut de
> la fourchette équilibrée. Ce qui vous différencie d'un client prudent, ce
> n'est pas le niveau de risque global — c'est **où** nous le plaçons : dans la
> poche à 30 ans, pas dans celle à 2 ans. Nous prenons du risque là où le temps
> le rémunère.

### La formalisation à retenir

La contrainte « 15 % » est floue dans l'énoncé. **Nous la définissons, et nous
expliquons pourquoi.**

> **Définition retenue :** perte maximale de pic à creux *(maximum drawdown)*
> sur toute fenêtre de 12 mois glissants, mesurée au niveau consolidé, en euros,
> avec une probabilité de dépassement inférieure à 10 %.

Trois choix, trois justifications à savoir défendre :

1. **Drawdown plutôt que VaR** — le drawdown est ce que le client vit réellement :
   l'écart entre le meilleur relevé qu'il a reçu et le pire. La VaR est un
   concept de salle de marché, pas de rendez-vous client. Le drawdown est aussi
   la mesure la plus *contraignante* : la choisir, c'est être conservateur.
2. **Au niveau consolidé** — appliquer les 15 % ligne à ligne interdirait toute
   action. C'est le patrimoine total qui compte.
3. **Probabilité < 10 % plutôt que « jamais »** — aucun gérant honnête ne peut
   garantir un plafond absolu. Promettre « jamais plus de 15 % » serait
   malhonnête. Dire « moins d'une année sur dix » est défendable et vérifiable.

**Au client, sur ce dernier point :**
> « Je ne vais pas vous promettre que vous ne perdrez jamais 15 %. Personne ne
> peut le promettre, et si on vous le promet, méfiez-vous. Ce que je vous dis,
> c'est que nous construisons le portefeuille pour que cela arrive moins d'une
> année sur dix, et nous vous montrerons les simulations qui le démontrent. »

---

## 4. « Protéger contre 4 % d'inflation » ne veut pas dire « viser 4 % »

**L'idée.** L'objectif est un rendement **net**. Le portefeuille doit donc
produire nettement plus en brut. Beaucoup de concurrents oublieront de le dire.

**Au client.**
> « Votre objectif est de préserver votre pouvoir d'achat face à une inflation
> de 4 %. Attention au piège : cela ne veut pas dire viser 4 % de performance.
>
> Entre la performance brute du portefeuille et ce qui reste dans votre poche,
> il y a deux prélèvements : nos frais, et l'impôt. Si je vise 4 % brut, vous
> vous appauvrissez chaque année. »

### Le calcul, à savoir refaire au tableau

```
Objectif net réel                              4,00 %   (inflation)
+ Frais totaux (mandat + instruments)          0,55 %
+ Friction fiscale annuelle
      structure optimisée                      0,30 %   →  4,85 %
      compte-titres BIEN GÉRÉ                  0,45 %   →  5,00 %
      compte-titres négligent (distribuants)   0,90 %   →  5,45 %
```

> **Objectif de rendement brut retenu : 4,85 % par an.**

> **CORRIGÉ v1.1.** La v1.0 opposait 0,35 % à 1,20 % et en tirait un écart de
> 0,85 %. C'était un homme de paille : personne de compétent ne met des fonds
> distribuants dans un compte-titres. L'écart réel contre un compte-titres
> **bien géré** est de **15 points de base**. En revanche, l'écart entre un
> compte-titres bien géré et un compte-titres négligent est de **60 points de
> base** — cet argument-là est solide, et gratuit.
>
> La valeur du contrat luxembourgeois est à la **transmission** (20 % contre
> 45 %) et dans l'accès, pas dans la friction annuelle. Reconstruire
> l'argument sur ce terrain-là : les chiffres y sont massifs.

**Au client — et c'est un moment fort du rendez-vous :**
> « Regardez ces deux chiffres. Avec une structuration fiscale correcte, votre
> portefeuille doit produire 5,0 % par an. Sans elle, il doit produire 5,8 %.
>
> Huit dixièmes de point, cela paraît peu. En réalité, c'est énorme : pour
> gagner 0,8 % de plus chaque année, je dois augmenter votre exposition
> actions d'environ quinze points. C'est-à-dire vous exposer à des pertes
> bien supérieures à vos 15 %.
>
> Autrement dit : **la structuration fiscale n'est pas un sujet de comptable,
> c'est ce qui rend votre objectif atteignable sans dépasser votre contrainte
> de risque.** C'est la première décision du dossier, avant même de choisir
> le moindre fonds. »

**Si on me challenge** — *« 0,55 % de frais, c'est cher. »*
> C'est le tarif d'un mandat institutionnel sur cette taille d'actifs, et il
> inclut les frais des instruments sous-jacents. Nous utilisons des supports
> indiciels dont le coût moyen est de 0,15 %, pas des fonds maison à 1,5 %.
> Et ce chiffre est négociable à la baisse en contrepartie d'un engagement
> de durée.

---

# PARTIE II — LA MÉTHODE

## 5. Le budget de risque : comment on passe de « 15 % » à une allocation

**L'idée.** Il existe une relation stable entre volatilité annuelle et perte
maximale. C'est elle qui traduit la contrainte du client en chiffres de gérant.

**La règle empirique :**
> **CORRIGÉ — mesuré, plus postulé.** 21,8 ans de données quotidiennes en EUR
> (2004-2026), `scripts/estimate_dd_ratio.py` et `validate_saa_risk.py`.

```
Ratio mesuré : 1,35   (et non 1,9)

Actifs croissance    vol     DD P90    pire     2008
        38 %        8,1 %    10,7 %   20,7 %   21,3 %
        42 %        9,0 %    12,0 %   23,0 %   23,8 %
        47 %        9,9 %    13,3 %   25,3 %   26,3 %   ← retenu
        51 %       10,8 %    14,6 %   27,6 %   28,7 %
```

Le ratio n'est pas constant : 1,81 à 20 % d'actions, 1,33 à 80 %. Le 1,9 de la
v1.0 était trop conservateur — il sous-allouait d'environ dix points d'actions.

**À NE JAMAIS OMETTRE DEVANT LE CLIENT :** le pire cas observé n'est pas 13 %
mais **26 % (2008)**. La contrainte tient « moins d'une année sur dix », pas
« jamais ». Les deux chiffres sur la même slide.

**Au client :**
> « Votre contrainte de 15 % se traduit techniquement par une volatilité cible
> d'environ 8 % sur l'ensemble. C'est le haut d'un profil équilibré. En
> équivalent actions, cela correspond à environ 50 % du portefeuille investi
> en actifs de croissance. »

### La vérification qui boucle le raisonnement

**C'est l'argument le plus solide du pitch. À maîtriser parfaitement.**

```
Rendement brut attendu (47 % de croissance)                  4,76 %
Rendement brut requis                                       4,85 %
                                                           ────────
Marge                                                       −0,09 %

Leviers :  frais de mandat 0,40 % → 0,25 %                  +0,06 %
           risque porté à 51 % de croissance                +0,16 %
                                         (mais DD P90 14,6 %)
```

> **CORRIGÉ v1.1.** La v1.0 annonçait +0,10 %, à partir d'une correspondance
> volatilité/actions fausse : 50 % d'actions ne produisent pas 8 % de
> volatilité mais 10,8 %. La marge réelle est **négative**.
>
> Position corrigée, et plus défendable à l'oral : l'objectif est atteignable
> mais **ne tolère aucun gaspillage** — ce qui donne sa force à l'exigence sur
> les frais, au lieu d'une marge confortable que les chiffres ne montrent pas.

**Au client :**
> « Je vais vous dire quelque chose que mes concurrents ne vous diront pas.
>
> Votre contrainte de risque autorise un portefeuille dont nous attendons
> **4,76 %** par an. Pour couvrir 4 % d'inflation après frais et impôts, il
> vous en faut **4,85 %**. Il manque neuf centièmes de point.
>
> Ce n'est pas un problème, c'est un cadrage : votre objectif est atteignable,
> mais il ne tolère aucun gaspillage. Et cela vous donne un levier immédiat —
> si nous ramenons nos frais de 0,40 % à 0,25 %, l'écart est comblé. Je
> préfère vous le dire ainsi plutôt que de vous vendre une marge confortable
> que les chiffres ne montrent pas. »

---

## 6. Pourquoi l'optimisation classique ne suffit pas

**L'idée.** L'outil standard (Markowitz) raisonne en volatilité. Notre contrainte
est un drawdown. Ce ne sont pas les mêmes mathématiques.

**Le problème, en une phrase :** la volatilité mesure l'amplitude moyenne des
mouvements ; le drawdown dépend de leur **enchaînement**. Douze mois de -1 %
d'affilée, ou six mois de -2 % alternés avec six mois de +2 % : même volatilité,
drawdown radicalement différent.

**Notre boucle de travail :**

```
1.  Black-Litterman      →  intégrer nos vues macro aux rendements d'équilibre
2.  Optimisation         →  frontière efficiente sous contraintes
    moyenne-variance        (ESG, UCITS, poids max, liquidité)
    avec resampling
3.  Sélection            →  3 ou 4 allocations candidates
4.  Block bootstrap      →  10 000 trajectoires réalistes sur 10 ans
5.  Test de contrainte   →  P(drawdown > 15 %) ≤ 10 % ?
6.  Si violée            →  retour en 3, moins de risque
```

**Au client, version courte :**
> « Nous n'optimisons pas une fois. Nous proposons une allocation, nous la
> passons dans dix mille scénarios de marché, nous regardons combien de fois
> elle dépasse vos 15 %, et nous corrigeons jusqu'à ce que la réponse soit
> satisfaisante. Ce n'est pas un calcul, c'est une boucle de validation. »

### Les trois techniques, expliquées simplement

**Black-Litterman** — *comment on intègre nos convictions sans casser le modèle*
> « Le marché reflète le consensus de tous les investisseurs. Notre point de
> départ, c'est ce consensus. Ensuite, nous exprimons nos convictions
> personnelles — par exemple : nous pensons que les actions européennes sont
> plus attractives que ne le dit le consensus — et **avec quel degré de
> confiance**. Le modèle mélange les deux proportionnellement à notre
> confiance. Résultat : nos vues influencent le portefeuille sans le
> déséquilibrer. »

*Pourquoi c'est indispensable ici :* l'optimisation classique, nourrie
directement de nos prévisions, produirait des portefeuilles absurdes — 80 %
sur une seule ligne. Black-Litterman est ce qui rend les vues exploitables.

**Le resampling** — *comment on obtient un portefeuille stable*
> « L'optimisation classique a un défaut connu : elle est hypersensible. Changez
> une prévision de rendement de deux dixièmes de point, et l'allocation
> recommandée bascule complètement. Impossible de défendre un portefeuille dont
> les fondations bougent à ce point. Nous optimisons donc des centaines de fois
> sur des hypothèses légèrement perturbées, et nous retenons la moyenne. On
> obtient un portefeuille plus diversifié et beaucoup plus robuste. »

**Le block bootstrap** — *pourquoi nos simulations sont crédibles*
> « La plupart des simulations tirent des rendements au hasard, mois par mois,
> en supposant une distribution bien sage. Le problème, c'est que les crises ne
> sont pas bien sages : les mauvais mois s'enchaînent. Une simulation naïve
> vous dirait que 2008 était impossible.
>
> Nous procédons autrement : nous rééchantillonnons l'histoire par **blocs** de
> plusieurs mois consécutifs, pour préserver les enchaînements réels.
>
> Mais je dois être franc sur ce que cette technique apporte. Nous l'avons
> testée sur vos données : elle donne des pertes maximales très proches de
> celles observées, parfois même légèrement inférieures. **Elle ne remplace pas
> le relevé historique, elle le recoupe.** »

> **CORRIGÉ.** La v1.0 affirmait que le block bootstrap donnait des estimations
> plus prudentes. Mesuré (blocs de 21 à 252 jours) : il tombe 0 à 0,6 point
> **en dessous** du P90 historique. Il recoupe, il ne durcit pas. La vraie
> queue, c'est 2008 à 26 %.

**Si on me challenge** — *« Vos simulations reposent sur le passé. »*
> Oui, en partie, et c'est une limite réelle. C'est pourquoi nous les complétons
> par des scénarios de stress nommés : 2008, mars 2020, 2011 sur la dette
> européenne, et surtout 2022. Nous vous montrons ce que votre portefeuille
> aurait fait dans chacun. Ce n'est pas une prédiction, c'est un test de
> résistance.

---

## 7. Pourquoi le 60/40 ne suffit plus — l'argument de 2022

**L'idée.** Le portefeuille équilibré traditionnel repose sur une hypothèse
— actions et obligations évoluent en sens inverse — qui a cessé d'être vraie
au moment exact où on en avait besoin.

**Au client :**
> « Le portefeuille classique, 60 % d'actions et 40 % d'obligations, repose sur
> une idée simple : quand les actions baissent, les obligations montent, et
> l'ensemble amortit.
>
> En 2022, cela n'a pas fonctionné. Les actions ont perdu environ 18 %, les
> obligations environ 17 %, en même temps. Un portefeuille équilibré a perdu
> près de 20 %. Pourquoi ? Parce que la cause de la baisse était l'inflation,
> et l'inflation fait mal aux deux classes d'actifs simultanément.
>
> Or c'est précisément votre inquiétude : vous nous demandez de vous protéger
> contre une inflation de 4 %. Vous protéger avec un 60/40 reviendrait à vous
> vendre le seul portefeuille qui échoue dans le scénario que vous craignez. »

**La conséquence pour l'allocation :** il faut de la diversification qui
fonctionne *dans* un régime inflationniste.

| Brique | Ce qu'elle apporte | Ce qu'on en dit |
|---|---|---|
| **Or** | Décorrélé, réserve de valeur, protège contre la défiance monétaire | Répond directement à son inquiétude sur l'euro |
| **Obligations indexées inflation** | Couverture directe du risque cité | Adossement littéral à l'objectif |
| **Infrastructure cotée** | Revenus contractuellement indexés sur l'inflation | Le meilleur actif réel liquide |
| **Stratégies de suivi de tendance** | Historiquement performantes en 2022 | À mentionner, sans jargon |
| **Actions de qualité / pricing power** | Entreprises capables de répercuter l'inflation | La protection inflation par les actions |

**Au client :**
> « Chaque brique du portefeuille répond à une question précise. Je peux vous
> justifier chaque ligne. S'il y en a une que je ne sais pas justifier, elle
> n'a rien à faire dans votre portefeuille. »

---

# PARTIE III — LES DÉCISIONS SPÉCIFIQUES AU DOSSIER

## 8. La poche de liquidité : montant, devise, duration

**L'idée.** 10 M€ à dépenser sous 2 ans, ce n'est pas « du cash ». C'est un
engagement daté qu'on adosse précisément.

**Au client :**
> « Vos 10 millions doivent être disponibles, mais ils n'ont aucune raison de
> dormir. Nous les plaçons ainsi :
>
> - **En euros**, intégralement. C'est la devise dans laquelle vous allez
>   dépenser cet argent. Y ajouter du risque de change pour gagner quelques
>   dixièmes de point serait la définition même de la mauvaise prise de risque :
>   un gain marginal contre un risque sur le capital d'un projet certain.
> - **Duration courte, 6 à 12 mois**, calée sur votre calendrier de dépense.
> - **Support** : fonds monétaires de haute qualité et obligations d'État
>   européennes de maturité courte, échelonnées sur vos échéances.
>
> Cette poche n'a pas vocation à performer. Elle a vocation à être là. »

**Si on me challenge** — *« Pourquoi pas du dollar, si j'ai des dépenses en
dollars ? »*
> Si une partie de la dépense est effectivement en dollars, alors nous plaçons
> exactement cette partie en dollars. La règle est simple : **la devise de la
> poche de liquidité est celle de la dépense, pas celle de l'opportunité.**
> Dites-nous la ventilation et nous calons dessus.

**Si on me challenge** — *« Et si je ne dépense finalement que 6 millions ? »*
> Le reliquat rejoint la poche B au fil de l'eau. Nous révisons le
> dimensionnement à chaque point d'étape.

---

## 9. La couverture de change des actifs étrangers

**L'idée.** Nous partons en euros, mais nous investissons dans le monde entier.
Chaque actif étranger ajoute un risque de devise qui n'est pas rémunéré à
long terme.

**La règle, et ses deux exceptions :**

| Classe d'actifs | Couverture | Pourquoi |
|---|---|---|
| **Obligations internationales** | **~100 %** | Le risque de change (8-10 % de volatilité) écraserait celui de l'obligation (4-5 %). On achèterait de la volatilité de devise déguisée en actif défensif. Absurde. |
| **Actions internationales** | **partielle, 30-50 %** | Le dollar monte quand les marchés paniquent. Le laisser partiellement nu, c'est acheter une assurance gratuite contre les krachs. |
| **Or** | **0 %** | L'or coté en dollars est une réserve de valeur. Le couvrir reviendrait à annuler une partie de sa fonction. |
| **Actions émergentes** | **0 %** | Couverture coûteuse, et la devise fait partie du moteur de performance. |

**Au client :**
> « Une règle simple : on couvre ce qui est là pour la sécurité, on laisse
> respirer ce qui est là pour la performance.
>
> Vos obligations sont là pour amortir les chocs. Si je les laisse exposées au
> dollar, elles deviennent plus volatiles que les actions que je cherchais à
> compenser. Je les couvre donc intégralement.
>
> Vos actions américaines, c'est différent. Historiquement, lorsque les marchés
> chutent, le dollar monte : les investisseurs du monde entier s'y réfugient. En
> mars 2020, en 2008, ce réflexe a joué. Donc une exposition partielle au dollar
> sur la poche actions amortit vos baisses. Je la conserve, sans excès. »

**Sur son inquiétude simultanée euro / dollar :**
> « Vous nous avez dit être inquiet sur l'Europe **et** sur les États-Unis. Je
> prends cette remarque très au sérieux, parce qu'elle élimine la réponse
> paresseuse.
>
> La réponse paresseuse serait : "vous craignez l'euro, mettons du dollar".
> Mais vous craignez aussi le dollar. Donc notre réponse n'est pas de choisir
> une devise contre l'autre — c'est de **ne dépendre d'aucune des deux** : une
> exposition résiduelle au franc suisse et au yen, de l'or, et des actifs réels
> dont la valeur ne dépend pas d'une banque centrale en particulier.
>
> Au fond, votre inquiétude porte moins sur une devise que sur la monnaie
> papier en général. C'est une inquiétude légitime, et elle a une réponse
> d'allocation. »

---

## 10. Enveloppes fiscales : le contenant compte plus que le contenu

**L'idée.** La performance nette dépend autant de *où* l'actif est logé que de
*quel* actif c'est.

**Au client :**
> « Il y a deux questions distinctes, et la deuxième est souvent négligée :
> qu'est-ce que j'achète, et dans quoi je le range.
>
> Le même fonds, exactement le même, logé dans un compte-titres ou dans un
> contrat luxembourgeois, ne produit pas le même résultat net. Sur trente ans,
> l'écart se compte en millions. »

| Enveloppe | Pendant la vie | À la transmission | Usage |
|---|---|---|---|
| **Compte-titres** | Flat tax 30 % sur revenus et plus-values réalisées | Droits de succession jusqu'à 45 % | Liquidité, flexibilité |
| **Assurance-vie luxembourgeoise** | **Zéro impôt tant qu'il n'y a pas de rachat** | 152 500 € d'abattement par bénéficiaire, puis 20 % / 31,25 % | **Le cœur du dispositif** |
| **Contrat de capitalisation** | Idem | Pas d'avantage successoral propre, mais **donnable en démembrement** | Transmission anticipée |
| **PEA** | Exonération d'IR après 5 ans | — | Plafond 150 k€ : marginal, mais gratuit |

### Les trois arguments à connaître sur le contrat luxembourgeois

**1. Le report d'imposition.**
> « Tant que vous ne retirez rien, il n'y a pas d'impôt. Les gains se
> réinvestissent en totalité. Ce n'est pas de l'évasion, c'est du report — mais
> sur trente ans, le report capitalisé représente des sommes considérables. »

**2. Le super-privilège.**
> « En France, si votre assureur fait faillite, vous êtes garanti à hauteur de
> 70 000 €. Sur un contrat de plusieurs dizaines de millions, cette garantie
> est symbolique. Au Luxembourg, vous êtes créancier de premier rang sur les
> actifs cantonnés de l'assureur — avant l'État, avant les salariés. Sur votre
> taille de patrimoine, ce n'est pas un détail juridique, c'est une différence
> de nature. »

**3. Le fonds d'assurance spécialisé (FAS).**
> « Résident français, vous n'avez pas accès en direct à certains supports
> pour des raisons réglementaires. À l'intérieur d'un contrat luxembourgeois,
> le champ des actifs éligibles est nettement plus large.
>
> Cela résout deux de vos contraintes d'un coup : l'accès à des supports non
> disponibles en direct, et le multi-devises natif — vous pouvez détenir des
> compartiments en dollars, en francs suisses, sans changer de contrat. Ce
> dernier point répond directement à votre inquiétude sur l'euro. »

### L'asset location — quel actif dans quelle enveloppe

**La règle :** les actifs fiscalement coûteux vont dans les enveloppes à
fiscalité différée.

```
→  Assurance-vie :   obligations à coupon élevé, haut rendement,
                     stratégies à forte rotation, actifs distribuants,
                     alternatifs
                     (lourdement taxés ailleurs, neutralisés ici)

→  Compte-titres :   ETF actions capitalisants, faible rotation, buy & hold
                     (aucun impôt avant cession → report quasi gratuit)
```

**Au client :**
> « Un fonds capitalisant, qui réinvestit ses dividendes au lieu de vous les
> verser, ne déclenche aucun impôt tant que vous ne vendez pas. Un fonds
> distribuant vous verse des dividendes qui sont taxés à 30 % chaque année,
> et vous devez ensuite les réinvestir. Même actif, même performance brute.
> L'écart net, sur trente ans, se compte en dizaines de points de patrimoine
> final.
>
> Nous n'achèterons donc que des supports capitalisants hors assurance-vie.
> C'est une décision gratuite, et pourtant très souvent négligée. »

**Le détail qui montre le niveau de soin :**
> « Pour vos actions américaines, nous choisirons systématiquement des fonds
> domiciliés en Irlande. La convention fiscale entre l'Irlande et les
> États-Unis ramène la retenue à la source sur les dividendes américains de
> 30 % à 15 %. Sur un rendement de 1,5 %, cela vous fait 22 points de base de
> performance par an, gratuitement. Multiplié par trente ans, sur votre
> allocation américaine, c'est une somme réelle. »

---

## 11. La transmission : changer la fonction objectif

**L'idée fondamentale.** L'objectif de M. Lauren n'est pas de maximiser sa
fortune. C'est de maximiser **ce qui arrive effectivement à ses enfants**.
Ce n'est pas le même problème mathématique.

```
Objectif classique :     max  E[ Patrimoine final ]
Objectif du dossier :    max  E[ Patrimoine final × (1 − coût de transmission) ]
```

**Au client :**
> « Nous mesurons notre performance sur le mauvais indicateur si nous regardons
> uniquement la valeur du portefeuille. Ce qui compte pour vous, c'est ce qui
> arrivera à vos enfants, après droits. Entre les deux, il peut y avoir 45 %
> d'écart. Aucune décision d'allocation ne produira jamais un gain de cette
> ampleur. »

### Les leviers, du plus puissant au moins puissant

**1. La donation en nue-propriété — le levier majeur**

> « Voici un mécanisme que beaucoup de gens découvrent trop tard.
>
> La pleine propriété d'un actif se décompose en deux droits : l'usufruit — le
> droit d'en percevoir les revenus — et la nue-propriété — le droit d'en être
> propriétaire à terme. Vous pouvez donner la nue-propriété à vos enfants tout
> en conservant l'usufruit : vous continuez de percevoir les revenus, votre
> train de vie ne change pas.
>
> L'intérêt fiscal est double.
>
> D'abord, la valeur taxable de la donation n'est pas 100 % de l'actif, mais
> seulement la valeur de la nue-propriété — déterminée par un barème légal
> fondé sur votre âge. À 60 ans, c'est **50 %**. Vous transmettez un actif de
> 10 millions en payant des droits sur 5.
>
> Ensuite, et c'est le plus important : **toute l'appréciation future appartient
> déjà à vos enfants**. Si ces 10 millions en valent 40 dans trente ans, les
> 30 millions de plus-value leur reviennent sans aucun droit supplémentaire.
>
> Et à votre décès, l'usufruit s'éteint. Vos enfants deviennent pleins
> propriétaires. **Sans aucun droit de succession** sur cette part. »

> ### Le point de timing — à placer impérativement en rendez-vous
>
> « Un dernier point, et il est urgent. Le barème légal évolue par tranches
> d'âge. À 60 ans, la nue-propriété que vous transmettez est valorisée à 50 %.
> **À partir de 61 ans, elle passe à 60 %.**
>
> Concrètement : une donation réalisée avant votre prochain anniversaire coûte
> dix points de base taxable de moins que la même donation quelques mois plus
> tard. Sur les montants dont nous parlons, cela représente plusieurs centaines
> de milliers d'euros de droits.
>
> C'est la raison pour laquelle je vous dis que ce dossier a un calendrier, et
> que ce calendrier commence maintenant. »

*C'est l'argument qui fait gagner le mandat. Il montre qu'on a travaillé le
dossier, pas seulement l'allocation.*

**2. L'assurance-vie avant 70 ans**
> « Les versements effectués avant votre 70e anniversaire bénéficient d'un
> régime de transmission spécifique : 152 500 € d'abattement par bénéficiaire,
> puis une taxation à 20 % — contre un barème successoral qui monte à 45 % en
> ligne directe.
>
> Vous avez 60 ans. Cette fenêtre vous est ouverte pour dix ans encore. Elle se
> fermera. C'est une raison supplémentaire de structurer maintenant plutôt que
> dans cinq ans. »

**3. L'abattement de 100 000 €, renouvelable tous les 15 ans**
> « Chaque parent peut donner 100 000 € à chaque enfant sans droits, tous les
> quinze ans. Avec votre épouse et deux enfants : 400 000 € par cycle. À votre
> échelle, c'est modeste — mais c'est gratuit, et cela se renouvelle. Il faut
> simplement **démarrer le compteur tôt** pour pouvoir le réutiliser. »

**4. La donation-partage**
> « Elle fige la valeur des biens au jour de la donation et répartit entre vos
> deux enfants de manière définitive. Son intérêt principal n'est pas fiscal,
> il est familial : elle évite les contestations au moment de la succession.
> Sur une transmission de cette taille entre deux enfants, ce n'est pas un
> sujet secondaire. »

### La slide qui conclut le pitch

Deux trajectoires projetées sur 30 ans :

```
Trajectoire A —  aucune structuration
                 tout en compte-titres, transmission au décès

Trajectoire B —  dispositif recommandé
                 assurance-vie luxembourgeoise + donations démembrées
                 échelonnées + abattements renouvelés
```

**Au client :**
> « L'écart entre ces deux courbes, c'est ce que vaut notre travail de
> structuration. Il est plus important que tout ce que je pourrai gagner en
> optimisant votre allocation à la marge. »

> **Réserve à énoncer explicitement en rendez-vous :**
> « Tout ce que je viens de vous présenter devra être validé par votre notaire
> et votre avocat fiscaliste avant mise en œuvre. Nous construisons la stratégie
> patrimoniale ; ils sécurisent la rédaction des actes. Nous travaillons
> habituellement avec eux et nous coordonnons. »

---

## 12. La crypto : répondre au fils sans se dédire

**La situation.** C'est le fils qui est intéressé, pas M. Lauren. Deux réponses
possibles sont mauvaises : refuser sèchement (on perd le fils, futur détenteur
du patrimoine), accepter mollement (on perd la crédibilité du père).

**L'idée.** Ne pas répondre par une allocation. Répondre par un **cadre de
gouvernance**.

**Au client :**
> « Je vais vous donner une réponse en trois temps, parce que la question
> mérite mieux qu'un oui ou un non.
>
> **Premièrement, le constat factuel.** Le bitcoin a une volatilité d'environ
> 60 %, soit quatre fois celle des actions. Ses baisses historiques dépassent
> 70 %. Et il ne s'est pas comporté comme une protection : en 2022, quand vous
> aviez besoin d'un actif décorrélé, il a chuté davantage que les actions.
> L'argument "or numérique" n'a pas résisté à son premier vrai test.
>
> **Deuxièmement, ce que cela implique pour votre contrainte.** Votre plafond
> est de 15 % de perte. Une ligne crypto de 2 % qui perd 70 % coûte 1,4 point
> à votre portefeuille : c'est absorbable. À 10 %, elle coûte 7 points —
> presque la moitié de votre budget de risque total, sur un seul actif. La
> réponse à "combien" n'est donc pas une question d'opinion sur la crypto : elle
> est déterminée par votre contrainte de risque.
>
> **Troisièmement, notre recommandation.** Une enveloppe plafonnée à **2 %**,
> soit 2 millions, logée dans la poche transmise à vos enfants — celle dont
> l'horizon est le plus long et qui peut absorber ce type de risque. Avec une
> règle explicite : jamais de renforcement après une hausse, et un
> rééquilibrage automatique qui prend les profits au-delà du plafond. »

**Pourquoi cette réponse est bonne, à savoir formuler si on vous le demande :**
> « Elle donne raison à votre fils sur le fond — cet actif a sa place dans un
> patrimoine long — et elle vous donne raison sur la prudence. Elle transforme
> un désaccord familial en règle écrite. Et franchement, sur un sujet
> patrimonial, une règle écrite vaut mieux qu'un consensus. »

*Note d'implémentation :* pas d'accès direct en tant que résident français
retail. Les voies sont soit un ETP coté européen, soit — plus élégant —
un compartiment logé dans le contrat luxembourgeois. Cela relie la réponse
crypto à l'argument du §10.

---

## 13. Le benchmark hybride : il se déduit, il ne se choisit pas

**L'idée.** Un benchmark n'est pas une référence qu'on choisit parce qu'elle
est flatteuse. C'est le portefeuille passif qui aurait la même politique
d'investissement que le nôtre.

**Au client :**
> « Vous devez pouvoir juger notre travail. Pour cela, il vous faut un point
> de comparaison — mais un point de comparaison honnête.
>
> Comparer votre portefeuille au CAC 40 n'aurait aucun sens : vous n'êtes pas
> investi à 100 % en actions françaises. Un tel indice nous ferait passer pour
> des génies dans les années de baisse et des incompétents dans les hausses.
> Ce serait du bruit, pas de l'information.
>
> Votre référence doit donc être **construite sur mesure** : la même répartition
> par classes d'actifs que votre portefeuille, les mêmes filtres éthiques, la
> même devise, la même politique de couverture. La seule différence : elle est
> purement passive.
>
> Ainsi, quand nous faisons mieux, vous saurez que c'est grâce à nos choix
> — et quand nous faisons moins bien, vous le verrez aussi. C'est le sens du
> mot transparence. »

**Les quatre critères de validité — à savoir énoncer :**
1. **Investissable** — chaque composant doit être achetable sous forme d'ETF
2. **Réplicable** — pondérations publiques, règles de rebalancement écrites
3. **Cohérent en devise** — libellé en euros, même politique de couverture
4. **Cohérent en ESG** — indices filtrés, sinon la référence contredit le mandat

**Si on me challenge** — *« Un benchmark sur mesure, c'est pratique pour vous. »*
> La critique est légitime et je la comprends. C'est pourquoi il est figé par
> écrit dans le mandat, avant d'investir, et ne peut être modifié qu'avec votre
> accord formel. Un benchmark qui bouge n'est pas un benchmark. Et nous le
> complétons par un second repère, plus rustique : votre objectif absolu,
> inflation + 0 %. Vous nous jugerez sur les deux.

---

## 14. La gouvernance : rebalancement par bandes

**L'idée.** Rebalancer à date fixe, c'est arbitraire. Rebalancer par seuils,
c'est discipliné.

**Au client :**
> « Le portefeuille dérive naturellement : ce qui monte prend de la place, ce
> qui baisse en perd. Sans intervention, votre allocation devient
> progressivement plus risquée pendant les hausses — exactement au pire moment.
>
> Nous fixons donc des bandes de tolérance : tant qu'une classe d'actifs reste
> à plus ou moins trois points de sa cible, nous ne touchons à rien. Au-delà,
> nous ramenons à la cible.
>
> L'avantage de cette méthode : elle nous force mécaniquement à vendre ce qui a
> beaucoup monté et à acheter ce qui a baissé. Elle impose la discipline que
> l'émotion rend difficile. Et elle réduit les frais et l'impôt par rapport à
> un rebalancement trimestriel systématique. »

**Calendrier de gouvernance :**
- Reporting mensuel — performance, risque, suivi du drawdown vs les 15 %
- Point trimestriel — revue tactique, bandes d'allocation
- Revue annuelle — révision de l'IPS, hypothèses de marché, calendrier de
  transmission
- Revue exceptionnelle — si le drawdown atteint 10 %, soit deux tiers du
  budget de risque

**Ce dernier point, au client :**
> « Nous ne vous appellerons pas seulement pour les bonnes nouvelles. Si votre
> portefeuille atteint 10 % de baisse — deux tiers de votre budget de risque —
> nous vous appelons, que vous le demandiez ou non, avec un plan. »

---

# ANNEXE — L'ARCHITECTURE DU RAISONNEMENT EN UNE PAGE

```
                        Objectif : inflation 4 %
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
         Rendement brut requis          Contrainte de perte 15 %
              ~5,0 %                            │
                   │                   Volatilité cible ~8 %
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                       Ces deux chiffres se rejoignent
                       à ~50 % d'actifs de croissance
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
         Ce qui rend l'égalité           Ce qui la sécurise
              possible                           │
                   │                     Diversification
         Structuration fiscale           au-delà du 60/40
         (−0,8 % de rendement            (or, inflation,
          brut requis)                    actifs réels)
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                        PORTEFEUILLE MODÈLE
                                  │
                        Benchmark hybride
                        (le même, en passif)
```

**La phrase de conclusion du rendez-vous :**
> « Votre objectif est atteignable, mais sans marge d'erreur. C'est pour cela
> que nous avons commencé par la structure fiscale et par la définition précise
> de votre contrainte de risque, avant de parler du moindre fonds. La plupart
> de nos concurrents feront l'inverse. »
