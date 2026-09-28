"""
Classeur de risque du mandat — outputs/Mandat_Lauren_risque.xlsx

TOUT CE QUI SE CALCULE EST UNE FORMULE. Les seuls nombres écrits en dur sont
les DONNÉES : les niveaux hebdomadaires des supports et des titres, les poids
du portefeuille (une décision d'allocation, pas un calcul) et les notes de
l'étape 3 (produites par core/scoring.py et core/outlook.py). Volatilités,
rendements, Sharpe, bêtas, covariances, corrélations, contributions au risque,
tracking error et ratios d'information sont écrits comme formules Excel et
recalculés à l'ouverture. On peut changer un poids et voir le risque bouger.

Deux onglets de données portent les séries :
  « Données »         niveaux hebdomadaires des 5 supports et du portefeuille,
                      puis variations, log-variations, excès sur le sans-risque
                      et baisse depuis le plus haut — toutes en formules.
  « Données actions » mêmes colonnes pour les 15 titres (cours CONVERTIS EN
                      EUROS), l'indice et le panier équipondéré.

DEUX CHOIX DE MÉTHODE, rappelés dans l'onglet « Lecture » :

1. Le TAUX SANS RISQUE est la série `etats_courts` — l'échelle AAA 6 à 24 mois
   reconstituée sur la courbe BCE. C'est un chemin, pas un taux fixe : il vaut
   4 % en 2008 et 0 % en 2021, ce qu'un taux d'aujourd'hui appliqué à vingt ans
   ne sait pas dire.

2. La TRACKING ERROR n'existe qu'au niveau des ACTIONS, contre le STOXX Europe
   600. Le portefeuille, lui, n'a pas d'indice de référence : le mandat fixe un
   objectif et une limite, il n'est indexé sur rien. Un écart de suivi y serait
   un écart à un repère inventé.

Le chemin du portefeuille est rééquilibré chaque mois, comme à l'étape 4 : ce
niveau-là vient de core/allocation.py et entre dans le classeur comme donnée.
Le classeur mesure, il ne refait pas la gestion.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from xlsxwriter.utility import xl_col_to_name as LET

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from core import actions, allocation, outlook, taux  # noqa: E402

SEM = 52
SORTIE = RACINE / "outputs" / "Mandat_Lauren_risque.xlsx"

HDR = 2          # ligne 0-based de l'en-tête des onglets de données
D0 = 3           # première ligne de données (0-based) -> ligne 4 d'Excel

# Les supports détenus. Le premier est le portefeuille lui-même, le dernier
# argument dit lequel sert de taux sans risque.
SUPPORTS = [
    ("Portefeuille retenu", None),
    ("Poche actions", "poche_actions"),
    ("États courts AAA", "etats_courts"),
    ("États longs", "etats_longs"),
    ("Obligations indexées", "indexees"),
    ("Or", "or"),
]
SANS_RISQUE = 2                      # indice dans SUPPORTS
LIGNES_RISQUE = [1, 2, 3, 4, 5]      # les cinq supports détenus


# ---------------------------------------------------------------- données

def donnees_portefeuille() -> tuple[pd.DataFrame, dict]:
    """Niveaux hebdomadaires du portefeuille et de ses cinq supports."""
    brut = allocation.series()
    debut = allocation.resultats()["fenetre"][0]
    brut = brut[debut:]
    poids = {k: x for k, x in
             allocation.resultats()["scenarios"][allocation.RETENU]
             ["poids"].items() if x > 0}

    poche = allocation.portefeuille(brut, allocation.MIX_ACTIONS)
    cles = [k for k in allocation.ORDRE if k in poids and k != "poche_actions"]
    s = pd.concat([poche.rename("poche_actions")] + [brut[k] for k in cles],
                  axis=1, sort=False).dropna()
    val = pd.concat(
        [allocation.portefeuille(s, poids).rename("Portefeuille retenu")]
        + [s[k].rename(n) for n, k in SUPPORTS[1:]], axis=1).dropna()
    # Le QUOTIDIEN est renvoyé en plus de l'hebdomadaire, pour la seule pire
    # baisse. Le creux du 18 mars 2020 est un mercredi : mesuré de vendredi en
    # vendredi, le portefeuille ne perd que 13,2 % au lieu de 14,0 %, et le
    # classeur contredirait l'application et le deck sur LE chiffre qui porte
    # la limite du mandat. Tout le reste — volatilités, corrélations, bêtas —
    # reste hebdomadaire, qui est la convention de core/allocation.py.
    return val.resample("W-FRI").last().dropna(), val, poids


def donnees_actions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cours hebdomadaires en euros des titres retenus, l'indice, le sans-risque."""
    sel = outlook.final(actions.selection(actions.univers()))
    d = RACINE / "data" / "actions"
    px = pd.read_csv(d / "prix_hebdo.csv", index_col=0, parse_dates=True)
    fx = pd.read_csv(d / "change_hebdo.csv", index_col=0,
                     parse_dates=True).reindex(px.index).ffill().bfill()
    dev = sel.set_index("ticker")["currency"].replace({"GBp": "GBP"})
    eur = pd.DataFrame({t: px[t] / fx[dev[t]] for t in sel["ticker"]})
    # Le panier est équipondéré et non rééquilibré (décision de l'étape 3).
    # Les titres entrés en cours de route n'y pèsent qu'à partir de leur
    # première cotation : `skipna` fait la moyenne des lignes disponibles.
    eur["Panier équipondéré"] = 100 * (
        1 + eur.pct_change().mean(axis=1, skipna=True).fillna(0)).cumprod()
    eur["STOXX Europe 600"] = px["EXSA.DE"]
    rf = allocation.series().resample("W-FRI").last()["etats_courts"]
    eur["Sans risque"] = rf.reindex(eur.index)
    return sel, eur.dropna(subset=["STOXX Europe 600", "Sans risque"])


# ------------------------------------------------------- écriture données

def bloc(ws, fm, col0: int, titre: str, noms: list[str], n: int,
         gabarit, valeurs: pd.DataFrame | None = None) -> int:
    """
    Écrit un bloc de colonnes calculées : un titre, des en-têtes, puis la
    formule `gabarit(i, ligne)` répétée sur n lignes. Renvoie la colonne
    suivant le bloc. `valeurs` fournit les résultats mis en cache, pour que
    le fichier s'affiche juste avant tout recalcul.
    """
    ws.write(HDR - 1, col0, titre, fm["bloc"])
    for i, nom in enumerate(noms):
        ws.write(HDR, col0 + i, nom, fm["entete"])
        for j in range(n):
            f = gabarit(i, D0 + j)
            if f is None:
                continue
            v = None
            if valeurs is not None:
                x = valeurs.iloc[j, i]
                v = None if pd.isna(x) else float(x)
            ws.write_formula(D0 + j, col0 + i, f, fm["num6"],
                             v if v is not None else "")
    return col0 + len(noms) + 1


def feuille_donnees(xl, fm, nom: str, val: pd.DataFrame, rf_col: int,
                    ref_col: int | None = None) -> dict:
    """
    Un onglet de données : dates, niveaux, puis variations, log-variations,
    excès sur le sans-risque, écarts à l'indice et baisses depuis le plus
    haut — tout en formules. Renvoie la position de chaque bloc.
    """
    ws = xl.book.add_worksheet(nom)
    xl.sheets[nom] = ws
    n, m = len(val), val.shape[1]
    ws.write(0, 0, f"{nom} — niveaux hebdomadaires et colonnes calculées",
             fm["titre"])
    ws.write(1, 0, "Seuls les niveaux (bloc « Niveaux ») sont des données. "
                   "Tout le reste est une formule.", fm["note"])
    ws.write(HDR, 0, "Date", fm["entete"])
    for j, d in enumerate(val.index):
        ws.write_datetime(D0 + j, 0, d.to_pydatetime(), fm["date"])
    ws.set_column(0, 0, 11)

    c_niv = 2
    ws.write(HDR - 1, c_niv, "Niveaux (données)", fm["bloc"])
    for i, nom_c in enumerate(val.columns):
        ws.write(HDR, c_niv + i, nom_c, fm["entete"])
        for j in range(n):
            x = val.iloc[j, i]
            if pd.notna(x):
                ws.write_number(D0 + j, c_niv + i, float(x), fm["num6"])

    def ref(c: int, r: int) -> str:
        return f"{LET(c)}{r + 1}"

    r_var = val.pct_change()
    c_var = bloc(ws, fm, c_niv + m + 1, "Variations hebdomadaires",
                 list(val.columns), n,
                 lambda i, r: None if r == D0 else
                 f'=IF(OR({ref(c_niv+i, r-1)}="",{ref(c_niv+i, r)}=""),"",'
                 f'{ref(c_niv+i, r)}/{ref(c_niv+i, r-1)}-1)',
                 r_var)
    c_v0 = c_niv + m + 1

    c_log = bloc(ws, fm, c_var, "Log-variations (pour le rendement annualisé)",
                 list(val.columns), n,
                 lambda i, r: None if r == D0 else
                 f'=IF({ref(c_v0+i, r)}="","",LN(1+{ref(c_v0+i, r)}))',
                 np.log1p(r_var))
    c_l0 = c_var

    ex = r_var.sub(r_var.iloc[:, rf_col], axis=0)
    c_exc = bloc(ws, fm, c_log, "Excès sur le sans-risque",
                 list(val.columns), n,
                 lambda i, r: None if r == D0 else
                 f'=IF({ref(c_v0+i, r)}="","",'
                 f'{ref(c_v0+i, r)}-{ref(c_v0+rf_col, r)})', ex)
    c_e0 = c_log

    c_act = c_a0 = None
    if ref_col is not None:
        ac = r_var.sub(r_var.iloc[:, ref_col], axis=0)
        c_a0 = c_exc
        c_act = bloc(ws, fm, c_exc, "Écart à l'indice (pour le suivi)",
                     list(val.columns), n,
                     lambda i, r: None if r == D0 else
                     f'=IF({ref(c_v0+i, r)}="","",'
                     f'{ref(c_v0+i, r)}-{ref(c_v0+ref_col, r)})', ac)

    dd = val / val.cummax() - 1
    c_dd0 = c_act if c_act is not None else c_exc
    bloc(ws, fm, c_dd0, "Baisse depuis le plus haut",
         list(val.columns), n,
         lambda i, r: f'=IF({ref(c_niv+i, r)}="","",{ref(c_niv+i, r)}/'
                      f'MAX({LET(c_niv+i)}${D0+1}:{ref(c_niv+i, r)})-1)', dd)

    ws.freeze_panes(D0, 2)
    ws.set_column(1, c_dd0 + m, 12, fm["num6"])
    return {"n": n, "niv": c_niv, "var": c_v0, "log": c_l0, "exc": c_e0,
            "act": c_a0, "dd": c_dd0, "premiere": D0 + 1,
            "derniere": D0 + n, "nom": nom}


def feuille_quotidien(xl, fm, val: pd.DataFrame) -> dict:
    """Niveaux quotidiens et baisse depuis le plus haut — rien d'autre."""
    nom = "Données quotidiennes"
    ws = xl.book.add_worksheet(nom)
    xl.sheets[nom] = ws
    n, m = len(val), val.shape[1]
    ws.write(0, 0, f"{nom} — pour la seule pire baisse", fm["titre"])
    ws.write(1, 0, "Le creux de mars 2020 tombe un mercredi : mesurée de "
                   "vendredi en vendredi, la pire baisse serait sous-estimée "
                   "de 0,8 point. Toutes les autres mesures restent "
                   "hebdomadaires.", fm["note"])
    ws.write(HDR, 0, "Date", fm["entete"])
    for j, d in enumerate(val.index):
        ws.write_datetime(D0 + j, 0, d.to_pydatetime(), fm["date"])
    ws.set_column(0, 0, 11)
    c_niv = 2
    ws.write(HDR - 1, c_niv, "Niveaux quotidiens (données)", fm["bloc"])
    for i, nom_c in enumerate(val.columns):
        ws.write(HDR, c_niv + i, nom_c, fm["entete"])
        for j in range(n):
            ws.write_number(D0 + j, c_niv + i, float(val.iloc[j, i]),
                            fm["num6"])
    c_dd = c_niv + m + 1
    dd = val / val.cummax() - 1
    bloc(ws, fm, c_dd, "Baisse depuis le plus haut", list(val.columns), n,
         lambda i, r: f'={LET(c_niv+i)}{r+1}/'
                      f'MAX({LET(c_niv+i)}${D0+1}:{LET(c_niv+i)}{r+1})-1', dd)
    ws.freeze_panes(D0, 2)
    ws.set_column(1, c_dd + m, 12, fm["num6"])
    return {"n": n, "niv": c_niv, "dd": c_dd, "premiere": D0 + 1,
            "derniere": D0 + n, "nom": nom}


def plage(p: dict, bloc_: str, i: int, depuis_deuxieme: bool = True) -> str:
    """Référence absolue d'une colonne d'un onglet de données."""
    c = LET(p[bloc_] + i)
    r1 = p["premiere"] + (1 if depuis_deuxieme and bloc_ != "niv" else 0)
    return f"'{p['nom']}'!${c}${r1}:${c}${p['derniere']}"


# ------------------------------------------------------------- le classeur

def main() -> None:
    val, val_j, poids = donnees_portefeuille()
    sel, eur = donnees_actions()
    SORTIE.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(SORTIE, engine="xlsxwriter") as xl:
        wb = xl.book
        fm = {
            "titre": wb.add_format({"bold": True, "font_size": 13}),
            "note": wb.add_format({"font_size": 9, "italic": True,
                                   "font_color": "#555555"}),
            "bloc": wb.add_format({"bold": True, "font_color": "#1F4E79"}),
            "entete": wb.add_format({"bold": True, "bottom": 1,
                                     "text_wrap": True, "valign": "bottom"}),
            "date": wb.add_format({"num_format": "dd/mm/yyyy"}),
            "num6": wb.add_format({"num_format": "0.000000"}),
            "num": wb.add_format({"num_format": "0.00"}),
            "num3": wb.add_format({"num_format": "0.000"}),
            "ent": wb.add_format({"num_format": "0"}),
            "txt": wb.add_format({}),
            "gras": wb.add_format({"bold": True}),
            "grasnum": wb.add_format({"num_format": "0.00", "bold": True,
                                      "top": 1}),
            "grastxt": wb.add_format({"bold": True, "top": 1}),
            "corps": wb.add_format({"text_wrap": True, "valign": "top"}),
        }
        lecture(xl, fm, val, eur, poids, sel)
        p = feuille_donnees(xl, fm, "Données", val, rf_col=SANS_RISQUE)
        pj = feuille_quotidien(xl, fm, val_j)
        pa = feuille_donnees(xl, fm, "Données actions", eur,
                             rf_col=eur.shape[1] - 1,
                             ref_col=eur.shape[1] - 2)
        feuille_portefeuille(xl, fm, p, pj, val, val_j)
        feuille_matrice(xl, fm, p, val, "Covariance")
        feuille_matrice(xl, fm, p, val, "Corrélation")
        feuille_risque(xl, fm, val, poids)
        feuille_actions(xl, fm, pa, eur, sel)
        wb.worksheets_objs.sort(key=lambda w: ORDRE_ONGLETS.index(w.name))

    print(f"Écrit : {SORTIE}")


ORDRE_ONGLETS = ["Lecture", "Portefeuille", "Covariance", "Corrélation",
                 "Risque", "Actions", "Données", "Données quotidiennes",
                 "Données actions"]


def lecture(xl, fm, val, eur, poids, sel) -> None:
    ws = xl.book.add_worksheet("Lecture")
    xl.sheets["Lecture"] = ws
    ws.set_column(0, 0, 30, fm["txt"])
    ws.set_column(1, 1, 105, fm["corps"])
    L = [
        ("Mandat Lauren — mesures de risque", ""),
        ("", ""),
        ("Ce classeur est calculé, pas recopié",
         "Chaque cellule de mesure est une FORMULE : volatilités, rendements, "
         "Sharpe, bêtas, covariances, corrélations, contributions au risque, "
         "tracking error, ratios d'information. Changez un poids dans "
         "l'onglet « Risque » et tout le bloc de risque suit."),
        ("Ce qui est écrit en dur",
         "Les DONNÉES, et elles seules : les niveaux hebdomadaires (onglets "
         "« Données » et « Données actions »), les poids du portefeuille — "
         "une décision d'allocation, pas un calcul — et les notes de l'étape 3, "
         "produites par la notation des cinq piliers et par la lecture des "
         "attentes d'analystes."),
        ("Le chemin du portefeuille",
         "Rééquilibré le premier jour de chaque mois, comme à l'étape 4. Ce "
         "calcul-là vient de l'application et entre ici comme donnée : le "
         "classeur mesure, il ne refait pas la gestion."),
        ("", ""),
        ("Fenêtres", ""),
        ("Portefeuille",
         f"{val.index[0]:%d/%m/%Y} → {val.index[-1]:%d/%m/%Y}, "
         f"{len(val)} points hebdomadaires du vendredi."),
        ("Actions",
         f"{eur.index[0]:%d/%m/%Y} → {eur.index[-1]:%d/%m/%Y}, "
         f"{len(eur)} points. Les cours sont CONVERTIS EN EUROS avant tout "
         f"calcul : trois lignes cotent hors zone euro, et un risque mesuré "
         f"en devise locale n'est pas celui que court le client."),
        ("Annualisation",
         "Les volatilités sont multipliées par la racine de 52, les "
         "rendements composés sur 52 semaines. Le rendement annualisé passe "
         "par la moyenne des log-variations : c'est ce qui permet aux titres "
         "entrés en cours de route (Var Energi en 2022, Airtel en 2019) "
         "d'être mesurés sur leur propre histoire, sans fausser les autres."),
        ("", ""),
        ("Deux choix de méthode", ""),
        ("Le taux sans risque est un chemin",
         "La série des emprunts d'État AAA 6 à 24 mois, reconstituée sur la "
         "courbe BCE — le placement sans risque de ce mandat. Elle vaut 4 % "
         "en 2008 et 0 % en 2021. Un taux d'aujourd'hui appliqué à vingt ans "
         "ferait dire au Sharpe que l'argent ne coûtait rien avant 2022."),
        ("La tracking error ne concerne que les actions",
         "Contre le STOXX Europe 600, qui est l'univers de départ des quinze "
         "titres : l'écart de suivi y a un sens. Le PORTEFEUILLE, lui, n'a "
         "aucun indice de référence — le mandat fixe un objectif (battre 4 % "
         "d'inflation) et une limite (perdre au plus 15 %), il n'est indexé "
         "sur rien. Mesurer son écart à un repère inventé donnerait un "
         "chiffre qui ne répond à aucune question du client."),
        ("", ""),
        ("Ce que ces chiffres ne disent pas", ""),
        ("Le passé du portefeuille",
         "Les séries longues sont celles qui ont servi à CONSTRUIRE "
         "l'allocation (l'optimisation visait 14 % de perte maximale). La "
         "pire baisse mesurée ici rappelle la cible, elle ne la valide pas. "
         "Ce qui s'y ajoute vraiment : Sharpe, bêtas, covariances et "
         "contributions au risque, que l'étape 4 ne regardait pas."),
        ("Le passé du panier d'actions",
         "IL NE VEUT RIEN DIRE. Les quinze titres ont été choisis avec les "
         "fondamentaux, le momentum et les attentes d'analystes de septembre "
         "2026, puis rejoués depuis 2019 : leur avance sur l'indice ne "
         "pouvait qu'arriver. Les colonnes de RENDEMENT et de RATIO "
         "D'INFORMATION de l'onglet « Actions » portent la mention (biaisé). "
         "La volatilité, le bêta et la tracking error, eux, décrivent ce que "
         "le panier EST et restent valables."),
        ("La sélection n'est pas figée",
         "Elle est recalculée à partir de data/actions/ à chaque exécution. "
         "Ce classeur porte celle du jour de sa génération."),
        ("", ""),
        ("Généré le", pd.Timestamp.today().strftime("%d/%m/%Y")),
        ("Relevés utilisés",
         f"Actions {actions.releve()} · Attentes {outlook.releve()} · Taux "
         f"{taux.charger()['releve']} · Optimisation "
         f"{allocation.resultats()['releve']}"),
        ("Régénérer", "python3 scripts/export_risque.py"),
    ]
    for i, (g, d) in enumerate(L):
        ws.write(i, 0, g, fm["gras"] if d == "" else fm["txt"])
        ws.write(i, 1, d)


def feuille_portefeuille(xl, fm, p, pj, val, val_j) -> None:
    ws = xl.book.add_worksheet("Portefeuille")
    xl.sheets["Portefeuille"] = ws
    ws.write(0, 0, "Le portefeuille et ses cinq poches", fm["titre"])
    ws.write(1, 0, f"Hebdomadaire, {val.index[0]:%d/%m/%Y} → "
                   f"{val.index[-1]:%d/%m/%Y}. Toutes les cellules sont des "
                   f"formules. Sans risque : les États courts AAA.", fm["note"])
    ws.set_column(0, 0, 34, fm["txt"])
    ws.set_column(1, len(SUPPORTS), 18, fm["num3"])

    r_var, r_log = val.pct_change(), np.log1p(val.pct_change())
    ex = r_var.sub(r_var.iloc[:, SANS_RISQUE], axis=0)
    dd = val_j / val_j.cummax() - 1             # quotidienne, voir l'onglet

    def var_cell(i):
        return f"{LET(1 + i)}9"

    lignes = [
        ("Rendement annualisé %",
         lambda i: f'=(EXP(AVERAGE({plage(p,"log",i)})*52)-1)*100',
         lambda i: (np.exp(r_log.iloc[:, i].mean() * SEM) - 1) * 100),
        ("Volatilité annuelle %",
         lambda i: f'=STDEV.S({plage(p,"var",i)})*SQRT(52)*100',
         lambda i: r_var.iloc[:, i].std() * SEM ** .5 * 100),
        ("Sharpe",
         lambda i: f'=IFERROR(AVERAGE({plage(p,"exc",i)})/'
                   f'STDEV.S({plage(p,"exc",i)})*SQRT(52),"")',
         lambda i: (ex.iloc[:, i].mean() / ex.iloc[:, i].std() * SEM ** .5)
                   if ex.iloc[:, i].std() else np.nan),
        ("Bêta / poche actions",
         lambda i: f'=SLOPE({plage(p,"var",i)},{plage(p,"var",1)})',
         lambda i: (np.cov(r_var.iloc[1:, i], r_var.iloc[1:, 1])[0, 1]
                    / np.var(r_var.iloc[1:, 1], ddof=1))),
        ("Pire baisse depuis le plus haut % (quotidien)",
         lambda i: f'=MIN({plage(pj,"dd",i,False)})*100',
         lambda i: dd.iloc[:, i].min() * 100),
        ("VaR 95 % hebdomadaire %",
         lambda i: f'=PERCENTILE.INC({plage(p,"var",i)},0.05)*100',
         lambda i: np.quantile(r_var.iloc[1:, i], .05) * 100),
        ("CVaR 95 % hebdomadaire %",
         lambda i: f'=AVERAGEIF({plage(p,"var",i)},"<="&{var_cell(i)}/100)*100',
         lambda i: r_var.iloc[1:, i][r_var.iloc[1:, i]
                   <= np.quantile(r_var.iloc[1:, i], .05)].mean() * 100),
        ("Semaines mesurées",
         lambda i: f'=COUNT({plage(p,"var",i)})',
         lambda i: float(r_var.iloc[:, i].count())),
    ]
    for i, (nom, _) in enumerate(SUPPORTS):
        ws.write(HDR, 1 + i, nom, fm["entete"])
    for j, (nom, f, v) in enumerate(lignes):
        ws.write(HDR + 1 + j, 0, nom, fm["txt"])
        for i in range(len(SUPPORTS)):
            x = v(i)
            ws.write_formula(HDR + 1 + j, 1 + i, f(i),
                             fm["ent"] if "Semaines" in nom else fm["num3"],
                             "" if pd.isna(x) else float(x))
    ws.freeze_panes(HDR + 1, 1)


def feuille_matrice(xl, fm, p, val, quoi: str) -> None:
    ws = xl.book.add_worksheet(quoi)
    xl.sheets[quoi] = ws
    cov = quoi == "Covariance"
    ws.write(0, 0, f"{quoi} des cinq supports détenus", fm["titre"])
    ws.write(1, 0,
             "Covariances annualisées (×52) des variations hebdomadaires. La "
             "diagonale est la variance annuelle de chaque ligne."
             if cov else
             "Corrélations des variations hebdomadaires, sur toute la "
             "fenêtre. C'est ce tableau qui explique pourquoi le "
             "portefeuille est moins agité que ses lignes.", fm["note"])
    ws.set_column(0, 0, 24, fm["txt"])
    ws.set_column(1, len(LIGNES_RISQUE), 20,
                  fm["num6"] if cov else fm["num3"])
    r = val.pct_change()
    m = (r.iloc[:, LIGNES_RISQUE].cov() * SEM if cov
         else r.iloc[:, LIGNES_RISQUE].corr())
    for a, i in enumerate(LIGNES_RISQUE):
        ws.write(HDR, 1 + a, SUPPORTS[i][0], fm["entete"])
        ws.write(HDR + 1 + a, 0, SUPPORTS[i][0], fm["txt"])
        for b, j in enumerate(LIGNES_RISQUE):
            f = (f'=COVARIANCE.S({plage(p,"var",i)},{plage(p,"var",j)})*52'
                 if cov else
                 f'=CORREL({plage(p,"var",i)},{plage(p,"var",j)})')
            ws.write_formula(HDR + 1 + a, 1 + b, f,
                             fm["num6"] if cov else fm["num3"],
                             float(m.iloc[a, b]))
    ws.freeze_panes(HDR + 1, 1)


def feuille_risque(xl, fm, val, poids) -> None:
    """Variance du portefeuille et contributions au risque, en formules."""
    ws = xl.book.add_worksheet("Risque")
    xl.sheets["Risque"] = ws
    ws.write(0, 0, "D'où vient le risque du portefeuille", fm["titre"])
    ws.write(1, 0, "Les poids de la colonne B sont la seule donnée de cet "
                   "onglet : changez-en un, tout le reste suit.", fm["note"])
    ws.set_column(0, 0, 24, fm["txt"])
    ws.set_column(1, 1, 10, fm["num3"])
    ws.set_column(2, 7, 19, fm["num3"])

    cles = {1: "poche_actions", 2: "etats_courts", 3: "etats_longs",
            4: "indexees", 5: "or"}
    w = np.array([poids[cles[i]] for i in LIGNES_RISQUE])
    cov = (val.pct_change().iloc[:, LIGNES_RISQUE].cov() * SEM).to_numpy()
    sw = cov @ w
    var = float(w @ sw)
    sig = var ** .5

    entetes = ["Support", "Poids", "Poids %", "Volatilité de la ligne %",
               "Covariance avec le portefeuille", "Contribution marginale %",
               "Contribution au risque %", "Part du risque %"]
    for i, h in enumerate(entetes):
        ws.write(HDR, i, h, fm["entete"])

    r0 = HDR + 1
    fin = r0 + len(LIGNES_RISQUE)
    VAR, SIG = f"$B${fin + 3}", f"$B${fin + 4}"
    for a, i in enumerate(LIGNES_RISQUE):
        r = r0 + a
        cl = LET(1 + a)                       # colonne de la matrice
        ws.write(r, 0, SUPPORTS[i][0], fm["txt"])
        ws.write_number(r, 1, float(w[a]), fm["num6"])
        ws.write_formula(r, 2, f"=B{r+1}*100", fm["num3"], float(w[a] * 100))
        ws.write_formula(r, 3, f"=SQRT(Covariance!{cl}{r+1})*100", fm["num3"],
                         float(cov[a, a] ** .5 * 100))
        ws.write_formula(r, 4,
                         f"=SUMPRODUCT(Covariance!{cl}${r0+1}:{cl}${fin},"
                         f"$B${r0+1}:$B${fin})", fm["num6"], float(sw[a]))
        ws.write_formula(r, 5, f"=E{r+1}/SQRT({VAR})*100", fm["num3"],
                         float(sw[a] / sig * 100))
        ws.write_formula(r, 6, f"=B{r+1}*F{r+1}", fm["num3"],
                         float(w[a] * sw[a] / sig * 100))
        ws.write_formula(r, 7, f"=G{r+1}/{SIG}*100", fm["num3"],
                         float(w[a] * sw[a] / var * 100))

    ws.write(fin, 0, "Total", fm["grastxt"])
    for c, (f, v) in {
        1: (f"=SUM(B{r0+1}:B{fin})", float(w.sum())),
        2: (f"=SUM(C{r0+1}:C{fin})", float(w.sum() * 100)),
        6: (f"=SUM(G{r0+1}:G{fin})", float(sig * 100)),
        7: (f"=SUM(H{r0+1}:H{fin})", 100.0),
    }.items():
        ws.write_formula(fin, c, f, fm["grasnum"], v)
    for c in (0, 3, 4, 5):
        if c:
            ws.write_blank(fin, c, None, fm["grasnum"])

    ws.write(fin + 2, 0, "Variance du portefeuille (annuelle)", fm["gras"])
    ws.write_formula(fin + 2, 1,
                     f"=SUMPRODUCT(B{r0+1}:B{fin},E{r0+1}:E{fin})",
                     fm["num6"], var)
    ws.write(fin + 3, 0, "Volatilité du portefeuille %", fm["gras"])
    ws.write_formula(fin + 3, 1, f"=SQRT({VAR})*100", fm["num3"], sig * 100)
    ws.write(fin + 5, 0, "À lire", fm["gras"])
    ws.write(fin + 5, 1, "La part du risque se compare à la part du capital "
                         "(colonne C). L'écart entre les deux est la "
                         "concentration du risque.", fm["corps"])
    ws.write(fin + 6, 0, "Deux volatilités, et pourquoi", fm["gras"])
    ws.write(fin + 6, 1,
             "Celle-ci (cellule B12) est DÉDUITE de la matrice de "
             "covariance, à poids constants. L'onglet « Portefeuille » en "
             "donne une autre, MESURÉE sur le chemin réellement suivi, qui "
             "est rééquilibré une fois par mois et dérive entre deux "
             "rééquilibrages. L'écart entre les deux — quelques centièmes de "
             "point — est le coût de cette dérive. Les deux sont justes ; "
             "c'est la première qui se décompose ligne à ligne.", fm["corps"])
    ws.set_row(fin + 6, 58)
    ws.set_column(1, 1, 10, fm["num6"])
    ws.set_column(1, 1, 12, fm["num6"])


def feuille_actions(xl, fm, pa, eur, sel) -> None:
    ws = xl.book.add_worksheet("Actions")
    xl.sheets["Actions"] = ws
    n_t = len(sel)
    i_ind = eur.shape[1] - 2                   # colonne de l'indice
    ws.write(0, 0, f"Les {n_t} titres détenus, à parts égales", fm["titre"])
    ws.write(1, 0,
             f"Hebdomadaire, cours en euros, {eur.index[0]:%d/%m/%Y} → "
             f"{eur.index[-1]:%d/%m/%Y}. Suivi et bêta contre le STOXX Europe "
             f"600. LES COLONNES (BIAISÉ) NE SE LISENT PAS COMME UNE "
             f"SURPERFORMANCE : les titres ont été choisis avec les données "
             f"de 2026 puis rejoués depuis 2019.", fm["note"])

    r_var = eur.pct_change()
    r_log = np.log1p(r_var)
    ex = r_var.sub(r_var.iloc[:, -1], axis=0)
    ac = r_var.sub(r_var.iloc[:, i_ind], axis=0)

    cols = [
        ("Ticker", 12, "txt"), ("Société", 30, "txt"), ("Secteur", 24, "txt"),
        ("Pays", 14, "txt"), ("Poids %", 9, "num"),
        ("Rendement annualisé % (biaisé)", 13, "num"),
        ("Volatilité annuelle %", 12, "num"), ("Sharpe", 9, "num3"),
        ("Bêta / STOXX 600", 11, "num3"), ("Tracking error %", 12, "num"),
        ("Ratio d'information (biaisé)", 12, "num3"),
        ("Valorisation", 11, "num3"), ("Croissance", 11, "num3"),
        ("Dynamique", 11, "num3"), ("Qualité", 11, "num3"),
        ("Résistance", 11, "num3"), ("Note des 5 piliers", 11, "num3"),
        ("Note avenir (analystes)", 11, "num3"),
        ("Potentiel vs cible %", 11, "num"),
        ("Révisions de BPA 30 j %", 11, "num"),
        ("Solde hausses − baisses %", 11, "num"),
        ("Nombre d'analystes", 10, "ent"),
        ("Semaines mesurées", 10, "ent"),
    ]
    for i, (h, larg, f) in enumerate(cols):
        ws.write(HDR, i, h, fm["entete"])
        ws.set_column(i, i, larg, fm[f])

    def mesures(r: int, i: int, biais_te: bool) -> None:
        """Les six mesures, en formules, pour la colonne i des données."""
        te = f"J{r+1}"
        ws.write_formula(r, 5, f'=(EXP(AVERAGE({plage(pa,"log",i)})*52)-1)*100',
                         fm["num"],
                         float((np.exp(r_log.iloc[:, i].mean() * SEM) - 1)
                               * 100))
        ws.write_formula(r, 6, f'=STDEV.S({plage(pa,"var",i)})*SQRT(52)*100',
                         fm["num"],
                         float(r_var.iloc[:, i].std() * SEM ** .5 * 100))
        ws.write_formula(r, 7, f'=IFERROR(AVERAGE({plage(pa,"exc",i)})/'
                               f'STDEV.S({plage(pa,"exc",i)})*SQRT(52),"")',
                         fm["num3"],
                         float(ex.iloc[:, i].mean() / ex.iloc[:, i].std()
                               * SEM ** .5))
        ws.write_formula(r, 8, f'=SLOPE({plage(pa,"var",i)},'
                               f'{plage(pa,"var",i_ind)})', fm["num3"],
                         beta_py(r_var.iloc[:, i], r_var.iloc[:, i_ind]))
        if not biais_te:
            ws.write_blank(r, 9, None, fm["num"])
            ws.write_blank(r, 10, None, fm["num3"])
            return
        ws.write_formula(r, 9, f'=STDEV.S({plage(pa,"act",i)})*SQRT(52)*100',
                         fm["num"],
                         float(ac.iloc[:, i].std() * SEM ** .5 * 100))
        ws.write_formula(r, 10, f'=IFERROR(AVERAGE({plage(pa,"act",i)})*52/'
                                f'({te}/100),"")',
                         fm["num3"],
                         float(ac.iloc[:, i].mean() * SEM
                               / (ac.iloc[:, i].std() * SEM ** .5)))

    for a, (_, t) in enumerate(sel.iterrows()):
        r = HDR + 1 + a
        i = list(eur.columns).index(t["ticker"])
        ws.write(r, 0, t["ticker"], fm["txt"])
        ws.write(r, 1, t["nom"], fm["txt"])
        ws.write(r, 2, t["secteur"], fm["txt"])
        ws.write(r, 3, t["pays"], fm["txt"])
        ws.write_formula(r, 4, f"=100/{n_t}", fm["num"], 100 / n_t)
        mesures(r, i, True)
        for c, k in enumerate(["Valorisation", "Croissance", "Dynamique",
                               "Qualité", "Résistance", "note", "note_avenir",
                               "potentiel", "revision", "solde", "analystes"]):
            x = t[k]
            ws.write(r, 11 + c, "" if pd.isna(x) else float(x))
        # Var Energi n'est cotée que depuis 2022, Airtel depuis mi-2019 : sans
        # cette colonne, leur volatilité se lirait comme celle des autres.
        ws.write_formula(r, 22, f'=COUNT({plage(pa,"var",i)})', fm["ent"],
                         float(r_var.iloc[:, i].count()))

    # le panier et l'indice
    r = HDR + 1 + n_t
    i_pan = list(eur.columns).index("Panier équipondéré")
    for nom, i, biais in ((f"Panier, {n_t} titres à parts égales", i_pan, True),
                          ("STOXX Europe 600 (indice)", i_ind, False)):
        ws.write(r, 1, nom, fm["grastxt"])
        for c in (0, 2, 3):
            ws.write_blank(r, c, None, fm["grastxt"])
        if biais:
            ws.write_formula(r, 4, f"=SUM(E{HDR+2}:E{HDR+1+n_t})",
                             fm["grasnum"], 100.0)
        else:
            ws.write_blank(r, 4, None, fm["grasnum"])
        mesures(r, i, biais)
        for c in range(11, 22):
            ws.write_blank(r, c, None, fm["grastxt"])
        ws.write_formula(r, 22, f'=COUNT({plage(pa,"var",i)})', fm["grasnum"],
                         float(r_var.iloc[:, i].count()))
        r += 1
    ws.freeze_panes(HDR + 1, 2)


def beta_py(y: pd.Series, x: pd.Series) -> float:
    d = pd.concat([y, x], axis=1).dropna()
    return float(np.cov(d.iloc[:, 0], d.iloc[:, 1])[0, 1]
                 / np.var(d.iloc[:, 1], ddof=1))


if __name__ == "__main__":
    main()
