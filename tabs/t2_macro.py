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

from core import credit, macro, marches, pedago, rendements, taux, viz
from core.ips import INFLATION_TARGET

SEUIL = INFLATION_TARGET * 100          # en points de pourcentage


def _pct(v: float) -> str:
    return viz.fr(v, "%", 2)


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
    _bloc_credit()
    _bloc_marches()
    _bloc_rendements()


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
    st.markdown(
        f"- **Monétaire** : {_pct(p['estr']['valeur'])}. Aucun risque, mais "
        f"le pouvoir d'achat recule chaque année.\n"
        f"- **Emprunts d'État** : {_pct(court_min)} à {_pct(court_max)} à "
        f"1-3 ans, {_pct(p['etat_euro']['valeur'])} pour l'ensemble du "
        f"marché. Sous le seuil.\n"
        f"- **Crédit bien noté** : {_pct(p['credit_ig_euro']['valeur'])}. À "
        f"peine au-dessus, en échange d'un risque de défaut.\n"
        f"- **Obligations indexées** : {_pct(p['indexees_reel']['valeur'])} "
        f"+ inflation, soit ≈ {_pct(indexee_nominal)}. Les seules qui "
        f"suivent l'inflation par construction."
    )

    st.info(
        "**Aucune obligation à taux fixe ne protège contre 4 % d'inflation.** "
        "Seules les indexées dépassent le seuil de façon certaine. Pour le "
        "reste, il faudra des actifs dont le rendement n'est pas fixé "
        "d'avance : actions, actifs réels.",
        icon=":material/lightbulb:",
    )

    _courbe(photo)

    pedago.explique(
        "Pourquoi le taux à l'achat dit ce que rapportera une obligation",
        "Une obligation est un prêt : si on la garde jusqu'au bout et que "
        "l'emprunteur ne fait pas défaut, on connaît son rendement dès le "
        "premier jour. Pour un fonds, c'est un peu moins exact, mais sur dix "
        "ans le taux de départ reste la meilleure estimation, sans aucune "
        "prévision économique : ce sont les chiffres les plus solides de "
        "l'exercice.",
        "Le revers : le montant versé est fixé une fois pour toutes. Une "
        "obligation <strong>indexée</strong> promet au contraire un taux "
        "<strong>réel</strong> : son capital est réévalué de l'inflation "
        f"constatée. À {_pct(p['indexees_reel']['valeur'])} de taux réel, "
        f"elle rapporte {_pct(p['indexees_reel']['valeur'] + 2)} si "
        f"l'inflation est de 2 %, {_pct(indexee_nominal)} si elle est de "
        "4 %. Si l'inflation reste basse, elle rapporte moins qu'une "
        "obligation classique : c'est le prix de l'assurance.",
        source=f"€STR et courbe BCE au {taux.date_fr(c['date'])} · "
               f"fiches iShares (Core € Govt, Core € Corp, € Inflation Linked, "
               f"taux réel au {taux.date_fr(p['indexees_reel']['date'])}) · "
               f"data/taux_marche.json, relevé du "
               f"{taux.date_fr(photo['releve'])}",
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
        f"Courbe de la BCE au {taux.date_fr(photo['courbes']['date'])}. "
        "Seules les durées au-delà de 15 ans, et pour les États les moins "
        "bien notés, dépassent 4 %."
    )


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
        f"contre {_pct(p['etat_euro']['valeur'])} en zone euro. Mais un "
        f"client qui vit en euros doit ramener ces rendements en euros. "
        f"**Couvrir le change coûte environ {_pct(cout)} par an** (l'écart "
        f"entre taux courts américains et européens) : une fois couvert, le "
        f"Trésor américain ne rapporte plus que "
        f"{_pct(p['us_10a']['valeur'] - cout)}."
    )
    _synthese(photo, cout)

    c = st.columns(3)
    c[0].metric("Variation typique du dollar en un an",
                viz.fr(fx["mediane"], "%", 1), "valeur médiane",
                delta_color="off")
    c[1].metric("Années où elle dépasse 10 %",
                f"{fx['part_plus_10']} %", "environ une sur trois",
                delta_color="off")
    c[2].metric("Plus forte variation observée", f"{fx['pire']} %",
                f"en douze mois, depuis {fx['debut']}", delta_color="off")

    st.info(
        "**Le supplément de rendement américain est le prix du risque de "
        "change.** Couvert, il disparaît ; non couvert, c'est un pari sur le "
        "dollar bien plus gros que le gain. Seul le haut rendement dépasse "
        "nettement le seuil, et son rendement affiché n'est pas celui qu'on "
        "touchera (il suppose zéro défaut).",
        icon=":material/lightbulb:",
    )

    pedago.explique(
        "Couvrir le change, et pourquoi le gain s'évapore",
        "Couvrir, c'est s'engager dès aujourd'hui à revendre ses dollars à "
        "un prix fixé d'avance. Ce prix intègre mécaniquement l'écart entre "
        "les taux courts des deux zones : celui qui couvre rend donc à peu "
        "près cet écart. Règle retenue : dans la partie obligataire, dont le "
        "rôle est de stabiliser, on couvre le change.",
        source=f"FRED (Trésor américain, indices ICE BofA) au "
               f"{taux.date_fr(p['us_10a']['date'])} · euro-dollar de la "
               f"Fed depuis {fx['debut']} · data/taux_marche.json",
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
    ch, ind = em["avance"]["chine"], em["avance"]["inde"]
    st.markdown(
        f"- **États-Unis** : l'activité tient (chômage "
        f"{viz.fr(us['chomage']['valeur'], '%', 1)}). L'inflation totale "
        f"passe de {viz.fr(us['inflation']['avant'], '%', 1)} à "
        f"{viz.fr(us['inflation']['valeur'], '%', 1)}, la sous-jacente reste "
        f"à {viz.fr(us['inflation_sj']['valeur'], '%', 1)} : la hausse vient "
        f"de l'énergie. La Fed n'a pas bougé, mais le taux à 2 ans "
        f"({_pct(us['taux_2a']['valeur'])}) annonce des hausses.\n"
        f"- **Zone euro** : croissance faible "
        f"({viz.fr(ea['pib']['valeur'], '%', 1)}), même schéma d'inflation "
        f"({viz.fr(ea['inflation']['valeur'], '%', 1)}, sous-jacente "
        f"{viz.fr(ea['inflation_sj']['valeur'], '%', 1)}). La BCE a déjà "
        f"monté son taux à {_pct(ea['banque_centrale']['valeur'])}, et le "
        f"marché en attend d'autres.\n"
        f"- **Émergents** : {viz.fr(em['croissance']['OEMDC']['2026'], '%', 1)} "
        f"de croissance prévue en 2026, mais la Chine ralentit (indicateur "
        f"avancé {viz.fr(ch['valeur'], '', 1)}) quand l'Inde accélère "
        f"({viz.fr(ind['valeur'], '', 1)}). Ils se regardent pays par pays."
    )

    st.info(
        "**Le régime actuel : un choc d'inflation venu de l'énergie, et des "
        "banques centrales qui resserrent.** C'est le scénario que redoute le "
        "client : il pèse sur les obligations à taux fixe et favorise les "
        "indexées et les actifs réels. À surveiller : si l'inflation hors "
        "énergie se met à monter, le choc s'installe.",
        icon=":material/lightbulb:",
    )

    pedago.explique(
        "Comment se lit la chaîne, et les trois indicateurs clés",
        "Quand l'économie croît, le chômage baisse et les prix montent ; la "
        "banque centrale relève alors son taux pour tenir l'inflation près "
        "de 2 %, et les taux de marché suivent. Quand les taux montent, "
        "obligations et actions baissent.",
        "<strong>L'inflation hors énergie et alimentation</strong> montre la "
        "tendance de fond : si la totale monte et qu'elle ne bouge pas, c'est "
        "un choc qui peut retomber. <strong>Le taux à 2 ans</strong> reflète "
        "ce que le marché attend de la banque centrale : au-dessus de son "
        "taux, il anticipe des hausses. <strong>L'indicateur avancé de "
        "l'OCDE</strong> : au-dessus de 100 et en hausse, l'activité "
        "accélère sur les six à neuf prochains mois.",
        source=f"FRED, BCE, Eurostat, FMI (Perspectives de l'économie "
               f"mondiale), OCDE · data/macro.json, relevé du "
               f"{taux.date_fr(m['releve'])} · scripts/fetch_macro.py",
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


# --------------------------------------------------------------------------
# Bloc 4 — les primes de crédit, comparées à leur histoire
# --------------------------------------------------------------------------

def _bloc_credit() -> None:
    c = credit.charger()
    s = c["series"]
    lien = c["lien_us_europe"]
    baa, hy = s["BAA10Y"], s["BAMLH0A0HYM2"]
    photo = taux.charger()["points"]
    ig_eur = photo["credit_ig_euro"]

    st.markdown("#### Le crédit est-il bien payé ?")
    st.markdown(
        "Une entreprise emprunte plus cher qu'un État, parce qu'elle peut "
        "faire défaut : l'écart s'appelle la **prime de crédit**. Faible "
        "quand tout va bien, très élevée en crise. La comparer à son histoire "
        "dit si l'on est bien payé pour prêter aux entreprises."
    )

    _graphique_credit()

    st.info(
        f"**Le crédit n'a presque jamais été aussi mal payé.** Sur quarante "
        f"ans, la prime des entreprises moyennement notées n'a été plus "
        f"basse qu'aujourd'hui que {baa['rang']} % du temps ; celle du haut "
        f"rendement américain, {hy['rang']} % du temps depuis 2010. Peu à "
        f"gagner, beaucoup à perdre : si la prime remonte d'un point, le "
        f"crédit européen perd environ {viz.fr(ig_eur['duration'], '%', 1)}, "
        f"plus d'une année de rendement. Le crédit ne mérite pas d'être "
        f"surpondéré ; qualité et durées courtes sont préférables.",
        icon=":material/lightbulb:",
    )

    pedago.explique(
        "Les limites de ces chiffres",
        "Les indices ICE ne sont plus diffusés gratuitement que sur trois "
        "ans, sans aucune crise dedans. On s'appuie donc sur la série de "
        "Moody's (depuis 1986) et l'historique américain depuis 2010. Il "
        "n'existe pas de série longue gratuite pour l'Europe, mais sa prime "
        f"suit de près l'américaine (corrélation de "
        f"{viz.fr(lien['niveaux'], '', 2)} en niveau) : un repère, pas une "
        f"mesure.",
        source=f"FRED (BAA10Y de Moody's, indices ICE BofA) · relevé du "
               f"{taux.date_fr(c['releve'])} · scripts/fetch_credit.py",
    )


def _graphique_credit() -> None:
    h = credit.histo()
    m = h[["BAA10Y", "BAMLH0A0HYM2"]].resample("ME").mean()
    c = credit.charger()["series"]
    fig = go.Figure()
    for cle, nom, couleur in [
            ("BAMLH0A0HYM2", "Haut rendement, États-Unis", viz.CATEGORICAL[1]),
            ("BAA10Y", "Entreprises notées Baa, États-Unis",
             viz.CATEGORICAL[0])]:
        x = m[cle].dropna()
        fig.add_trace(go.Scatter(
            x=x.index, y=x, name=nom, mode="lines",
            line={"color": couleur, "width": 2},
            hovertemplate=f"{nom}<br>%{{x|%b %Y}} : %{{y:.2f}} %<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[pd.Timestamp(c[cle]["date"])], y=[c[cle]["valeur"]],
            mode="markers+text", showlegend=False,
            marker={"size": 9, "color": couleur,
                    "line": {"color": viz.SURFACE, "width": 2}},
            text=[f"aujourd'hui : {_pct(c[cle]['valeur'])}"],
            textposition="middle left", textfont={"color": viz.INK_2},
            hoverinfo="skip",
        ))
    for annee, (x, y) in {"2008": ("2008-12-01", 6.3),
                          "2020": ("2020-03-01", 10.9)}.items():
        fig.add_annotation(x=x, y=y, text=annee, showarrow=False,
                           yshift=10, font={"color": viz.INK_2, "size": 11})
    fig.update_layout(**viz.layout(
        "Primes de crédit américaines, en points au-dessus de l'État",
        height=420, hovermode="x unified",
        yaxis={"ticksuffix": " %", "gridcolor": viz.GRID,
               "rangemode": "tozero"},
        xaxis={"gridcolor": viz.GRID},
    ))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Moyennes mensuelles. Les pics correspondent aux crises : 2002, "
        "2008, 2012, 2016, 2020. Les deux courbes sont aujourd'hui proches "
        "du plus bas de leur histoire."
    )


# --------------------------------------------------------------------------
# Bloc 5 — la dynamique des marchés actions
# --------------------------------------------------------------------------

HORIZONS = ["1 mois", "3 mois", "12 mois"]


def _couleur_perf(v: float) -> str:
    """Divergente : bleu pour la hausse, orange pour la baisse, gris au centre."""
    if pd.isna(v) or abs(v) < 1:
        return "background-color: #f1f3f6"
    a = min(abs(v) / 30, 1) * 0.55 + 0.1
    base = "42,120,214" if v > 0 else "235,104,52"
    return f"background-color: rgba({base},{a:.2f})"


def _tableau_perf(lignes: dict, groupes: tuple[str, ...]) -> None:
    rows = [(d["libelle"], *[d[h] for h in HORIZONS])
            for d in lignes.values() if d["groupe"] in groupes]
    df = pd.DataFrame(rows, columns=["Marché", *HORIZONS])
    df = df.sort_values("12 mois", ascending=False).set_index("Marché")
    cols = HORIZONS
    sty = (df.style
           .map(_couleur_perf, subset=cols)
           .format(lambda v: ("+" if v > 0 else "") + viz.fr(v, "%", 1),
                   subset=cols))
    st.table(sty)


def _bloc_marches() -> None:
    m = marches.charger()
    L = m["lignes"]

    def p(t, h="12 mois"):
        return ("+" if L[t][h] > 0 else "") + viz.fr(L[t][h], "%", 1)

    st.markdown("#### Où va l'argent : la dynamique des marchés actions")
    st.markdown(
        "Les marchés montrent en temps réel où les investisseurs placent leur "
        "argent. Performances **en euros**, ce qu'aurait réellement vécu le "
        "client."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Par zone géographique**")
        _tableau_perf(L, ("zone",))
    with c2:
        st.markdown("**Par secteur, et l'or**")
        _tableau_perf(L, ("secteur", "reel"))
    st.caption(
        "Bleu : hausse, orange : baisse, d'autant plus foncé que le "
        "mouvement est fort. Classé sur 12 mois. Données au "
        f"{taux.date_fr(next(iter(L.values()))['date'])}."
    )

    _graphique_marches(m)

    st.markdown(
        f"**Lecture.**\n"
        f"- Sur un an, presque tout a monté (pays développés {p('EUNL.DE')}, "
        f"émergents {p('XMME.DE')}), sauf la Chine ({p('XCS6.DE')}) et l'Inde "
        f"({p('QDV5.DE')}).\n"
        f"- **L'énergie mène** ({p('XDW0.DE')}) : le marché confirme que "
        f"l'inflation vient de là. La consommation discrétionnaire recule "
        f"({p('XDWC.DE')}), des ménages dont l'énergie ampute le budget.\n"
        f"- Sur un mois, l'élan faiblit en Europe ({p('EXSA.DE', '1 mois')}) "
        f"et dans l'industrie ({p('XDWI.DE', '1 mois')}) : à surveiller."
    )
    st.info(
        "**Les marchés confirment le diagnostic : l'énergie mène, la "
        "consommation souffre.** Mais la dynamique dit ce qui monte, pas ce "
        "qui est bon marché : un marché qui a pris 30 % en un an est aussi "
        "devenu plus cher. Le bloc suivant mesure les valorisations.",
        icon=":material/lightbulb:",
    )
    pedago.explique(
        "Pourquoi regarder ce qui a monté",
        "Sur trois à douze mois, ce qui a monté a tendance à continuer "
        "(l'effet « momentum ») ; sur plusieurs années, l'effet s'inverse. "
        "La dynamique sert donc à ajuster une allocation à la marge, jamais "
        "à la fonder.",
        source=f"ETF cotés à Francfort en euros, dividendes réinvestis, noms "
               f"et devises vérifiés, prix aberrants retirés · "
               f"data/marches.json, relevé du {taux.date_fr(m['releve'])} · "
               f"Yahoo Finance",
    )


def _graphique_marches(m: dict) -> None:
    choix = [("SXR8.DE", "États-Unis"), ("EXSA.DE", "Europe"),
             ("XMME.DE", "Émergents"), ("4GLD.DE", "Or")]
    fig = go.Figure()
    for (t, nom), couleur in zip(choix, viz.CATEGORICAL):
        b = m["base100"][t]
        fig.add_trace(go.Scatter(
            x=b["dates"], y=b["valeurs"], name=nom, mode="lines",
            line={"color": couleur, "width": 2},
            hovertemplate=f"{nom} : %{{y:.1f}}<extra></extra>",
        ))
        fig.add_annotation(x=b["dates"][-1], y=b["valeurs"][-1], text=nom,
                           showarrow=False, xanchor="left", xshift=6,
                           font={"color": viz.INK_2, "size": 11})
    fig.add_hline(y=100, line={"color": viz.GRID, "width": 1})
    fig.update_layout(**viz.layout(
        "Un an de marchés, en euros (base 100 il y a un an)", height=400,
        hovermode="x unified",
        margin={"l": 10, "r": 80, "t": 46, "b": 10},
        yaxis={"gridcolor": viz.GRID}, xaxis={"gridcolor": viz.GRID},
    ))
    st.plotly_chart(fig, width="stretch")


# --------------------------------------------------------------------------
# Bloc 6 — les rendements espérés : la sortie de l'onglet
# --------------------------------------------------------------------------

NATURE = {"mesuré": "Mesuré", "estimé": "Estimé", "supposé": "Supposé"}
COULEUR_NATURE = {"mesuré": viz.CATEGORICAL[0], "estimé": viz.CATEGORICAL[1],
                  "supposé": viz.CATEGORICAL[3]}


def _bloc_rendements() -> None:
    r = rendements.charger()
    C = r["classes"]
    g = r["croissance"]
    src = r["sources"]

    st.markdown("#### Ce qu'on peut attendre de chaque classe d'actifs")
    st.markdown(
        "L'aboutissement de l'onglet : ce que chaque classe peut rapporter "
        "par an, en euros, sur dix ans, à 4 % d'inflation."
    )

    _graphique_rendements(C)

    lignes = []
    for k in rendements.ORDRE:
        v = C[k]
        fourchette = ("—" if v["bas"] == v["haut"]
                      else f"{viz.fr(v['bas'], '', 1)} à {viz.fr(v['haut'], '%', 1)}")
        lignes.append((v["libelle"], _pct(v["central"]), fourchette,
                       NATURE[v["etiquette"]]))
    st.table(pd.DataFrame(lignes, columns=[
        "Classe d'actifs", "Rendement espéré", "Fourchette", "Nature"])
        .set_index("Classe d'actifs"))
    st.caption(
        "**Mesuré** : lu sur le marché ; **estimé** : calculé à partir de "
        "mesures ; **supposé** : hypothèse faute de mieux. Le haut rendement "
        "figure pour mémoire."
    )

    st.info(
        f"**Seules les actions, l'infrastructure cotée et les obligations "
        f"indexées dépassent nettement 4 %.** Préserver le pouvoir d'achat "
        f"impose donc une part importante d'actifs de croissance ; la limite "
        f"de 15 % dira jusqu'où aller (étape 4). L'Europe et le Japon "
        f"({_pct(C['europe']['central'])} et {_pct(C['japon']['central'])}) "
        f"sont attendus au-dessus des États-Unis "
        f"({_pct(C['us']['central'])}), parce qu'ils sont moins chers.",
        icon=":material/lightbulb:",
    )

    us = C["us"]["detail"]
    pedago.explique(
        "Comment on estime ce que rapportera une action",
        "Deux mesures qui se recoupent. <strong>Le rendement des "
        "bénéfices</strong> (l'inverse du PER : à un PER de 20, on achète 5 % "
        "de bénéfices par an). <strong>Le dividende plus la croissance des "
        f"bénéfices</strong>, mesurée depuis 1900 à "
        f"{viz.fr(g['central'], '%', 1)} par an au-delà de l'inflation. On "
        "fait la moyenne des deux, puis on ajoute l'inflation de l'énoncé. "
        "Plus un marché est cher, moins il rapporte ensuite : d'où les "
        f"États-Unis (PER {viz.fr(us['per_ishares'], '', 1)}) attendus plus "
        "bas que l'Europe.",
        "<strong>Contrôle</strong> : une fois corrigées de leur inflation à "
        "2 %, les hypothèses de J.P. Morgan sont à moins d'un point des "
        "nôtres. <strong>Limites</strong> : ce sont des moyennes sur dix "
        "ans, pas des promesses (une classe attendue à 9 % peut perdre 20 % "
        "une année), hors frais, fiscalité et effet de change.",
        source=f"data/rendements.json · relevé du "
               f"{taux.date_fr(r['releve'])} · scripts/estimer_rendements.py "
               f"· {src['moodys']} · {src['jpm']} · {g['source']}",
    )

    st.markdown("#### Conclusion de l'étape 2")
    st.markdown(
        "Inflation qui remonte avec l'énergie, banques centrales qui "
        "resserrent, crédit très mal payé, actions américaines chères. "
        "Chaque classe d'actifs a désormais un rendement espéré et une "
        "fourchette. Reste à choisir les supports (étape 3), puis les "
        "proportions (étape 4)."
    )
    st.markdown(
        "**Où cette lecture agit, et où elle n'agit pas.** Ces rendements "
        "espérés sont l'entrée directe du calcul de l'étape 4 : c'est cette "
        "lecture macro qui décide des proportions entre classes d'actifs. "
        "Elle ne descend en revanche **pas** jusqu'au choix des titres de "
        "l'étape 3, dont la notation compare chaque société à son propre "
        "secteur et reste donc aveugle aux secteurs. Ce n'est pas un oubli : "
        "en tirer aussi des paris sectoriels reviendrait à miser deux fois "
        "sur le même diagnostic. Un portefeuille, un pari."
    )


def _graphique_rendements(C: dict) -> None:
    cles = [k for k in rendements.ORDRE if k != "hy_euro"]
    cles = sorted(cles, key=lambda k: C[k]["central"])
    noms = [C[k]["libelle"].replace("dont ", "  dont ") for k in cles]
    fig = go.Figure()
    for k, nom in zip(cles, noms):
        v = C[k]
        fig.add_trace(go.Scatter(
            x=[v["bas"], v["haut"]], y=[nom, nom], mode="lines",
            line={"color": viz.GRID, "width": 6}, showlegend=False,
            hoverinfo="skip"))
    for nature, lib in NATURE.items():
        ks = [k for k in cles if C[k]["etiquette"] == nature]
        fig.add_trace(go.Scatter(
            x=[C[k]["central"] for k in ks],
            y=[noms[cles.index(k)] for k in ks], mode="markers",
            name=lib, marker={"size": 11, "color": COULEUR_NATURE[nature],
                              "line": {"color": viz.SURFACE, "width": 2}},
            customdata=[[C[k]["bas"], C[k]["haut"]] for k in ks],
            hovertemplate="%{y} : %{x:.2f} %<br>fourchette %{customdata[0]:.1f}"
                          " à %{customdata[1]:.1f} %<extra></extra>"))
    fig.add_vline(x=SEUIL, line={"color": viz.INK_2, "width": 1.5,
                                 "dash": "dash"},
                  annotation={"text": f"Seuil : {viz.fr(SEUIL, '%', 0)}",
                              "font": {"color": viz.INK_2, "size": 12}},
                  annotation_position="top")
    fig.update_layout(**viz.layout(
        "Rendement annuel espéré sur dix ans, en euros, à 4 % d'inflation",
        height=520,
        xaxis={"ticksuffix": " %", "gridcolor": viz.GRID, "range": [-0.5, 11.5]},
        yaxis={"gridcolor": "rgba(0,0,0,0)"},
    ))
    st.plotly_chart(fig, width="stretch")
    st.caption("Point : estimation centrale, couleur selon sa nature. Barre "
               "grise : fourchette. La crypto est comptée à zéro par "
               "principe, pas par prévision.")
