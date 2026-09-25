"""
Onglet 3, bloc 5 — les fonds et ETF des autres classes d'actifs.

Les chiffres viennent de data/fonds.json (scripts/fetch_fonds.py) ; la règle
de choix est appliquée dans le script, l'app ne fait que l'afficher.
Décision d'Allan du 2026-09-18 : actions développées hors Europe en deux
fonds séparés, États-Unis et Japon, plutôt qu'un MSCI World qui aurait
compté l'Europe deux fois.

CE BLOC A ÉTÉ COMPLÉTÉ LE 2026-09-25. Il ne portait que deux commentaires ;
le tableau des fonds retenus, avec l'indice suivi, les frais, la taille et ce
qui avait écarté les concurrents, vivait à l'étape 4 (tabs/t4_allocation.py).
C'était la démonstration d'un choix, rangée dans l'étape qui en consomme le
résultat. Elle revient ici, augmentée du STATUT D'EXCLUSION de chaque fonds
retenu, qui est la première des trois règles de sélection et n'était affichée
nulle part. L'étape 4 garde les fonds et leur montant, rien de plus.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import fonds, taux, viz


def _taille(m: float | None) -> str:
    if m is None:
        return "—"
    return viz.fr(m / 1000, "Md€", 1) if m >= 1000 else viz.fr(m, "M€", 0)


def _signe(v: float | None, unite: str = "pt") -> str:
    if v is None or pd.isna(v):
        return "—"
    return ("+" if v > 0 else "") + viz.fr(v, unite, 2)


def bloc() -> None:
    d = fonds.charger()
    cl = d["classes"]

    st.markdown("#### Les fonds pour les autres classes d'actifs")
    st.markdown(
        "Pour les autres classes, on passe par des fonds indiciels. **Trois "
        "règles, dans cet ordre** : exclusions conformes au mandat, puis "
        "taille d'au moins 1 Md€ — pour ne jamais peser plus de 1 % d'un "
        "fonds —, puis les frais les plus bas."
    )
    st.markdown(
        "Les actions hors Europe sont prises en deux fonds, **États-Unis** et "
        "**Japon**, plutôt qu'un fonds « Monde » qui contient environ 15 % "
        "d'actions européennes, déjà détenues en direct."
    )
    _table(cl)
    _exclusions()
    _lectures(cl)
    st.caption(f"Frais, taille, indice, réplication et domicile : justETF ; "
               f"prix : Yahoo. Relevé du {taux.date_fr(d['releve'])}.")


# --------------------------------------------------------------------------
STATUTS = {"conforme": "Conforme", "sans objet": "Sans objet"}


def _table(cl: dict) -> None:
    """Le fonds retenu par classe, et ce qui a écarté ses concurrents."""
    rows = [(x["libelle"], f"{x['ticker'].split('.')[0]} · {x['nom']}",
             x["indice"] or "Or physique, pas d'indice",
             STATUTS.get(x["statut"], x["statut"]),
             viz.fr(x["frais"], "%", 2), _taille(x["taille"]),
             _ecartes(cl[x["cle"]]))
            for x in fonds.exclusions(cl)]
    st.table(pd.DataFrame(rows, columns=[
        "Classe", "Fonds retenu", "Indice suivi", "Exclusions du mandat",
        "Frais / an", "Taille", "Ce qui a écarté les autres"]
    ).set_index("Classe"))


def _ecartes(c: dict) -> str:
    """
    Ce qui a fait perdre les autres candidats, et non la règle de sélection.

    La règle est la même pour toutes les classes — conforme, plus de 1 Md€,
    puis les frais les plus bas — donc la recopier dans chaque ligne
    n'apprend rien. Ce qui diffère, c'est POURQUOI les concurrents sont
    tombés, et data/fonds.json porte un verdict par candidat.
    """
    par_motif: dict[str, list[str]] = {}
    for t, r in c["candidats"].items():
        if t == c["retenu"]:
            continue
        par_motif.setdefault(r["verdict"], []).append(t.split(".")[0])
    bouts = [f"{m} ({', '.join(sorted(v))})" for m, v in par_motif.items()]
    return f"{len(c['candidats'])} examinés · " + " · ".join(bouts)


def _exclusions() -> None:
    """
    Le contrôle des exclusions du mandat, affiché plutôt que supposé.

    Demande d'Allan du 2026-09-25 : « sélectionne uniquement les fonds qui
    correspondent parfaitement aux critères d'exclusion de la cliente ». La
    règle existait dans scripts/fetch_fonds.py ; son résultat n'était écrit
    nulle part, et l'application affirmait la conformité sans la montrer.
    """
    manque = fonds.non_conformes()
    if manque:
        st.error(
            "**Exclusions non tenues** : "
            + ", ".join(f"{x['ticker']} ({x['statut']})" for x in manque)
            + ". Ces fonds ne doivent pas être retenus.",
            icon=":material/block:")
        return
    st.markdown(
        "**Les exclusions du mandat, fonds par fonds.** *Conforme* : le "
        "filtre de l'indice retire le tabac, l'armement et le charbon, au "
        "moins aussi strictement que le mandat. *Sans objet* : le fonds ne "
        "détient aucune action d'entreprise — emprunts d'État indexés, or "
        "physique, contrats à terme de matières premières —, il n'y a donc "
        "rien à exclure. **Aucun fonds retenu n'est dans un autre cas**, et "
        "l'application le vérifie à chaque affichage."
    )
    st.caption(
        "Le filtre « Screened » est écarté partout où il existe : il ne "
        "retire pas l'armement conventionnel, que nous excluons des actions "
        "en direct. Un fonds Screened contredirait la règle appliquée aux "
        "titres. Les indices « SRI » l'excluent dès 5 % du chiffre "
        "d'affaires, comme le mandat ; les indices « Low Carbon SRI "
        "Selection » y ajoutent pétrole, gaz et nucléaire, donc plus strict "
        "que demandé — au prix d'un écart au marché plus grand."
    )


def _lectures(cl: dict) -> None:
    em = cl["emergents"]
    xzem = em["candidats"][em["retenu"]]
    rizd = cl["infrastructure"]["candidats"]["RIZD.DE"]
    st.markdown(
        f"**Deux constats à dire au client.**\n"
        f"- Le filtre éloigne peu du marché, **sauf pour les émergents** : "
        f"le seul fonds conforme a fait "
        f"{_signe(xzem['ecart_moyen'], 'points')} par an face au marché sur "
        f"{viz.fr(xzem['fenetre'], 'ans', 0)}. On le garde, et l'écart est "
        f"annoncé.\n"
        f"- **L'infrastructure est retirée de l'univers** : le seul fonds "
        f"filtré ne pèse que {_taille(rizd['taille'])}, et les gros fonds ne "
        f"filtrent rien. Aucun support conforme, donc aucune ligne.\n"
        f"- **Pas de fonds Bitcoin proposé** : la décision est de ne pas en "
        f"détenir (étape 4). Les candidats restent mesurés, ils ne sont pas "
        f"présentés comme investissables."
    )
    st.caption(
        "Neuf fonds étaient mal identifiés dans l'univers hérité — dont un "
        "fonds d'actions américaines présenté comme de la dette émergente. "
        "Chacun est désormais contrôlé sur deux sources par son ISIN."
    )
