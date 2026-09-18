"""
Encadres pedagogiques depliables.

Un seul point de passage, pour deux raisons.

La premiere est l'uniformite : cinq onglets ecrits par a-coups finissent avec
cinq styles d'explication differents, et c'est exactement ce qui rendait la
version precedente confuse.

La seconde est une contrainte deliberee : `formule()` EXIGE une traduction en
francais courant. On ne peut pas afficher une formule nue. Le lecteur suppose
n'est pas un quant -- en gestion privee la plupart des interlocuteurs ne le
sont pas -- et une formule sans sa phrase est une formule qui ne sera pas lue.
"""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
  .peda p {font-size: .92rem; line-height: 1.62; margin: 0 0 .85em 0;
           color: #23262b; max-width: 78ch;}
  .peda p:last-child {margin-bottom: 0;}
  .peda strong {color: #14304f;}
  .peda-trad {font-size: .88rem; color: #45484d; font-style: italic;
              border-left: 2px solid #2a78d6; padding-left: .7em;
              margin: .2em 0 1em 0; max-width: 78ch;}
  .peda-source {font-size: .78rem; color: #6b6f76; margin-top: 1em;
                padding-top: .6em; border-top: 1px solid #e3e6ea;}
</style>
"""

_css_pose = False


def _poser_css() -> None:
    global _css_pose
    if not _css_pose:
        st.markdown(CSS, unsafe_allow_html=True)
        _css_pose = True


def explique(titre: str, *paragraphes: str, source: str | None = None,
             ouvert: bool = False) -> None:
    """
    Encadre depliable : un titre, des paragraphes rediges, une source.

    Chaque argument positionnel est UN paragraphe. Pas de puces : une puce
    enonce, un paragraphe explique, et c'est d'explications qu'il s'agit ici.
    """
    _poser_css()
    with st.expander(titre, expanded=ouvert):
        corps = "".join(f"<p>{p.strip()}</p>" for p in paragraphes if p.strip())
        st.markdown(f'<div class="peda">{corps}</div>', unsafe_allow_html=True)
        if source:
            st.markdown(f'<div class="peda-source">{source}</div>',
                        unsafe_allow_html=True)


def formule(latex: str, traduction: str) -> None:
    """
    Une formule ET sa traduction en francais. Les deux, toujours.

    `traduction` n'a pas de valeur par defaut : c'est voulu. Oublier la
    traduction doit casser, pas passer silencieusement.
    """
    if not traduction.strip():
        raise ValueError("une formule sans traduction en francais n'a rien "
                         "a faire dans cette application")
    _poser_css()
    st.latex(latex)
    st.markdown(f'<div class="peda-trad">{traduction.strip()}</div>',
                unsafe_allow_html=True)


def etape(numero: int, titre: str, resume: str) -> None:
    """En-tete d'onglet : ou l'on est dans la chaine, et ce qu'on y fait."""
    _poser_css()
    st.markdown(f"### {numero}. {titre}")
    st.markdown(f'<div class="peda"><p>{resume.strip()}</p></div>',
                unsafe_allow_html=True)


def a_construire(numero: int, titre: str, *prevu: str) -> None:
    """
    Marqueur d'onglet non encore construit.

    Il annonce ce qui viendra, sans rien simuler. Un graphique de
    demonstration dans un onglet vide est la meilleure facon de se mentir
    sur l'avancement.
    """
    _poser_css()
    st.info(f"Onglet {numero} — {titre} : a construire.", icon=":material/build:")
    if prevu:
        st.markdown("**Ce que cet onglet contiendra**")
        for p in prevu:
            st.markdown(f"- {p}")


# --------------------------------------------------------------------------
# La chaine. Les cinq onglets sont SEQUENTIELS : la sortie de chacun est
# l'entree du suivant. L'afficher en haut de chaque onglet evite au lecteur
# de se demander ou il en est -- c'est le defaut principal de la version
# precedente, qui juxtaposait neuf onglets sans ordre lisible.
# --------------------------------------------------------------------------

CHAINE = (
    (1, "Paramètres", "ce que le mandat impose"),
    (2, "Macro", "où nous sommes dans le cycle"),
    (3, "Ligne à ligne", "ce qui est investissable"),
    (4, "Allocation", "combien de chaque"),
    (5, "Backtests", "ce que ça aurait donné"),
)

CSS_CHAINE = """
<style>
  .chaine {display: flex; flex-wrap: wrap; gap: .35rem; align-items: stretch;
           margin: 0 0 1.4rem 0;}
  .chaine-e {flex: 1 1 8.5rem; min-width: 8.5rem; padding: .5rem .7rem;
             border-radius: 5px; background: #f1f3f6; border: 1px solid #e3e6ea;}
  .chaine-e.on {background: #14304f; border-color: #14304f;}
  .chaine-n {font-size: .7rem; letter-spacing: .06em; color: #7b828c;}
  .chaine-t {font-size: .84rem; font-weight: 600; color: #23262b;
             line-height: 1.25;}
  .chaine-s {font-size: .72rem; color: #6b6f76; line-height: 1.3;
             margin-top: .15rem;}
  .chaine-e.on .chaine-t, .chaine-e.on .chaine-n {color: #ffffff;}
  .chaine-e.on .chaine-s {color: #c3d2e4;}
</style>
"""


def chaine(courante: int) -> None:
    """Le fil des cinq etapes, avec celle-ci mise en avant."""
    st.markdown(CSS_CHAINE, unsafe_allow_html=True)
    blocs = []
    for n, titre, sous in CHAINE:
        on = " on" if n == courante else ""
        blocs.append(
            f'<div class="chaine-e{on}">'
            f'<div class="chaine-n">ÉTAPE {n}</div>'
            f'<div class="chaine-t">{titre}</div>'
            f'<div class="chaine-s">{sous}</div></div>'
        )
    st.markdown(f'<div class="chaine">{"".join(blocs)}</div>',
                unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Un fil de causalité : des boîtes reliées par des flèches, pour montrer
# qu'une chose en entraîne une autre. Même dessin que la chaîne des étapes.
# --------------------------------------------------------------------------

CSS_FIL = """
<style>
  .fil {display: flex; flex-wrap: wrap; align-items: center; gap: .3rem;
        margin: .4rem 0 1.2rem 0;}
  .fil-e {flex: 1 1 7.5rem; min-width: 7.5rem; padding: .45rem .65rem;
          border-radius: 5px; background: #f1f3f6; border: 1px solid #e3e6ea;}
  .fil-t {font-size: .84rem; font-weight: 600; color: #23262b;}
  .fil-s {font-size: .72rem; color: #6b6f76; line-height: 1.3;
          margin-top: .1rem;}
  .fil-f {color: #8a8e95; font-size: 1rem;}
</style>
"""


def fil(maillons: list[tuple[str, str]]) -> None:
    """Maillons (titre, sous-titre) reliés par des flèches."""
    st.markdown(CSS_FIL, unsafe_allow_html=True)
    blocs = [f'<div class="fil-e"><div class="fil-t">{t}</div>'
             f'<div class="fil-s">{s}</div></div>' for t, s in maillons]
    st.markdown('<div class="fil">' + '<span class="fil-f">→</span>'.join(blocs)
                + "</div>", unsafe_allow_html=True)
