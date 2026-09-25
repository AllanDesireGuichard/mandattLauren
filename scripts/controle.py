"""
Contrôle de cohérence du dossier -> rien d'anormal à l'écran si tout va bien.

Lancer :  PYTHONPATH=. python3 scripts/controle.py
          (après scripts/pitch/extraire.py, pour comparer app et deck)

POURQUOI. Trois fois en deux jours, un chiffre du dossier a été faux à un
endroit et juste à un autre : le nombre de titres de la poche actions, le
rendement de l'or, le rendement du portefeuille lui-même. Chaque fois la cause
était la même — deux chemins pour le même chiffre, et un seul mis à jour. Ce
script relit les deux sorties (l'application par ses modules, le deck par
scripts/pitch/data.json) et vérifie qu'elles disent la même chose, puis
contrôle ce qui doit être vrai par construction.

CE QU'IL NE FAIT PAS : il ne juge pas les chiffres, il vérifie qu'ils
concordent et qu'ils respectent les règles du mandat. Un rendement faux mais
cohérent partout passe ce contrôle.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from core import (actions, allocation, fiches, fonds, ips,  # noqa: E402
                  outlook, vue_secteurs)

DECK = RACINE / "scripts" / "pitch" / "data.json"
TOL = 5e-3                     # points de pourcentage


class Rapport:
    def __init__(self) -> None:
        self.echecs: list[str] = []

    def egal(self, nom: str, a: float, b: float, tol: float = TOL) -> None:
        bon = abs(a - b) <= tol
        if not bon:
            self.echecs.append(f"{nom} : app {a:.4f} ≠ deck {b:.4f}")
        print(f"  {'ok   ' if bon else 'ÉCART'} {nom:44} "
              f"{a:10.4f} / {b:10.4f}")

    def vrai(self, nom: str, cond: object, detail: str = "") -> None:
        if not cond:
            self.echecs.append(f"{nom}{(' — ' + detail) if detail else ''}")
        print(f"  {'ok   ' if cond else 'ÉCHEC'} {nom}"
              f"{(' — ' + detail) if detail else ''}")


def main() -> int:
    r = Rapport()
    e = allocation.entrees()
    w = allocation.poids_retenus()
    res = allocation.resultats()
    brut = allocation.rendement_retenu(e)
    ctl = allocation.controle_optimisation(e)

    # ------------------------------------------------------------------
    print("\nCe qui doit être vrai par construction")
    r.vrai("les poids retenus somment à 100 %", abs(sum(w.values()) - 1) < 1e-9)
    r.vrai("le rendement retenu est la somme pondérée des lignes",
           abs(brut - sum(w[k] * e.loc[k, "rendement"] for k in w)) < 1e-9)
    r.vrai("la pire baisse tient la limite du mandat",
           -res["scenarios"][allocation.RETENU]["pire_baisse"] / 100
           <= allocation.LIMITE,
           f"{res['scenarios'][allocation.RETENU]['pire_baisse']:.2f} % pour "
           f"une limite de {-allocation.LIMITE * 100:.0f} %")
    r.vrai("aucun plafond de l'étape 4 n'est dépassé",
           all(w.get(k, 0) <= c + 1e-9 for k, c in allocation.PLAFONDS.items()),
           ", ".join(f"{k} {w.get(k, 0) * 100:.2f} % / {c * 100:.0f} %"
                     for k, c in allocation.PLAFONDS.items()))
    r.vrai("le plancher de l'échelle AAA est tenu",
           w["etats_courts"] >= allocation.MIN_AAA - 1e-9)
    r.vrai("la clé des actions 40/35/10/15 est respectée",
           all(abs(w[k] / sum(w[x] for x in allocation.MIX_ACTIONS) - m) < 1e-6
               for k, m in allocation.MIX_ACTIONS.items()))

    # ------------------------------------------------------------------
    print("\nLes exclusions du mandat")
    r.vrai("aucun fonds retenu n'est hors des exclusions",
           not fonds.non_conformes(),
           ", ".join(f"{x['ticker']} ({x['statut']})"
                     for x in fonds.non_conformes()))
    r.vrai("aucun fonds crypto n'est proposé comme investissable",
           "crypto" not in fonds.ORDRE)
    d = actions.univers()
    sel = actions.selection(d)
    fin = outlook.final(sel)
    r.vrai("aucun titre retenu ne porte une exclusion",
           fin["exclusion"].isna().all(),
           ", ".join(fin.loc[fin["exclusion"].notna(), "longName"]))
    r.vrai("aucun titre retenu sous la taille minimale",
           (~fin["trop_petite"]).all())
    notes = d[d["note"].notna()]
    ecartees = set(notes.loc[vue_secteurs.ecartees(notes), "ticker"])
    r.vrai("aucun titre retenu dans un métier écarté par la vue sectorielle",
           not (set(fin["ticker"]) & ecartees),
           f"{len(ecartees)} sociétés notées écartées, "
           f"{len(vue_secteurs.VUE)} métiers")

    # ------------------------------------------------------------------
    print("\nLa poche actions")
    r.vrai(f"{outlook.N_FINAL} titres retenus", len(fin) == outlook.N_FINAL)
    r.vrai("une fiche rédigée pour chaque titre retenu",
           not fiches.manquantes(fin), ", ".join(fiches.manquantes(fin)))
    r.vrai("les plafonds du second étage sont tenus",
           fin["secteur"].value_counts().max() <= outlook.MAX_SECTEUR
           and fin["pays"].value_counts().max() <= outlook.MAX_PAYS,
           f"{fin['secteur'].nunique()} secteurs, {fin['pays'].nunique()} pays")
    p15 = actions.rendement_panier(fin)["central"]
    p30 = actions.rendement_panier(sel)["central"]
    r.vrai("le rendement de la poche dépend de la sélection",
           round(p15, 3) != round(p30, 3),
           f"15 titres {p15:.3f} % / 30 titres {p30:.3f} %")
    r.vrai("chaque titre retenu a un PER exploitable",
           actions.rendement_panier(fin)["sans_per"] == 0)

    # ------------------------------------------------------------------
    print("\nLes poids datent-ils d'une optimisation encore valable ?")
    r.vrai("dérive du rendement sous le seuil de relance",
           not ctl["a_relancer"],
           f"{ctl['derive']:+.4f} pt, seuil {allocation.DERIVE_MAX} pt "
           f"(optimisation du {ctl['date']})")

    # ------------------------------------------------------------------
    if not DECK.exists():
        print(f"\n{DECK.relative_to(RACINE)} absent : comparaison avec le deck "
              f"ignorée (lancer scripts/pitch/extraire.py).")
    else:
        D = json.loads(DECK.read_text(encoding="utf-8"))
        print("\nL'application et le deck (app / deck)")
        r.egal("rendement brut retenu", brut,
               D["scenarios"][allocation.RETENU]["rdt"])
        r.egal("rendement net de frais",
               ips.rendement_net(brut, D["frais_inst"]), D["net"])
        r.egal("rendement de la poche actions Europe",
               allocation.rendement_panier()["central"],
               D["panier_rdt"]["central"])
        r.egal("pire baisse du portefeuille retenu",
               res["scenarios"][allocation.RETENU]["pire_baisse"],
               D["scenarios"][allocation.RETENU]["pire"])
        for n in ["libre"] + res["etapes"]:
            r.egal(f"rendement du scénario {n}",
                   allocation.rendement(res["scenarios"][n]["poids"], e),
                   D["scenarios"][n]["rdt"])
        for k, v in w.items():
            if v >= 0.0005:
                r.egal(f"poids {k}", v * 100, D["retenu"][k] * 100)
        r.vrai("le deck retient les mêmes titres que l'app",
               D["entonnoir"]["final"] == len(fin))
        r.vrai("le deck ne propose aucun fonds non conforme",
               not D["fonds_non_conformes"],
               ", ".join(D["fonds_non_conformes"]))

    # ------------------------------------------------------------------
    if r.echecs:
        print(f"\n{len(r.echecs)} problème(s) :")
        for x in r.echecs:
            print(f"  - {x}")
        return 1
    print("\ncohérence : rien à signaler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
