"""
Chiffres du pitch oral -> scripts/pitch/data.json

Lancer :  PYTHONPATH=. python3 scripts/pitch/extraire.py
Puis   :  cd scripts/pitch && npm install && npm run build
          -> outputs/Mandat_Lauren_pitch_genere.pptx
Enfin  :  python3 scripts/pitch/controle.py        (géométrie du rendu)
          puis recopier sur outputs/Mandat_Lauren_pitch.pptx, qui est le
          deck de référence depuis la bascule validée le 2026-09-21.

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

from core import (actions, allocation, backtests, credit, fonds, ips, macro,
                  marches, obligations, outlook, rendements, scoring, taux,
                  vue_secteurs)

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
    notes = d[d["note"].notna()]
    # Le second étage (core/outlook) et la vue sectorielle (core/vue_secteurs)
    # n'étaient pas extraits : le deck a parlé de trente titres pendant que
    # l'application en affichait quinze.
    j = outlook.juger(sel, outlook.indicateurs())
    fin = outlook.selectionner(j)
    cv = vue_secteurs.cout(d)
    out["entonnoir"] = {
        "n": len(d), "excl": len(excl), "inv": int(d["societe_invest"].sum()),
        "petites": int((d["trop_petite"] & d["exclusion"].isna()
                        & ~d["societe_invest"]).sum()),
        "notees": int(notes["note"].notna().sum()),
        "vue": cv["titres_notes"], "sel": len(sel), "final": len(fin),
        "excl_motifs": excl.groupby("exclusion").size().to_dict(),
    }
    out["vue"] = {
        "industries": [(i, v[1], v[2]) for i, v in vue_secteurs.VUE.items()],
        "depuis": next(iter(vue_secteurs.VUE.values()))[0],
        "titres": cv["titres_notes"],
        "meilleur": cv["meilleur_titre"],
        "meilleure_note": round(cv["meilleure_note"], 3),
        "trentieme": round(float(sel["note"].min()), 3),
    }
    out["trente"] = [(r.longName, r.secteur, r.pays, round(r.note, 2))
                     for r in sel.itertuples()]
    out["quinze"] = [(r.longName, r.secteur, r.pays, round(r.note, 2),
                      round(r.note_avenir, 2), round(r.revision, 1),
                      round(r.solde, 0), round(r.potentiel, 1))
                     for r in fin.itertuples()]
    out["ecartes"] = [(r.longName, r.secteur, r.motif)
                      for r in j[j["motif"].notna()].itertuples()]
    out["avenir"] = {
        "releve": outlook.releve(),
        "plafond_dispersion": round(outlook.plafond_dispersion(
            outlook.indicateurs()), 1),
        "revision_min": outlook.REVISION_MIN,
        "revisions_min": outlook.REVISIONS_MIN,
        "max_secteur": outlook.MAX_SECTEUR, "max_pays": outlook.MAX_PAYS,
    }
    out["secteurs"] = fin["secteur"].value_counts().to_dict()
    out["pays"] = fin["pays"].value_counts().to_dict()
    out["secteurs30"] = sel["secteur"].value_counts().to_dict()
    pa, p30 = actions.panier_face_indice(fin), actions.panier_face_indice(sel)
    out["panier"] = {k: {x: pa[k][x] for x in ("vol_3a", "dd_2020", "dd_2022")}
                     for k in ("panier", "indice")}
    out["panier"]["trente"] = {x: p30["panier"][x]
                               for x in ("vol_3a", "dd_2020", "dd_2022")}
    # Le plafond de volatilité est devenu sectoriel le 2026-09-25 : la
    # technologie sortait entièrement d'un plafond mesuré sur tout l'univers.
    pv = scoring.plafonds_volatilite(notes)
    out["vol_plafond"] = {"univers": round(scoring.plafond_volatilite(notes), 1),
                          "max": round(float(pv.max()), 1),
                          "secteur_max": str(pv.idxmax())}

    # Performance SUR la fenêtre de crise, à ne pas confondre avec la pire
    # baisse DANS la fenêtre : le deck affirmait « l'or +39 % en 2008 », un
    # chiffre qui ne sort d'aucune de nos séries. Mesuré ici, en euros.
    sr = allocation.series_risque()
    out["perf_crises"] = {
        k: {nom: round((x.iloc[-1] / x.iloc[0] - 1) * 100, 1)
            for nom, (a, b, _l) in allocation.CRISES.items()
            if len(x := sr[k][a:b].dropna()) > 1}
        for k in ("poche_actions", "etats_longs", "indexees", "or", "matieres")
        if k in sr.columns
    }

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

    hors, crise, semaines = allocation.correlations(s)
    out["corr"] = {
        "ordre": list(hors.index),
        "hors": [[round(v * 100) for v in ligne] for ligne in hors.to_numpy()],
        "crise": [[round(v * 100) for v in ligne] for ligne in crise.to_numpy()],
        "semaines": semaines,
    }

    # Les plafonds sont exportés plutôt que recopiés dans le deck : la slide
    # des règles doit pouvoir dire lesquels sont SATURÉS et lesquels ne le
    # sont pas — c'est ce qui explique le 3,3 % d'or (plafond 10 %).
    out["plafonds"] = {k: v * 100 for k, v in allocation.PLAFONDS.items()}

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

    # --- du brut au net (correction du 2026-09-21) -----------------------
    # L'objectif du client est NET : ce qui doit battre l'inflation, c'est ce
    # qui lui reste. Le deck comparait un rendement brut à un seuil net.
    out["frais_inst"] = out["frais_total"] / allocation.MONTANT * 100
    out["frais_mandat"] = ips.FRAIS_MANDAT * 100
    out["net"] = ips.rendement_net(
        res["scenarios"][allocation.RETENU]["rendement_espere"],
        out["frais_inst"])
    out["seuil"] = ips.INFLATION_TARGET * 100

    # --- étape 5 : backtests --------------------------------------------
    # L'inflation RÉELLEMENT constatée sur la fenêtre du rejeu : c'est elle
    # qui juge le rendement réalisé, pas les 4 % de l'énoncé, qui décrivent
    # un régime que la période n'a pas connu.
    _infl = json.loads((allocation.DATA / "inflation_realisee.json").read_text(
        encoding="utf-8"))
    out["inflation"] = {
        "annuel": _infl["backtest"]["annuel"],
        "cumul": _infl["backtest"]["cumul"],
        "annees": _infl["backtest"]["annees"],
        "cinq_ans": _infl["fenetres"]["5 ans"]["annuel"],
    }
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
        "reel": ((v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1) * 100
                - _infl["backtest"]["annuel"],
        "pire": t["pire"], "sous": t["sous"], "s5": t["5"], "s10": t["10"],
        "episodes": [(x.sommet.strftime("%m/%Y"), x.creux.strftime("%m/%Y"),
                      x.perte * 100, backtests.mois(x.sommet, x.creux),
                      x.retour.strftime("%m/%Y") if pd.notna(x.retour) else None,
                      backtests.mois(x.sommet, x.retour) if pd.notna(x.retour) else None)
                     for x in ep.itertuples()],
        "var95": backtests.var_cvar(r, .95), "var99": backtests.var_cvar(r, .99),
        "rmin": r.min(), "rmax": r.max(), "n": len(r),
        "neg": (r < 0).mean() * 100, "sous4": (r < 4).mean() * 100,
        "sous_infl": (r < _infl["backtest"]["annuel"]).mean() * 100,
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
