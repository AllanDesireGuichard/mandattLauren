"""
Etape 7 -- projection du patrimoine NET TRANSMIS.

Compare trois strategies sur l'horizon de transmission. L'indicateur n'est
jamais le patrimoine brut : c'est ce qui arrive effectivement aux enfants.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ips                                    # noqa: E402
from core.succession import (Poche, droits_donation_np,  # noqa: E402
                             taux_effectif)

ROOT = Path(__file__).resolve().parent.parent

HORIZON = 25               # esperance de vie residuelle retenue a 60 ans
N_ENFANTS = 2
AGE = ips.CLIENT_AGE

GROSS = 0.0579             # rendement brut attendu de la SAA
FEES = ips.TOTAL_FEES      # mandat + instruments
FRAIS_CONTRAT_AV = 0.0025  # contrat luxembourgeois, negocie sur cette taille

R_CTO = GROSS - FEES - ips.TAX_DRAG_CTO_COMPETENT
R_AV = GROSS - FEES - ips.TAX_DRAG_STRUCTURED - FRAIS_CONTRAT_AV


def scenario(nom: str, av: float, np_don: float, cto: float,
             detail: str) -> dict:
    """
    av      montant verse en assurance-vie luxembourgeoise
    np_don  valeur en pleine propriete de l'actif dont la NUE-PROPRIETE
            est donnee immediatement
    cto     montant conserve en compte-titres
    """
    droits_don, base = droits_donation_np(np_don, AGE, N_ENFANTS) if np_don else (0.0, 0.0)

    # Les droits de donation sont acquittes par le donateur, sur le CTO.
    cto_net = cto - droits_don

    poches = [
        Poche("Assurance-vie LUX", av, "av_990i"),
        Poche("Nue-propriete donnee", np_don, "deja_transmis"),
        Poche("Compte-titres", cto_net, "succession"),
    ]
    for p in poches:
        p.croitre(R_AV if p.regime == "av_990i" else R_CTO, HORIZON)

    brut = sum(p.montant for p in poches)
    droits_deces = sum(p.droits_au_deces(N_ENFANTS) for p in poches)
    net = brut - droits_deces
    total_impot = droits_don + droits_deces

    return {"nom": nom, "detail": detail, "brut": brut,
            "droits_donation": droits_don, "droits_deces": droits_deces,
            "impot_total": total_impot, "net": net,
            "taux": taux_effectif(total_impot, brut + droits_don),
            "poches": poches}


def main() -> int:
    A = ips.TOTAL_ASSETS - ips.LIQUIDITY_NEED      # 90 M, hors poche liquidite
    print(f"Assiette                : {A:,.0f} EUR  (hors besoin de liquidite)")
    print(f"Horizon de transmission : {HORIZON} ans")
    print(f"Rendement net, CTO      : {R_CTO:.2%}")
    print(f"Rendement net, AV LUX   : {R_AV:.2%}"
          f"   (frais de contrat {FRAIS_CONTRAT_AV:.2%} deduits)\n")

    scenarios = [
        scenario("A -- Aucune structuration", 0, 0, A,
                 "tout en compte-titres, transmission au deces"),
        scenario("B -- Recommandee", 0.30 * A, 0.40 * A, 0.30 * A,
                 "30 % AV LUX, 40 % en nue-propriete donnee, 30 % CTO"),
        scenario("C -- Maximale", 0.30 * A, 0.60 * A, 0.10 * A,
                 "30 % AV LUX, 60 % en nue-propriete donnee, 10 % CTO"),
    ]

    print("=" * 78)
    print(f"PATRIMOINE NET TRANSMIS AUX ENFANTS, DANS {HORIZON} ANS")
    print("=" * 78)
    print(f"\n{'strategie':<28}{'brut':>12}{'impot':>12}{'NET':>12}{'taux':>8}")
    for s in scenarios:
        print(f"  {s['nom']:<26}{s['brut']/1e6:>11,.0f}M"
              f"{s['impot_total']/1e6:>11,.0f}M{s['net']/1e6:>11,.0f}M"
              f"{s['taux']:>8.1%}")

    base = scenarios[0]
    print(f"\n{'':<28}{'gain vs A':>12}")
    for s in scenarios[1:]:
        g = s["net"] - base["net"]
        print(f"  {s['nom']:<26}{g/1e6:>11,.0f}M   "
              f"soit {g/base['net']:+.0%} de plus pour les enfants")

    print("\n" + "=" * 78)
    print("DETAIL PAR ENVELOPPE -- strategie recommandee")
    print("=" * 78)
    s = scenarios[1]
    print(f"\n{'poche':<26}{'valeur a 25 ans':>18}{'droits':>12}{'net':>12}")
    for p in s["poches"]:
        d = p.droits_au_deces(N_ENFANTS)
        print(f"  {p.nom:<24}{p.montant/1e6:>17,.0f}M{d/1e6:>11,.0f}M"
              f"{(p.montant-d)/1e6:>11,.0f}M")
    print(f"  {'droits de donation (t=0)':<24}{'':>17} "
          f"{s['droits_donation']/1e6:>10,.0f}M")

    print("\n" + "=" * 78)
    print("LE CALENDRIER -- ce que coute un anniversaire")
    print("=" * 78)
    montant = 0.40 * A
    d60, _ = droits_donation_np(montant, 60, N_ENFANTS)
    d61, _ = droits_donation_np(montant, 61, N_ENFANTS)
    print(f"\n  Donation en nue-propriete de {montant/1e6:.0f} M EUR")
    print(f"    realisee avant 61 ans (nue-propriete a 50 %)   "
          f"{d60/1e6:>8,.1f}M de droits")
    print(f"    realisee apres  61 ans (nue-propriete a 60 %)   "
          f"{d61/1e6:>8,.1f}M de droits")
    print(f"    ECART                                          "
          f"{(d61-d60)/1e6:>8,.1f}M")
    print(f"\n  C'est la raison pour laquelle ce dossier a une date limite,")
    print(f"  et que cette date est le prochain anniversaire du client.")

    pd.DataFrame([{k: v for k, v in s.items() if k != "poches"}
                  for s in scenarios]).to_csv(
        ROOT / "data" / "transmission.csv", index=False)
    print("\n-> data/transmission.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
