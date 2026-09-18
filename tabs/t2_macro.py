"""
Étape 2 — Macro top-down.

Construit bloc par bloc. Premier bloc (2026-09-18) : ce que rapportent
aujourd'hui les placements de taux en euros, lus sur la photo datée
data/taux_marche.json.

L'inflation de 4 % reste celle de l'énoncé et n'est PAS confrontée à
l'inflation anticipée par le marché : décision d'Allan du 2026-09-18, c'est
une donnée du problème. On s'en sert uniquement comme seuil à battre.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core import macro, pedago, taux, viz
from core.ips import INFLATION_TARGET

SEUIL = INFLATION_TARGET * 100          # en points de pourcentage


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


def _ecart(v: float) -> str:
    return ("+" if v >= 0 else "−") + viz.fr(abs(v), "pt", 2)


def render() -> None:
    pedago.chaine(2)
    pedago.etape(
        2, "Macro top-down",
        "L'analyse descendante : on part de ce que le marché paie aujourd'hui "
        "et de l'état de l'économie, pour en déduire ce qu'on peut attendre "
        "de chaque grande classe d'actifs. La sortie de cet onglet est un jeu "
        "de rendements espérés, qui devient l'entrée de l'étape 4.",
    )
    _bloc_taux()
    _bloc_etranger()
    _bloc_cycle()
    _suite()


# --------------------------------------------------------------------------
# Bloc 1 — ce que rapportent aujourd'hui les placements de taux
# --------------------------------------------------------------------------

def _bloc_taux() -> None:
    photo = taux.charger()
    p = photo["points"]
    c = photo["courbes"]

    st.markdown("#### Ce que rapportent aujourd'hui les placements en euros")
    st.markdown(
        "Avant de parler de cycle économique, on regarde ce que le marché "
        "paie. Pour une obligation, c'est presque tout ce qu'il faut savoir : "
        "son taux à l'achat est ce qu'elle rapportera si on la garde. On "
        "compare chaque placement au seuil de l'énoncé, une inflation de "
        f"**{viz.fr(SEUIL, '%', 0)}**."
    )

    court_min, court_max = c["toutes"][0], c["toutes"][2]
    indexee_nominal = p["indexees_reel"]["valeur"] + SEUIL
    lignes = [
        ("Monétaire", _pct(p["estr"]["valeur"]),
         p["estr"]["valeur"] - SEUIL,
         "Aucun risque, mais le pouvoir d'achat recule chaque année. C'est "
         "là que resteront les 10 M€ à décaisser : cette perte est le prix "
         "de leur disponibilité."),
        ("Emprunts d'État à 1-3 ans",
         f"{_pct(court_min)} à {_pct(court_max)}",
         (court_min + court_max) / 2 - SEUIL,
         "Un peu mieux que le monétaire, toujours sous l'inflation."),
        ("Emprunts d'État, ensemble du marché",
         _pct(p["etat_euro"]["valeur"]),
         p["etat_euro"]["valeur"] - SEUIL,
         "Le placement de référence n'atteint pas le seuil. Prêter aux États "
         "de la zone euro ne préserve pas le patrimoine dans le monde de "
         "l'énoncé."),
        ("Crédit d'entreprises bien notées",
         _pct(p["credit_ig_euro"]["valeur"]),
         p["credit_ig_euro"]["valeur"] - SEUIL,
         "À peine au-dessus du seuil, en échange d'un risque de défaut. La "
         "marge est trop mince pour porter l'objectif à elle seule."),
        ("Obligations indexées sur l'inflation",
         f"{_pct(p['indexees_reel']['valeur'])} + inflation "
         f"≈ {_pct(indexee_nominal)}",
         p["indexees_reel"]["valeur"],
         "La seule obligation qui suit l'inflation, par construction : elle "
         "verse un taux réel, en plus de l'inflation effectivement "
         "constatée. Tant que son taux réel reste positif, elle bat "
         "le seuil quelle que soit l'inflation."),
    ]
    tableau = pd.DataFrame(
        [(nom, rdt, _ecart(reel), sens) for nom, rdt, reel, sens in lignes],
        columns=["Placement", "Rendement aujourd'hui",
                 f"Après {viz.fr(SEUIL, '%', 0)} d'inflation",
                 "Ce que cela signifie"],
    )
    st.table(tableau.set_index("Placement"))

    st.info(
        "**Aucune obligation à taux fixe ne protège contre 4 % d'inflation.** "
        "Leur rendement est fixé le jour de l'achat, et il est aujourd'hui "
        "inférieur ou à peine égal au seuil. Seules les obligations indexées "
        "le dépassent de façon certaine. Pour le reste de l'objectif, il "
        "faudra des actifs dont le rendement n'est pas fixé d'avance : "
        "actions, actifs réels. C'est ce que les blocs suivants examinent.",
        icon=":material/lightbulb:",
    )

    _courbe(photo)

    pedago.explique(
        "Pourquoi le taux à l'achat dit ce que rapportera une obligation",
        "Une obligation est un prêt : on avance une somme, l'emprunteur verse "
        "des intérêts puis rembourse à une date fixée. Si on la garde "
        "jusqu'au bout et que l'emprunteur ne fait pas défaut, on connaît "
        "son rendement dès le premier jour. C'est le taux à l'achat, appelé "
        "rendement à l'échéance.",
        "Pour un fonds qui détient des centaines d'obligations et les "
        "renouvelle en permanence, c'est un peu moins exact. Mais sur dix "
        "ans, le taux moyen du portefeuille au départ reste la meilleure "
        "estimation de ce qu'il rapportera. Aucune prévision économique "
        "n'est nécessaire, ce qui en fait les chiffres les plus solides de "
        "tout l'exercice.",
        "C'est aussi ce qui les rend vulnérables à l'inflation. Le montant "
        "versé est fixé une fois pour toutes. Si les prix montent de 4 % par "
        f"an, un placement qui rapporte {_pct(p['etat_euro']['valeur'])} fait "
        "perdre du pouvoir d'achat chaque année, sans que rien ne puisse le "
        "corriger.",
    )
    pedago.explique(
        "Taux nominal, taux réel : ce que change une obligation indexée",
        "Le taux nominal est ce qu'un placement rapporte en euros. Le taux "
        "réel est ce qu'il rapporte une fois l'inflation déduite, c'est-à-dire "
        "en pouvoir d'achat. Pour le client, seul le second compte.",
        "Une obligation indexée ne promet pas un taux nominal mais un taux "
        "réel : son capital est réévalué chaque année de l'inflation "
        f"constatée. Avec un taux réel de "
        f"{_pct(p['indexees_reel']['valeur'])}, elle rapporte "
        f"{_pct(p['indexees_reel']['valeur'] + 2)} si l'inflation est de 2 %, "
        f"et {_pct(indexee_nominal)} si elle est de 4 %. Elle ne gagne pas "
        "davantage quand l'inflation monte : elle garantit simplement de ne "
        "pas perdre face à elle.",
        "Sa contrepartie : si l'inflation reste basse, elle rapporte moins "
        "qu'une obligation classique. C'est le prix de l'assurance.",
    )

    pedago.explique(
        "D'où viennent ces chiffres",
        f"<strong>Monétaire</strong> : €STR, taux au jour le jour publié par la BCE, au "
        f"{taux.date_fr(p['estr']['date'])}. Le taux de dépôt de la BCE est "
        f"de {_pct(p['depot_bce']['valeur'])}.",
        f"<strong>Emprunts d'État</strong> : courbe des taux de la BCE au "
        f"{taux.date_fr(c['date'])} pour les maturités, et rendement moyen de "
        f"l'ETF iShares Core € Govt Bond pour l'ensemble du marché "
        f"(durée moyenne de {viz.fr(p['etat_euro']['duration'], 'ans', 1)}).",
        f"<strong>Crédit</strong> : rendement moyen de l'ETF iShares Core € Corp Bond au "
        f"{taux.date_fr(p['credit_ig_euro']['date'])} (durée moyenne de "
        f"{viz.fr(p['credit_ig_euro']['duration'], 'ans', 1)}).",
        f"<strong>Obligations indexées</strong> : taux réel publié dans la fiche mensuelle "
        f"de l'ETF iShares € Inflation Linked Govt Bond, au "
        f"{taux.date_fr(p['indexees_reel']['date'])}. C'est le chiffre le "
        "plus ancien du tableau, parce que ce taux réel n'est publié qu'une "
        "fois par mois. La page web du même fonds affiche un rendement plus "
        f"récent ({_pct(p['indexees_nominal']['valeur'])} au "
        f"{taux.date_fr(p['indexees_nominal']['date'])}), mais c'est un "
        "équivalent nominal qui inclut une hypothèse d'inflation propre à "
        "iShares : il ne faut pas le lire comme un taux réel.",
        "Ces chiffres sont une photo datée, pas un flux en direct. Chaque "
        "ligne affiche sa propre date, parce que les sources ne publient pas "
        "au même rythme.",
        source=f"data/taux_marche.json · relevé du "
               f"{taux.date_fr(photo['releve'])} · scripts/fetch_taux.py",
    )


def _courbe(photo: dict) -> None:
    df = taux.courbe(photo)
    x = df["Maturité (ans)"]
    fig = go.Figure()
    for nom, couleur in [("Tous États de la zone euro", viz.CATEGORICAL[0]),
                         ("États notés AAA", viz.CATEGORICAL[1])]:
        fig.add_trace(go.Scatter(
            x=x, y=df[nom], name=nom, mode="lines+markers",
            line={"color": couleur, "width": 2},
            marker={"size": 8, "color": couleur,
                    "line": {"color": viz.SURFACE, "width": 2}},
            hovertemplate=f"{nom}<br>%{{x}} ans : %{{y:.2f}} %<extra></extra>",
        ))
    fig.add_hline(y=SEUIL, line={"color": viz.INK_2, "width": 1.5,
                                 "dash": "dash"},
                  annotation={"text": f"Seuil de l'énoncé : "
                                      f"{viz.fr(SEUIL, '%', 0)}",
                              "font": {"color": viz.INK_2, "size": 12}},
                  annotation_position="top left")
    fig.update_layout(**viz.layout(
        "Taux des emprunts d'État de la zone euro selon leur durée",
        height=400, hovermode="x unified",
        xaxis={"title": "Durée jusqu'au remboursement (ans)",
               "gridcolor": viz.GRID, "tickvals": list(x)},
        yaxis={"title": "Taux annuel (%)", "gridcolor": viz.GRID,
               "ticksuffix": " %", "range": [2.5, 4.8]},
    ))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Courbe de la BCE au {taux.date_fr(photo['courbes']['date'])}. Plus "
        "on prête longtemps, plus le taux est élevé. Seules les durées "
        "au-delà de 15 ans dépassent 4 %, et uniquement pour les États les "
        "moins bien notés : il faudrait immobiliser l'argent quinze ans ou "
        "plus, en acceptant un risque accru, pour égaler l'inflation de "
        "l'énoncé."
    )
    with st.expander("Voir les chiffres de la courbe"):
        st.table(df.set_index("Maturité (ans)").apply(lambda col: col.map(_pct)))


# --------------------------------------------------------------------------
# Bloc 2 — les placements de taux hors zone euro, ramenés en euros
# --------------------------------------------------------------------------

def _bloc_etranger() -> None:
    photo = taux.charger()
    p = photo["points"]
    fx = p["change_12m"]
    cout = p["us_3m"]["valeur"] - p["estr"]["valeur"]     # coût de couverture

    st.markdown("#### Ailleurs, les taux sont plus élevés : est-ce une "
                "meilleure affaire ?")
    st.markdown(
        f"Le Trésor américain paie {_pct(p['us_10a']['valeur'])} à dix ans, "
        f"contre {_pct(p['etat_euro']['valeur'])} pour les États de la zone "
        "euro. Mais un client qui vit en euros ne touche pas des dollars : il "
        "faut ramener ces rendements en euros. Il y a deux façons de le "
        "faire, et aucune n'est gratuite."
    )

    lignes = [
        ("Trésor américain à 10 ans", p["us_10a"]["valeur"], True,
         "L'avantage sur les emprunts européens disparaît presque "
         "entièrement une fois le change couvert."),
        ("Crédit d'entreprises américaines bien notées",
         p["credit_ig_us"]["valeur"], True,
         "Couvert, il rapporte à peu près autant que son équivalent "
         "européen. Aucun gain à aller le chercher."),
        ("Dette d'entreprises émergentes",
         p["em_corp"]["valeur"], True,
         "Un peu au-dessus du seuil, pour un risque de défaut et un risque "
         "politique plus élevés."),
        ("Haut rendement américain", p["hy_us"]["valeur"], True,
         "Au-dessus du seuil sur le papier. Mais ce rendement suppose "
         "qu'aucune entreprise ne fasse défaut."),
        ("Haut rendement européen", p["hy_euro"]["valeur"], False,
         "Déjà en euros, pas de couverture à payer. Même réserve : c'est un "
         "rendement avant défauts."),
    ]
    tableau = pd.DataFrame(
        [(nom, _pct(r), _pct(r - cout) if couvert else "déjà en euros",
          _ecart((r - cout if couvert else r) - SEUIL), sens)
         for nom, r, couvert, sens in lignes],
        columns=["Placement", "Rendement affiché", "Ramené en euros "
                 "(change couvert)", f"Après {viz.fr(SEUIL, '%', 0)} "
                 "d'inflation", "Ce que cela signifie"],
    )
    st.table(tableau.set_index("Placement"))
    st.caption(
        f"Couvrir le change coûte aujourd'hui environ {_pct(cout)} par an : "
        f"c'est l'écart entre les taux courts américains "
        f"({_pct(p['us_3m']['valeur'])}) et européens "
        f"({_pct(p['estr']['valeur'])}). Ordre de grandeur, qui varie avec "
        "la durée de la couverture."
    )

    st.info(
        "**Le supplément de rendement américain est, pour l'essentiel, le "
        "prix du risque de change.** Si on le couvre, il disparaît. Si on "
        "ne le couvre pas, on le garde, mais en échange d'un pari sur le "
        "dollar bien plus gros que le gain. Les seuls placements de taux qui "
        "dépassent nettement le seuil sont ceux à haut rendement, et leur "
        "rendement affiché n'est pas celui qu'on touchera.",
        icon=":material/lightbulb:",
    )

    c = st.columns(3)
    c[0].metric("Variation typique du dollar en un an",
                viz.fr(fx["mediane"], "%", 1), "valeur médiane",
                delta_color="off")
    c[1].metric("Années où elle dépasse 10 %",
                f"{fx['part_plus_10']} %", "environ une sur trois",
                delta_color="off")
    c[2].metric("Plus forte variation observée", f"{fx['pire']} %",
                f"en douze mois, depuis {fx['debut']}", delta_color="off")

    _synthese(photo, cout)

    pedago.explique(
        "Comment on ramène un rendement étranger en euros",
        "<strong>Sans couverture</strong>, on achète des dollars, on place "
        "ces dollars, et on les revend dans dix ans. On touche le taux "
        "américain entier, mais le résultat en euros dépend de ce que vaudra "
        "le dollar ce jour-là. Mesuré depuis la création de l'euro, le "
        f"dollar varie en un an de {viz.fr(fx['mediane'], '%', 1)} en "
        f"valeur médiane, et de plus de 10 % une année sur trois. Un gain "
        f"de rendement d'un ou deux points par an pèse peu face à cela : "
        "c'est un pari sur une devise, pas un placement obligataire.",
        "<strong>Avec couverture</strong>, on s'engage dès aujourd'hui à "
        "revendre ses dollars à un prix fixé d'avance. Ce prix n'est pas "
        "le cours du jour : il intègre l'écart entre les taux courts des "
        "deux zones. Le mécanisme est automatique. Celui qui couvre rend "
        "donc à peu près l'écart de taux courts, et c'est pour cela que le "
        "supplément de rendement américain s'évapore.",
        "La règle qu'on en tire est simple : dans la partie obligataire, "
        "dont le rôle est de stabiliser le portefeuille, on couvre le "
        "change. Une obligation doit rester une obligation, pas devenir un "
        "pari sur le dollar.",
    )
    pedago.explique(
        "Rendement affiché et rendement réellement touché : le haut rendement",
        "Le rendement d'une obligation à haut rendement suppose que "
        "l'entreprise paie tous ses coupons et rembourse à l'échéance. Or "
        "une partie de ces entreprises fera défaut, et on ne récupère alors "
        "qu'une fraction de sa mise. Le rendement affiché est donc un "
        "maximum, pas une espérance.",
        "Une grande partie de l'écart entre le haut rendement et les "
        "emprunts d'État sert précisément à payer ces défauts. Ce qui reste "
        "une fois les pertes déduites est bien plus mince que ne le laisse "
        "croire le chiffre affiché. Les pertes attendues seront estimées à "
        "l'étape 4, au moment de construire l'allocation. D'ici là, ces "
        "rendements doivent se lire comme des plafonds.",
        "Pour les obligations bien notées, la question se pose à peine : "
        "les défauts y sont rares, et l'écart entre rendement affiché et "
        "rendement touché est faible.",
    )
    pedago.explique(
        "D'où viennent ces chiffres",
        f"<strong>Taux américains</strong> : Trésor américain, via FRED, au "
        f"{taux.date_fr(p['us_10a']['date'])}.",
        "<strong>Crédit, haut rendement et dette émergente</strong> : "
        "rendements effectifs des indices ICE BofA, via FRED, au "
        f"{taux.date_fr(p['hy_us']['date'])}. On utilise le rendement "
        "complet de chaque indice, pas seulement son écart avec les emprunts "
        "d'État, pour comparer des choses comparables.",
        "<strong>Coût de la couverture</strong> : écart entre le taux "
        "américain à 3 mois et le €STR. C'est une approximation : le coût "
        "réel dépend de la durée de couverture et des conditions de marché.",
        f"<strong>Variations du dollar</strong> : taux de change euro-dollar "
        f"de la Réserve fédérale, en fin de mois depuis {fx['debut']}, "
        "mesuré sur toutes les périodes de douze mois glissants.",
        source=f"data/taux_marche.json · relevé du "
               f"{taux.date_fr(photo['releve'])} · scripts/fetch_taux.py",
    )


def _synthese(photo: dict, cout: float) -> None:
    """Tous les placements de taux, ramenés en euros, face au seuil."""
    p = photo["points"]
    c = photo["courbes"]
    rows = [
        ("Monétaire", p["estr"]["valeur"]),
        ("États euro 1-3 ans", (c["toutes"][0] + c["toutes"][2]) / 2),
        ("États euro, ensemble", p["etat_euro"]["valeur"]),
        ("Trésor américain 10 ans, couvert", p["us_10a"]["valeur"] - cout),
        ("Crédit américain bien noté, couvert",
         p["credit_ig_us"]["valeur"] - cout),
        ("Crédit euro bien noté", p["credit_ig_euro"]["valeur"]),
        ("Dette émergente, couverte", p["em_corp"]["valeur"] - cout),
        ("Obligations indexées (à 4 % d'inflation)",
         p["indexees_reel"]["valeur"] + SEUIL),
        ("Haut rendement américain, couvert *", p["hy_us"]["valeur"] - cout),
        ("Haut rendement euro *", p["hy_euro"]["valeur"]),
    ]
    df = pd.DataFrame(rows, columns=["Placement", "Rendement"]).sort_values(
        "Rendement")
    fig = go.Figure(go.Bar(
        x=df["Rendement"], y=df["Placement"], orientation="h",
        marker={"color": viz.CATEGORICAL[0], "cornerradius": 4},
        text=[_pct(v) for v in df["Rendement"]], textposition="outside",
        textfont={"color": viz.INK_2},
        hovertemplate="%{y}<br>%{x:.2f} %<extra></extra>",
    ))
    fig.add_vline(x=SEUIL, line={"color": viz.INK_2, "width": 1.5,
                                 "dash": "dash"},
                  annotation={"text": f"Seuil : {viz.fr(SEUIL, '%', 0)}",
                              "font": {"color": viz.INK_2, "size": 12}},
                  annotation_position="top")
    fig.update_layout(**viz.layout(
        "Tous les placements de taux, ramenés en euros", height=460,
        bargap=0.35, showlegend=False,
        xaxis={"title": "Rendement annuel en euros (%)", "ticksuffix": " %",
               "gridcolor": viz.GRID, "range": [0, 7.2]},
        yaxis={"gridcolor": "rgba(0,0,0,0)"},
    ))
    st.plotly_chart(fig, width="stretch")
    st.caption("* Rendement avant défauts : un plafond, pas ce qu'on "
               "touchera. Tout ce qui est à gauche de la ligne pointillée "
               "perd du pouvoir d'achat dans le monde de l'énoncé.")


# --------------------------------------------------------------------------
# Bloc 3 — où en est l'économie : la chaîne causale
# --------------------------------------------------------------------------

def _fleche(v: float, avant: float, seuil: float) -> str:
    if v - avant > seuil:
        return "↗"
    if avant - v > seuil:
        return "↘"
    return "→"


def _cellule(d: dict | None, unite: str = "%", dec: int = 1,
             seuil: float = 0.1) -> str:
    if d is None:
        return "—"
    v, a = d["valeur"], d["avant"]
    return (f"{viz.fr(v, unite, dec)} {_fleche(v, a, seuil)} "
            f"(avant : {viz.fr(a, unite, dec)})")


def _bloc_cycle() -> None:
    m = macro.charger()
    us, ea, em = m["etats_unis"], m["zone_euro"], m["emergents"]

    st.markdown("#### Où en est l'économie : de la croissance aux taux")
    st.markdown(
        "Les taux vus plus haut ne tombent pas du ciel. Ils sont le dernier "
        "maillon d'une chaîne : l'activité fait l'emploi, l'emploi et les "
        "matières premières font l'inflation, l'inflation décide de ce que "
        "fait la banque centrale, et la banque centrale entraîne les taux. "
        "Lire cette chaîne dit dans quel sens les taux vont plutôt aller, et "
        "donc quels placements le contexte favorise."
    )
    pedago.fil([
        ("Activité", "croissance, emploi"),
        ("Inflation", "totale et hors énergie"),
        ("Banque centrale", "monte ou baisse son taux"),
        ("Taux de marché", "à 2 ans et à 10 ans"),
        ("Prix des actifs", "obligations, actions"),
    ])

    lignes = [
        ("Croissance (PIB sur un an)", _cellule(us["pib"]),
         _cellule(ea["pib"])),
        ("Chômage", _cellule(us["chomage"]), _cellule(ea["chomage"])),
        ("Inflation totale", _cellule(us["inflation"]),
         _cellule(ea["inflation"])),
        ("Inflation hors énergie et alimentation",
         _cellule(us["inflation_sj"]), _cellule(ea["inflation_sj"])),
        ("Taux de la banque centrale", _cellule(us["banque_centrale"], dec=2),
         _cellule(ea["banque_centrale"], dec=2)),
        ("Taux à 2 ans", _cellule(us["taux_2a"], dec=2),
         _cellule(ea["taux_2a"], dec=2)),
        ("Taux à 10 ans", _cellule(us["taux_10a"], dec=2),
         _cellule(ea["taux_10a"], dec=2)),
    ]
    st.table(pd.DataFrame(lignes, columns=["Maillon", "États-Unis",
                                           "Zone euro"]).set_index("Maillon"))
    st.caption("« Avant » : six mois plus tôt, un an pour la croissance. "
               "Taux de la zone euro : BCE, États notés AAA. Dates exactes "
               "dans l'encadré des sources.")

    _graphique_inflation(us, ea)

    st.markdown(f"**Ce qu'on en lit, au {taux.date_fr(m['releve'])}**")
    st.markdown(
        f"**États-Unis.** L'activité tient : la croissance est de "
        f"{viz.fr(us['pib']['valeur'], '%', 1)} sur un an et le chômage "
        f"recule à {viz.fr(us['chomage']['valeur'], '%', 1)}. L'inflation "
        f"totale est passée de {viz.fr(us['inflation']['avant'], '%', 1)} à "
        f"{viz.fr(us['inflation']['valeur'], '%', 1)} en six mois, mais "
        f"l'inflation hors énergie et alimentation est restée stable autour "
        f"de {viz.fr(us['inflation_sj']['valeur'], '%', 1)} : la hausse vient "
        f"de l'énergie et de l'alimentation. La Fed n'a pas bougé depuis "
        f"janvier ({_pct(us['banque_centrale']['valeur'])}). Le marché, lui, "
        f"anticipe qu'elle devra remonter ses taux : le taux à 2 ans est passé "
        f"de {_pct(us['taux_2a']['avant'])} à {_pct(us['taux_2a']['valeur'])}, "
        f"au-dessus du taux de la Fed, et le 10 ans a suivi."
    )
    st.markdown(
        f"**Zone euro.** La croissance est faible "
        f"({viz.fr(ea['pib']['valeur'], '%', 1)}) et le chômage stable "
        f"({viz.fr(ea['chomage']['valeur'], '%', 1)}). Même schéma "
        f"d'inflation : la totale est passée de "
        f"{viz.fr(ea['inflation']['avant'], '%', 1)} à "
        f"{viz.fr(ea['inflation']['valeur'], '%', 1)}, la sous-jacente est "
        f"stable à {viz.fr(ea['inflation_sj']['valeur'], '%', 1)}. Mais la "
        f"BCE, elle, a déjà agi : son taux est passé de "
        f"{_pct(ea['banque_centrale']['avant'])} à "
        f"{_pct(ea['banque_centrale']['valeur'])}. Le taux à 2 ans, à "
        f"{_pct(ea['taux_2a']['valeur'])}, indique que le marché attend "
        f"d'autres hausses."
    )
    cr, inf = em["croissance"], em["inflation"]
    ch, ind = em["avance"]["chine"], em["avance"]["inde"]
    st.markdown(
        f"**Émergents.** La croissance reste bien supérieure à celle des pays "
        f"développés : {viz.fr(cr['OEMDC']['2026'], '%', 1)} prévus par le "
        f"FMI pour 2026. Mais elle diverge : la Chine ralentit (indicateur "
        f"avancé à {viz.fr(ch['valeur'], '', 1)} et en baisse, inflation "
        f"proche de zéro) quand l'Inde accélère "
        f"({viz.fr(ind['valeur'], '', 1)} et en hausse). Parler « des "
        f"émergents » comme d'un bloc a peu de sens aujourd'hui."
    )
    _tableau_emergents(em)

    st.info(
        "**Le régime actuel : un choc d'inflation venu de l'énergie, et des "
        "banques centrales qui resserrent.** C'est le scénario que redoute le "
        "client. Pour un portefeuille, ce contexte pèse sur les obligations "
        "à taux fixe (quand les taux montent, leur prix baisse), favorise les "
        "obligations indexées et les actifs réels, et rend le monétaire plus "
        "rémunérateur. La question qui décidera de la suite : le choc va-t-il "
        "se diffuser au reste des prix ? Tant que l'inflation hors énergie "
        "reste stable, c'est un choc passager. Si elle se met à monter, "
        "l'inflation s'installe.",
        icon=":material/lightbulb:",
    )

    pedago.explique(
        "Comment se lit la chaîne, maillon par maillon",
        "<strong>L'activité.</strong> Quand l'économie croît, les entreprises "
        "embauchent, le chômage baisse et les salaires montent. La demande "
        "augmente, et avec elle la capacité des entreprises à relever leurs "
        "prix.",
        "<strong>L'inflation.</strong> Elle vient de deux sources : une "
        "demande trop forte pour ce que l'économie peut produire, ou un choc "
        "sur un prix de base, comme l'énergie. La première est durable, la "
        "seconde peut n'être que passagère.",
        "<strong>La banque centrale.</strong> Son mandat est de tenir "
        "l'inflation près de 2 %. Si l'inflation monte, elle relève son taux "
        "pour freiner le crédit et la demande. Si l'activité faiblit, elle "
        "le baisse.",
        "<strong>Les taux de marché.</strong> Le taux à 2 ans suit ce que le "
        "marché attend de la banque centrale sur deux ans. Le taux à 10 ans "
        "y ajoute l'inflation attendue à long terme et une prime pour le "
        "risque de prêter longtemps.",
        "<strong>Le prix des actifs.</strong> Quand les taux montent, le prix "
        "des obligations déjà émises baisse, parce que les nouvelles "
        "rapportent davantage. Les actions souffrent aussi, parce que leurs "
        "bénéfices futurs valent moins aujourd'hui.",
    )
    pedago.explique(
        "Inflation totale et inflation hors énergie : pourquoi on regarde "
        "les deux",
        "L'inflation totale mesure la hausse des prix de tout ce que "
        "consomment les ménages. L'inflation hors énergie et alimentation, "
        "dite sous-jacente, retire les prix les plus volatils. Elle montre "
        "la tendance de fond, celle qui dépend des salaires et de la "
        "demande.",
        "Quand la totale monte et que la sous-jacente ne bouge pas, comme "
        "aujourd'hui, la hausse vient d'un choc sur l'énergie ou "
        "l'alimentation. Un tel choc peut retomber aussi vite qu'il est "
        "venu. Il ne devient durable que s'il se diffuse : entreprises qui "
        "répercutent leurs coûts, salariés qui obtiennent des hausses de "
        "salaire. C'est la sous-jacente qui le signalera en premier.",
    )
    pedago.explique(
        "Ce que dit le taux à 2 ans",
        "Prêter à un État pour deux ans, c'est à peu près comme placer son "
        "argent au taux de la banque centrale pendant deux ans. Le taux à "
        "2 ans reflète donc ce que le marché pense que la banque centrale "
        "fera sur cette période.",
        "Quand il est nettement au-dessus du taux de la banque centrale, "
        "comme aujourd'hui aux États-Unis et en zone euro, le marché "
        "anticipe des hausses. Quand il est en dessous, il anticipe des "
        "baisses. C'est l'indicateur le plus direct des attentes du marché, "
        "et il se lit sans modèle.",
    )
    pedago.explique(
        "Ce que dit l'indicateur avancé de l'OCDE",
        "L'OCDE combine, pour chaque pays, des indicateurs qui changent de "
        "direction avant l'économie elle-même : commandes, confiance des "
        "entreprises, marchés financiers. Le résultat est ramené à une "
        "échelle où 100 correspond à la tendance de long terme.",
        "Au-dessus de 100 et en hausse : l'activité accélère. En dessous de "
        "100 et en baisse : elle ralentit. C'est un signal de direction "
        "pour les six à neuf prochains mois, pas une prévision chiffrée.",
    )
    pedago.explique(
        "D'où viennent ces chiffres",
        f"<strong>États-Unis</strong> : FRED (Réserve fédérale de "
        f"Saint-Louis). Croissance au "
        f"{taux.date_fr(us['pib']['date'])} (trimestre), inflation et "
        f"chômage au {taux.date_fr(us['inflation']['date'])} (mois), taux "
        f"au {taux.date_fr(us['taux_2a']['date'])}.",
        f"<strong>Zone euro</strong> : inflation via FRED (indices IPCH "
        f"d'Eurostat), au {taux.date_fr(ea['inflation']['date'])} ; chômage "
        f"BCE au {taux.date_fr(ea['chomage']['date'])} ; croissance "
        f"Eurostat au {taux.date_fr(ea['pib']['date'])} (trimestre) ; taux "
        f"BCE au {taux.date_fr(ea['taux_2a']['date'])}.",
        "<strong>Émergents</strong> : FMI, Perspectives de l'économie "
        "mondiale, pour la croissance et l'inflation. Les années 2026 et "
        "2027 sont des prévisions. L'inflation « ensemble des émergents » "
        "n'est pas affichée : elle est tirée vers le haut par quelques pays "
        "en très forte inflation (Turquie, Argentine, Iran) et ne dit rien "
        "de la situation typique. Indicateurs avancés : OCDE via FRED.",
        "Les séries d'inflation de la BCE et d'Eurostat interrogées "
        "directement s'arrêtent en décembre 2025, à la suite d'un changement "
        "de nomenclature. On passe donc par FRED, qui reprend les indices "
        "d'Eurostat jusqu'en août 2026.",
        source=f"data/macro.json · relevé du {taux.date_fr(m['releve'])} · "
               f"scripts/fetch_macro.py",
    )


def _graphique_inflation(us: dict, ea: dict) -> None:
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=("États-Unis", "Zone euro"),
                        horizontal_spacing=0.04)
    series = [("inflation", "Inflation totale", viz.CATEGORICAL[0]),
              ("sous_jacente", "Inflation hors énergie et alimentation",
               viz.CATEGORICAL[1]),
              ("taux", "Taux de la banque centrale", viz.CATEGORICAL[2])]
    for col, zone in [(1, us), (2, ea)]:
        h = zone["histo"]
        for cle, nom, couleur in series:
            fig.add_trace(go.Scatter(
                x=h["dates"], y=h[cle], name=nom, legendgroup=cle,
                showlegend=(col == 1), mode="lines",
                line={"color": couleur, "width": 2},
                hovertemplate=f"{nom} : %{{y:.1f}} %<extra></extra>",
            ), row=1, col=col)
        fig.add_hline(y=SEUIL, row=1, col=col,
                      line={"color": viz.INK_2, "width": 1, "dash": "dash"})
    fig.add_annotation(xref="x domain", yref="y", x=0.01, y=SEUIL,
                       text=f"Inflation de l'énoncé : "
                            f"{viz.fr(SEUIL, '%', 0)}",
                       showarrow=False, yshift=9, xanchor="left",
                       font={"color": viz.INK_2, "size": 11})
    fig.update_layout(**viz.layout(
        "Inflation et taux directeurs depuis 2021", height=420,
        hovermode="x unified",
        yaxis={"ticksuffix": " %", "gridcolor": viz.GRID},
    ))
    fig.update_xaxes(gridcolor=viz.GRID)
    fig.update_yaxes(gridcolor=viz.GRID, ticksuffix=" %")
    fig.update_annotations(font_color=viz.INK_2)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "En 2022, l'inflation a dépassé 8 % des deux côtés de l'Atlantique "
        "et les banques centrales ont relevé leurs taux avec retard. Elle "
        "est ensuite retombée vers 2 à 3 %. Depuis le début de 2026, "
        "l'inflation totale remonte alors que la sous-jacente reste stable : "
        "c'est la signature d'un choc sur l'énergie."
    )


def _tableau_emergents(em: dict) -> None:
    cr, inf, av = em["croissance"], em["inflation"], em["avance"]

    def signal(d):
        return f"{viz.fr(d['valeur'], '', 1)} {_fleche(d['valeur'], d['avant'], 0.1)}"

    lignes = [
        ("Ensemble des émergents", "OEMDC", "—"),
        ("Chine", "CHN", signal(av["chine"])),
        ("Inde", "IND", signal(av["inde"])),
        ("Brésil", "BRA", "—"),
    ]
    df = pd.DataFrame(
        [(nom, viz.fr(cr[z]["2025"], "%", 1), viz.fr(cr[z]["2026"], "%", 1),
          viz.fr(cr[z]["2027"], "%", 1),
          "—" if z == "OEMDC" else viz.fr(inf[z]["2026"], "%", 1), sig)
         for nom, z, sig in lignes],
        columns=["Zone", "Croissance 2025", "2026 (prévision)",
                 "2027 (prévision)", "Inflation 2026 (prévision)",
                 "Indicateur avancé OCDE"],
    )
    st.table(df.set_index("Zone"))


# --------------------------------------------------------------------------
# Suite de l'onglet
# --------------------------------------------------------------------------

def _suite() -> None:
    st.markdown("#### La suite de cet onglet")
    pedago.a_construire(
        2, "Macro top-down, blocs suivants",
        "**Les primes de crédit** : ce que les entreprises paient en plus "
        "des États, comparé à leur histoire, et ce que cela dit du risque "
        "perçu.",
        "**La dynamique des marchés actions** sur plusieurs horizons, zone "
        "par zone et secteur par secteur.",
        "**Les rendements espérés par classe d'actifs**, construits sur ces "
        "observations : c'est la sortie de l'onglet.",
    )
