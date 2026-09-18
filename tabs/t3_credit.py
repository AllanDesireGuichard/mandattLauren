"""
Onglet 3, bloc 5 — le crédit : prêter aux entreprises.

Chiffres : data/fonds_credit.json (scripts/fetch_fonds_credit.py) pour les
fonds, data/rendements.json pour les rendements espérés de l'étape 2, courbe
de la BCE (ensemble de la zone euro) pour l'État de même échéance.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st

from core import obligations, pedago, rendements, taux, viz

FICHIER = Path(__file__).resolve().parents[1] / "data" / "fonds_credit.json"
DEFAUTS_IG = 0.11      # perte moyenne annuelle sur défauts, Moody's (étape 2)


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


def _etat(maturite: float, zone: dict) -> float:
    """Taux de l'État zone euro à la même échéance, en taux annuel."""
    return (math.exp(obligations.taux_zero(maturite, zone) / 100) - 1) * 100


def bloc() -> None:
    d = json.loads(FICHIER.read_text(encoding="utf-8"))
    f, ret, rep = d["fonds"], d["retenu"], d["repere_etat"]
    r = rendements.charger()["classes"]
    zone = taux.charger()["svensson"]["toutes"]
    c = f[ret]

    st.markdown("#### Le crédit : prêter aux entreprises")
    st.markdown(
        "Acheter une obligation d'entreprise, c'est lui prêter de l'argent. "
        "Elle paie un peu plus qu'un État, parce qu'elle peut faire défaut. "
        "L'étape 2 a montré que ce supplément, la prime de crédit, est "
        "aujourd'hui parmi les plus faibles depuis quarante ans. Trois "
        "questions en découlent : quel crédit, sur quelle durée, et avec "
        "quel fonds."
    )

    # --- 1. quel crédit ---------------------------------------------------
    st.markdown("**1. Quel crédit : seulement les entreprises bien notées**")
    st.table(pd.DataFrame([
        ("Emprunts d'État de la zone euro", _pct(r["govt_bonds_eur"]["central"]),
         "Référence"),
        ("Entreprises bien notées (investment grade)",
         _pct(r["credit_ig_eur"]["central"]), "Retenu"),
        ("Entreprises à haut rendement", _pct(r["hy_euro"]["central"]),
         "Écarté"),
    ], columns=["Emprunteur", "Rendement espéré, défauts déduits (étape 2)",
                "Décision"]).set_index("Emprunteur"))
    st.markdown(
        "Le haut rendement affiche un taux élevé à l'achat, mais une fois "
        "retirées les pertes moyennes sur défauts, il rapporte **moins que "
        "les États**. On ne prend que des entreprises bien notées."
    )

    # --- 2. quelle durée --------------------------------------------------
    st.markdown("**2. Quelle durée : courte**")
    st.markdown(
        "On compare cinq fonds de la même famille, du plus court au plus "
        "long. Pour chacun : ce qu'il rapporte, ce que rapporte un emprunt "
        "d'État de même échéance, la différence (la prime), et ce qu'il a "
        "perdu dans les deux dernières crises."
    )
    lignes = []
    for t, x in sorted(f.items(), key=lambda kv: kv[1]["duree"]):
        e = _etat(x["maturite"], zone)
        lignes.append((
            f"{t} · {x['nom']}", viz.fr(x["duree"], "ans", 1),
            _pct(x["rendement"]), _pct(e), viz.fr(x["rendement"] - e, "pt", 2),
            viz.fr(-x["duree"], "%", 1),
            viz.fr(x["pires_baisses"].get("2020", float("nan")), "%", 1),
            viz.fr(x["pires_baisses"].get("2022", float("nan")), "%", 1)))
    lignes.append((
        f"Repère : {rep['ticker']} · emprunts d'État zone euro 1-3 ans", "—",
        "—", "—", "—", "—", viz.fr(rep["pires_baisses"]["2020"], "%", 1),
        viz.fr(rep["pires_baisses"]["2022"], "%", 1)))
    st.table(pd.DataFrame(lignes, columns=[
        "Fonds", "Durée", "Rendement à l'échéance", "État, même échéance",
        "Prime", "Si la prime monte d'un point", "Pire baisse 2020",
        "Pire baisse 2022"]).set_index("Fonds"))
    st.caption(
        f"Rendement et durée : fiches iShares au {taux.date_fr(c['date'])}. État : courbe "
        f"de la BCE, ensemble de la zone euro, à l'échéance moyenne du "
        f"fonds. Baisses mesurées sur les cours du vendredi (voir l'encadré "
        f"sur mars 2020)."
    )
    longs = [x for x in f.values() if x["duree"] > 4]
    p_court = c["rendement"] - _etat(c["maturite"], zone)
    st.info(
        f"**Allonger ne paie pas.** Du fonds le plus court au plus long, la "
        f"prime passe de {viz.fr(p_court, 'point', 2)} à environ "
        f"{viz.fr(max(x['rendement'] - _etat(x['maturite'], zone) for x in longs), 'point', 2)}, "
        f"alors que la durée est multipliée par trois, et les pertes avec : "
        f"{viz.fr(-c['pires_baisses']['2022'], '%', 1)} en 2022 pour le "
        f"fonds court, {viz.fr(-min(x['pires_baisses']['2022'] for x in longs), '%', 1)} "
        f"pour les longs. C'est la conclusion de l'étape 2, mesurée : quand "
        f"la prime est faible, on reste court.",
        icon=":material/lightbulb:",
    )

    # --- 3. quel fonds -----------------------------------------------------
    st.markdown("**3. Quel fonds**")
    st.markdown(
        f"Même règle qu'au bloc précédent : exclusions conformes, taille "
        f"d'au moins 1 Md€, puis les frais les plus bas, avec ici une durée "
        f"d'au plus {viz.fr(d['duree_max'], 'ans', 0)}."
    )
    lignes = []
    for t, x in sorted(f.items(), key=lambda kv: kv[1]["duree"]):
        lignes.append((
            f"{t} · {x['nom']}", x["indice"] or "—",
            "conforme" if x["exclusions"] == "conforme" else "aucun filtre",
            _pct(x["frais"]),
            viz.fr(x["taille"] / 1000, "Md€", 1),
            "retenu" if x["verdict"] == "retenu" else "écarté : " + x["verdict"]))
    st.table(pd.DataFrame(lignes, columns=[
        "Fonds", "Indice suivi", "Exclusions", "Frais par an", "Taille",
        "Verdict"]).set_index("Fonds"))

    net = c["rendement"] - DEFAUTS_IG
    echelle = [obligations.analyse(m, zone)["rendement"] for m in (2, 3, 5, 7, 10)]
    ech = sum(echelle) / len(echelle)
    st.warning(
        f"**Le crédit court rapporte à peine plus que l'État.** Le fonds "
        f"retenu rapporte {_pct(c['rendement'])}, soit "
        f"{viz.fr(p_court, 'point', 2)} de plus qu'un emprunt d'État de même "
        f"échéance ; défauts moyens déduits, il reste "
        f"{viz.fr(p_court - DEFAUTS_IG, 'point', 2)}. En échange, il a perdu "
        f"{viz.fr(-c['pires_baisses']['2020'], '%', 1)} lors du choc de 2020, "
        f"contre {viz.fr(-rep['pires_baisses']['2020'], '%', 1)} pour les "
        f"États de même durée. Conséquence pour l'étape 4 : le crédit tel "
        f"qu'on l'investit rapporte **{_pct(net)}** défauts déduits, et non "
        f"les {_pct(r['credit_ig_eur']['central'])} de l'indice toutes "
        f"durées de l'étape 2 ; c'est moins que l'échelle d'emprunts d'État "
        f"de 2 à 10 ans du bloc 3 ({_pct(ech)}). Sa place dans "
        f"l'allocation sera donc, au mieux, modeste.",
        icon=":material/warning:",
    )

    _pedagogie(c, rep)


def _pedagogie(c: dict, rep: dict) -> None:
    pedago.explique(
        "Ce que la prime de crédit rémunère, et ce qu'elle coûte en crise",
        "La prime, c'est l'écart entre ce que paie l'entreprise et ce que "
        "paie un État pour la même durée. Elle rémunère deux choses : le "
        "risque que l'entreprise ne rembourse pas, et le risque que la prime "
        "elle-même augmente, ce qui fait baisser le prix des obligations "
        "déjà achetées.",
        "Le second risque se voit dans les chiffres de 2020 : les défauts "
        "sont restés rares parmi les entreprises bien notées, mais la prime "
        "s'est "
        "envolée en quelques semaines, et le fonds court a perdu "
        f"{viz.fr(-c['pires_baisses']['2020'], '%', 1)}, trois fois plus que "
        f"les États de même durée ({viz.fr(-rep['pires_baisses']['2020'], '%', 1)}). "
        "En 2022, au contraire, c'est la hausse des taux qui a tout fait "
        "baisser : crédit et États courts ont perdu à peu près autant.",
        "Plus un fonds est long, plus une hausse de la prime fait mal : la "
        "perte est à peu près égale à la durée multipliée par la hausse. "
        "C'est pour cela qu'une prime faible pousse vers les durées courtes.",
    )
    pedago.explique(
        "« Screened » ne veut pas dire la même chose pour les actions et les "
        "obligations",
        "Au bloc précédent, l'indice actions « MSCI Screened » a été écarté "
        "parce qu'il laisse passer l'armement conventionnel. Pour les "
        "obligations, le filtre de base de Bloomberg MSCI, qui porte le même "
        "nom, exclut au contraire l'armement conventionnel dès 5 % du "
        "chiffre d'affaires, le tabac et le charbon dès 5 %. Les indices "
        "« ESG SRI » retenus ici appliquent ce filtre, et y ajoutent le "
        "pétrole et le gaz.",
        "La leçon est la même qu'avec les libellés faux : on ne juge pas un "
        "fonds sur son nom, on lit la méthodologie de son indice.",
        source="Méthodologies Bloomberg MSCI Euro Corporate 0-3 ESG SRI "
               "(juill. 2025) et Bloomberg MSCI ESG Fixed Income, lues le "
               "18/09/2026 · scripts/fetch_fonds_credit.py",
    )
    pedago.explique(
        "Mars 2020 : quand le prix en bourse s'écarte de la valeur du fonds",
        "Au plus fort de la panique, le 18 mars 2020, le fonds retenu a "
        "coté un jour 6 % sous la veille, avant de revenir le lendemain. Les "
        "obligations qu'il détenait n'avaient pas perdu 6 % en un jour : "
        "c'est le prix en bourse du fonds qui s'est brièvement écarté de la "
        "valeur de son contenu, faute d'acheteurs.",
        "On a donc mesuré les baisses sur les cours du vendredi, pour tous "
        "les fonds, afin de ne pas prendre ce point isolé pour une perte. "
        "Mais le phénomène est réel, et il a une conséquence pratique : un "
        "fonds obligataire ne se vend pas en pleine panique. La poche de "
        "10 M€ à décaisser est en obligations d'État détenues en direct "
        "(bloc 3), précisément pour ne jamais avoir à le faire.",
    )
