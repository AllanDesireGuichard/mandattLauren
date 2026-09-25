"""
Étape 1 — Paramètres d'entrée.

Cet onglet ne contient AUCUN résultat. Ni rendement attendu, ni volatilité,
ni drawdown mesuré : tous dépendent d'une allocation qui n'existe qu'à
l'étape 4, et les afficher ici revenait à présenter la conclusion avant la
démonstration (défaut relevé par Allan le 2026-09-18 sur la première version
de cet onglet).

Il fait quatre choses : restituer l'énoncé, dire ce que chaque ligne signifie
concrètement, en tirer un portrait du client et les questions qu'il faudrait
lui poser, puis annoncer la méthode des quatre étapes suivantes.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import pedago


def render() -> None:
    pedago.chaine(1)
    pedago.etape(
        1, "Paramètres d'entrée",
        "Avant de chercher des réponses, il faut comprendre la demande. Cet "
        "onglet ne calcule rien : il lit l'énoncé, dit ce qu'il signifie, ce "
        "qu'il révèle du client et les questions qu'il laisse ouvertes, puis "
        "explique comment les quatre étapes suivantes vont y répondre.",
    )

    # ------------------------------------------------------------------
    st.markdown("#### L'énoncé")

    st.markdown(
        "> M. Lauren, 60 ans, marié, deux enfants, résident fiscal français, "
        "vient de céder sa startup. Il dispose de **100 M€**. Il aura besoin "
        "de **10 M€ dans les deux ans**. Il veut **protéger le reste contre "
        "une inflation de 4 %**, sans jamais **perdre plus de 15 %**. Il "
        "exclut le **tabac, l'armement et le charbon**. Son fils voudrait de "
        "la **crypto**, lui hésite. Il est **inquiet sur l'Europe comme sur "
        "les États-Unis**."
    )
    st.caption("La transmission aux enfants et la fiscalité font partie du "
               "cas mais pas de cet exercice, qui porte uniquement sur la "
               "chaîne d'investissement.")

    # ------------------------------------------------------------------
    st.markdown("#### Ce que chaque ligne veut dire")

    lecture = pd.DataFrame([
        ("100 M€",
         "Une somme importante mais surtout liquide : tout est aujourd'hui "
         "en cash, après la vente. On part d'une feuille blanche, sans "
         "portefeuille existant à réaménager."),
        ("10 M€ sous deux ans",
         "Un décaissement quasi certain à court terme. Cet argent ne peut pas "
         "être exposé au risque : il sera mis de côté et ne participera pas "
         "à la recherche de rendement. On investit donc réellement 90 M€."),
        ("Protéger contre une inflation de 4 %",
         "L'objectif n'est pas de s'enrichir mais de ne pas s'appauvrir. Le "
         "portefeuille doit rapporter au moins 4 % par an, sans quoi le "
         "pouvoir d'achat du patrimoine recule. Ce 4 % est le seuil à battre."),
        ("Ne pas perdre plus de 15 %",
         "La limite de risque. C'est elle qui fixe la part d'actifs risqués "
         "qu'on peut se permettre, donc le rendement qu'on peut espérer. Elle "
         "entre en tension directe avec l'objectif précédent."),
        ("Tabac, armement, charbon exclus",
         "Des convictions personnelles, qui réduisent l'univers "
         "d'investissement. Elles concernent les entreprises : un emprunt "
         "d'État ou de l'or ne sont pas touchés."),
        ("Crypto : le fils veut, le père hésite",
         "Une question familiale autant que financière. Elle appelle une "
         "réponse mesurée — une petite poche plafonnée, ou rien — plutôt "
         "qu'un choix tranché."),
        ("Inquiet sur l'Europe et sur les États-Unis",
         "Pas de zone refuge évidente dans l'esprit du client. Cela plaide "
         "pour une vraie diversification géographique et pour des actifs "
         "qui ne dépendent d'aucune économie en particulier, comme l'or."),
    ], columns=["L'énoncé dit", "Ce que cela signifie"])
    st.table(lecture.set_index("L'énoncé dit"))

    st.info(
        "Le cœur du problème tient en une phrase : **rapporter au moins 4 % "
        "par an sans jamais perdre plus de 15 %.** Viser 4 % impose de "
        "prendre du risque ; limiter la perte à 15 % en interdit trop. Tout "
        "l'exercice consiste à vérifier qu'il existe un portefeuille qui "
        "tient les deux à la fois.",
        icon=":material/balance:",
    )

    # ------------------------------------------------------------------
    st.markdown("#### Ce que cela dit du client")

    st.markdown(
        "**Le portrait.** M. Lauren a bâti sa fortune sur un risque très "
        "concentré, vient de la transformer en cash, et cherche désormais à "
        "la garder plutôt qu'à la faire croître."
    )
    st.markdown(
        "Son hypothèse d'inflation à 4 % est le double de la cible de la "
        "BCE ; sa limite de perte à 15 % est modérée. Il est méfiant envers "
        "les deux grandes économies développées et ouvert aux actifs non "
        "conventionnels."
    )
# ------------------------------------------------------------------
    st.markdown("#### Les questions que l'énoncé laisse ouvertes")
    st.caption("Des questions qu'il faudrait poser au client. Faute de "
               "réponse, chacune appelle une hypothèse de travail, qui sera "
               "énoncée à l'étape où elle intervient.")

    questions = pd.DataFrame([
        ("La perte de 15 %",
         "Mesurée sur quelle durée : une année, ou depuis le point le plus "
         "haut jamais atteint ? Et est-ce une limite absolue, ou acceptable "
         "si elle n'arrive que très rarement ? Une limite « jamais » est "
         "impossible à garantir pour un portefeuille investi."),
        ("L'inflation à 4 %",
         "Est-ce une prévision du client ou un scénario de prudence ? Quelle "
         "inflation : française, européenne ? Et que veut dire « protéger » : "
         "maintenir le pouvoir d'achat chaque année, ou en moyenne sur dix "
         "ans ?"),
        ("L'horizon",
         "Combien de temps l'argent restera-t-il investi ? À 60 ans, avec une "
         "transmission en vue, l'horizon réel dépasse probablement celui du "
         "client lui-même."),
        ("Les 10 M€",
         "Pour quoi faire, et à quelle date ? Un achat immobilier daté ne se "
         "gère pas comme une réserve de précaution."),
        ("L'inquiétude géographique",
         "Qu'est-ce qui inquiète exactement : la croissance, la dette "
         "publique, la politique ? La réponse ne sera pas la même selon le "
         "risque redouté."),
        ("La crypto",
         "Qui décide, et jusqu'à quel montant ? Est-ce un placement ou un "
         "geste envers le fils ?"),
        ("Les supports accessibles",
         "Un particulier résidant en France n'a accès qu'aux fonds européens "
         "(UCITS). Avec 100 M€, M. Lauren pourrait demander à être traité en "
         "client professionnel, ce qui élargirait l'univers. Le souhaite-t-il ?"),
    ], columns=["Sujet", "Question"])
    st.table(questions.set_index("Sujet"))

    # ------------------------------------------------------------------
    st.markdown("#### Comment nous allons procéder")

    st.markdown(
        "La démarche suit le processus d'un fonds multi-actifs "
        "institutionnel. Elle part du plus général — l'état de l'économie — "
        "et descend jusqu'au détail — le choix de chaque support —, avant de "
        "vérifier le résultat sur le passé. Chaque étape utilise ce que la "
        "précédente a produit."
    )

    methode = pd.DataFrame([
        ("2 · Macro",
         "Où en est l'économie ?",
         "Lire les taux d'intérêt, l'inflation anticipée par les marchés et "
         "le cycle économique, zone par zone. Confronter l'hypothèse de 4 % "
         "du client à ce que le marché anticipe.",
         "Un rendement espéré pour chaque grande classe d'actifs"),
        ("3 · Ligne à ligne",
         "Dans quoi peut-on investir ?",
         "Noter les actions européennes sur cinq piliers (valorisation, "
         "croissance, dynamique, qualité, résistance en crise), resserrer sur "
         "ce que les analystes attendent, évaluer les obligations à partir "
         "des courbes de taux, appliquer les exclusions.",
         "La liste des supports retenus"),
        ("4 · Allocation",
         "Combien mettre dans chaque ?",
         "Chercher la répartition qui rapporte au moins 4 % tout en "
         "respectant la limite de perte de 15 %.",
         "Le portefeuille proposé"),
        ("5 · Backtests",
         "Aurait-il tenu ?",
         "Rejouer le portefeuille de 2006 à aujourd'hui, à travers les crises "
         "de 2008, 2011, 2020 et 2022, et mesurer ses pertes et leur durée.",
         "Ses pertes, leur durée, et ce qu'est une mauvaise année"),
    ], columns=["Étape", "Question", "Ce qu'on fait", "Ce qu'on en sort"])
    st.table(methode.set_index("Étape"))
