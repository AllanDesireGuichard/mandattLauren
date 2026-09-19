"""
Chiffres du pitch oral -> scripts/pitch/data.json

Lancer :  PYTHONPATH=. python3 scripts/pitch/extraire.py
Puis   :  cd scripts/pitch && npm install && node build.js ../../outputs/Mandat_Lauren_pitch.pptx

POURQUOI. Le deck ne recalcule rien : il lit les mêmes modules que l'app
(core/*), si bien que ses chiffres sont ceux affichés dans les onglets. Après
une mise à jour des données (scripts/fetch_*.py, optimiser.py), relancer les
deux commandes suffit à remettre le deck à jour.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from core import (actions, allocation, backtests, credit, fonds, macro,
                  marches, obligations, rendements, taux)

RACINE = Path(__file__).resolve().parents[2]
SORTIE = Path(__file__).resolve().parent / "data.json"


def _cell(d: dict | None) -> list | None:
    return None if d is None else [d["valeur"], d["avant"]]


def _poids_par_ligne(po: dict) -> dict:
    """Poche actions éclatée selon la clé 40/35/10/15."""
    o = dict(po)
    pc = o.pop("poche_actions", None)
    if pc is not None:
        for k, m in allocation.MIX_ACTIONS.items():
            o[k] = pc * m
    return o


def main() -> None:
    out: dict = {}

    # --- étape 2 : taux, cycle, crédit, marchés, rendements -------------
    ph = taux.charger()
    p, c = ph["points"], ph["courbes"]
    cout = p["us_3m"]["valeur"] - p["estr"]["valeur"]          # couverture
    out["taux"] = {
        "estr": p["estr"]["valeur"], "etat_1_3": [c["toutes"][0], c["toutes"][2]],
        "etat_euro": p["etat_euro"]["valeur"], "credit_ig": p["credit_ig_euro"]["valeur"],
        "idx_reel": p["indexees_reel"]["valeur"], "us10": p["us_10a"]["valeur"],
        "cout_couv": cout, "releve": ph["releve"],
        "synthese": [
            ("Monétaire", p["estr"]["valeur"]),
            ("États euro 1-3 ans", (c["toutes"][0] + c["toutes"][2]) / 2),
            ("États euro, ensemble", p["etat_euro"]["valeur"]),
            ("Trésor US 10 ans, couvert", p["us_10a"]["valeur"] - cout),
            ("Crédit US bien noté, couvert", p["credit_ig_us"]["valeur"] - cout),
            ("Crédit euro bien noté", p["credit_ig_euro"]["valeur"]),
            ("Dette émergente, couverte", p["em_corp"]["valeur"] - cout),
            ("Indexées (à 4 % d'inflation)", p["indexees_reel"]["valeur"] + 4),
            ("Haut rendement US, couvert*", p["hy_us"]["valeur"] - cout),
            ("Haut rendement euro*", p["hy_euro"]["valeur"]),
        ],
    }

    m = macro.charger()
    us, ea, em = m["etats_unis"], m["zone_euro"], m["emergents"]
    cles = ["pib", "chomage", "inflation", "inflation_sj", "banque_centrale",
            "taux_2a", "taux_10a"]
    out["cycle"] = {z: {k: _cell(zz[k]) for k in cles}
                    for z, zz in (("us", us), ("ea", ea))}
    out["cycle"]["em"] = {"croiss26": em["croissance"]["OEMDC"]["2026"],
                          "chine": em["avance"]["chine"]["valeur"],
                          "inde": em["avance"]["inde"]["valeur"]}
    out["cycle"]["releve"] = m["releve"]

    cr = credit.charger()["series"]
    out["credit"] = {
        "baa_rang": cr["BAA10Y"]["rang"], "hy_rang": cr["BAMLH0A0HYM2"]["rang"],
        "baa": cr["BAA10Y"]["valeur"], "hy": cr["BAMLH0A0HYM2"]["valeur"],
        "duration_ig": p["credit_ig_euro"]["duration"],
    }
    h = credit.histo()[["BAA10Y", "BAMLH0A0HYM2"]].resample("QE").mean()
    out["credit"]["histo"] = {
        "dates": [d.strftime("%Y") for d in h.index],
        "baa": [None if pd.isna(x) else round(x, 2) for x in h["BAA10Y"]],
        "hy": [None if pd.isna(x) else round(x, 2) for x in h["BAMLH0A0HYM2"]],
    }

    out["marches"] = [(d["libelle"], d["groupe"], d["1 mois"], d["12 mois"])
                      for d in marches.charger()["lignes"].values()]

    R = rendements.charger()
    C = R["classes"]
    out["rendements"] = [(k, C[k]["libelle"], C[k]["central"], C[k]["bas"],
                          C[k]["haut"], C[k]["etiquette"], C[k]["jpm"])
                         for k in rendements.ORDRE]
    out["eu_us"] = {k: C[k]["detail"] for k in ("europe", "us")}
    out["croissance"] = R["croissance"]["central"]

    # --- étape 3 : actions, souverains, fonds, crédit -------------------
    d = actions.univers()
    sel = actions.selection(d)
    excl = d[d["exclusion"].notna()]
    out["entonnoir"] = {
        "n": len(d), "excl": len(excl), "inv": int(d["societe_invest"].sum()),
        "petites": int((d["trop_petite"] & d["exclusion"].isna()
                        & ~d["societe_invest"]).sum()),
        "notees": int(d["note"].notna().sum()), "sel": len(sel),
        "excl_motifs": excl.groupby("exclusion").size().to_dict(),
    }
    out["trente"] = [(r.longName, r.secteur, r.pays, round(r.note, 2))
                     for r in sel.itertuples()]
    out["secteurs"] = sel["secteur"].value_counts().to_dict()
    out["pays"] = sel["pays"].value_counts().to_dict()
    pa = actions.panier_face_indice(sel)
    out["panier"] = {k: {x: pa[k][x] for x in ("vol_3a", "dd_2020", "dd_2022")}
                     for k in ("panier", "indice")}

    sv = ph["svensson"]
    ech = obligations.echelle(allocation.TRANCHES, sv["aaa"])
    longue = [obligations.analyse(n, sv["toutes"]) for n in allocation.ECHELLE_LONGUE]
    out["souverains"] = {
        "cout": sum(x["cout"] for x in ech),
        "cout_mon": sum(mt / (1 + p["estr"]["valeur"] / 100) ** t
                        for t, mt in allocation.TRANCHES.items()),
        "taux": [x["taux"] for x in ech],
        "rdt_long": sum(x["rendement"] for x in longue) / len(longue),
        "choc_long": sum(x["choc_plus_1"] for x in longue) / len(longue),
    }

    cl = fonds.charger()["classes"]
    out["fonds"] = [(cl[k]["libelle"], cl[k]["retenu"].split(".")[0],
                     cl[k]["candidats"][cl[k]["retenu"]]["nom"],
                     cl[k]["candidats"][cl[k]["retenu"]]["frais"],
                     cl[k]["candidats"][cl[k]["retenu"]]["taille"])
                    for k in fonds.ORDRE]
    out["xzem_ecart"] = cl["emergents"]["candidats"][cl["emergents"]["retenu"]]["ecart_moyen"]
    fc = json.loads((RACINE / "data" / "fonds_credit.json").read_text(encoding="utf-8"))
    q = fc["fonds"][fc["retenu"]]
    out["credit_fonds"] = {
        "ticker": fc["retenu"].split(".")[0], "nom": q["nom"], "rdt": q["rendement"],
        "duree": q["duree"], "frais": q["frais"], "taille": q["taille"],
        "dd2020": q["pires_baisses"]["2020"],
        "etat2020": fc["repere_etat"]["pires_baisses"]["2020"],
    }

    # --- étape 4 : entrées, risque, scénarios, portefeuille -------------
    e = allocation.entrees()
    out["entrees"] = [(k, e.loc[k, "classe"], e.loc[k, "rendement"])
                      for k in e.index if not e.loc[k, "hors_calcul"]]
    s = allocation.series_risque()
    pe = allocation.pertes_crises(s)
    pend, _ = allocation.pendant_la_baisse(s)

    def tab(df: pd.DataFrame) -> dict:
        return {k: {c_: None if pd.isna(df.loc[k, c_]) else round(df.loc[k, c_], 1)
                    for c_ in allocation.CRISES} for k in df.index}
    out["pertes"], out["pendant"] = tab(pe), tab(pend)
    out["crises_lib"] = {c_: lib for c_, (_, _, lib) in allocation.CRISES.items()}

    res = allocation.resultats()
    out["scenarios"] = {n: {"rdt": x["rendement_espere"], "pire": x["pire_baisse"],
                            "poids": _poids_par_ligne(x["poids"]),
                            "variante": x.get("variante")}
                        for n, x in res["scenarios"].items()}
    out["realise"] = res["scenarios"][allocation.RETENU]["realise"]

    w = allocation.poids_retenus()
    out["retenu"] = w
    out["retenu_lignes"] = [
        (k, e.loc[k, "classe"],
         cl[k]["retenu"].split(".")[0] if k in cl else e.loc[k, "support"],
         x, e.loc[k, "rendement"])
        for k, x in w.items() if x >= 0.0005]
    out["frais_total"] = sum(
        w[k] * allocation.MONTANT * cl[k]["candidats"][cl[k]["retenu"]]["frais"] / 100
        for k in ("usa", "japon", "emergents", "indexees", "or", "matieres")
        if w[k] >= 0.0005)

    # --- étape 5 : backtests --------------------------------------------
    v = backtests.valeur()
    ep = backtests.episodes(v)
    t = backtests.temps_sous(v)
    r = backtests.un_an(v)
    ans = (v.index[-1] - v.index[0]).days / 365.25
    vm = (v / 1e6).resample("ME").last()
    dd = ((v / v.cummax() - 1) * 100).resample("ME").min()
    hist = pd.cut(r, bins=range(int(math.floor(r.min())) - 1,
                                int(math.ceil(r.max())) + 2)).value_counts().sort_index()
    out["bt"] = {
        "final": v.iloc[-1] / 1e6,
        "cagr": ((v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1) * 100,
        "pire": t["pire"], "sous": t["sous"], "s5": t["5"], "s10": t["10"],
        "episodes": [(x.sommet.strftime("%m/%Y"), x.creux.strftime("%m/%Y"),
                      x.perte * 100, backtests.mois(x.sommet, x.creux),
                      x.retour.strftime("%m/%Y") if pd.notna(x.retour) else None,
                      backtests.mois(x.sommet, x.retour) if pd.notna(x.retour) else None)
                     for x in ep.itertuples()],
        "var95": backtests.var_cvar(r, .95), "var99": backtests.var_cvar(r, .99),
        "rmin": r.min(), "rmax": r.max(), "n": len(r),
        "neg": (r < 0).mean() * 100, "sous4": (r < 4).mean() * 100,
        "serie": {"dates": [d_.strftime("%Y-%m") for d_ in vm.index],
                  "valeur": [round(x, 2) for x in vm],
                  "dd": [round(x, 2) for x in dd]},
        "hist": [(int(i.left), int(n)) for i, n in hist.items()],
    }

    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float),
                      encoding="utf-8")
    print(f"écrit : {SORTIE}")


if __name__ == "__main__":
    main()
