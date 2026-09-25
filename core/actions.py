"""
Univers des actions européennes en direct, assemblé et noté.

Lit data/actions/ (produit par scripts/fetch_actions.py), applique les
exclusions (core/exclusions.py), écarte de la notation les sociétés
d'investissement, puis note (core/scoring.py). Tout est recalculé à la
lecture : la notation est instantanée, et c'est ce qui la rend lisible.

La vue sectorielle du gérant (core/vue_secteurs.py) agit APRÈS la notation,
dans `selection` et non dans `univers` : les titres qu'elle écarte gardent
leur note, sans quoi on ne pourrait pas dire ce que la décision coûte.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core import exclusions, rendements, scoring, vue_secteurs

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


def selection(d: pd.DataFrame, n: int = 30, vue: bool = True) -> pd.DataFrame:
    """
    Les n titres présélectionnés. `vue` applique la vue sectorielle du
    gérant ; le passer à False sert à mesurer ce qu'elle coûte, pas à s'en
    passer en production.
    """
    notes = d[d["note"].notna()]
    if vue:
        notes = notes[~vue_secteurs.ecartees(notes)]
    return scoring.selectionner(notes, n=n)


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


# --------------------------------------------------------------------------
# Rendement espéré du panier réellement détenu
# --------------------------------------------------------------------------
# POURQUOI CE CALCUL EXISTE. Jusqu'au 2026-09-25, la poche d'actions
# européennes entrait dans l'allocation avec le rendement espéré de l'INDICE
# (étape 2, MSCI Europe). Conséquence : changer les titres retenus ne changeait
# rien au rendement du portefeuille, alors que c'est la seule poche construite
# titre par titre. Le chiffre annoncé au client ne dépendait pas de la
# sélection qu'on lui présentait.
#
# LA MÉTHODE EST CELLE DE L'ÉTAPE 2, sans exception : moyenne du rendement des
# bénéfices (1 / PER) et du dividende augmenté de la croissance réelle des
# bénéfices, puis l'inflation de l'énoncé. Rien n'est inventé ici — on applique
# la même formule à 15 lignes au lieu d'un indice. Voir
# scripts/estimer_rendements.py, fonction `actions`.
#
# POURQUOI LA MOYENNE DES 1/PER, ET NON 1/PER MOYEN. Le panier est détenu à
# parts égales : son rendement des bénéfices est la moyenne de ceux de ses
# lignes. Prendre l'inverse du PER moyen donnerait le rendement d'un panier
# pondéré par les bénéfices, qui n'est pas celui qu'on achète.
#
# CE QUE ÇA NE DIT PAS. Ce n'est pas une prévision de surperformance : c'est
# une mesure de ce que coûtent les bénéfices des sociétés retenues, comparée à
# ce que coûtent ceux de l'indice. Les deux peuvent tomber au même niveau — au
# relevé du 2026-09-18 c'est le cas, à deux décimales près — et ce résultat est
# plus solide que l'hypothèse qu'il remplace, parce qu'il est mesuré.


def rendement_panier(sel: pd.DataFrame) -> dict:
    """
    Rendement espéré du panier d'actions retenu, méthode de l'étape 2.

    `sel` : les titres RÉELLEMENT détenus (sortie de core.outlook.final), qui
    portent les colonnes `trailingPE` et `dividendYield` de data/actions/
    fondamentaux.csv.
    """
    r = rendements.charger()
    g = r["croissance"]["central"]
    infl = r["inflation"]

    per = pd.to_numeric(sel["trailingPE"], errors="coerce")
    div = pd.to_numeric(sel["dividendYield"], errors="coerce")
    # Un PER négatif ou nul (société en perte) ne s'inverse pas en rendement
    # des bénéfices : la ligne sort de cette moyenne et son absence est
    # comptée. Un dividende absent, lui, vaut ZÉRO : chez Yahoo le champ
    # manque quand la société n'en verse pas (argenx), et l'écarter de la
    # moyenne ferait croire que le panier rend plus qu'il ne rend.
    benefices = 100 / per.where(per > 0)
    m1 = float(benefices.mean())
    dividende = float(div.fillna(0).mean())
    m2 = dividende + g
    reel = (m1 + m2) / 2
    return {
        "n": len(sel), "central": reel + infl, "reel": reel,
        "m1_reel": m1, "m2_reel": m2,
        "dividende": dividende, "croissance": g, "inflation": infl,
        "per_median": float(per.median()),
        "sans_per": int(benefices.isna().sum()),
        "sans_dividende": int(div.isna().sum()),
        "methode": (f"Moyenne de deux méthodes sur les {len(sel)} titres "
                    f"détenus, à parts égales : rendement des bénéfices "
                    f"(moyenne des 1 / PER, {m1:.2f} %) et dividende "
                    f"({dividende:.2f} %) + croissance réelle des bénéfices "
                    f"({g:.2f} %), plus {infl:.0f} % d'inflation."),
    }
