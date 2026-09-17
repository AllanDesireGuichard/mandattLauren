"""
Selectionne le support principal et le suppleant de chaque classe d'actifs,
depuis les ~218 candidats.

Produit data/universe.csv (l'univers retenu) et un rapport de couverture
indiquant, classe par classe, si un instrument conforme au mandat existe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.esg import esg_required, esg_status  # noqa: E402
from core.ips import SAA_INDICATIVE          # noqa: E402
from core.metrics import describe, load_prices, rank_within_class  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Classes hors SAA conservees comme briques d'optimisation ou de repli.
EXTRA_CLASSES = ["global_agg_hedged", "green_bonds", "credit_hy",
                 "credit_ig_global", "govt_bonds_global", "bonds_em",
                 "real_estate"]


def main() -> int:
    uni = pd.read_csv(ROOT / "data" / "universe_candidates.csv")

    # libelles recuperes pour les tickers d'extension, puis re-marquage ESG
    names_path = ROOT / "data" / "extension_names.csv"
    if names_path.exists():
        nm = pd.read_csv(names_path).set_index("ticker")["name"].dropna()
        uni["name"] = uni.apply(
            lambda r: nm.get(r["ticker"], r["name"])
            if (not isinstance(r["name"], str) or not r["name"]) else r["name"],
            axis=1)
        import re as _re
        _esg = _re.compile(r"ESG|SRI|Screen|Sustain|Paris|Green|Socially|CTB|PAB", _re.I)
        uni["esg"] = uni["name"].fillna("").str.contains(_esg)
        # les obligations vertes le sont par construction
        uni.loc[uni.saa_class == "green_bonds", "esg"] = True

        # capitalisant / distribuant, lu dans le libelle quand la colonne est vide
        _acc = _re.compile(r"\(acc\)|\bacc\b|accumul|\b\dC\b|\(C\)|\bCap\b", _re.I)
        _dis = _re.compile(r"\(dist\)|\bdist\b|\bdis\b|\binc\b|\b\dD\b|distrib", _re.I)
        def _dist(r):
            if isinstance(r["distribution"], str) and r["distribution"]:
                return r["distribution"]
            n = r["name"] if isinstance(r["name"], str) else ""
            if _acc.search(n):
                return "acc"
            if _dis.search(n):
                return "dist"
            return ""
        uni["distribution"] = uni.apply(_dist, axis=1)

    px = load_prices(uni.ticker.tolist())
    print(f"Candidats          : {len(uni)}")
    print(f"Series recuperees  : {px.shape[1]}")

    stats = describe(px, dict(zip(uni.ticker, uni.saa_class)))
    print(f"Series exploitables: {len(stats)}\n")
    stats.to_csv(ROOT / "data" / "instrument_stats.csv")

    classes = list(SAA_INDICATIVE) + EXTRA_CLASSES
    kept, report = [], []
    for c in classes:
        r = rank_within_class(uni, stats, c)
        if r.empty:
            report.append({"classe": c, "poids": SAA_INDICATIVE.get(c, 0.0),
                           "candidats": 0, "retenus": 0, "esg": 0,
                           "statut": "AUCUN CANDIDAT"})
            continue
        elig = r[r.ok_hist & r.ok_clean & r.ok_data & r.ok_vol]
        # Quand le filtre ESG est exige, le support PRINCIPAL doit le porter.
        # Se contenter d'un suppleant ESG viderait le mandat de son sens.
        if esg_required(c) and len(elig):
            esg_ok = elig[elig["esg"].fillna(False).astype(bool)]
            if len(esg_ok):
                elig = pd.concat([esg_ok, elig[~elig.index.isin(esg_ok.index)]])
        eligible = len(elig) > 0
        top = elig.head(3) if eligible else r.head(1)
        for rank, (t, row) in enumerate(top.iterrows()):
            kept.append({
                "ticker": t, "name": row["name"], "saa_class": c,
                "esg": bool(row["esg"]) if pd.notna(row["esg"]) else False,
                "esg_scope": esg_status(c), "domicile": row["domicile"],
                "distribution": row["distribution"], "years": row["years"],
                "vol": round(row["vol"], 4), "max_dd": round(row["max_dd"], 4),
                "cagr": round(row["cagr"], 4), "source": row["source"],
                "role": ("primary" if rank == 0 else "alternate")
                        if eligible else "RECALE",
                "verdict": row["verdict"],
                "why_vol": row.get("why_vol", ""),
            })
        n_esg = int(elig["esg"].fillna(False).sum()) if len(elig) else 0
        w = SAA_INDICATIVE.get(c, 0.0)
        if not len(elig):
            st = "AUCUN ELIGIBLE"
        elif esg_required(c) and n_esg == 0:
            st = "ESG MANQUANT"
        elif esg_required(c) and not bool(top.iloc[0]["esg"]):
            st = "PRINCIPAL NON ESG"
        elif esg_required(c):
            st = "OK"
        else:
            st = f"OK ({esg_status(c)})"
        report.append({"classe": c, "poids": w, "candidats": len(r),
                       "retenus": len(top), "esg": n_esg,
                       "esg_scope": esg_status(c), "statut": st})

    sel = pd.DataFrame(kept)
    sel.to_csv(ROOT / "data" / "universe.csv", index=False)
    rep = pd.DataFrame(report).sort_values("poids", ascending=False)

    print("--- COUVERTURE PAR CLASSE D'ACTIFS ---")
    print(f"{'classe':<24}{'poids':>7}{'cand.':>7}{'ESG':>5}  {'filtre':<16}statut")
    for _, x in rep.iterrows():
        w = f"{x.poids:.0%}" if x.poids else "-"
        print(f"{x.classe:<24}{w:>7}{x.candidats:>7}{x.esg:>5}  "
              f"{x.esg_scope:<16}{x.statut}")

    prob = rep[(rep.poids > 0) & (~rep.statut.str.startswith("OK"))]
    if len(prob):
        print(f"\n--- TROUS RESTANTS : {prob.poids.sum():.0%} de l'allocation ---")
        for _, x in prob.iterrows():
            print(f"  {x.classe} ({x.poids:.0%}) : {x.statut}")
    else:
        print("\nToutes les classes ponderees sont couvertes.")

    print(f"\n-> data/universe.csv  ({len(sel)} supports retenus)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
