"""
Mandat Lauren — chaine d'investissement en cinq etapes.

Lancer :  PYTHONPATH=. streamlit run main.py

STRUCTURE. Cinq onglets SEQUENTIELS : la sortie de chacun est l'entree du
suivant. C'est le reproche principal fait a la version precedente, qui
juxtaposait neuf onglets sans ordre lisible.

    1. Parametres d'entree    ce que le mandat impose
    2. Macro top-down         ou nous sommes dans le cycle
    3. Analyse ligne a ligne  ce qui est investissable
    4. Allocation             combien de chaque
    5. Backtests              ce que la contrainte donne

En marge de la chaine, un SIXIEME onglet qui n'en fait pas partie : une
variante qui reprend l'etape 4 en changeant la seule lecture de la limite
de 15 % (pire cas -> une annee sur vingt), pour chiffrer ce que couterait
un objectif de 4 % AU-DESSUS de l'inflation. Reserve de pitch, pas une
proposition.

PRINCIPE DE CALCUL. L'application LIT les resultats calcules (data/*.csv)
plutot que de les recalculer : l'optimisation prend une dizaine de minutes.
Ce qui se recalcule en direct le fait sur des formules fermees, donc
instantanement.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Mandat Lauren", page_icon="📐",
                   layout="wide", initial_sidebar_state="collapsed")

from core import version                                        # noqa: E402
from tabs import (t1_parametres, t2_macro, t3_lignes,            # noqa: E402
                  t4_allocation, t5_backtests, t6_croissance)

st.markdown("""
<style>
  .block-container {padding-top: 2.2rem; max-width: 1400px;}
  h1 {font-size: 1.7rem; letter-spacing: -.01em;}
  h3 {font-size: 1.12rem; margin-top: .2rem;}
  h4 {font-size: .98rem; color: #14304f; margin-top: 2rem;
      padding-bottom: .3rem; border-bottom: 1px solid #e3e6ea;}
  [data-testid="stMetricValue"] {font-size: 1.4rem;}
  .stTabs [data-baseweb="tab"] {font-size: .9rem;}
  .tampon {font-size: .72rem; color: #8a8e95; text-align: right;
           margin-top: 2.5rem; padding-top: .6rem;
           border-top: 1px solid #eceef1;}
</style>
""", unsafe_allow_html=True)

st.title("Mandat Lauren")
st.caption("Cas de gestion · 100 M€ · préserver le pouvoir d'achat sous "
           "contrainte de perte maximum de 15 %")

ONGLETS = [
    ("1 · Paramètres d'entrée",   t1_parametres.render),
    ("2 · Macro top-down",        t2_macro.render),
    ("3 · Analyse ligne à ligne", t3_lignes.render),
    ("4 · Allocation",            t4_allocation.render),
    ("5 · Backtests",             t5_backtests.render),
    ("6 · Variante croissance",   t6_croissance.render),
]

for onglet, (_, rendre) in zip(st.tabs([t for t, _ in ONGLETS]), ONGLETS):
    with onglet:
        rendre()

st.markdown(f'<div class="tampon">{version.tampon()}</div>',
            unsafe_allow_html=True)
