"""
Notation des actions européennes sur quatre piliers, à la manière de TCP Kenz.

Décisions validées avec Allan le 2026-09-18 :
  - cinq piliers à POIDS ÉGAUX (20 % chacun) : aucun n'est privilégié sans
    raison mesurée. Le cinquième, « Résistance », a été ajouté à la demande
    d'Allan : la limite de perte de 15 % se tient au niveau du portefeuille,
    mais un panier d'actions qui baisse moins en crise permet d'en détenir
    davantage pour la même limite ;
  - grandes capitalisations seulement (10 Md€ et plus), voir core/actions.py ;
  - notes CALCULÉES AU SEIN DE CHAQUE SECTEUR : une banque ne se compare pas
    à un éditeur de logiciels, leurs PER et leurs marges n'ont pas le même
    sens (Kenz note en écart au secteur) ;
  - 30 titres retenus.

Procédure, indicateur par indicateur :
  1. orienté pour que « plus haut = mieux » (rendement des bénéfices plutôt
     que PER, dette comptée en négatif) ;
  2. bornes de plausibilité : hors bornes, la donnée est jugée fausse et
     écartée (ex. PER multiplié par 100 quand Yahoo confond pence et livres) ;
  3. écrêtage aux 5e et 95e percentiles de l'univers, pour qu'un chiffre
     extrême ne fasse pas à lui seul la note (ex. Sanofi, dont la croissance
     des bénéfices sort à −91 % à cause d'éléments exceptionnels) ;
  4. score z au sein du secteur (écart à la moyenne du secteur, en nombre
     d'écarts-types) ;
  5. note de pilier = moyenne des indicateurs disponibles (au moins la
     moitié) ; note finale = moyenne des piliers (au moins quatre sur cinq).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FINANCE = {"Finance", "Immobilier"}

# Sociétés d'investissement cotées : leur bénéfice comptable inclut la
# réévaluation de leurs participations, si bien que PER, rentabilité et
# croissance n'ont pas le sens qu'ils ont pour une entreprise. Notées comme
# les autres, elles arrivaient en tête du classement (Aker, Investor,
# Industrivärden) pour une raison purement comptable. Elles restent dans
# l'univers mais sortent de la notation.
SOCIETES_INVESTISSEMENT = {
    "INVE-B.ST": "Investor", "INDU-C.ST": "Industrivärden",
    "LUND-B.ST": "Lundbergföretagen", "LATO-B.ST": "Latour",
    "AKER.OL": "Aker", "EXO.AS": "Exor", "GBLB.BR": "Groupe Bruxelles Lambert",
    "SOF.BR": "Sofina", "ACKB.BR": "Ackermans & van Haaren",
    "KBCA.BR": "KBC Ancora", "III.L": "3i Group",
}

# indicateur : (pilier, libellé, borne basse, borne haute, ignoré pour la finance)
INDICATEURS = {
    "rdt_benefices":   ("Valorisation", "Rendement des bénéfices (1 / PER)", -0.2, 0.3, False),
    "rdt_benef_prev":  ("Valorisation", "Rendement des bénéfices attendus", -0.2, 0.3, False),
    "valeur_comptable": ("Valorisation", "Valeur comptable / cours", 0, 5, False),
    "rdt_fcf":         ("Valorisation", "Flux de trésorerie libre / capitalisation", -0.3, 0.4, True),
    "rdt_dividende":   ("Valorisation", "Rendement du dividende", 0, 15, False),
    "crois_benefices": ("Croissance", "Croissance des bénéfices sur un an", -1, 3, False),
    "crois_ventes":    ("Croissance", "Croissance du chiffre d'affaires sur un an", -0.5, 1.5, False),
    "revision_bpa":    ("Croissance", "Bénéfice attendu / bénéfice passé", -0.8, 2, False),
    "mom_12_1":        ("Dynamique", "Performance 12 mois hors dernier mois", -80, 300, False),
    "mom_6":           ("Dynamique", "Performance 6 mois", -70, 200, False),
    "roe":             ("Qualité", "Rentabilité des fonds propres", -0.5, 1.5, False),
    "roa":             ("Qualité", "Rentabilité des actifs", -0.3, 0.5, False),
    "marge_nette":     ("Qualité", "Marge nette", -0.5, 0.8, False),
    "marge_op":        ("Qualité", "Marge opérationnelle", -0.5, 0.9, True),
    "dette":           ("Qualité", "Endettement (dette / fonds propres, inversé)", -1000, 0, True),
    "vol":             ("Résistance", "Volatilité sur 3 ans (inversée)", -120, 0, False),
    "dd_2020":         ("Résistance", "Perte maximale en 2020", -100, 0, False),
    "dd_2022":         ("Résistance", "Perte maximale en 2022", -100, 0, False),
    "beta":            ("Résistance", "Bêta face à l'indice (inversé)", -4, 1, False),
}
PILIERS = ["Valorisation", "Croissance", "Dynamique", "Qualité", "Résistance"]


def indicateurs(f: pd.DataFrame) -> pd.DataFrame:
    """Construit les indicateurs orientés à partir des champs Yahoo."""
    x = pd.DataFrame(index=f.index)

    def inv(col, lo, hi):
        v = pd.to_numeric(f[col], errors="coerce")
        return 1 / v.where((v > lo) & (v <= hi))

    x["rdt_benefices"] = inv("trailingPE", 0, 150)
    x["rdt_benef_prev"] = inv("forwardPE", 0, 150)
    x["valeur_comptable"] = inv("priceToBook", 0, 50)
    cap = pd.to_numeric(f["marketCap"], errors="coerce")
    x["rdt_fcf"] = pd.to_numeric(f["freeCashflow"], errors="coerce") / cap
    x["rdt_dividende"] = pd.to_numeric(f["dividendYield"], errors="coerce")
    x["crois_benefices"] = pd.to_numeric(f["earningsGrowth"], errors="coerce")
    x["crois_ventes"] = pd.to_numeric(f["revenueGrowth"], errors="coerce")
    te = pd.to_numeric(f["trailingEps"], errors="coerce")
    fe = pd.to_numeric(f["forwardEps"], errors="coerce")
    x["revision_bpa"] = (fe / te - 1).where(te > 0)
    x["mom_12_1"] = pd.to_numeric(f["mom_12_1"], errors="coerce")
    x["mom_6"] = pd.to_numeric(f["mom_6"], errors="coerce")
    x["roe"] = pd.to_numeric(f["returnOnEquity"], errors="coerce")
    x["roa"] = pd.to_numeric(f["returnOnAssets"], errors="coerce")
    x["marge_nette"] = pd.to_numeric(f["profitMargins"], errors="coerce")
    x["marge_op"] = pd.to_numeric(f["operatingMargins"], errors="coerce")
    x["dette"] = -pd.to_numeric(f["debtToEquity"], errors="coerce")
    x["vol"] = -pd.to_numeric(f["vol_3a"], errors="coerce")
    x["dd_2020"] = pd.to_numeric(f["dd_2020"], errors="coerce")
    x["dd_2022"] = pd.to_numeric(f["dd_2022"], errors="coerce")
    x["beta"] = -pd.to_numeric(f["beta_3a"], errors="coerce")

    fin = f["secteur"].isin(FINANCE)
    for k, (_, _, lo, hi, ignore_fin) in INDICATEURS.items():
        x[k] = x[k].where((x[k] >= lo) & (x[k] <= hi))
        if ignore_fin:
            x.loc[fin, k] = np.nan
    return x


def _z_secteur(v: pd.Series, secteur: pd.Series) -> pd.Series:
    lo, hi = v.quantile(0.05), v.quantile(0.95)
    v = v.clip(lo, hi)

    def z(g):
        if g.notna().sum() < 5:                      # secteur trop maigre :
            return (g - v.mean()) / v.std()          # repli sur l'univers
        s = g.std()
        return (g - g.mean()) / s if s and s > 0 else g * 0

    return v.groupby(secteur).transform(z)


def noter(f: pd.DataFrame) -> pd.DataFrame:
    """
    f : un titre par ligne, avec 'secteur' et les champs Yahoo.
    Renvoie les notes par pilier, la note finale et le rang (percentile).
    """
    x = indicateurs(f)
    z = pd.DataFrame({k: _z_secteur(x[k], f["secteur"]) for k in x.columns},
                     index=f.index)
    out = pd.DataFrame(index=f.index)
    for p in PILIERS:
        cols = [k for k, v in INDICATEURS.items() if v[0] == p]
        dispo = z[cols].notna().sum(axis=1)
        out[p] = z[cols].mean(axis=1).where(dispo >= max(1, len(cols) // 2))
    n = out[PILIERS].notna().sum(axis=1)
    out["note"] = out[PILIERS].mean(axis=1).where(n >= 4)
    out["rang"] = out["note"].rank(pct=True) * 100
    out["piliers_dispo"] = n
    return out


VOL_QUANTILE_MAX = 0.90


def plafond_volatilite(d: pd.DataFrame) -> float:
    """
    Volatilité maximale d'un titre retenu : le 90e percentile des titres
    notés. Demande d'Allan (« des titres avec une vol okay ») : les 10 % les
    plus agités ne peuvent pas être retenus, même bien notés. Seuil MESURÉ
    sur l'univers, pas fixé à la main : il suit l'agitation des marchés.
    """
    return float(d.loc[d["note"].notna(), "vol_3a"].quantile(VOL_QUANTILE_MAX))


def selectionner(d: pd.DataFrame, n: int = 30, max_secteur: int = 4,
                 max_pays: int = 6) -> pd.DataFrame:
    """
    Les n meilleures notes, sous trois plafonds : au plus `max_secteur`
    titres par secteur et `max_pays` par pays (sans eux, une notation
    relative peut concentrer le portefeuille sur un thème), et une volatilité
    inférieure au plafond mesuré (voir plafond_volatilite).
    """
    vol_max = plafond_volatilite(d)
    retenus, par_secteur, par_pays = [], {}, {}
    for i, r in d.sort_values("note", ascending=False).iterrows():
        if pd.isna(r["note"]):
            continue
        if pd.isna(r["vol_3a"]) or r["vol_3a"] > vol_max:
            continue
        if par_secteur.get(r["secteur"], 0) >= max_secteur:
            continue
        if par_pays.get(r["pays"], 0) >= max_pays:
            continue
        retenus.append(i)
        par_secteur[r["secteur"]] = par_secteur.get(r["secteur"], 0) + 1
        par_pays[r["pays"]] = par_pays.get(r["pays"], 0) + 1
        if len(retenus) == n:
            break
    return d.loc[retenus]
