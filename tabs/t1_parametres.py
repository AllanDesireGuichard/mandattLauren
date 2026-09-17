"""
Étape 1 — Paramètres d'entrée.

Aucun curseur. Volontairement. Ce que cet onglet affiche, ce sont les données
du problème : ce que le client a, ce qu'il veut, ce qu'il refuse. Un curseur
sur l'inflation transformerait une hypothèse de mandat en variable de
présentation, et l'expérience de la version précédente est nette là-dessus —
un paramètre réglable finit toujours réglé pour que le résultat arrange.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import ips, pedago
from core.viz import fr


def render() -> None:
    pedago.chaine(1)
    pedago.etape(
        1, "Paramètres d'entrée",
        "Tout ce qui suit est imposé, mesuré ou déjà décidé. Rien n'y est "
        "réglable, et c'est le point de départ des quatre étapes suivantes : "
        "la macro (2) fournit les hypothèses, l'analyse ligne à ligne (3) "
        "fournit les supports, l'allocation (4) les combine sous ces "
        "contraintes, et les backtests (5) vérifient que la contrainte de "
        "perte tient.",
    )

    # ------------------------------------------------------------------
    st.markdown("#### Le mandat")

    c = st.columns(4)
    c[0].metric("Actifs", "100 M€")
    c[1].metric("Besoin de liquidité", "10 M€", "sous 24 mois",
                delta_color="off")
    c[2].metric("Devise de référence", ips.BASE_CURRENCY)
    c[3].metric("Horizon des hypothèses", f"{ips.HORIZON_YEARS} ans")

    pedago.explique(
        "Pourquoi aucun de ces chiffres n'est réglable",
        "Un paramètre qu'on peut déplacer est un paramètre qu'on déplacera. "
        "Si l'inflation devient un curseur, la question « le portefeuille "
        "atteint-il l'objectif ? » perd son sens : il suffit de baisser le "
        "curseur jusqu'à ce que la réponse soit oui. L'hypothèse d'inflation "
        "de 4 % est une donnée du mandat, formulée par le client. Notre "
        "travail est de dire si le portefeuille y répond, pas de négocier "
        "l'énoncé.",
        "Le besoin de liquidité de 10 M€ est un engagement daté et certain. "
        "Il ne se gère pas comme un placement mais comme une dette à honorer : "
        "la poche qui le finance est dimensionnée sur le calendrier de "
        "décaissement, et sortie du calcul d'optimisation. C'est une décision "
        "de politique, pas un arbitrage de rendement — un optimiseur à qui on "
        "donne du monétaire dans son univers le charge massivement, parce "
        "qu'à rendement voisin il préfère toujours moins de volatilité.",
    )

    # ------------------------------------------------------------------
    st.markdown("#### La contrainte de risque")
    st.caption("C'est elle qui pilote tout le dimensionnement du portefeuille. "
               "Pas le profil de risque, pas l'appétence déclarée : cette "
               "phrase chiffrée.")

    st.markdown(
        f"> Une perte maximum de **{ips.MAX_DRAWDOWN:.0%}**, mesurée de pic à "
        f"creux sur **12 mois glissants**, en **euros consolidés**, avec une "
        f"probabilité de dépassement inférieure à "
        f"**{ips.DD_BREACH_PROBABILITY:.0%}**."
    )

    c = st.columns(4)
    c[0].metric("Volatilité cible", f"{ips.TARGET_VOL:.1%}")
    c[1].metric("Drawdown P90 mesuré", f"{ips.EXPECTED_DD_P90:.1%}",
                f"{ips.MAX_DRAWDOWN - ips.EXPECTED_DD_P90:+.1%} vs contrainte",
                delta_color="normal")
    c[2].metric("P(perte > 15 %)", f"{ips.DD_BREACH_MEASURED:.1%}",
                f"tolérance {ips.DD_BREACH_PROBABILITY:.0%}",
                delta_color="off")
    c[3].metric("Pire cas observé (2008)", f"{ips.WORST_OBSERVED_DD:.1%}",
                "au-delà de la contrainte", delta_color="inverse")

    st.warning(
        f"Les deux derniers chiffres vont ensemble ou pas du tout. Le "
        f"portefeuille respecte la contrainte **neuf années sur dix** — c'est "
        f"le P90 à {ips.EXPECTED_DD_P90:.1%}. La dixième, il ne la respecte "
        f"pas : en 2008, une allocation de ce niveau de risque a perdu "
        f"{ips.WORST_OBSERVED_DD:.1%}. Présenter le P90 seul serait "
        f"présenter une contrainte comme une garantie.",
        icon=":material/warning:",
    )

    pedago.explique(
        "Comment une perte maximum devient un budget de volatilité",
        "Un client exprime son risque en perte : « je ne veux pas perdre plus "
        "de 15 % ». Un portefeuille, lui, se construit en volatilité — c'est "
        "la grandeur qu'une matrice de covariance sait manipuler. Il faut donc "
        "un pont entre les deux, et ce pont est un rapport empirique entre le "
        "drawdown qu'on observe et la volatilité annuelle.",
        "La version initiale de ce dossier utilisait un rapport de 1,9, posé "
        "comme règle empirique. Mesuré sur 21,8 ans de données quotidiennes en "
        "euros, il vaut **1,35**. L'écart n'est pas anodin : l'ancienne valeur "
        "sous-allouait le risque d'environ dix points d'actions, donc "
        "sacrifiait du rendement pour respecter une contrainte qui n'était "
        "jamais menacée.",
        "Le rapport n'est d'ailleurs pas constant. Il vaut 1,81 pour un "
        "portefeuille à 20 % d'actions et 1,33 à 80 %, parce que la poche "
        "obligataire agit davantage sur le drawdown que sur la volatilité. "
        "C'est pourquoi le budget retenu n'est pas déduit du rapport mais lu "
        "directement sur l'allocation testée : on simule, on mesure, on "
        "n'extrapole pas.",
        source="scripts/estimate_dd_ratio.py · 21,8 ans de données "
               "quotidiennes EUR (2004-2026)",
    )
    pedago.formule(
        r"\text{volatilité cible} \;=\; "
        r"\frac{\text{perte maximum acceptée}}{\text{rapport perte / volatilité}}"
        r" \;=\; \frac{15\,\%}{1{,}35} \;\approx\; 11\,\%",
        "On divise la perte que le client refuse par le rapport mesuré entre "
        "perte et volatilité. Le résultat est le niveau d'agitation annuelle "
        "que le portefeuille peut se permettre. Nous retenons 9,6 % et non "
        "11 %, parce que l'estimation elle-même porte une erreur et qu'on ne "
        "construit pas à la limite d'une mesure incertaine.",
    )

    pedago.explique(
        "Pourquoi une contrainte chiffrée prime sur un profil de risque",
        "Le client se décrit volontiers comme « dynamique ». Dans la plupart "
        "des grilles maison, dynamique signifie 70 à 80 % d'actions. Or 70 % "
        "d'actions produisent une perte à dix ans nettement supérieure à "
        "15 %. L'adjectif et le chiffre sont incompatibles, et il faut "
        "choisir.",
        "Nous choisissons le chiffre, pour une raison simple : c'est le seul "
        "des deux qui soit vérifiable. On peut mesurer si une perte dépasse "
        "15 %, on ne peut pas mesurer si un portefeuille est dynamique. Le "
        "profil déclaré est honoré autrement — non par le niveau de risque, "
        "mais par sa composition : c'est la part d'actifs de croissance qui "
        "porte l'ambition, dans la limite du budget.",
        "Ce point est le plus important à savoir tenir à l'oral. Un client "
        "qui s'entend dire que son profil ne sera pas suivi doit comprendre "
        "que c'est sa propre contrainte qui l'interdit, pas une prudence de "
        "gérant.",
    )

    # ------------------------------------------------------------------
    st.markdown("#### Le seuil de rendement à franchir")

    seuil = ips.required_gross_return()
    deriv = pd.DataFrame([
        ("Préservation du pouvoir d'achat", ips.INFLATION_TARGET,
         "hypothèse du client, figée"),
        ("Coût des supports (TER moyen pondéré)", ips.INSTRUMENT_TER,
         "mesuré sur les supports retenus — étape 3"),
        ("Seuil de rendement brut requis", seuil, ""),
    ], columns=["Composante", "Taux", "Provenance"])
    deriv["Taux"] = deriv["Taux"].map(lambda v: f"{v:.2%}")
    st.dataframe(deriv, hide_index=True, width="stretch")

    faisa = pd.DataFrame(
        [(lab, f"{er:.2%}", f"{s:.2%}", f"{m:+.2%}")
         for lab, er, s, m in ips.feasibility()],
        columns=["Régime d'inflation", "Rendement attendu", "Seuil requis",
                 "Marge"],
    )
    st.dataframe(faisa, hide_index=True, width="stretch")

    st.success(
        f"L'objectif est atteint dans les deux régimes. C'est le point de "
        f"pitch le plus solide du dossier : *« votre hypothèse à 4 % est "
        f"au-dessus du consensus, nous ne l'avons pas corrigée — vous êtes "
        f"couvert dans les deux cas, donc vous ne dépendez pas du fait que "
        f"nous ayons raison sur l'inflation »*.",
        icon=":material/check_circle:",
    )

    pedago.explique(
        "Ce que ce seuil ne contient pas, et pourquoi il faut le dire",
        "Ce seuil comprend l'inflation et le coût des supports. Il ne comprend "
        "ni frais de gestion, ni fiscalité. C'est une décision de périmètre : "
        "cette application documente un processus d'investissement, pas la "
        "structuration d'un mandat.",
        f"La conséquence doit être énoncée franchement, parce qu'elle flatte "
        f"le résultat. Avec des frais de gestion de "
        f"{ips.FRAIS_GESTION_REFERENCE:.2%} — un ordre de grandeur de marché "
        f"sur un encours de cette taille — le seuil passerait de "
        f"{seuil:.2%} à {ips.SEUIL_REFERENCE_AVEC_FRAIS:.2%} et la marge "
        f"tomberait de "
        f"{ips.expected_gross_return() - seuil:+.2%} à "
        f"{ips.expected_gross_return() - ips.SEUIL_REFERENCE_AVEC_FRAIS:+.2%}. "
        f"La marge affichée ci-dessus est donc une marge **avant frais de "
        f"gestion**. Elle reste positive dans les deux cas, ce qui est le "
        f"point qui compte.",
        "Un chiffre a disparu du dossier avec ce changement de périmètre, et "
        "il était le plus puissant : la structuration fiscale et la "
        "transmission valaient environ 50 M€ de patrimoine net transmis, "
        "contre 5,5 M€ pour l'ensemble de l'optimisation d'allocation. Un "
        "facteur neuf. Ce travail existe toujours dans l'historique du "
        "projet ; il ne fait simplement plus partie de ce qu'on démontre ici.",
    )

    pedago.explique(
        "Pourquoi le seuil et le rendement attendu doivent être jugés dans "
        "le même régime d'inflation",
        "C'est la correction la plus importante de tout le projet, et la plus "
        "facile à commettre. Les premières versions comparaient un seuil bâti "
        "sur 4 % d'inflation à des rendements attendus bâtis implicitement sur "
        "2 %. Le portefeuille était évalué dans un monde et jugé dans un "
        "autre. La marge annoncée était fausse, et elle était fausse dans le "
        "sens pessimiste.",
        "La correction consiste à faire porter à chaque classe d'actifs un "
        "coefficient de répercussion de l'inflation : dans quelle proportion "
        "son rendement nominal suit une surprise d'inflation sur dix ans. Le "
        "monétaire et les obligations indexées suivent intégralement. Le "
        "souverain à taux fixe ne suit qu'à 45 %, parce qu'une hausse des taux "
        "lui fait d'abord perdre du capital avant qu'il ne réinvestisse plus "
        "cher. Les matières premières suivent à plus de 100 %, étant souvent "
        "la cause même de la surprise.",
        "Le tableau ci-dessus est donc lisible ligne par ligne : chaque ligne "
        "est un monde cohérent, dans lequel le seuil et le rendement sont "
        "calculés avec la même hypothèse d'inflation.",
        source="core/cma.py · coefficients de répercussion par classe",
    )

    # ------------------------------------------------------------------
    st.markdown("#### Les exclusions")

    esg = pd.DataFrame([
        ("Tabac", "Production 0 % · distribution 5 %",
         "Exigé sur les actions et le crédit d'entreprise"),
        ("Armement", "Controversé 0 % · conventionnel 5 %",
         "Exigé sur les actions et le crédit d'entreprise"),
        ("Charbon thermique", "Extraction 5 % · production électrique 5 %",
         "Exigé sur les actions et le crédit d'entreprise"),
    ], columns=["Exclusion", "Seuil de chiffre d'affaires", "Portée"])
    st.dataframe(esg, hide_index=True, width="stretch")

    c = st.columns(2)
    c[0].metric("Univers", "UCITS uniquement",
                "résident français retail, contrainte PRIIPs",
                delta_color="off")
    c[1].metric("Concentration maximum par ligne",
                f"{ips.CONCENTRATION_LIMITS['single_line']:.0%}")

    pedago.explique(
        "La portée d'un filtre d'exclusion, et une erreur qu'on avait commise",
        "Les trois exclusions visent des émetteurs d'entreprise. Il n'y a rien "
        "à filtrer dans une obligation d'État allemande ni dans un lingot d'or "
        "— ce ne sont pas des entreprises et elles ne produisent ni tabac ni "
        "charbon. Une première version de ce dossier appliquait néanmoins le "
        "filtre partout, ce qui conduisait à écarter des supports parfaitement "
        "conformes et à en retenir de moins bons.",
        "La règle retenue distingue trois cas : le filtre est **exigé** (les "
        "actions et le crédit d'entreprise), **sans objet** (souverain, or, "
        "monétaire), ou **sous condition** (les indices mixtes, où il faut "
        "regarder la poche d'entreprises). Et quand le filtre est exigé, c'est "
        "le support principal qui doit le porter — pas un suppléant qu'on "
        "montre en annexe.",
        "La contrainte UCITS, elle, n'est pas un choix : un résident français "
        "particulier ne peut pas acheter de fonds non-UCITS depuis un compte "
        "ordinaire, le règlement PRIIPs l'interdit. Cela écarte l'essentiel "
        "des fonds domiciliés aux États-Unis, souvent moins chers, et c'est "
        "une contrainte qui coûte de la performance.",
        source="core/esg.py",
    )

    # ------------------------------------------------------------------
    st.markdown("#### Ce que ces paramètres ne disent pas")

    st.markdown(
        "- **L'hypothèse d'inflation de 4 % n'est pas une prévision.** "
        "L'étape 2 mesure ce que le marché anticipe réellement. Les deux "
        "chiffres diffèrent sensiblement, et c'est un point de conversation, "
        "pas un problème.\n"
        "- **La contrainte de perte est probabiliste, pas absolue.** "
        "« Moins d'une année sur dix » signifie qu'il y aura des années "
        "au-delà de 15 %.\n"
        "- **Le rendement attendu est une hypothèse, pas un engagement.** "
        "Son mode de construction, classe par classe, est exposé à l'étape 2.\n"
        "- **La durée d'une perte compte autant que sa profondeur.** "
        "2022 fut moins profond que 2020 mais trois fois plus long à "
        "récupérer. L'étape 5 mesure le temps passé sous l'eau."
    )
