"""Onglet Concepts -- l'argumentaire oral, pour preparer le rendez-vous."""
from __future__ import annotations

import streamlit as st

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent

ARTIFACT = "https://claude.ai/code/artifact/108496cb-e142-4cde-9ad5-d44bbba44d2a"

CONCEPTS = [
    ("Quatre poches, pas un portefeuille",
     "Un patrimoine n'a pas un objectif, il en a plusieurs, avec des horizons "
     "différents. Un portefeuille unique moyenne ces objectifs et les sert "
     "tous mal.",
     "Vos 100 millions ne servent pas tous la même chose. 10 millions doivent "
     "être disponibles dans deux ans : cet argent n'a pas le droit de baisser. "
     "À l'inverse, la part qui ira à vos enfants sera investie pendant trente "
     "ans : lui interdire de prendre du risque, ce serait lui interdire de "
     "performer.",
     "« C'est de la complexité pour faire joli. » — Non : la contrainte de "
     "15 % s'applique au total. La poche transmission peut donc porter bien "
     "plus de risque qu'elle n'en porterait seule, parce qu'elle est diluée. "
     "Sans découpage, nous n'atteignons pas votre objectif."),
    ("L'horizon n'est pas l'âge du client",
     "M. Lauren a 60 ans. Son portefeuille, lui, a 30 ans — parce que l'argent "
     "ne s'arrête pas à lui.",
     "Beaucoup vous diraient : vous avez 60 ans, donc horizon 20 ans, donc "
     "portefeuille prudent. C'est une erreur d'analyse. Cet argent ne sera pas "
     "consommé à votre décès, il continuera d'être investi par vos enfants. "
     "Et c'est une bonne nouvelle : le temps est le seul ingrédient qui "
     "transforme le risque en rendement.",
     "« Et si j'ai besoin de tout d'un coup ? » — C'est le rôle de la poche A, "
     "dimensionnée pour cela et redimensionnable à tout moment."),
    ("« Dynamique » contre 15 % — la tension centrale",
     "Le client demande deux choses qui se contredisent partiellement. Notre "
     "valeur ajoutée est de le dire, puis de résoudre.",
     "Un portefeuille dynamique standard, c'est 13 % de volatilité — et en "
     "2008, une perte de 35 %. Si nous vous vendions un profil dynamique "
     "classique, nous vous exposerions à plus du double de ce que vous "
     "acceptez. Entre les deux, c'est la contrainte de 15 % qui commande. Le "
     "mot « dynamique » décrit votre état d'esprit, pas une cible de "
     "volatilité.",
     "« Alors vous me classez prudent ? » — Non. Ce qui vous différencie, ce "
     "n'est pas le niveau de risque global mais **où** nous le plaçons : dans "
     "la poche à 30 ans, pas dans celle à 2 ans."),
    ("« Protéger contre 4 % » ne veut pas dire « viser 4 % »",
     "L'objectif est un rendement net. Le portefeuille doit donc produire "
     "nettement plus en brut.",
     "Entre la performance brute et ce qui reste dans votre poche, il y a deux "
     "prélèvements : nos frais et l'impôt. Si je vise 4 % brut, vous vous "
     "appauvrissez chaque année. Il vous faut 4,80 %.",
     "« 0,55 % de frais, c'est cher. » — C'est le tarif d'un mandat "
     "institutionnel sur cette taille, et il inclut les frais des instruments "
     "sous-jacents. Négociable contre un engagement de durée."),
    ("Le 60/40 échoue dans le scénario que vous craignez",
     "Le portefeuille équilibré repose sur une hypothèse — actions et "
     "obligations évoluent en sens inverse — qui a cessé d'être vraie au "
     "moment exact où on en avait besoin.",
     "En 2022, actions −18 % et obligations −17 %, en même temps. Parce que la "
     "cause de la baisse était l'inflation, et que l'inflation fait mal aux "
     "deux simultanément. Or c'est précisément votre inquiétude. Vous protéger "
     "avec un 60/40 reviendrait à vous vendre le seul portefeuille qui échoue "
     "dans le scénario que vous craignez.",
     "Nous l'avons vérifié sur votre propre portefeuille : passer des actions "
     "aux obligations ne réduit presque pas la queue de distribution "
     "(14,1 % → 13,8 %). Seul le monétaire la réduit."),
    ("La crypto : répondre au fils sans se dédire",
     "Ne pas répondre par une allocation. Répondre par un cadre de gouvernance.",
     "Le bitcoin a une volatilité de 60 %, quatre fois celle des actions, et "
     "en 2022 il a chuté davantage que les actions. Votre plafond est de 15 % "
     "de perte. Une ligne de 2 % ajoute 0,7 point à votre perte maximale ; à "
     "5 %, elle en ajoute 1,6. La réponse à « combien » n'est donc pas une "
     "opinion sur la crypto : elle est déterminée par votre contrainte.",
     "Cette réponse donne raison à votre fils sur le fond et à vous sur la "
     "prudence. Elle transforme un désaccord familial en règle écrite — et sur "
     "un sujet patrimonial, une règle écrite vaut mieux qu'un consensus."),
    ("Le contenant compte plus que le contenu",
     "La performance nette dépend autant de *où* l'actif est logé que de "
     "*quel* actif c'est.",
     "Le même fonds, logé dans un compte-titres ou dans un contrat "
     "luxembourgeois, ne produit pas le même résultat net. Mais soyons précis : "
     "l'écart annuel est de 38 points de base. Si quelqu'un vous promet des "
     "points entiers grâce à l'enveloppe, demandez-lui le calcul. Le vrai "
     "sujet est successoral — 50 millions de plus pour vos enfants.",
     "L'écart entre un compte-titres bien géré et un compte-titres négligent, "
     "lui, vaut 60 points de base par an. Et il est gratuit à corriger."),
    ("La transmission change la fonction objectif",
     "L'objectif n'est pas de maximiser la fortune, mais ce qui arrive "
     "effectivement aux enfants.",
     "Nous mesurons notre performance sur le mauvais indicateur si nous "
     "regardons la valeur du portefeuille. Ce qui compte, c'est ce qui "
     "arrivera à vos enfants après droits. Entre les deux, il peut y avoir "
     "45 % d'écart. Aucune décision d'allocation ne produira jamais un gain de "
     "cette ampleur.",
     "Point de calendrier : le barème évolue par tranches d'âge. À 60 ans la "
     "nue-propriété est valorisée à 50 %, à partir de 61 ans à 60 %. Une "
     "donation avant votre anniversaire coûte plusieurs centaines de milliers "
     "d'euros de moins."),
]


def render() -> None:
    st.header("Concepts et argumentaire")
    st.caption("Chaque décision du portefeuille, et la manière de la défendre "
               "à l'oral. Format : l'idée · ce qu'on dit au client · la "
               "réponse à l'objection.")

    st.link_button("Ouvrir l'argumentaire complet (14 concepts, mode oral)",
                   ARTIFACT, width='content')

    mode = st.toggle("Mode oral — ne montrer que ce qu'on dit au client")

    for i, (titre, idee, client, chal) in enumerate(CONCEPTS, 1):
        with st.container(border=True):
            st.markdown(f"##### {i:02d} · {titre}")
            if not mode:
                st.markdown(f"**L'idée.** {idee}")
            st.markdown(
                f"<div style='background:#1b2530;color:#e8ebee;padding:18px 22px;"
                f"border-radius:3px;font-family:Georgia,serif;font-size:1.02rem;"
                f"line-height:1.6'>{client}</div>", unsafe_allow_html=True)
            if not mode:
                st.markdown(
                    f"<div style='border-left:2px solid #8c5a2b;"
                    f"background:#f5ede3;padding:12px 18px;margin-top:12px;"
                    f"font-size:.92rem'>{chal}</div>", unsafe_allow_html=True)
