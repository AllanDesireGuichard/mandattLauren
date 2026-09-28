"""
Export Excel des mesures de risque du portefeuille retenu et du panier
d'actions — outputs/Mandat_Lauren_risque.xlsx

Rien n'est inventé ici : le portefeuille, ses poids et ses séries viennent de
core/allocation.py, le panier d'actions de core/actions.py + core/outlook.py.
Ce script ne fait que MESURER, et chaque convention est écrite dans l'onglet
« Lecture » du classeur.

TROIS CHOIX DE MÉTHODE, parce qu'ils ne sont pas donnés par le mandat :

1. TAUX SANS RISQUE. Le Sharpe compare un excès de rendement à un risque, et
   l'excès se mesure contre ce qu'on aurait eu sans risque À CHAQUE INSTANT.
   Un taux constant d'aujourd'hui (€STR 2,44 %) appliqué à 2006-2026 ferait
   dire au ratio que l'argent ne coûtait rien en 2008, quand la BCE était à
   4 %. On prend donc le CHEMIN : la série `etats_courts` (échelle AAA 6-24
   mois reconstituée sur la courbe BCE), qui est le placement sans risque de
   ce mandat. Le Sharpe au taux constant du jour est donné à côté, pour
   comparaison, jamais seul.

2. INDICE DE RÉFÉRENCE. Le mandat n'en désigne AUCUN — c'est un mandat à
   objectif (battre 4 % d'inflation, perdre au plus 15 %), pas un mandat
   indiciel. Une tracking error n'a donc pas de référence naturelle : elle
   est calculée contre deux repères construits ici et nommés comme tels,
   30/70 et 50/50. Le chiffre mesure un ÉCART À UN REPÈRE CHOISI, pas une
   déviation par rapport à une contrainte du client.

3. BÊTA DES ACTIONS, EN EUROS. data/actions/risque.csv porte un `beta_3a`
   calculé sur les cours en DEVISE LOCALE face à un indice en euros : pour
   NEXT ou Airtel (GBp), IHG (GBp), Var Energi (NOK), il mélange deux
   monnaies et mesure en partie le taux de change. On le recalcule ici sur
   les cours CONVERTIS EN EUROS, et les deux colonnes sont affichées côte à
   côte. L'écart est la part de change.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from core import actions, allocation, ips, outlook, taux  # noqa: E402

SEM = 52                                   # pas hebdomadaire, W-FRI
SORTIE = RACINE / "outputs" / "Mandat_Lauren_risque.xlsx"

# Repères construits pour la tracking error (voir l'en-tête, point 2).
REPERES = {
    "30/70": {"poche_actions": .30, "etats_longs": .70},
    "50/50": {"poche_actions": .50, "etats_longs": .50},
}


# ---------------------------------------------------------------- outils

def hebdo(v: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Variations hebdomadaires (vendredi), la convention de core/allocation."""
    return v.resample("W-FRI").last().pct_change(fill_method=None)


def annualise(r: pd.Series) -> float:
    """Rendement annualisé géométrique d'une série de variations."""
    n = len(r.dropna())
    return float((1 + r.dropna()).prod() ** (SEM / n) - 1) if n else np.nan


def mesures(r: pd.Series, rf: pd.Series, v: pd.Series) -> dict:
    """Le bloc standard : rendement, risque, Sharpe, pire baisse, VaR."""
    r, rf = r.dropna().align(rf.dropna(), join="inner")
    ex = r - rf
    vol = float(r.std() * SEM ** .5)
    dd = v / v.cummax() - 1
    q = float(np.quantile(r, .05))
    baisses = r[r < 0]
    return {
        "Rendement annualisé %": annualise(r) * 100,
        "Volatilité annuelle %": vol * 100,
        "Excès sur le sans-risque %": annualise(r) * 100 - annualise(rf) * 100,
        "Sharpe": float(ex.mean() / ex.std() * SEM ** .5) if ex.std() else np.nan,
        "Sortino": float(ex.mean() / baisses.std() * SEM ** .5)
                   if len(baisses) > 1 else np.nan,
        "Pire baisse depuis le plus haut %": float(dd.min() * 100),
        "VaR 95 % hebdomadaire %": q * 100,
        "CVaR 95 % hebdomadaire %": float(r[r <= q].mean() * 100),
        "Semaines mesurées": int(len(r)),
    }


def beta(a: pd.Series, b: pd.Series) -> tuple[float, float, float]:
    """Bêta, alpha annualisé et R² de a expliqué par b."""
    x, y = b.dropna().align(a.dropna(), join="inner")
    if len(x) < 30:
        return np.nan, np.nan, np.nan
    bta = float(np.cov(y, x)[0, 1] / np.var(x, ddof=1))
    alpha = float((y.mean() - bta * x.mean()) * SEM)
    r2 = float(np.corrcoef(y, x)[0, 1] ** 2)
    return bta, alpha * 100, r2


def tracking(r: pd.Series, ref: pd.Series) -> dict:
    """Écart de suivi et ratio d'information contre un repère."""
    a, b = r.dropna().align(ref.dropna(), join="inner")
    d = a - b
    te = float(d.std() * SEM ** .5)
    return {"Écart annualisé %": (annualise(a) - annualise(b)) * 100,
            "Tracking error %": te * 100,
            "Ratio d'information": float(d.mean() * SEM / te) if te else np.nan,
            "Corrélation": float(np.corrcoef(a, b)[0, 1])}


# ------------------------------------------------- niveau portefeuille

def bloc_portefeuille() -> dict:
    """
    Mesures du portefeuille retenu, de ses repères et de chaque support.

    ATTENTION À LA FENÊTRE. Toute fonction qui aligne les colonnes par un
    dropna coupe l'histoire sur la plus courte d'entre elles — le bitcoin,
    qui ne commence qu'au 2014-09-17. La première version de ce script
    mesurait ainsi douze ans au lieu de vingt, et annonçait 4,03 % de
    rendement réalisé au lieu de 4,47 %, sans que rien ne le signale.
    `allocation.avec_poche_actions` est depuis protégée ; ici on construit
    la matrice à la main, avec les SEULES lignes mesurées — celles du
    portefeuille et celles des repères — pour ne pas dépendre de ce garde-fou.
    """
    brut = allocation.series()
    debut = allocation.resultats()["fenetre"][0]
    brut = brut[debut:]
    poids = allocation.resultats()["scenarios"][allocation.RETENU]["poids"]
    poids = {k: x for k, x in poids.items() if x > 0}

    poche = allocation.portefeuille(brut, allocation.MIX_ACTIONS)
    lignes_p = ["poche_actions"] + [k for k in allocation.ORDRE
                                    if k in poids and k != "poche_actions"]
    besoin = sorted({k for w in REPERES.values() for k in w} | set(lignes_p))
    s = pd.concat([poche.rename("poche_actions")]
                  + [brut[k] for k in besoin if k != "poche_actions"],
                  axis=1, sort=False).dropna()

    val = {"Portefeuille retenu": allocation.portefeuille(s, poids)}
    for nom, w in REPERES.items():
        val[f"Repère {nom}"] = allocation.portefeuille(s, w)
    for k in s.columns:
        val[k] = s[k]
    # les supports non détenus, mesurés pour comparaison, chacun sur sa
    # propre histoire : les mêler au tableau aligné raccourcirait la fenêtre
    for k in allocation.ORDRE:
        if k not in val and k not in allocation.HORS_CALCUL:
            val[k] = brut[k]
    val = pd.DataFrame(val)

    r = hebdo(val)
    rf = r["etats_courts"]
    lignes = {}
    for k in val.columns:
        m = mesures(r[k], rf, val[k].dropna())
        b, al, r2 = beta(r[k], r["poche_actions"])
        m["Bêta / poche actions"] = b
        m["Alpha annualisé / poche actions %"] = al
        m["R² / poche actions"] = r2
        for nom in REPERES:
            t = tracking(r[k], r[f"Repère {nom}"])
            m[f"Tracking error vs {nom} %"] = t["Tracking error %"]
            m[f"Ratio d'information vs {nom}"] = t["Ratio d'information"]
        lignes[k] = m
    tableau = pd.DataFrame(lignes)

    # Sharpe au taux constant du jour, pour comparaison seulement
    estr = taux.charger()["points"]["estr"]["valeur"] / 100
    hebdo_estr = (1 + estr) ** (1 / SEM) - 1
    cst = {}
    for k in val.columns:
        ex = (r[k] - hebdo_estr).dropna()
        cst[k] = float(ex.mean() / ex.std() * SEM ** .5)
    tableau.loc[f"Sharpe au taux constant du jour ({estr*100:.2f} %)"] = cst

    rp = r[lignes_p].dropna()
    cov = rp.cov() * SEM
    corr = rp.corr()

    w = pd.Series({k: poids[k] for k in lignes_p})
    var = float(w @ cov @ w)
    sigma = var ** .5
    mcr = (cov @ w) / sigma
    contrib = w * mcr
    risque = pd.DataFrame({
        "Poids %": w * 100,
        "Volatilité de la ligne %": np.sqrt(np.diag(cov)) * 100,
        "Contribution marginale %": mcr * 100,
        "Contribution au risque %": contrib * 100,
        "Part du risque %": contrib / sigma * 100,
        "Part du capital %": w * 100,
    })
    risque.loc["Total"] = [w.sum() * 100, np.nan, np.nan, sigma * 100,
                           100.0, 100.0]
    return {"valeurs": val, "rendements": r, "mesures": tableau,
            "cov": cov, "corr": corr, "risque": risque,
            "variance": var, "sigma": sigma, "poids": poids,
            "estr": estr, "debut": s.index[0], "fin": s.index[-1]}


# ------------------------------------------------------ niveau actions

def panier_eur(sel: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Cours hebdomadaires des titres retenus, convertis en euros, + l'indice."""
    d = RACINE / "data" / "actions"
    px = pd.read_csv(d / "prix_hebdo.csv", index_col=0, parse_dates=True)
    fx = pd.read_csv(d / "change_hebdo.csv", index_col=0,
                     parse_dates=True).reindex(px.index).ffill().bfill()
    dev = sel.set_index("ticker")["currency"].replace({"GBp": "GBP"})
    eur = pd.DataFrame({t: px[t] / fx[dev[t]] for t in sel["ticker"]
                        if t in px.columns})
    return eur, px["EXSA.DE"]


def bloc_actions() -> dict:
    u = actions.univers()
    trente = actions.selection(u)
    sel = outlook.final(trente)
    eur, indice = panier_eur(sel)

    r = eur.pct_change(fill_method=None)
    ri = indice.pct_change(fill_method=None)
    trois_ans = r.index >= r.index[-1] - pd.DateOffset(years=3)

    # le panier est détenu à parts égales (décision de l'étape 3)
    n = eur.shape[1]
    val_panier = (1 + r.mean(axis=1, skipna=True)).cumprod().dropna()
    r_panier = val_panier.pct_change().dropna()

    lignes = []
    for _, t in sel.iterrows():
        k = t["ticker"]
        x = r[k] if k in r else pd.Series(dtype=float)
        b3, a3, r23 = beta(x[trois_ans], ri[trois_ans])
        bt, at, r2t = beta(x, ri)
        xx = x.dropna()
        x3 = x[trois_ans].dropna()
        lignes.append({
            "Ticker": k, "Société": t["nom"], "Secteur": t["secteur"],
            "Pays": t["pays"], "Devise de cotation": t["devise"],
            "Poids dans le panier %": 100 / n,
            "Capitalisation Md€": t["cap_eur"] / 1e9,
            "PER": t["trailingPE"], "PER prévisionnel": t["forwardPE"],
            "Prix / actif net": t["priceToBook"],
            "Dividende %": t["dividendYield"],
            "Rentabilité des fonds propres %": t["returnOnEquity"] * 100
                if pd.notna(t["returnOnEquity"]) else np.nan,
            "Marge opérationnelle %": t["operatingMargins"] * 100
                if pd.notna(t["operatingMargins"]) else np.nan,
            "Dette / fonds propres": t["debtToEquity"],
            "Momentum 12-1 %": t["mom_12_1"], "Momentum 6 mois %": t["mom_6"],
            "Volatilité 3 ans, EUR %": float(x3.std() * SEM ** .5 * 100)
                if len(x3) > 30 else np.nan,
            "Volatilité 3 ans, devise locale %": t["vol_3a"],
            "Bêta 3 ans, EUR": b3,
            "Bêta 3 ans, devise locale (fichier)": t["beta_3a"],
            "Part du change (écart de bêta)": b3 - t["beta_3a"]
                if pd.notna(t["beta_3a"]) else np.nan,
            "Alpha 3 ans annualisé, EUR %": a3, "R² 3 ans": r23,
            "Bêta 2019-2026, EUR": bt, "R² 2019-2026": r2t,
            "Corrélation à l'indice, 3 ans": np.sqrt(r23) if pd.notna(r23)
                else np.nan,
            "Perte max 2020 %": t["dd_2020"], "Perte max 2022 %": t["dd_2022"],
            "Note des 5 piliers": t["note"],
            "Valorisation": t["Valorisation"], "Croissance": t["Croissance"],
            "Dynamique": t["Dynamique"], "Qualité": t["Qualité"],
            "Résistance": t["Résistance"],
            "Note avenir (analystes)": t["note_avenir"],
            "Potentiel vs cours cible %": t["potentiel"],
            "Révisions de BPA 30 j %": t["revision"],
            "Solde hausses − baisses": t["solde"],
            "Nombre d'analystes": t["analystes"],
            "Semaines de cours": int(xx.shape[0]),
        })
    fiches = pd.DataFrame(lignes)

    # le panier face à l'indice
    def bloc(x: pd.Series, v: pd.Series, ref: pd.Series) -> dict:
        b, a, r2 = beta(x, ref)
        t = tracking(x, ref)
        dd = v / v.cummax() - 1
        q = float(np.quantile(x.dropna(), .05))
        # Les quatre lignes marquées (biaisé) mesurent la performance
        # PASSÉE d'une sélection faite avec les données d'AUJOURD'HUI : le
        # panier ne pouvait pas être détenu en 2019. Elles sont gardées parce
        # qu'un lecteur les cherchera, et marquées pour qu'il ne les lise pas
        # comme une surperformance. Le risque (volatilité, bêta, tracking
        # error, VaR) ne souffre pas du même biais : il décrit ce que le
        # panier EST, pas ce qu'il aurait rapporté.
        return {
            "Rendement annualisé % (biaisé)": annualise(x) * 100,
            "Volatilité annuelle %": float(x.std() * SEM ** .5 * 100),
            "Bêta / STOXX 600": b, "Alpha annualisé % (biaisé)": a, "R²": r2,
            "Tracking error %": t["Tracking error %"],
            "Ratio d'information (biaisé)": t["Ratio d'information"],
            "Écart de rendement annualisé % (biaisé)": t["Écart annualisé %"],
            "Pire baisse depuis le plus haut %": float(dd.min() * 100),
            "VaR 95 % hebdomadaire %": q * 100,
            "CVaR 95 % hebdomadaire %": float(x[x <= q].mean() * 100),
            "Semaines mesurées": int(len(x.dropna())),
        }

    ind_v = indice.dropna()
    face = pd.DataFrame({
        f"Panier, {n} titres à parts égales": bloc(r_panier, val_panier, ri),
        "STOXX Europe 600 (EXSA)": bloc(ri.dropna(), ind_v, ri),
    })

    # même chose sur les trois dernières années
    face3 = pd.DataFrame({
        f"Panier, {n} titres (3 ans)":
            bloc(r_panier[r_panier.index >= r_panier.index[-1]
                          - pd.DateOffset(years=3)],
                 val_panier[val_panier.index >= val_panier.index[-1]
                            - pd.DateOffset(years=3)],
                 ri[trois_ans]),
        "STOXX Europe 600 (3 ans)":
            bloc(ri[trois_ans].dropna(),
                 ind_v[ind_v.index >= ind_v.index[-1]
                       - pd.DateOffset(years=3)], ri[trois_ans]),
    })

    # covariance, corrélation et décomposition du risque du panier
    noms = dict(zip(fiches["Ticker"], fiches["Société"]))
    r3 = r[trois_ans].dropna(axis=1, how="all")
    cov = r3.cov() * SEM
    corr = r3.corr()
    w = pd.Series(1 / cov.shape[0], index=cov.index)
    sig = float((w @ cov @ w) ** .5)
    mcr = (cov @ w) / sig
    contrib = w * mcr
    deco = pd.DataFrame({
        "Société": [noms.get(k, k) for k in cov.index],
        "Poids %": w * 100,
        "Volatilité 3 ans %": np.sqrt(np.diag(cov)) * 100,
        "Contribution marginale %": mcr * 100,
        "Contribution au risque %": contrib * 100,
        "Part du risque %": contrib / sig * 100,
    })
    deco.loc["Total"] = ["Panier", 100.0, np.nan, np.nan, sig * 100, 100.0]

    cov = cov.rename(index=noms, columns=noms)
    corr = corr.rename(index=noms, columns=noms)

    # `outlook.juger` renvoie déjà les 30 augmentés des mesures d'avenir et
    # du motif d'exclusion : on le prend tel quel plutôt que de refaire une
    # jointure qui perdait les colonnes (constaté à la génération).
    jugees = outlook.juger(trente, outlook.indicateurs())
    colonnes_30 = ["ticker", "nom", "secteur", "pays", "cap_eur", "note",
                   "rang", "Valorisation", "Croissance", "Dynamique",
                   "Qualité", "Résistance", "trailingPE", "dividendYield",
                   "mom_12_1", "vol_3a", "beta_3a", "note_avenir",
                   "potentiel", "revision", "revisions_30j", "solde",
                   "dispersion", "analystes", "avis", "motif"]
    presel = jugees[[c for c in colonnes_30 if c in jugees.columns]].copy()
    presel["retenu"] = presel["ticker"].isin(sel["ticker"])

    return {"fiches": fiches, "face": face, "face3": face3, "cov": cov,
            "corr": corr, "deco": deco, "presel": presel,
            "n": n, "debut": eur.index[0], "fin": eur.index[-1],
            "panier": val_panier, "indice": ind_v,
            "sigma": sig}


# ------------------------------------------------------------- écriture

FORMATS = {}


def ecrire(xl, feuille: str, df: pd.DataFrame, titre: str, note: str = "",
           index: bool = True, largeur: int = 22, pct: bool = False) -> None:
    df.to_excel(xl, sheet_name=feuille, startrow=3, index=index)
    ws = xl.sheets[feuille]
    ws.write(0, 0, titre, FORMATS["titre"])
    if note:
        ws.write(1, 0, note, FORMATS["note"])
    ws.set_column(0, 0, max(largeur, 34), FORMATS["texte"])
    ws.set_column(1, df.shape[1] + 1, largeur,
                  FORMATS["pct"] if pct else FORMATS["num"])
    ws.freeze_panes(4, 1)
    ws.set_row(3, None, FORMATS["entete"])


def main() -> None:
    p = bloc_portefeuille()
    a = bloc_actions()
    SORTIE.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(SORTIE, engine="xlsxwriter") as xl:
        wb = xl.book
        FORMATS.update({
            "titre": wb.add_format({"bold": True, "font_size": 13}),
            "note": wb.add_format({"font_size": 9, "italic": True,
                                   "font_color": "#555555"}),
            "entete": wb.add_format({"bold": True, "bottom": 1,
                                     "text_wrap": True, "valign": "bottom"}),
            "texte": wb.add_format({"text_wrap": False}),
            "num": wb.add_format({"num_format": "0.00"}),
            "pct": wb.add_format({"num_format": "0.00"}),
            "corps": wb.add_format({"text_wrap": True, "valign": "top"}),
            "gras": wb.add_format({"bold": True}),
        })

        # ---- Lecture
        ws = wb.add_worksheet("Lecture")
        xl.sheets["Lecture"] = ws
        ws.set_column(0, 0, 32, FORMATS["texte"])
        ws.set_column(1, 1, 110, FORMATS["corps"])
        L = [
            ("Mandat Lauren — mesures de risque", ""),
            ("", ""),
            ("Ce que contient ce classeur",
             "Les mesures de risque du portefeuille retenu à l'étape 4 et du "
             "panier d'actions européennes retenu à l'étape 3. Tout est "
             "recalculé depuis les séries du projet ; aucun chiffre n'est "
             "recopié d'un autre document."),
            ("Portefeuille mesuré",
             "Scénario « " + allocation.resultats()["scenarios"]
             [allocation.RETENU]["nom"] + " » — "
             + ", ".join(f"{k} {v*100:.2f} %" for k, v in p["poids"].items())),
            ("Fenêtre, portefeuille",
             f"{p['debut']:%d/%m/%Y} → {p['fin']:%d/%m/%Y}, variations "
             f"hebdomadaires du vendredi (data/indices_longs.csv). "
             f"Rééquilibrage mensuel, comme à l'étape 4."),
            ("Fenêtre, actions",
             f"{a['debut']:%d/%m/%Y} → {a['fin']:%d/%m/%Y}, variations "
             f"hebdomadaires (data/actions/prix_hebdo.csv). Les cours sont "
             f"CONVERTIS EN EUROS avant tout calcul."),
            ("", ""),
            ("Taux sans risque", ""),
            ("Convention retenue",
             "La série `etats_courts` — échelle AAA 6 à 24 mois reconstituée "
             "sur la courbe BCE. C'est le placement sans risque de ce mandat, "
             "et c'est un CHEMIN : il vaut 4 % en 2008 et 0 % en 2021, ce "
             "qu'un taux d'aujourd'hui appliqué à vingt ans ne sait pas dire."),
            ("Convention de comparaison",
             f"€STR du {taux.charger()['points']['estr']['date']}, "
             f"{p['estr']*100:.2f} %, constant sur toute la fenêtre. Donné "
             f"sur la dernière ligne de l'onglet « Portefeuille », jamais "
             f"seul : il surestime le Sharpe des années de taux hauts."),
            ("", ""),
            ("Indice de référence", ""),
            ("Ce que dit le mandat",
             "RIEN. Le mandat fixe un objectif (battre 4 % d'inflation) et "
             "une limite (perdre au plus 15 %) : il n'est indexé sur aucun "
             "indice. Une tracking error n'y a donc pas de référence "
             "naturelle — et ce n'est pas une mesure de conformité au mandat."),
            ("Repères construits ici",
             "« 30/70 » = 30 % poche actions (Europe 40 / États-Unis 35 / "
             "Japon 10 / émergents 15) + 70 % emprunts d'État zone euro. "
             "« 50/50 » = le même, moitié-moitié. Le premier a la même "
             "proportion d'actions que le portefeuille : sa tracking error "
             "mesure le CHOIX DES SUPPORTS (indexées, or, échelle courte). Le "
             "second mesure en plus l'écart d'allocation."),
            ("", ""),
            ("Bêtas des actions", ""),
            ("Deux colonnes, et pourquoi",
             "data/actions/risque.csv calcule le bêta sur les cours en DEVISE "
             "LOCALE face à un indice en euros. Pour les titres cotés à "
             "Londres ou Oslo, ce chiffre contient du taux de change. La "
             "colonne « Bêta 3 ans, EUR » le recalcule après conversion ; la "
             "colonne « Part du change » donne l'écart entre les deux. C'est "
             "le bêta EUR qui vaut pour un investisseur en euros."),
            ("", ""),
            ("Ce que ces chiffres ne disent pas", ""),
            ("Limite 1",
             "Les séries longues sont celles qui ont servi à CONSTRUIRE le "
             "portefeuille (l'optimisation visait 14 % de perte maximale). "
             "La pire baisse mesurée ici ne prouve donc rien — elle rappelle "
             "la cible. Ce qui s'y ajoute : Sharpe, VaR, bêtas, covariances, "
             "que l'étape 4 ne regardait pas."),
            ("Limite 2",
             "Le panier d'actions ne commence qu'en 2019 (les cours ligne à "
             "ligne s'arrêtent là) : il ne traverse ni 2008 ni 2011. Son "
             "bêta et sa tracking error valent pour 2019-2026, pas pour un "
             "cycle complet."),
            ("Limite 3",
             "LA PERFORMANCE PASSÉE DU PANIER D'ACTIONS NE VEUT RIEN DIRE. "
             "Les quinze titres ont été choisis avec les fondamentaux, le "
             "momentum et les attentes d'analystes de septembre 2026, puis "
             "rejoués depuis 2019 : le résultat ne pouvait qu'être bon, et il "
             "l'est (+14 points par an sur l'indice). Les lignes concernées "
             "portent la mention (biaisé) et ne doivent pas être montrées au "
             "client comme une surperformance. Ce qui reste interprétable : "
             "la volatilité, le bêta, la tracking error, la VaR, les "
             "corrélations — ils décrivent ce que le panier EST."),
            ("Limite 4",
             "Trois des quinze lignes sont cotées hors zone euro (Londres, "
             "Oslo). Leur risque en euros inclut un risque de change non "
             "couvert, compris dans les volatilités et bêtas EUR de cet "
             "onglet mais jamais isolé."),
            ("Limite 5",
             "La sélection d'actions est RECALCULÉE à l'exécution, à partir "
             "de data/actions/. Ce classeur porte celle du jour de sa "
             "génération. Un nouveau relevé la change."),
            ("", ""),
            ("Généré le", pd.Timestamp.today().strftime("%d/%m/%Y")),
            ("Relevés utilisés",
             f"Actions {actions.releve()} · Outlook {outlook.releve()} · "
             f"Taux {taux.charger()['releve']} · Optimisation "
             f"{allocation.resultats()['releve']}"),
            ("Régénérer", "python3 scripts/export_risque.py"),
        ]
        for i, (g, d) in enumerate(L):
            ws.write(i, 0, g, FORMATS["gras"] if d == "" else FORMATS["texte"])
            ws.write(i, 1, d)
        ws.set_row(0, 20)

        ecrire(xl, "Portefeuille", p["mesures"],
               "Portefeuille retenu, repères et supports ligne à ligne",
               f"Hebdomadaire {p['debut']:%d/%m/%Y} → {p['fin']:%d/%m/%Y}. "
               f"Sans risque : série etats_courts. Bêtas contre la poche "
               f"actions 40/35/10/15.", largeur=17)

        ecrire(xl, "Contributions au risque", p["risque"],
               "D'où vient la volatilité du portefeuille",
               f"Volatilité totale {p['sigma']*100:.2f} % par an. La part du "
               f"risque se compare à la part du capital : l'écart est la "
               f"concentration du risque.", largeur=20)

        ecrire(xl, "Covariance", p["cov"],
               "Covariances annualisées des supports détenus",
               "Variations hebdomadaires annualisées (×52). La diagonale est "
               "la variance de chaque ligne ; sa racine est sa volatilité.",
               largeur=16)

        ecrire(xl, "Corrélation", p["corr"],
               "Corrélations des supports détenus",
               "Mêmes variations hebdomadaires, toute la fenêtre. L'étape 4 "
               "de l'application les redonne séparément hors crise et en "
               "crise — elles ne sont pas les mêmes.", largeur=16)

        ecrire(xl, "Actions — les 15", a["fiches"],
               f"Les {a['n']} titres détenus, à parts égales",
               "Fondamentaux, notes des cinq piliers, vue des analystes et "
               "risque. Volatilités et bêtas calculés sur les cours convertis "
               "en euros.", index=False, largeur=15)

        ecrire(xl, "Actions — panier vs indice", a["face"],
               "Le panier face au STOXX Europe 600",
               f"Fenêtre {a['debut']:%d/%m/%Y} → {a['fin']:%d/%m/%Y}, panier "
               f"équipondéré non rééquilibré. LES LIGNES MARQUÉES (BIAISÉ) NE "
               f"SE LISENT PAS COMME UNE SURPERFORMANCE : les titres ont été "
               f"choisis avec les données de 2026 puis rejoués depuis 2019. "
               f"Les mesures de risque, elles, restent valables.", largeur=26)

        ecrire(xl, "Actions — 3 ans", a["face3"],
               "Le panier face à l'indice, trois dernières années",
               "Même méthode et même biais de sélection sur les lignes de "
               "performance. Fenêtre courte : c'est celle des bêtas et "
               "volatilités du fichier de risque.", largeur=26)

        ecrire(xl, "Actions — contributions", a["deco"],
               "D'où vient la volatilité du panier",
               f"Trois ans, cours en euros. Volatilité du panier "
               f"{a['sigma']*100:.2f} % par an contre "
               f"{a['deco']['Volatilité 3 ans %'][:-1].mean():.2f} % en "
               f"moyenne par ligne : l'écart est la diversification.",
               largeur=20)

        ecrire(xl, "Actions — covariance", a["cov"],
               "Covariances annualisées des 15 titres (3 ans, EUR)",
               "Diagonale = variance annuelle de chaque titre.", largeur=13)

        ecrire(xl, "Actions — corrélation", a["corr"],
               "Corrélations des 15 titres (3 ans, EUR)",
               "C'est ce tableau qui explique pourquoi le panier est moins "
               "volatil que ses lignes.", largeur=13)

        ecrire(xl, "Actions — les 30", a["presel"],
               "Les 30 présélectionnées, avant le second étage",
               "La colonne `retenu` dit lesquelles passent le filtre des "
               "attentes d'analystes. Les 15 autres gardent leur note : "
               "c'est ce qui permet de dire ce que le filtre coûte.",
               index=False, largeur=14)

    print(f"Écrit : {SORTIE}")
    print(f"Portefeuille : vol {p['sigma']*100:.2f} %, "
          f"Sharpe {p['mesures'].loc['Sharpe', 'Portefeuille retenu']:.2f}, "
          f"TE 30/70 {p['mesures'].loc['Tracking error vs 30/70 %', 'Portefeuille retenu']:.2f} %")
    c = a["face"].columns[0]
    print(f"Panier : vol {a['face'].loc['Volatilité annuelle %', c]:.2f} %, "
          f"bêta {a['face'].loc['Bêta / STOXX 600', c]:.2f}, "
          f"TE {a['face'].loc['Tracking error %', c]:.2f} %")


if __name__ == "__main__":
    main()
