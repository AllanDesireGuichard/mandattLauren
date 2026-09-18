"""
Univers des actions européennes en direct, assemblé et noté.

Lit data/actions/ (produit par scripts/fetch_actions.py), applique les
exclusions (core/exclusions.py), écarte de la notation les sociétés
d'investissement, puis note (core/scoring.py). Tout est recalculé à la
lecture : la notation est instantanée, et c'est ce qui la rend lisible.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core import exclusions, scoring

DOSSIER = Path(__file__).resolve().parents[1] / "data" / "actions"

# Grandes capitalisations seulement : décision d'Allan du 2026-09-18.
TAILLE_MIN = 10e9                                    # euros

PAYS_FR = {
    "Vereinigtes Königreich": "Royaume-Uni", "Frankreich": "France",
    "Deutschland": "Allemagne", "Schweiz": "Suisse", "Niederlande": "Pays-Bas",
    "Schweden": "Suède", "Italien": "Italie", "Spanien": "Espagne",
    "Dänemark": "Danemark", "Norwegen": "Norvège", "Finnland": "Finlande",
    "Belgien": "Belgique", "Polen": "Pologne", "Österreich": "Autriche",
    "Irland": "Irlande", "Portugal": "Portugal", "Luxemburg": "Luxembourg",
    "Jersey": "Jersey", "Isle of Man": "Île de Man", "Guernsey": "Guernesey",
    "Georgien": "Géorgie", "Zypern": "Chypre", "Mexiko": "Mexique",
    "Vereinigte Staaten": "États-Unis", "Bermuda": "Bermudes",
}


def date_change() -> str:
    return str(pd.read_csv(DOSSIER / "change.csv")["date"].iloc[0])


def releve() -> str:
    return (DOSSIER / "releve.txt").read_text().strip()


def univers() -> pd.DataFrame:
    c = pd.read_csv(DOSSIER / "composition.csv")
    tk = pd.read_csv(DOSSIER / "tickers.csv")
    f = pd.read_csv(DOSSIER / "fondamentaux.csv")
    m = pd.read_csv(DOSSIER / "momentum.csv")
    r = pd.read_csv(DOSSIER / "risque.csv")
    fx = pd.read_csv(DOSSIER / "change.csv").set_index("devise")
    d = (c.merge(tk, on=["ticker_ishares", "place"])
          .merge(f, on="ticker").merge(m, on="ticker")
          .merge(r, on="ticker", how="left"))
    d["pays"] = d["pays"].map(PAYS_FR).fillna(d["pays"])
    # capitalisation en euros ; Yahoo la donne en livres pour Londres,
    # même quand le cours est en pence (GBp)
    dev = d["currency"].replace({"GBp": "GBP"})
    d["cap_eur"] = d["marketCap"] / dev.map(fx["unites_pour_1_eur"])
    d = d.join(exclusions.classer(d))
    d["societe_invest"] = d["ticker"].isin(scoring.SOCIETES_INVESTISSEMENT)
    d["trop_petite"] = d["cap_eur"] < TAILLE_MIN
    a_noter = (d["exclusion"].isna() & ~d["societe_invest"]
               & ~d["trop_petite"])
    d = d.join(scoring.noter(d[a_noter]))
    return d


def selection(d: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    return scoring.selectionner(d[d["note"].notna()], n=n)


def panier_face_indice(sel: pd.DataFrame) -> dict:
    """
    Le panier retenu, à poids égaux et converti en euros, face à l'indice
    (ETF EXSA, en euros) : volatilité sur 3 ans et pertes maximales en 2020
    et 2022. C'est le contrôle demandé par Allan : la limite de perte se tient
    au niveau du portefeuille, et ce panier en est la poche actions Europe.
    """
    px = pd.read_csv(DOSSIER / "prix_hebdo.csv", index_col=0, parse_dates=True)
    fx = pd.read_csv(DOSSIER / "change_hebdo.csv", index_col=0,
                     parse_dates=True).reindex(px.index).ffill().bfill()
    devises = sel.set_index("ticker")["currency"].replace({"GBp": "GBP"})
    eur = pd.DataFrame({t: px[t] / fx[devises[t]] for t in sel["ticker"]
                        if t in px.columns})
    r = eur.pct_change(fill_method=None)
    panier = (1 + r.mean(axis=1, skipna=True)).cumprod()
    indice = px["EXSA.DE"]

    def mesures(s: pd.Series) -> dict:
        rr = s.pct_change().dropna()
        rr3 = rr[rr.index >= rr.index[-1] - pd.DateOffset(years=3)]
        out = {"vol_3a": float(rr3.std() * 52 ** 0.5 * 100)}
        for a in ("2020", "2022"):
            x = s[f"{a}-01-01":f"{a}-12-31"]
            out[f"dd_{a}"] = float((x / x.cummax() - 1).min() * 100)
        return out

    return {"panier": mesures(panier.dropna()),
            "indice": mesures(indice.dropna()),
            "nb_titres": int(eur.shape[1]),
            "series": {"panier": panier.dropna(), "indice": indice.dropna()}}
