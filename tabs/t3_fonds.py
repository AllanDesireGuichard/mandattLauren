"""
Onglet 3, bloc 4 — les fonds et ETF des autres classes d'actifs.

Les chiffres viennent de data/fonds.json (scripts/fetch_fonds.py) ; la règle
de choix est appliquée dans le script, l'app ne fait que l'afficher.
Décision d'Allan du 2026-09-18 : actions développées hors Europe en deux
fonds séparés, États-Unis et Japon, plutôt qu'un MSCI World qui aurait
compté l'Europe deux fois.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import fonds, pedago, taux, viz


def _taille(m: float | None) -> str:
    if m is None:
        return "—"
    return viz.fr(m / 1000, "Md€", 1) if m >= 1000 else viz.fr(m, "M€", 0)


def _signe(v: float | None, unite: str = "pt") -> str:
    if v is None or pd.isna(v):
        return "—"
    return ("+" if v > 0 else "") + viz.fr(v, unite, 2)


EXCLUSIONS_FR = {
    "conforme": "conforme",
    "non conforme": "armement conventionnel non exclu",
    "non filtré": "aucun filtre",
    "à vérifier": "non vérifiées",
    "sans objet": "sans objet",
}


def bloc() -> None:
    d = fonds.charger()
    cl = d["classes"]

    st.markdown("#### Les fonds pour les autres classes d'actifs")
    st.markdown(
        "Les actions européennes et les emprunts d'État s'achètent en direct. "
        "Pour les autres classes, acheter les titres un par un n'aurait pas "
        "de sens : des centaines de valeurs américaines ou émergentes, des "
        "lingots, des contrats à terme sur matières premières. On passe donc "
        "par des fonds cotés en bourse (ETF), qui répliquent un indice. Pour "
        "chaque classe, on a comparé trois ou quatre fonds, tous cotés à "
        "Francfort en euros, pour que leurs chiffres soient comparables."
    )
    st.markdown(
        "Les actions des pays développés hors Europe sont traitées en deux "
        "fonds, **États-Unis** et **Japon**, plutôt qu'un fonds « Monde ». "
        "Un fonds Monde contient environ 15 % d'actions européennes, que le "
        "portefeuille détient déjà en direct : on les aurait eues deux fois. "
        "Et l'étape 2 a estimé séparément ce que rapportent les deux marchés."
    )

    st.markdown("**Cinq critères, dans cet ordre**")
    st.table(pd.DataFrame([
        ("1. Exclusions", "L'indice suivi exclut-il le tabac, l'armement et "
         "le charbon ?", "Le mandat les interdit, et on les a déjà retirés "
         "des actions en direct.", "Éliminatoire"),
        ("2. Taille", "Montant total investi dans le fonds.",
         "Une ligne de 5 à 10 M€ ne doit pas dépasser 1 % du fonds, pour ne "
         "pas dépendre des autres porteurs.", "Éliminatoire sous 1 Md€"),
        ("3. Frais", "Frais prélevés chaque année par le gérant du fonds.",
         "Ils viennent en déduction du rendement, année après année.",
         "Le moins cher l'emporte"),
        ("4. Écart de suivi", "Écart de performance mois par mois avec un "
         "fonds de référence.", "Vérifie que les frais annoncés sont les "
         "frais réels, et mesure combien un filtre éloigne du marché.",
         "Contrôle"),
        ("5. Liquidité", "Montants échangés chaque jour en bourse.",
         "Indique la facilité d'exécution (voir l'encadré plus bas).",
         "Information"),
    ], columns=["Critère", "Ce qu'on regarde", "Pourquoi", "Règle"])
        .set_index("Critère"))

    # --- ce qu'on retient ------------------------------------------------
    st.markdown("**Ce qu'on retient**")
    lignes = []
    for k in fonds.ORDRE:
        c = cl[k]
        r = c["candidats"].get(c["retenu"]) if c["retenu"] else None
        lignes.append((c["libelle"],
                       f"{c['retenu']} · {r['nom']}" if r else "à décider",
                       r["indice"] or "—" if r else "—",
                       viz.fr(r["frais"], "%", 2) if r else "—",
                       _taille(r["taille"]) if r else "—"))
    st.table(pd.DataFrame(lignes, columns=[
        "Classe", "Fonds retenu", "Indice suivi", "Frais par an", "Taille"])
        .set_index("Classe"))
    st.caption(f"Frais, taille et indice : justETF ; prix et volumes : Yahoo. "
               f"Relevé du {taux.date_fr(d['releve'])}.")

    # --- le détail, classe par classe ----------------------------------------
    st.markdown("**Le détail, classe par classe**")
    onglets = st.tabs([cl[k]["libelle"] for k in fonds.ORDRE])
    for k, o in zip(fonds.ORDRE, onglets):
        with o:
            _classe(cl[k])

    _lectures(cl)
    _pedagogie()


def _classe(c: dict) -> None:
    ref = c["reference"]
    lignes = []
    for t, x in c["candidats"].items():
        verdict = "retenu" if x["verdict"] == "retenu" else (
            "écarté : " + x["verdict"])
        lignes.append((
            f"{t} · {x['nom']}", EXCLUSIONS_FR[x["exclusions"]],
            viz.fr(x["frais"], "%", 2), _taille(x["taille"]),
            viz.fr(x["echange_jour"], "M€", 1),
            "référence" if t == ref else _signe(x.get("ecart_moyen")),
            "référence" if t == ref else _signe(x.get("ecart_type")).lstrip("+"),
            verdict))
    st.table(pd.DataFrame(lignes, columns=[
        "Fonds", "Exclusions", "Frais par an", "Taille",
        "Échangé par jour", "Écart moyen par an*", "Variabilité de l'écart*",
        "Verdict"]).set_index("Fonds"))
    fen = [x.get("fenetre") for x in c["candidats"].values() if x.get("fenetre")]
    st.caption(
        f"* Face à {ref}, en données mensuelles, sur la période commune "
        f"(jusqu'à {viz.fr(max(fen), 'ans', 1) if fen else '—'}). « Écart "
        f"moyen » : ce que le fonds a rapporté de plus (+) ou de moins (−) "
        f"par an. « Variabilité » : de combien il s'en écarte une année "
        f"ordinaire, dans un sens ou dans l'autre."
    )


def _lectures(cl: dict) -> None:
    us, jp, em = cl["usa"], cl["japon"], cl["emergents"]
    xzmu = us["candidats"][us["retenu"]]
    xzmj = jp["candidats"][jp["retenu"]]
    xzem = em["candidats"][em["retenu"]]
    ayem = em["candidats"]["AYEM.DE"]
    st.info(
        f"**Actions : le filtre éloigne peu du marché, sauf dans les pays "
        f"émergents.** Une année ordinaire, le fonds américain retenu "
        f"s'écarte du S&P 500 d'environ "
        f"{viz.fr(xzmu['ecart_type'], 'points', 1)}, le japonais du marché "
        f"japonais d'environ {viz.fr(xzmj['ecart_type'], 'points', 1)} : "
        f"c'est peu. Pour les émergents, le seul fonds "
        f"conforme a fait **{_signe(xzem['ecart_moyen'], 'points')} par an** "
        f"face au marché sur {viz.fr(xzem['fenetre'], 'ans', 0)}, avec une "
        f"variabilité de {viz.fr(xzem['ecart_type'], 'points', 1)}. Son "
        f"indice ne garde que la moitié la mieux notée de chaque secteur et "
        f"exclut aussi le pétrole et le gaz : il est bien plus strict que le "
        f"mandat, et ne ressemble plus vraiment au marché. Le fonds "
        f"« Screened », lui, colle au marché ({_signe(ayem['ecart_moyen'], 'point')} "
        f"par an) mais laisse passer l'armement conventionnel. On garde "
        f"le fonds conforme : le passé ne dit pas l'avenir, mais cet écart "
        f"sera annoncé au client.",
        icon=":material/lightbulb:",
    )
    rizd = cl["infrastructure"]["candidats"]["RIZD.DE"]
    iqqi = cl["infrastructure"]["candidats"]["IQQI.DE"]
    st.warning(
        f"**L'infrastructure est retirée de l'univers.** Aucun fonds ne "
        f"passe les deux premiers critères. Le seul fonds filtré ne pèse que "
        f"{_taille(rizd['taille'])} : une ligne de 5 M€ en représenterait "
        f"{viz.fr(500 / rizd['taille'], '%', 0)}. Les fonds assez gros, comme "
        f"celui d'iShares ({_taille(iqqi['taille'])}, "
        f"{viz.fr(iqqi['frais'], '%', 2)} de frais), ne filtrent rien, alors "
        f"que l'infrastructure cotée compte des producteurs d'électricité "
        f"au charbon. Plutôt que de faire une exception au mandat, on s'en "
        f"passe : l'étape 4 répartira entre les classes restantes.",
        icon=":material/warning:",
    )
    btc = cl["crypto"]
    ib1t, btce = btc["candidats"]["IB1T.DE"], btc["candidats"]["BTCE.DE"]
    gld = cl["or"]["candidats"]["4GLD.DE"]
    st.info(
        f"**Les frais mesurés confirment les frais annoncés.** Sur le "
        f"bitcoin, le fonds retenu (frais de {viz.fr(ib1t['frais'], '%', 2)}) "
        f"a fait {viz.fr(ib1t['ecart_moyen'], 'point', 2)} par an de mieux que "
        f"BTCE ({viz.fr(btce['frais'], '%', 2)}), que l'ancien univers avait "
        f"retenu : l'écart de frais se retrouve presque entièrement dans les "
        f"performances. Même chose pour l'or : Xetra-Gold, sans frais "
        f"annoncés, a fait {viz.fr(gld['ecart_moyen'], 'point', 2)} par an de "
        f"mieux que le fonds de référence, qui prélève "
        f"{viz.fr(cl['or']['candidats']['PPFB.DE']['frais'], '%', 2)}.",
        icon=":material/lightbulb:",
    )


def _pedagogie() -> None:
    pedago.explique(
        "Pourquoi un filtre « Screened » ne suffit pas",
        "Les fournisseurs d'indices proposent plusieurs niveaux de filtre. "
        "Le plus léger, « Screened », retire les armes controversées (mines, "
        "armes à sous-munitions), les armes nucléaires, les armes civiles, "
        "le tabac et le charbon. Il ne retire <strong>pas</strong> les "
        "fabricants d'armement conventionnel : avions de combat, missiles, "
        "blindés.",
        "Or, pour les actions européennes en direct, on a exclu tout le "
        "secteur aéronautique et défense. Un fonds américain « Screened » "
        "pourrait contenir des fabricants de blindés ou de munitions : la "
        "règle ne serait plus la même selon qu'on investit en direct ou par un fonds. "
        "On retient donc des indices « SRI », qui excluent l'armement "
        "conventionnel dès 5 % du chiffre d'affaires.",
        "Ces indices sont plus stricts que le mandat : ils écartent aussi le "
        "pétrole et le gaz, le nucléaire civil, et ne gardent que la moitié "
        "des entreprises les mieux notées de chaque secteur. C'est le prix "
        "d'une règle cohérente, et il se mesure : c'est l'écart au marché "
        "affiché dans le détail.",
        source="Méthodologies MSCI ESG Screened (déc. 2024), MSCI SRI "
               "(janv. 2024), MSCI Low Carbon SRI Selection (déc. 2024), "
               "lues le 18/09/2026 · core/fonds.py",
    )
    pedago.explique(
        "La liquidité d'un ETF n'est pas celle qu'on voit en bourse",
        "Les montants échangés chaque jour en bourse sont souvent faibles : "
        "un million d'euros pour le fonds américain retenu. Cela ne veut pas "
        "dire qu'on ne peut pas en acheter dix. Pour un ordre important, on "
        "passe par un teneur de marché, qui crée de nouvelles parts du fonds "
        "en achetant les actions sous-jacentes. La vraie liquidité d'un ETF "
        "est celle de ce qu'il contient : les actions américaines comptent "
        "parmi les plus échangées au monde.",
        "C'est pour cela que la liquidité n'est ici qu'une information, et "
        "que la taille du fonds compte davantage : un fonds trop petit peut "
        "être fermé par son gérant, et on serait alors forcé de vendre.",
    )
    pedago.explique(
        "Or, bitcoin : des titres de créance, pas des fonds",
        "Xetra-Gold et le produit bitcoin retenu ne sont pas des fonds au "
        "sens réglementaire : ce sont des titres de créance (ETC ou ETP) "
        "émis par une société, garantis par de l'or ou des bitcoins "
        "réellement détenus. Pour Xetra-Gold, le porteur peut même demander "
        "la livraison physique de l'or.",
        "La différence tient au cas où l'émetteur ferait faillite : dans un "
        "fonds, les actifs sont séparés et appartiennent aux porteurs ; "
        "pour un titre de créance, c'est la garantie qui protège. Le risque "
        "est faible avec une garantie physique, mais il existe, et c'est une "
        "raison de plus de préférer les gros émetteurs.",
    )
    pedago.explique(
        "Corrigé : neuf fonds mal identifiés dans l'univers de départ",
        "En revérifiant chaque fonds de l'univers hérité de la version "
        "précédente (48 fonds), on a trouvé neuf libellés faux. Les deux plus "
        "graves concernaient des fonds principaux : ce qui était noté "
        "« obligations émergentes » était un fonds d'actions américaines, et "
        "ce qui était noté « haut rendement » un fonds d'emprunts d'État.",
        "Les prix, eux, étaient bien ceux des vrais produits : c'est le nom "
        "qu'on leur avait donné qui était faux. C'est pour cela qu'aucun "
        "contrôle ne l'a repéré. Désormais, chaque fonds est vérifié à chaque "
        "mise à jour sur deux sources : son nom chez Yahoo et, via son code "
        "ISIN, son nom chez justETF. Si les deux ne concordent pas, le fonds "
        "est rejeté. " + " ".join(
            f"<strong>{t}</strong> : noté « {avant} », en réalité "
            f"« {vrai} »." for t, avant, vrai in fonds.CORRECTIONS),
        source="Liste complète et classes corrigées : data/universe.csv, "
               "colonne « correction » · core/fonds.py",
    )
