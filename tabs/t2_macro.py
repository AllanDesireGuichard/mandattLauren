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

from core import pedago, taux, viz
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
# Suite de l'onglet
# --------------------------------------------------------------------------

def _suite() -> None:
    st.markdown("#### La suite de cet onglet")
    pedago.a_construire(
        2, "Macro top-down, blocs suivants",
        "**Les taux hors zone euro** : Trésor américain, crédit américain, "
        "dette émergente, et ce qu'ils rapportent une fois le risque de "
        "change couvert en euros.",
        "**La chaîne causale**, maillon par maillon, pour les États-Unis, la "
        "zone euro et les émergents : croissance → inflation → politique "
        "monétaire → taux → prime de risque.",
        "**Les indicateurs d'activité** : PIB, enquêtes auprès des "
        "entreprises, confiance des ménages, emploi.",
        "**Les primes de crédit** : ce que les entreprises paient en plus "
        "des États, et ce que cela dit du risque perçu.",
        "**La dynamique des marchés actions** sur plusieurs horizons, zone "
        "par zone et secteur par secteur.",
        "**Le régime économique** actuel, tenu volontairement simple et "
        "lisible.",
        "**Les rendements espérés par classe d'actifs**, construits sur ces "
        "observations : c'est la sortie de l'onglet.",
    )
