"""Onglet Univers -- les supports retenus et le controle qualite."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import viz
from core.esg import EXCLUSIONS, RECOMMENDED_FAMILY, esg_status
from core.ips import SAA_INDICATIVE

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


@st.cache_data
def _uni() -> pd.DataFrame:
    p = ROOT / "data" / "universe.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    n = ROOT / "data" / "extension_names.csv"
    if n.exists():
        nm = pd.read_csv(n).set_index("ticker")["name"].to_dict()
        df["name"] = df.apply(
            lambda r: nm.get(r.ticker, r["name"])
            if not isinstance(r["name"], str) or not r["name"] else r["name"],
            axis=1)
    return df


def render() -> None:
    st.header("Univers investissable")

    df = _uni()
    if df.empty:
        st.info("Lancer `scripts/select_instruments.py`.")
        return

    c = st.columns(4)
    c[0].metric("Candidats évalués", "226")
    c[1].metric("Séries exploitables", "182")
    c[2].metric("Supports retenus", str(len(df)))
    c[3].metric("Supports principaux", str((df.role == "primary").sum()))

    st.markdown("## Exclusions du mandat")
    st.dataframe(pd.DataFrame([
        {"Secteur": e.label,
         "Seuils de chiffre d'affaires":
             " · ".join(f"{k} {v:.0%}" for k, v in e.thresholds.items())}
        for e in EXCLUSIONS]), width='stretch', hide_index=True)

    st.success(f"**Famille d'indices retenue : {RECOMMENDED_FAMILY}.** "
               "Le mandat demande trois exclusions précises, pas une démarche "
               "best-in-class. ESG Screened exclut exactement ces trois secteurs "
               "et rien de plus — l'univers reste à ~95 % de l'indice parent, "
               "donc le coût d'opportunité du filtre est négligeable.")

    st.markdown("### La portée du filtre — une erreur de catégorie à éviter")
    st.markdown("""
Les trois exclusions visent des **émetteurs d'entreprise**. Il n'y a rien à
filtrer dans une obligation d'État allemande ou dans un lingot d'or. Exiger un
label ESG sur ces classes reviendrait soit à payer une surcouche marketing sans
contenu, soit à écarter des instruments parfaitement conformes au mandat.
""")
    st.dataframe(pd.DataFrame([
        {"Classe": viz.LABEL[c], "Poids": SAA_INDICATIVE[c],
         "Filtre ESG": esg_status(c)}
        for c in SAA_INDICATIVE]).style.format({"Poids": "{:.0%}"}),
        width='stretch', hide_index=True)

    st.markdown("## Supports retenus")
    show = df[df.role == "primary"].copy()
    show["Classe"] = show.saa_class.map(viz.LABEL).fillna(show.saa_class)
    show["Poids"] = show.saa_class.map(SAA_INDICATIVE)
    show = show.sort_values("Poids", ascending=False)
    st.dataframe(
        show[["Poids", "ticker", "name", "Classe", "years", "vol",
              "max_dd", "distribution"]].rename(columns={
                  "ticker": "Code", "name": "Libellé", "years": "Historique",
                  "vol": "Volatilité", "max_dd": "Perte max",
                  "distribution": "Type"}).style.format({
                      "Poids": "{:.0%}", "Historique": "{:.1f} ans",
                      "Volatilité": "{:.1%}", "Perte max": "{:.1%}"}),
        width='stretch', hide_index=True)

    st.markdown("## Contrôle qualité des prix")
    st.error("""
**Les séries de cotation londoniennes mélangent les devises.** Sans filtre,
un ETF d'obligations d'État 1-3 ans affichait **29 % de volatilité et 99 % de
drawdown**.

```
SPXS.L   2014-01-02   303,05 → 3,02      rupture ×100, pence → livres
SGLN.L   2011-04      −39 %, +64 %, −38 %   oscillation entre deux lignes
```

Une erreur de données ne se voit pas dans le résultat : **elle le déplace
silencieusement.** D'où `core/quality.py` — réparation des ruptures d'échelle,
rejet des séries oscillantes, et contrôle de plausibilité par classe d'actifs.
""")

    st.warning("""
**Trois tickers n'étaient pas ce que leur code suggérait.** `CTA.L` est
*CT Automotive Group plc*, un équipementier automobile — pas un fonds de
tendance. `XZEC.DE` et `EEDS.L` sont des fonds d'actions, pas du crédit. Leur
volatilité les a trahis. Vérifier le libellé, jamais deviner sur le code.
""")
