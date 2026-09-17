"""
Mandat Lauren -- application de pilotage.

Lance avec :  PYTHONPATH=. streamlit run main.py

Principe : l'app LIT les resultats calcules (data/*.csv) plutot que de les
recalculer. L'optimisation prend une dizaine de minutes ; la relancer a chaque
interaction rendrait l'outil inutilisable. Les onglets qui recalculent
(Faisabilite, Transmission) le font sur des formules fermees, instantanees.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Mandat Lauren", page_icon="📐",
                   layout="wide", initial_sidebar_state="expanded")

from tabs import (allocation, benchmark, concepts, fiscalite,  # noqa: E402
                  ips_tab, process, risque, transmission, univers)

st.markdown("""
<style>
  .block-container {padding-top: 2.2rem; max-width: 1400px;}
  h1 {font-size: 1.7rem; letter-spacing: -.01em;}
  h2 {font-size: 1.15rem; margin-top: 1.6rem;}
  h3 {font-size: .95rem; color: #52514e;}
  [data-testid="stMetricValue"] {font-size: 1.45rem;}
  .stTabs [data-baseweb="tab"] {font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

st.title("Mandat Lauren")
st.caption("Gestion privée · 100 M€ · préservation contre l'inflation "
           "sous contrainte de perte maximum de 15 %")

TABS = [
    ("Faisabilité", ips_tab.render),
    ("Univers", univers.render),
    ("Allocation", allocation.render),
    ("Risque", risque.render),
    ("Benchmark", benchmark.render),
    ("Fiscalité", fiscalite.render),
    ("Transmission", transmission.render),
    ("Concepts", concepts.render),
    ("Process", process.render),
]

for tab, (_, fn) in zip(st.tabs([t for t, _ in TABS]), TABS):
    with tab:
        fn()
