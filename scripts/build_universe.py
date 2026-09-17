"""
Construit l'univers investissable etendu.

Deux sources :
  1. equitydb2 -- 266 tickers europeens deja references et deja en cache
     (10 ans d'historique quotidien, suffisant pour SELECTIONNER des
     instruments ; la calibration longue passe par les proxys de core/data.py)
  2. une liste d'extension ciblee sur les trous : credit EUR filtre ESG,
     obligations vertes, monetaire EUR, infrastructure, alternatifs

Le classement vers les classes d'actifs de la SAA est fait par regles
explicites sur le libelle, avec derogations manuelles. Chaque ligne porte sa
provenance, pour qu'on sache toujours d'ou vient un support.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
EQDB = Path.home() / "projets" / "equitydb2"
EQDB_UNIVERSE = EQDB / "state" / "etf_universe.csv"
EQDB_CACHE = EQDB / "state" / "cache" / "etf"

EU_DOMICILES = {"IE", "LU", "DE", "FR", "CH", "JE", "NL", "AT", "GB"}

ESG_RE = re.compile(r"ESG|SRI|Screen|Sustain|Paris|Green|Socially", re.I)

# --------------------------------------------------------------------------
# Extension ciblee sur les trous. Candidats larges : la validation tranchera.
# --------------------------------------------------------------------------

EXTENSION: dict[str, list[str]] = {
    "credit_ig_eur": [
        "SUOE.L", "IEAC.L", "EUCR.DE", "SRIE.DE", "EBBB.L",
        "ECRP.L", "CBE3.DE", "IEBC.L", "XB4E.DE", "UEFD.DE", "EEXD.PA",
        # NOTE : XZEC.DE et EEDS.L figuraient ici sur la foi de leur ticker.
        # Verification faite, ce sont des fonds d'ACTIONS (Stoxx European
        # Market Leaders et MSCI USA CTB). Reclasses en actions ci-dessous.
    ],
    "green_bonds": [
        "GRON.DE", "EGRN.L", "XGBE.DE", "GRNB.L", "EGRE.DE",
    ],
    "govt_bonds_eur": [
        "IBGL.L", "IBGX.L", "SEGA.L", "X03G.DE", "MTH.PA", "C53.PA",
        "XGLE.DE", "EM710.DE", "IEGA.L", "SEGA.DE",
    ],
    "inflation_linked": [
        "IBCI.DE", "XEIN.DE", "EMI.PA", "IL15.L", "GISG.L", "INFL.L",
    ],
    "global_agg_hedged": [
        "AGGH.MI", "VAGF.L", "XBAE.DE", "GLAG.L", "AGGG.L", "VDTE.L",
    ],
    "cash": [
        "CSH2.PA", "PST.PA", "ERNE.L", "ERNA.L", "ERND.L", "SMRT.DE",
        "XEON.DE", "C3M.PA",
    ],
    # Souverain EUR court : la poche A (IPS §6.2) combine monetaire ET
    # souverain court echelonne. MTA.PA etait classe en monetaire a tort.
    "govt_bonds_eur_short": [
        "MTA.PA", "SEGA.DE", "X13G.DE", "DBXN.DE", "IBGS.DE", "EM13.DE",
    ],
    "infrastructure": [
        "INFR.L", "GIN.L", "NFRA.L", "GLIN.L", "IFRA.L", "MAGI.L",
        "DH2O.L", "GLGI.L",
    ],
    "gold": [
        "4GLD.DE", "EWG2.DE", "GZUR.SW", "ZGLD.SW", "OD7F.DE", "VZLD.SW",
    ],
    "alternatives": [
        "MAFU.L", "DBMF.L", "TREN.L", "CTA.L", "ALTS.L", "LSAU.L",
        "ICOM.L", "COMF.L", "CMFP.L", "IAUP.L", "SPGP.L", "GDGB.L",
        "WCOB.L", "XDBC.DE",
    ],
    "equity_developed": [
        "SUJP.L", "SRIW.DE", "EESG.L", "SAWD.L", "PABW.L", "WSRI.DE",
        "EDMW.L", "SUSW.L", "SUWS.L", "XZEC.DE", "EEDS.L",
    ],
    "equity_emerging": [
        "XZEM.DE", "EMSR.L", "SUSM.L", "EGRA.L",
    ],
}

# --------------------------------------------------------------------------
# Regles de classement depuis le referentiel equitydb2
# --------------------------------------------------------------------------

def classify(row: pd.Series) -> str | None:
    name, cat, reg = str(row["name"]), str(row["category"]), str(row.get("region", ""))
    n = name.lower()

    if cat == "crypto":
        return "crypto"
    if cat == "currency" or "overnight" in n or "ultra-short" in n or "ultrashort" in n:
        return "cash"
    if cat == "commodity":
        return "gold" if ("gold" in n) else "alternatives"
    if cat == "real_estate":
        return "real_estate"

    if cat == "bond":
        if "inflation" in n or "index-linked" in n or "tips" in n:
            return "inflation_linked"
        if "high yield" in n or " hy " in n:
            return "credit_hy"
        if any(k in n for k in ("0-1", "1-3", "ultra")):
            return "govt_bonds_eur_short" if reg == "Europe" else None
        if "em bond" in n or reg == "EM":
            return "bonds_em"
        if "aggregate" in n:
            return "global_agg_hedged"
        if "corp" in n:
            return "credit_ig_eur" if reg == "Europe" else "credit_ig_global"
        if any(k in n for k in ("govt", "government", "sovereign", "treasury", "gilt")):
            return "govt_bonds_eur" if reg == "Europe" else "govt_bonds_global"
        return None

    if cat == "sector":
        if "utilit" in n or "infrastructure" in n:
            return "infrastructure"
        return None

    if cat in ("core_equity", "region"):
        if reg == "EM":
            return "equity_emerging"
        if reg in ("US", "Europe", "Global", "Japan", "UK", "DM"):
            return "equity_developed"
        return None

    # L'eau et les utilities thematiques ne sont PAS de l'infrastructure au
    # sens de l'allocation : on cherche des actifs a revenus contractuellement
    # indexes sur l'inflation, pas un pari sectoriel.
    if cat == "thematic" and "infrastructure" in n:
        return "infrastructure"
    return None


def main() -> int:
    eq = pd.read_csv(EQDB_UNIVERSE)
    eu = eq[eq.domicile.isin(EU_DOMICILES)].copy()
    eu["saa_class"] = eu.apply(classify, axis=1)
    eu = eu[eu.saa_class.notna()].copy()
    eu["esg"] = eu["name"].str.contains(ESG_RE)
    eu["source"] = "equitydb2"
    eu = eu[["ticker", "name", "saa_class", "esg", "domicile", "distribution",
             "region", "source"]]

    ext = pd.DataFrame([
        {"ticker": t, "name": "", "saa_class": k, "esg": None,
         "domicile": "", "distribution": "", "region": "", "source": "extension"}
        for k, ts in EXTENSION.items() for t in ts
    ])
    ext = ext[~ext.ticker.isin(eu.ticker)]

    uni = pd.concat([eu, ext], ignore_index=True).drop_duplicates("ticker")
    uni.to_csv(ROOT / "data" / "universe_candidates.csv", index=False)

    print(f"equitydb2 europeen classe : {len(eu)}")
    print(f"extension ajoutee         : {len(ext)}")
    print(f"TOTAL candidats           : {len(uni)}\n")

    piv = (uni.assign(esg=uni.esg.fillna(False))
              .pivot_table(index="saa_class", columns="source", values="ticker",
                           aggfunc="count", fill_value=0))
    esg = eu[eu.esg].groupby("saa_class").size().rename("esg_deja_valide")
    out = piv.join(esg).fillna(0).astype(int)
    out["total"] = out.sum(axis=1) - out.get("esg_deja_valide", 0)
    print(out.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
