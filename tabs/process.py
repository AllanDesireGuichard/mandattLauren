"""
Onglet Process -- la chaine complete, source par source et decision par
decision.

Objectif : qu'un lecteur puisse reconstituer chaque chiffre du dossier, savoir
d'ou viennent les donnees, ce qu'on leur a fait subir, ce qu'on a ecarte et
pourquoi. Y compris les erreurs : elles expliquent pourquoi certains
parametres valent ce qu'ils valent.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

SOURCES = [
    {"Source": "equitydb2 — référentiel",
     "Chemin": "~/projets/equitydb2/state/etf_universe.csv",
     "Contenu": "643 ETF, dont 266 domiciliés en Europe",
     "Usage": "Base de l'univers de candidats",
     "Limite": "La colonne expense_ratio mélange les conventions décimale et "
               "pourcentage (IBGS.L à 0,2 = 20 %). NON réutilisée."},
    {"Source": "equitydb2 — cache de prix",
     "Chemin": "~/projets/equitydb2/state/cache/etf/*.parquet",
     "Contenu": "731 séries quotidiennes, plafonnées à 10 ans",
     "Usage": "Sélection d'instruments (comparaison sur fenêtre commune)",
     "Limite": "10 ans maximum : insuffisant pour calibrer le risque. "
               "Partiellement corrompu (voir Traitements)."},
    {"Source": "yfinance — proxys longs",
     "Chemin": "data/prices/ (SPY, EFA, EEM, IEF, TIP, LQD, GLD, VNQ)",
     "Contenu": "21,8 ans quotidiens (2004-2026)",
     "Usage": "Calibration du risque, stress tests, backtest",
     "Limite": "Indices larges NON filtrés ESG — assumé, voir Choix n°6."},
    {"Source": "yfinance — extension ciblée",
     "Chemin": "data/universe_candidates.csv",
     "Contenu": "88 candidats sur les trous (crédit ESG, infra, alternatifs, "
                "monétaire, obligations vertes)",
     "Usage": "Combler les classes sans support",
     "Limite": "53 résolus sur 88. Échecs intermittents de yfinance."},
    {"Source": "yfinance — change",
     "Chemin": "EURUSD=X",
     "Contenu": "Depuis 2003",
     "Usage": "Conversion en EUR et application des ratios de couverture",
     "Limite": "—"},
    {"Source": "Barèmes fiscaux",
     "Chemin": "core/ips.py (art. 669, 777, 990 I CGI)",
     "Contenu": "Usufruit par tranche d'âge, barème ligne directe, "
                "abattements",
     "Usage": "Moteur de transmission",
     "Limite": "À faire confirmer par un notaire avant mise en œuvre."},
]

TRAITEMENTS = [
    ("1 · Récupération robuste", "core/data.py", """
yfinance renvoie des échecs **intermittents par ticker** : un code qui répond
peut échouer vingt minutes plus tard. `SGLN.L`, `SPY` et `AAPL` ont tous
échoué à un moment et fonctionné à un autre.

**Traitement** : une tentative à la fois, backoff progressif, liste de tickers
de repli par classe, cache incrémental pour ne jamais reperdre ce qui est
descendu. Ne jamais utiliser `yf.download()` sur une liste.
"""),
    ("2 · Contrôle qualité des prix", "core/quality.py", """
**Le traitement le plus important de la chaîne.** Les séries des lignes
londoniennes mélangent les devises de cotation :

```
SPXS.L   2014-01-02   303,05 → 3,02        rupture ×100, pence → livres
IBGS.L   2008-05      −22 % puis +28 %     oscillation entre deux lignes
SGLN.L   2011-04      −39 %, +64 %, −38 %  idem
```

Sans filtre, un ETF d'obligations d'État 1-3 ans affiche **29 % de volatilité
et 99 % de drawdown**.

**Traitement en trois étages :**
1. *Réparation* des ruptures d'échelle d'un facteur 100 ou 1000 — on remet le
   segment antérieur à l'échelle du segment récent.
2. *Rejet* des séries oscillantes — un saut suivi d'un saut inverse sous dix
   jours n'est pas réparable : on ne sait pas quel point appartient à quelle
   série.
3. *Contrôle de plausibilité par classe d'actifs* — c'est le vrai garde-fou.
   Un souverain court au-dessus de 3 % de volatilité est faux quelle qu'en
   soit la cause. Sur 182 séries, une inspection manuelle est impossible.

> Une erreur de données ne se voit pas dans le résultat : **elle le déplace
> silencieusement.**
"""),
    ("3 · Classement et enrichissement", "scripts/build_universe.py, enrich_names.py", """
Les 266 tickers européens sont classés dans les onze classes de l'allocation
par règles explicites sur le libellé, avec dérogations manuelles.

**Piège rencontré** : trois tickers n'étaient pas ce que leur code suggérait.
`CTA.L` est *CT Automotive Group plc*, un équipementier automobile — pas un
fonds de tendance. `XZEC.DE` et `EEDS.L` sont des fonds d'actions, pas du
crédit. Leur volatilité les a trahis (19 % et 17 %).

**Traitement** : récupération systématique des libellés via yfinance, puis
re-marquage ESG et capitalisant/distribuant sur le libellé réel. Consigné dans
`core.universe.TICKER_TRAPS`.
"""),
    ("4 · Sélection", "core/metrics.py, scripts/select_instruments.py", """
Filtres **durs** — sur ce qui est mesurablement faux :
historique ≥ 3 ans · série propre (peu de trous, peu de jours sans mouvement)
· verdict qualité OK · volatilité dans la fourchette plausible de la classe.

Préférences **souples**, par score :
historique ×16 · propreté ×8 · filtre ESG ×4 · couverture de change conforme
×4 · cohérence devise/place ×3 · capitalisant ×2 · fiabilité de la place ×1.

**Correction en route** : ma première règle « pas de cotation londonienne pour
les classes euro » rejetait `SUOE.L` (5,4 % de volatilité, plausible) en même
temps qu'`ECRP.L` (9,8 %, contaminé par le GBP). Inversé : **filtre dur sur ce
qui est mesurable, préférence souple sur le reste.**
"""),
    ("5 · Hypothèses de marché", "core/cma.py", """
Prospectif, pas historique. Une moyenne de rendements passés n'est pas une
prévision — elle dit surtout d'où l'on vient en matière de valorisation.

Chaque entrée porte sa **provenance** : *mesurée* (le taux monétaire EUR à
2,05 %, lu sur XEON.DE), *marché* (rendements actuariels obligataires), ou
*hypothèse* (blocs constitutifs actions).

Chaque classe porte un **coefficient de répercussion de l'inflation** à dix
ans : 1,00 pour le monétaire et les indexées, 0,45 pour le souverain à taux
fixe, 0,80 pour les actions, 0,90 pour l'infrastructure, 1,10 pour les
matières premières.
"""),
    ("6 · Optimisation", "core/optimizer.py, scripts/optimize_saa.py", """
Parité de risque sur les actifs risqués → rendements d'équilibre →
Black-Litterman → frontière resamplée (120 tirages) → contraintes de second
niveau → validation du drawdown par simulation.

Volatilités remises à l'échelle : les corrélations viennent de la fenêtre
instruments (6,2 ans, plus stables), les volatilités de la référence longue
(21,8 ans). Sans cet ajustement on optimiserait sur un risque sous-estimé,
faute de 2008 et 2011 dans la fenêtre.
"""),
    ("7 · Risque et backtest", "scripts/stress_tests.py, backtest.py", """
Fenêtres glissantes de 252 jours sur 21,8 ans — 5 438 observations. Crises
définies **a priori** (Lehman, dette souveraine 2011, COVID, inflation 2022),
jamais par sélection sur les données.

Backtest net de 0,85 % de frais et fiscalité annuels, sur indices larges.
"""),
]

CHOIX = [
    ("Définition de la contrainte de 15 %",
     "Drawdown 12 mois glissants, consolidé EUR, probabilité de dépassement "
     "< 10 %",
     "VaR à 95 % · plafond absolu « jamais »",
     "Le drawdown est ce que le client vit — l'écart entre son meilleur relevé "
     "et le pire. C'est aussi la mesure la plus contraignante. Un plafond "
     "absolu n'est garantissable par personne : le promettre serait "
     "malhonnête."),
    ("Famille d'indices ESG",
     "MSCI ESG Screened",
     "MSCI SRI (best-in-class) · Paris-Aligned",
     "Le mandat demande trois exclusions précises, pas une démarche ESG large. "
     "ESG Screened exclut exactement ces trois secteurs et rien de plus : "
     "l'univers reste à ~95 % de l'indice parent, la tracking error sous 1 %. "
     "Le SRI irait bien au-delà de la demande."),
    ("Portée du filtre ESG",
     "Exigé sur actions, émergents, crédit, infrastructure. Sans objet sur "
     "souverain, or, matières premières, monétaire, crypto",
     "Filtre uniforme sur tout le portefeuille",
     "Les trois exclusions visent des **émetteurs d'entreprise**. Les "
     "appliquer à un Bund allemand ou à un lingot d'or est une erreur de "
     "catégorie : il n'y a rien à filtrer."),
    ("Ancrage de Black-Litterman",
     "Les hypothèses de marché comme prior, vues appliquées en écarts",
     "Optimisation inverse depuis un neutre en parité de risque",
     "L'optimisation inverse suppose le portefeuille de référence **optimal**. "
     "Or nos hypothèses disent l'inverse : à 4 % d'inflation le souverain "
     "rapporte moins que le monétaire. La parité de risque étant obligataire "
     "à 53 %, l'aversion déduite tombait à 1,76 et la prime des actions "
     "ressortait à 1,49 % au lieu de 3,65 %. Un prior qui contredit ses "
     "propres hypothèses n'est pas un prior."),
    ("Méthode de backtest",
     "Indices larges non filtrés sur 21,8 ans, effet ESG mesuré séparément",
     "Backtest sur les ETF · backtest sur indices ESG reconstitués",
     "Les ETF filtrés datent de 2016-2020 et ne couvrent aucune crise majeure. "
     "Les séries d'indices ESG antérieures à 2017 sont **rétro-calculées** : "
     "un indice n'est lancé qu'une fois qu'il a montré qu'il fonctionnait, "
     "donc backtester dessus flatte systématiquement l'ESG."),
    ("Niveau de risque",
     "45 % d'actifs de croissance",
     "50 % (sortie de l'optimisation)",
     "À 50 %, le drawdown P90 ressortait à 14,1 % et la probabilité de "
     "dépassement à 9,2 % — juste sous les seuils. Construire à la limite "
     "d'une mesure qui venait de bouger de deux points n'était pas "
     "défendable. Coût du dé-risquage : 19 points de base."),
    ("Partage de la poche de liquidité",
     "5 % monétaire + 5 % souverain court, échelonné",
     "100 % monétaire (sortie de l'optimisation)",
     "L'optimiseur raisonne en risque, pas en **adossement**. La poche A "
     "finance un décaissement daté. À soulever avec le client : si les dates "
     "sont incertaines, le tout-monétaire est préférable."),
    ("Stratégie de transmission",
     "B — 30 % assurance-vie, 40 % en nue-propriété donnée, 30 % compte-titres",
     "C — 30 / 60 / 10, qui transmet 15 M€ de plus",
     "C donne la nue-propriété de 60 % du patrimoine dès aujourd'hui. Revenus "
     "conservés, contrôle perdu. Décision irréversible que le gain fiscal seul "
     "ne justifie pas. **À poser comme question au client, pas à trancher à "
     "sa place.**"),
]

ERREURS = [
    ("Ratio drawdown / volatilité",
     "1,9 posé comme « règle empirique »",
     "1,35 mesuré sur 21,8 ans",
     "L'ancienne valeur sous-allouait le risque d'environ dix points d'actions."),
    ("Cohérence poche A / allocation",
     "Poche A à 10 % des actifs mais 5 % de monétaire dans l'allocation",
     "5 % monétaire + 5 % souverain court, explicités",
     "Les cinq points manquants n'étaient logés nulle part, alors que le "
     "calcul du budget de risque supposait 10 % sans risque. Une assertion "
     "vérifie désormais l'égalité à chaque exécution."),
    ("Régime d'inflation",
     "Seuil bâti sur 4 % comparé à des rendements bâtis sur 2 %",
     "Coefficients de répercussion par classe, même régime des deux côtés",
     "**La correction la plus importante du projet.** La marge passe de "
     "−0,09 % à +0,99 %. On jugeait un portefeuille évalué dans un monde avec "
     "une exigence formulée dans un autre."),
    ("Écart fiscal annuel",
     "85 pb, puis 15 pb",
     "38 pb, dérivés",
     "Le premier chiffre opposait une bonne structure à un compte-titres garni "
     "de fonds distribuants — un homme de paille. Le second sous-estimait la "
     "friction de rebalancement. Le calcul dérivé tranche."),
    ("Corrélations de stress",
     "Estimées sur le décile des jours où la moyenne des actifs était la plus "
     "basse",
     "Périodes de crise définies a priori",
     "Conditionner sur une **somme** biaise mécaniquement à la baisse les "
     "corrélations entre ses composantes. Le tableau montrait des corrélations "
     "qui *diminuent* en crise — l'inverse du phénomène connu."),
    ("Échelle des pondérations",
     "Poids déjà nets de la poche A, multipliés une seconde fois",
     "Échelle unique",
     "Le portefeuille testé était à 72 % de risqué au lieu de 84 %. Le "
     "drawdown P90 annoncé à 12,0 % valait en réalité 14,1 %."),
    ("Apport du block bootstrap",
     "Présenté comme donnant des estimations plus prudentes",
     "Il recoupe, il ne durcit pas",
     "Mesuré sur blocs de 21 à 252 jours, il tombe 0 à 0,6 point **en dessous** "
     "du P90 historique."),
    ("Devise de cotation — trois fois",
     "ECRP.L en pence · XZW0.DE (EUR) comparé à URTH (USD) · SAWD.L en dollars "
     "malgré le suffixe .L",
     "Vérification ticker par ticker",
     "**Mode de défaillance dominant du projet.** Le suffixe de place ne "
     "détermine pas la devise. Un écart de suivi apparent de 19 % n'était que "
     "de la volatilité de change."),
    ("Parité de risque avec du monétaire",
     "82 % de monétaire, « neutre » à 0,99 % de volatilité",
     "Parité de risque sur les actifs risqués uniquement",
     "Pour égaliser les contributions au risque, un actif à 0,4 % de "
     "volatilité doit peser énormément. Mathématiquement correct, "
     "économiquement absurde."),
]


def render() -> None:
    st.header("Process — d'où vient chaque chiffre")
    st.caption("La chaîne complète : sources, traitements, arbitrages, et les "
               "erreurs corrigées en route. Un chiffre du dossier doit pouvoir "
               "être reconstitué de bout en bout.")

    st.markdown("""
```
  equitydb2                yfinance                  barèmes CGI
  643 ETF référencés       proxys longs 21,8 ans     art. 669 · 777 · 990 I
  731 séries ≤ 10 ans      extension 88 candidats
        │                        │                          │
        └────────────┬───────────┘                          │
                     ▼                                      │
         core/data.py  —  retry, replis, cache              │
                     ▼                                      │
         core/quality.py  —  réparation, rejet,             │
                            plausibilité par classe         │
                     ▼                                      │
         core/metrics.py  —  filtres durs + score           │
                     ▼                                      │
         226 candidats → 182 séries → 48 supports           │
                     ▼                                      │
         core/cma.py  —  blocs constitutifs,                │
                        répercussion de l'inflation         │
                     ▼                                      │
         core/optimizer.py  —  BL + resampling              │
                     ▼                                      │
         contraintes de second niveau                       │
                     ▼                                      ▼
         ALLOCATION  ──────────────────────►  core/succession.py
                     │                               core/tax.py
                     ▼                                      ▼
         stress_tests · backtest · benchmark        transmission
```
""")

    t1, t2, t3, t4 = st.tabs(["Sources de données", "Traitements",
                              "Arbitrages", "Erreurs corrigées"])

    with t1:
        st.markdown("### Six sources, et la limite de chacune")
        for s in SOURCES:
            with st.container(border=True):
                st.markdown(f"**{s['Source']}**  ·  `{s['Chemin']}`")
                c = st.columns([1, 1, 1.4])
                c[0].markdown(f"**Contenu**  \n{s['Contenu']}")
                c[1].markdown(f"**Usage**  \n{s['Usage']}")
                c[2].markdown(f"**Limite**  \n{s['Limite']}")

    with t2:
        st.markdown("### Sept traitements, dans l'ordre")
        for titre, module, corps in TRAITEMENTS:
            with st.expander(f"**{titre}**  —  `{module}`",
                             expanded=titre.startswith("2")):
                st.markdown(corps)

    with t3:
        st.markdown("### Huit arbitrages — ce qui a été écarté, et pourquoi")
        st.caption("Un choix dont on ne sait pas nommer l'alternative écartée "
                   "n'est pas un choix.")
        for sujet, retenu, ecarte, pourquoi in CHOIX:
            with st.container(border=True):
                st.markdown(f"##### {sujet}")
                c = st.columns(2)
                c[0].success(f"**Retenu** — {retenu}")
                c[1].error(f"**Écarté** — {ecarte}")
                st.markdown(f"*{pourquoi}*")

    with t4:
        st.markdown("### Neuf erreurs trouvées et corrigées")
        st.info("Elles figurent ici parce qu'elles expliquent pourquoi "
                "certains paramètres valent ce qu'ils valent — et parce qu'un "
                "dossier qui ne montre aucune correction n'a pas été vérifié.")
        st.dataframe(pd.DataFrame([
            {"Sujet": s, "Avant": a, "Après": b, "Ce que ça changeait": c}
            for s, a, b, c in ERREURS]), width="stretch", hide_index=True,
            column_config={
                "Ce que ça changeait": st.column_config.TextColumn(width="large")})
