"""
Genere le pitch client au format PowerPoint.

Parti pris : une presentation COMPLETE, qui se comprend sans commentaire.
On n'a pas suivi le ratio du document TCP Kenz (12 slides + 49 annexes) :
ici chaque decision est exposee avec son alternative ecartee et sa raison.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
CH = ROOT / "outputs" / "charts"
OUT = ROOT / "outputs" / "Mandat_Lauren_pitch.pptx"

# URL publique de l'application. Renseigner apres deploiement : le deck
# fabrique alors un lien cliquable sur la couverture et une slide dediee.
# Peut aussi etre passee en argument :  python3 scripts/build_deck.py <url>
APP_URL = "https://mandat-lauren.streamlit.app"
if len(sys.argv) > 1:
    APP_URL = sys.argv[1].strip()

SLATE = RGBColor(0x1B, 0x2A, 0x3A)
SLATE_2 = RGBColor(0x2F, 0x48, 0x58)
ACCENT = RGBColor(0x2A, 0x78, 0xD6)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
RED = RGBColor(0xE3, 0x49, 0x48)
GREEN = RGBColor(0x1B, 0xAF, 0x7A)
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x6B, 0x72, 0x80)
LINE = RGBColor(0xDD, 0xE1, 0xE5)
SOFT = RGBColor(0xF4, 0xF6, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

W, H = Inches(13.333), Inches(7.5)
FONT = "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
_section = {"name": ""}
_n = {"i": 0}


def _box(sl, x, y, w, h):
    return sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))


def _rect(sl, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    s = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color
    s.line.fill.background(); s.shadow.inherit = False
    return s


def _txt(tf, text, size=14, color=INK, bold=False, italic=False,
         space_after=6, align=PP_ALIGN.LEFT, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run(); r.text = text
    r.font.size, r.font.bold, r.font.italic = Pt(size), bold, italic
    r.font.color.rgb = color; r.font.name = FONT
    return p


def slide(title: str, sub: str = "") -> object:
    _n["i"] += 1
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(sl, 0, 0, 13.333, 0.52, SLATE)
    b = _box(sl, 0.45, 0.04, 8, 0.42); tf = b.text_frame; tf.word_wrap = True
    _txt(tf, _section["name"].upper(), 10.5, WHITE, bold=True, first=True)
    b2 = _box(sl, 9.5, 0.04, 3.5, 0.42); tf2 = b2.text_frame
    _txt(tf2, "Mandat Lauren", 10.5, RGBColor(0x9F, 0xB0, 0xBD),
         align=PP_ALIGN.RIGHT, first=True)

    b3 = _box(sl, 0.55, 0.72, 12.2, 0.8); tf3 = b3.text_frame; tf3.word_wrap = True
    _txt(tf3, title, 26, SLATE, bold=True, first=True, space_after=0)
    if sub:
        b4 = _box(sl, 0.55, 1.42, 12.2, 0.5); tf4 = b4.text_frame
        tf4.word_wrap = True
        _txt(tf4, sub, 13, MUTED, italic=True, first=True)

    f = _box(sl, 0.45, 7.05, 9, 0.35); tff = f.text_frame
    _txt(tff, "Banque privée  ·  proposition de mandat  ·  septembre 2026",
         9, RGBColor(0xA8, 0xAE, 0xB6), first=True)
    f2 = _box(sl, 12.3, 7.05, 0.7, 0.35); tff2 = f2.text_frame
    _txt(tff2, str(_n["i"]), 10, MUTED, align=PP_ALIGN.RIGHT, first=True)
    return sl


def cover():
    _n["i"] += 0
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(sl, 0, 0, 13.333, 7.5, SLATE)
    _rect(sl, 0, 4.42, 13.333, 0.035, GOLD)
    b = _box(sl, 1.1, 2.1, 11, 1.1); tf = b.text_frame
    _txt(tf, "PROPOSITION DE MANDAT DE GESTION", 13, GOLD, bold=True,
         first=True)
    b2 = _box(sl, 1.1, 2.62, 11, 1.5); tf2 = b2.text_frame; tf2.word_wrap = True
    _txt(tf2, "Famille Lauren", 48, WHITE, bold=True, first=True, space_after=0)
    b3 = _box(sl, 1.1, 4.75, 10.5, 1.6); tf3 = b3.text_frame; tf3.word_wrap = True
    _txt(tf3, "Préserver 100 millions d'euros contre l'inflation,",
         19, RGBColor(0xD6, 0xDD, 0xE3), first=True, space_after=2)
    _txt(tf3, "sous contrainte de perte maximum de 15 %,", 19,
         RGBColor(0xD6, 0xDD, 0xE3), space_after=2)
    _txt(tf3, "et transmettre.", 19, GOLD, bold=True)
    b4 = _box(sl, 1.1, 6.6, 11, 0.4); tf4 = b4.text_frame
    _txt(tf4, "Septembre 2026", 11, RGBColor(0x8A, 0x99, 0xA6), first=True)
    if APP_URL:
        from pptx.enum.shapes import MSO_SHAPE
        btn = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.55),
                                  Inches(6.42), Inches(2.75), Inches(0.52))
        btn.fill.solid(); btn.fill.fore_color.rgb = GOLD
        btn.line.fill.background(); btn.shadow.inherit = False
        tfb = btn.text_frame; tfb.word_wrap = False
        pb = tfb.paragraphs[0]; pb.alignment = PP_ALIGN.CENTER
        rb = pb.add_run(); rb.text = "Ouvrir l'outil interactif"
        rb.font.size, rb.font.bold = Pt(12), True
        rb.font.color.rgb = SLATE; rb.font.name = FONT
        rb.hyperlink.address = APP_URL


def section(name: str, num: str, points: list[str]):
    _section["name"] = name
    _n["i"] += 1
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(sl, 0, 0, 13.333, 7.5, SLATE)
    _rect(sl, 1.1, 2.5, 0.06, 1.5, GOLD)
    b = _box(sl, 1.45, 2.42, 10, 0.5); tf = b.text_frame
    _txt(tf, num, 15, GOLD, bold=True, first=True)
    b2 = _box(sl, 1.45, 2.85, 10.5, 1); tf2 = b2.text_frame; tf2.word_wrap = True
    _txt(tf2, name, 34, WHITE, bold=True, first=True)
    b3 = _box(sl, 1.45, 4.15, 10.5, 2); tf3 = b3.text_frame; tf3.word_wrap = True
    for i, p in enumerate(points):
        _txt(tf3, "— " + p, 14, RGBColor(0xB8, 0xC4, 0xCE), first=(i == 0),
             space_after=9)
    f2 = _box(sl, 12.3, 7.05, 0.7, 0.35); tff2 = f2.text_frame
    _txt(tff2, str(_n["i"]), 10, RGBColor(0x6B, 0x7A, 0x88),
         align=PP_ALIGN.RIGHT, first=True)


def bullets(sl, items, x=0.55, y=2.05, w=12.2, size=14, lead=""):
    b = _box(sl, x, y, w, 4.6); tf = b.text_frame; tf.word_wrap = True
    first = True
    if lead:
        _txt(tf, lead, size + 2, SLATE, bold=True, first=True, space_after=12)
        first = False
    for it in items:
        if isinstance(it, tuple):
            head, body = it
            p = _txt(tf, head, size, SLATE, bold=True, first=first,
                     space_after=2); first = False
            _txt(tf, body, size - 0.5, INK, space_after=11)
        else:
            _txt(tf, "• " + it, size, INK, first=first, space_after=8)
            first = False
    return sl


def chart(sl, name, x=1.05, y=1.95, w=11.2):
    p = CH / f"{name}.png"
    if p.exists():
        sl.shapes.add_picture(str(p), Inches(x), Inches(y), width=Inches(w))
    return sl


def table(sl, headers, rows, y=2.05, widths=None, size=11.5):
    n_r, n_c = len(rows) + 1, len(headers)
    h = min(0.42 + 0.36 * len(rows), 4.7)
    shape = sl.shapes.add_table(n_r, n_c, Inches(0.55), Inches(y),
                                Inches(12.2), Inches(h))
    t = shape.table
    if widths:
        total = sum(widths)
        for i, wd in enumerate(widths):
            t.columns[i].width = Emu(int(Inches(12.2) * wd / total))
    for j, htxt in enumerate(headers):
        c = t.cell(0, j); c.text = ""
        c.fill.solid(); c.fill.fore_color.rgb = SLATE
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        _txt(c.text_frame, htxt, 11, WHITE, bold=True, first=True, space_after=0)
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.text = ""
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 else SOFT
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            txt = str(val); col, bold = INK, False
            if txt.startswith("!"):
                txt, col, bold = txt[1:], RED, True
            elif txt.startswith("+"):
                col, bold = GREEN, True
            elif txt.startswith("*"):
                txt, bold = txt[1:], True
            _txt(c.text_frame, txt, size, col, bold=bold, first=True,
                 space_after=0)
    return sl


def kpis(sl, items, y=2.2):
    n = len(items)
    gap, wid = 0.28, (12.2 - 0.28 * (n - 1)) / n
    for i, (label, value, note) in enumerate(items):
        x = 0.55 + i * (wid + gap)
        _rect(sl, x, y, wid, 1.65, SOFT)
        _rect(sl, x, y, wid, 0.045, ACCENT)
        b = _box(sl, x + 0.18, y + 0.2, wid - 0.36, 1.3); tf = b.text_frame
        tf.word_wrap = True
        _txt(tf, label.upper(), 9.5, MUTED, bold=True, first=True, space_after=5)
        _txt(tf, value, 27, SLATE, bold=True, space_after=3)
        _txt(tf, note, 10, MUTED)
    return sl


def quote(sl, text, y=4.4, label="CE QUE NOUS DISONS AU CLIENT"):
    _rect(sl, 0.55, y, 12.2, 0.05 + 0.32 * (1 + text.count("\n")) + 0.75, SLATE)
    b = _box(sl, 0.95, y + 0.22, 11.4, 2)
    tf = b.text_frame; tf.word_wrap = True
    _txt(tf, label, 9.5, RGBColor(0x9F, 0xB0, 0xBD), bold=True, first=True,
         space_after=9)
    for i, line in enumerate(text.split("\n")):
        _txt(tf, line, 15, WHITE, space_after=4)
    return sl


def callout(sl, text, y=5.9, color=GOLD, h=0.85):
    _rect(sl, 0.55, y, 0.05, h, color)
    b = _box(sl, 0.78, y + 0.02, 11.9, h); tf = b.text_frame; tf.word_wrap = True
    _txt(tf, text, 13.5, SLATE, bold=True, first=True)
    return sl


# ==========================================================================
# LE DECK
# ==========================================================================

cover()

_section["name"] = "Sommaire"
sl = slide("Ce que contient cette présentation")
table(sl, ["", "Section", "Ce qu'elle établit"], [
    ["1", "Le mandat", "Ce que vous nous demandez, et les trois tensions que "
     "cela contient"],
    ["2", "Le cadre de risque", "Ce que « perte maximum de 15 % » veut dire "
     "précisément, et ce que cela autorise"],
    ["3", "Marché et hypothèses", "Nos vues, leur provenance, et pourquoi le "
     "régime d'inflation change tout"],
    ["4", "Construction du portefeuille", "L'univers, les données, "
     "l'optimisation — et ce que nous n'avons pas suivi"],
    ["5", "Risque et performance", "Ce que vous auriez vécu dans les crises "
     "qui ont eu lieu"],
    ["6", "Fiscalité et transmission", "Le levier qui pèse neuf fois "
     "l'allocation"],
    ["7", "Mise en œuvre", "Gouvernance, calendrier, et ce qui reste à valider"],
], widths=[.5, 3, 8.5], size=12.5)

# ---------------------------------------------------------------- 1
section("Le mandat", "SECTION 1", [
    "Votre situation, telle que nous la comprenons",
    "Trois tensions que votre demande contient",
    "Le cadrage chiffré qui en découle"])

sl = slide("Votre situation")
table(sl, ["", "Donnée", "Ce que cela implique pour nous"], [
    ["", "60 ans, marié, deux enfants", "L'horizon n'est pas le vôtre seul"],
    ["", "Résident fiscal français", "Univers UCITS, et une fiscalité qui se "
     "pilote"],
    ["", "100 M€ après cession", "Taille institutionnelle : frais négociables"],
    ["", "10 M€ à dépenser sous 2 ans", "Un engagement daté, à adosser"],
    ["", "Protection contre 4 % d'inflation", "Un objectif net, pas brut"],
    ["", "Perte maximum 15 %", "La contrainte qui commande tout le reste"],
    ["", "Ni tabac, ni armement, ni charbon", "Trois exclusions précises, pas "
     "une démarche ESG large"],
    ["", "Transmission progressive aux enfants", "L'indicateur devient le net "
     "transmis, pas le brut"],
    ["", "Votre fils veut de la crypto", "Une question de gouvernance, pas "
     "d'allocation"],
    ["", "Inquiet sur l'Europe ET les États-Unis", "Ne dépendre d'aucune des "
     "deux"],
], widths=[.3, 4.2, 7.5], size=11.5)

sl = slide("Trois tensions dans votre demande",
           "Nous préférons les nommer d'emblée plutôt que vous les laisser "
           "découvrir.")
bullets(sl, [
    ("1 · « Profil dynamique » contre « perte maximum 15 % »",
     "Un portefeuille dynamique standard, c'est 13 % de volatilité — et une "
     "perte de 35 % en 2008. Les deux phrases ne sont pas compatibles. "
     "C'est le chiffre qui commande, pas l'adjectif."),
    ("2 · « Protéger contre 4 % » ne veut pas dire « viser 4 % »",
     "Entre la performance brute et ce qui reste dans votre poche, il y a nos "
     "frais et l'impôt. Viser 4 % brut vous appauvrit chaque année."),
    ("3 · Inquiet sur l'euro ET sur le dollar",
     "Cette remarque élimine la réponse paresseuse — « vous craignez l'euro, "
     "mettons du dollar ». Elle appelle une réponse d'allocation, pas un "
     "arbitrage de devise."),
], y=2.15)
callout(sl, "Notre valeur ajoutée commence par dire ce qui ne va pas de soi.",
        y=6.15)

sl = slide("Le cadrage chiffré")
kpis(sl, [("Rendement requis", "4,80 %", "brut, net de frais et d'impôts"),
          ("Rendement attendu", "5,79 %", "hypothèses de marché à 10 ans"),
          ("Marge", "+0,99 %", "par an"),
          ("Volatilité cible", "9,6 %", "45 % d'actifs de croissance"),
          ("Perte P90", "13,8 %", "contrainte : 15 %")])
bullets(sl, [
    ("L'objectif est atteignable, avec environ un point de marge annuelle.",
     "Et il le reste si l'inflation se révèle conforme au consensus plutôt "
     "qu'à votre hypothèse — la marge passe alors à +1,40 %. Vous ne dépendez "
     "pas du fait que nous ayons raison sur l'inflation."),
], y=4.3)
callout(sl, "Chiffre à ne pas omettre : dans une crise comme 2008, cette "
            "allocation aurait perdu 25,6 %. Nous vous le disons maintenant.",
        y=5.85, color=RED)

sl = slide("Quatre poches, pas un portefeuille",
           "Un patrimoine n'a pas un objectif, il en a plusieurs.")
table(sl, ["Poche", "Montant", "Horizon", "Rôle", "Risque"], [
    ["A — Liquidité", "10 M€", "0-2 ans", "Le projet que vous financez",
     "Quasi nul"],
    ["B — Cœur patrimonial", "58 M€", "10-20 ans",
     "Votre niveau de vie, protégé de l'inflation", "Modéré"],
    ["C — Transmission", "30 M€", "25-30 ans", "Ce qui ira à vos enfants",
     "Élevé, assumé"],
    ["D — Satellite", "2 M€", "10 ans +", "Convictions, dont crypto",
     "Très élevé, plafonné"],
], widths=[2.6, 1.3, 1.4, 5, 1.9], size=12)
quote(sl, "Si je mélange vos deux ans et vos trente ans dans un portefeuille\n"
          "unique, j'obtiens un compromis qui ne convient à aucun des deux :\n"
          "trop risqué pour l'un, trop timide pour l'autre.", y=4.35)

sl = slide("Votre horizon n'est pas votre âge")
quote(sl, "Beaucoup vous diraient : vous avez 60 ans, donc horizon 20 ans,\n"
          "donc portefeuille prudent. Je crois que c'est une erreur d'analyse.\n\n"
          "Cet argent ne sera pas consommé à votre décès : il continuera d'être\n"
          "investi par vos enfants. L'horizon réel, c'est votre espérance de vie\n"
          "PLUS la leur. Trente ans, au bas mot.\n\n"
          "Et c'est une bonne nouvelle : le temps est le seul ingrédient qui\n"
          "transforme le risque en rendement.", y=2.15)
callout(sl, "C'est ce qui autorise le budget de risque de la poche "
            "transmission — et donc l'atteinte de votre objectif.", y=6.3)

# ---------------------------------------------------------------- 2
section("Le cadre de risque", "SECTION 2", [
    "Ce que « 15 % » veut dire précisément",
    "Comment nous l'avons mesuré plutôt que postulé",
    "Ce que cela autorise, et ce que cela interdit"])

sl = slide("Ce que nous entendons par « perte maximum 15 % »",
           "L'énoncé est volontairement flou. Nous le définissons, et nous "
           "défendons chaque choix.")
_rect(sl, 0.55, 2.0, 12.2, 0.9, SOFT)
b = _box(sl, 0.85, 2.12, 11.6, 0.8); tf = b.text_frame; tf.word_wrap = True
_txt(tf, "Perte maximale de pic à creux sur toute fenêtre de 12 mois "
         "glissants, mesurée au niveau consolidé, en euros, avec une "
         "probabilité de dépassement inférieure à 10 %.",
     15, SLATE, bold=True, first=True)
table(sl, ["Choix", "Alternative écartée", "Pourquoi"], [
    ["Drawdown", "VaR à 95 %", "Le drawdown est ce que vous vivez : l'écart "
     "entre votre meilleur relevé et le pire. C'est aussi la mesure la plus "
     "contraignante."],
    ["Niveau consolidé", "Ligne à ligne", "Appliquer 15 % à chaque ligne "
     "interdirait toute exposition actions."],
    ["Probabilité < 10 %", "Plafond absolu « jamais »",
     "Aucun gérant ne peut garantir un plafond absolu. Le promettre serait "
     "malhonnête."],
], y=3.15, widths=[2, 2.6, 7.6], size=11.5)
callout(sl, "Nous ne vous promettons pas que vous ne perdrez jamais 15 %. "
            "Nous construisons pour que cela arrive moins d'une année sur dix.",
        y=5.75)

sl = slide("Du « 15 % » au budget de risque — mesuré, pas postulé",
           "21,8 ans de données quotidiennes en euros, incluant 2008, 2011, "
           "2020 et 2022.")
table(sl, ["Actifs de croissance", "Volatilité", "Perte P90", "Pire observé",
           "2008", "Contrainte"], [
    ["38 %", "8,4 %", "11,1 %", "22,2 %", "22,9 %", "respectée"],
    ["43 %", "9,5 %", "12,6 %", "25,0 %", "25,8 %", "respectée"],
    ["*45 %", "*9,6 %", "*13,8 %", "*24,9 %", "*25,6 %", "*RETENU"],
    ["48 %", "10,5 %", "14,1 %", "27,7 %", "28,6 %", "à la limite"],
    ["53 %", "11,6 %", "15,6 %", "30,3 %", "31,3 %", "!VIOLÉE"],
], y=2.3, widths=[2.4, 1.8, 1.8, 2, 1.7, 2.3], size=12)
bullets(sl, [
    ("Nous avions d'abord postulé une règle empirique. Elle était fausse.",
     "Le rapport entre volatilité et perte maximale, que nous avions posé à "
     "1,9 « par convention », vaut en réalité 1,35 une fois mesuré. Cette "
     "erreur sous-allouait le risque d'environ dix points d'actions."),
], y=4.85)
callout(sl, "Nous avons dé-risqué de 48 % à 45 % après ces tests. "
            "Coût : 19 points de base par an. Gain : 1,5 point de marge sur "
            "la perte maximale.", y=6.3)

# ---------------------------------------------------------------- 3
section("Marché et hypothèses", "SECTION 3", [
    "D'où viennent nos chiffres, ligne par ligne",
    "Pourquoi le régime d'inflation change la réponse",
    "Nos vues par classe d'actifs"])

sl = slide("Nos hypothèses, et leur provenance",
           "Prospectif, pas historique. Une moyenne de rendements passés n'est "
           "pas une prévision.")
table(sl, ["Classe d'actifs", "Attendu à 4 % d'inflation", "Provenance",
           "Sur quoi elle repose"], [
    ["Actions développées", "7,70 %", "hypothèse",
     "Dividende 1,9 % + rachats 1,0 % + croissance réelle 2,0 % − dérive de "
     "valorisation 0,8 %"],
    ["Actions émergentes", "8,80 %", "hypothèse",
     "Prime justifiée par la valorisation d'entrée, pas par la croissance du PIB"],
    ["Infrastructure cotée", "7,60 %", "hypothèse",
     "Dividende 3,2 % + croissance 1,5 %, revenus contractuellement indexés"],
    ["Obligations indexées", "4,50 %", "marché",
     "Rendement réel du gisement + inflation, répercussion intégrale"],
    ["Crédit IG euro", "4,35 %", "marché",
     "Rendement actuariel, net d'une perte attendue par défaut"],
    ["Souverain euro", "3,60 %", "marché",
     "Rendement actuariel — inférieur au monétaire dans ce régime"],
    ["Or", "4,50 %", "hypothèse",
     "Rendement réel proche de 0,5 % + inflation. Détenu pour la "
     "décorrélation, pas pour son espérance"],
    ["Monétaire", "4,05 %", "*mesuré",
     "€STR implicite, lu sur la série de XEON.DE au 17 septembre 2026"],
    ["Crypto", "0,00 %", "hypothèse",
     "Espérance comptée à zéro délibérément — non estimable avec une précision "
     "utile"],
], y=2.05, widths=[2.4, 2, 1.4, 6.4], size=10.5)
callout(sl, "Chaque ligne porte son étiquette : mesurée, lue sur le marché, "
            "ou supposée. Vous devez pouvoir nous demander d'où vient un "
            "chiffre.", y=6.4)

sl = slide("Le régime d'inflation change la réponse",
           "Le seuil requis ET le rendement attendu dépendent tous deux de "
           "l'inflation. Les comparer dans des régimes différents revient à "
           "évaluer un portefeuille dans un monde et à le juger dans un autre.")
chart(sl, "faisabilite", x=2.35, y=1.9, w=8.6)

sl = slide("Comment l'inflation se transmet à chaque classe d'actifs",
           "Coefficient de répercussion : la part d'une surprise d'inflation "
           "qui se retrouve dans le rendement nominal à dix ans.")
table(sl, ["Classe", "Répercussion", "Mécanisme"], [
    ["Monétaire", "1,00", "Suit la politique monétaire, donc l'inflation"],
    ["Obligations indexées", "1,00", "Protection mécanique — c'est leur "
     "définition, et c'est ce qui justifie leur poids de 15 %"],
    ["Matières premières", "1,10", "Souvent la CAUSE de la surprise "
     "d'inflation, pas seulement sa victime"],
    ["Infrastructure", "0,90", "Revenus contractuellement indexés"],
    ["Or", "1,00", "Réserve de valeur, aucun flux à actualiser"],
    ["Actions", "0,80", "Pouvoir de fixation des prix, mais compression des "
     "multiples en régime inflationniste"],
    ["Souverain taux fixe", "!0,45", "Perte en capital d'abord, "
     "réinvestissement à taux plus élevé ensuite"],
], y=2.55, widths=[2.6, 1.8, 7.8], size=12)
callout(sl, "Un jeu d'hypothèses aveugle au régime d'inflation ne peut pas "
            "répondre à un mandat de protection contre l'inflation.", y=6.2)

sl = slide("Nos vues, et la confiance que nous leur accordons")
table(sl, ["Vue", "Ampleur", "Confiance", "Ce sur quoi elle repose"], [
    ["Obligations indexées > souverain nominal", "+0,80 %", "*75 %",
     "Coefficients de répercussion mesurés : 1,00 contre 0,45. Propriété "
     "mécanique, pas une prévision."],
    ["Crédit IG > souverain", "+0,65 %", "55 %",
     "Écart de rendement actuariel constaté. Ancré sur un prix de marché, "
     "mais le spread peut s'écarter."],
    ["Or > monétaire", "+0,45 %", "50 %",
     "Seule brique dont la corrélation aux actions BAISSE sous stress "
     "(0,07 → −0,07 en 2022, mesuré)."],
    ["Actions émergentes > développées", "+1,20 %", "!30 %",
     "Point d'entrée en valorisation. Confiance faible assumée : les paris "
     "relatifs entre zones actions sont les moins fiables du métier."],
], y=2.3, widths=[3.6, 1.4, 1.4, 5.8], size=11.5)
bullets(sl, [
    ("La hiérarchie des confiances est le vrai contenu.",
     "Une vue mécanique pèse 75 %, un pari directionnel sur les actions en "
     "pèse 30 — et le modèle en tient compte tout seul."),
], y=5.3)

# ---------------------------------------------------------------- 4
section("Construction du portefeuille", "SECTION 4", [
    "L'univers, et le nettoyage qu'il a fallu",
    "Le processus d'optimisation",
    "Ce que l'optimiseur voulait, et pourquoi nous ne l'avons pas suivi"])

sl = slide("L'univers investissable",
           "226 candidats évalués, 48 supports retenus, un principal par "
           "classe d'actifs.")
table(sl, ["Exclusion", "Seuils de chiffre d'affaires", "Où le filtre "
           "s'applique"], [
    ["Tabac", "Production 0 % · distribution 5 %", ""],
    ["Armement", "Armes controversées 0 % · conventionnel 5 %", ""],
    ["Charbon thermique", "Extraction et production d'électricité 5 %", ""],
], y=2.1, widths=[2.6, 5, 4.6], size=12)
bullets(sl, [
    ("Le filtre s'applique là où il a un objet — et nulle part ailleurs.",
     "Les trois exclusions visent des émetteurs d'entreprise. Il n'y a rien à "
     "filtrer dans une obligation d'État allemande ou dans un lingot d'or. "
     "Exiger un label ESG sur ces classes reviendrait à payer une surcouche "
     "marketing sans contenu."),
    ("Nous avons retenu MSCI ESG Screened plutôt que SRI.",
     "Votre mandat demande trois exclusions précises, pas une démarche "
     "best-in-class. ESG Screened exclut exactement ces trois secteurs et rien "
     "de plus : l'univers reste à 95 % de l'indice parent. Le SRI irait bien "
     "au-delà de votre demande — c'est une question que nous vous posons "
     "plutôt qu'un choix que nous faisons à votre place."),
], y=3.6)

sl = slide("Le travail invisible : nettoyer les données",
           "Sans ce filtre, l'optimisation aurait tourné sur des chiffres faux "
           "sans que rien ne le signale.")
chart(sl, "qualite", x=1.3, y=1.95, w=10.7)
callout(sl, "Une erreur de données ne se voit pas dans le résultat : "
            "elle le déplace silencieusement.", y=6.25, color=RED)

sl = slide("Ce que nous avons trouvé dans les données")
table(sl, ["Problème", "Exemple", "Traitement"], [
    ["Rupture d'échelle", "SPXS.L le 2014-01-02 : 303,05 → 3,02 — passage des "
     "pence aux livres", "Réparation : le segment antérieur est remis à "
     "l'échelle"],
    ["Oscillation de devise", "SGLN.L en avril 2011 : −39 %, +64 %, −38 %, "
     "+62 %", "Rejet : on ne sait pas quel point appartient à quelle série"],
    ["Contamination diffuse", "Un ETF souverain 1-3 ans affichant 29 % de "
     "volatilité", "Contrôle de plausibilité par classe d'actifs"],
    ["Ticker trompeur", "CTA.L n'est pas un fonds de tendance mais "
     "CT Automotive Group plc", "Vérification systématique des libellés"],
], y=2.1, widths=[2.4, 5.4, 4.4], size=11.5)
bullets(sl, [
    ("Sur 182 séries, une inspection manuelle est impossible.",
     "Le garde-fou est un contrôle automatique : une fourchette de volatilité "
     "plausible par classe d'actifs. Un souverain court au-dessus de 3 % de "
     "volatilité est faux, quelle qu'en soit la cause."),
], y=5.0)

sl = slide("Le processus d'optimisation")
table(sl, ["Étape", "Ce qu'elle fait", "Pourquoi elle est là"], [
    ["1 · Ancrage neutre", "Parité de risque sur les actifs risqués",
     "Un point de départ qui ne suppose aucune vue"],
    ["2 · Vues", "Black-Litterman, quatre vues avec confiance explicite",
     "Nos convictions n'influencent le portefeuille qu'à proportion de notre "
     "confiance"],
    ["3 · Resampling", "120 optimisations sur hypothèses perturbées",
     "L'optimisation classique est instable : déplacez une prévision de 20 pb "
     "et l'allocation bascule"],
    ["4 · Contraintes", "Plafonds et planchers de second niveau",
     "Encoder ce que la matrice de covariance ne peut pas voir"],
    ["5 · Validation", "Simulation du drawdown sur 21,8 ans",
     "Vérifier que la contrainte de 15 % tient réellement"],
], y=2.1, widths=[2.4, 4.4, 5.4], size=11.5)
callout(sl, "Nous n'optimisons pas une fois. Nous proposons, nous simulons, "
            "nous corrigeons — jusqu'à ce que la contrainte tienne.", y=5.6)

sl = slide("Ce que l'optimiseur voulait faire",
           "Une allocation mathématiquement optimale, et pratiquement "
           "inutilisable.")
table(sl, ["Classe d'actifs", "Optimisation libre", "Retenu",
           "Ce que la covariance ne voit pas"], [
    ["Infrastructure cotée", "!27,8 %", "*9 %",
     "Un seul secteur. Le support filtré ESG a 3,1 ans d'historique et une "
     "capacité limitée : risque d'exécution."],
    ["Actions émergentes", "20,9 %", "*11 %",
     "Concentration géographique et risque politique, absents de la "
     "volatilité."],
    ["Actions développées", "!7,1 %", "*23 %",
     "Liquidité et capacité : la seule classe qui absorbe un mandat de 100 M€."],
    ["Or", "!0,8 %", "*7 %",
     "Seule brique dont la corrélation aux actions baisse sous stress. Une "
     "covariance pleine période efface ce comportement."],
    ["Souverain euro", "!0,0 %", "*10 %",
     "Nos hypothèses sont calées sur un seul régime. Elles ne tarifient pas la "
     "récession — seul scénario où le souverain protège."],
    ["Crypto", "0,0 %", "*2 %",
     "Décision de gouvernance arrêtée avec vous, pas une sortie "
     "d'optimisation."],
], y=2.05, widths=[2.4, 1.9, 1.3, 6.6], size=11)
quote(sl, "L'optimiseur nous a dit où nos hypothèses poussent.\n"
          "Notre travail était de décider ce que nos hypothèses ne "
          "pouvaient pas voir.", y=5.35)

sl = slide("Le portefeuille modèle")
chart(sl, "allocation", x=1.7, y=1.85, w=9.9)
callout(sl, "Effet des contraintes : l'instabilité moyenne des poids entre "
            "tirages passe de 3,8 % à 2,3 %. Le portefeuille contraint est "
            "plus prudent ET plus reproductible.", y=6.35)

sl = slide("Votre poche de liquidité",
           "10 M€ à dépenser sous deux ans. Ce n'est pas « du cash », c'est un "
           "engagement daté.")
table(sl, ["Paramètre", "Décision", "Pourquoi"], [
    ["Devise", "*Euro, intégralement",
     "C'est la devise dans laquelle vous allez dépenser. Ajouter du risque de "
     "change pour gagner quelques dixièmes de point serait la définition même "
     "de la mauvaise prise de risque."],
    ["Duration", "6 à 12 mois",
     "Adossée à votre calendrier de décaissement, pas à une vue de marché"],
    ["Support", "5 % monétaire + 5 % souverain court, échelonné",
     "Le monétaire sert de tampon, les obligations courtes portent le "
     "rendement"],
    ["Rendement attendu", "≈ 2,2 %", "Proche du taux monétaire euro"],
], y=2.1, widths=[2.2, 3.4, 6.6], size=11.5)
bullets(sl, [
    ("Une décision que nous n'avons pas confiée à l'optimiseur.",
     "Il y plaçait 100 % de monétaire — économiquement juste, puisqu'à "
     "rendement voisin 0,4 % de volatilité domine 1,6 %. Mais il raisonne en "
     "risque, pas en adossement. Si vos dates de dépense sont incertaines, le "
     "tout-monétaire redevient préférable : dites-le nous."),
], y=5.0)
callout(sl, "La devise de la poche de liquidité est celle de la dépense, "
            "jamais celle de l'opportunité.", y=6.45)

sl = slide("Votre inquiétude sur l'euro et sur le dollar")
table(sl, ["Classe d'actifs", "Couverture", "Pourquoi"], [
    ["Obligations internationales", "*100 %",
     "La volatilité de change (8-10 %) écraserait celle de l'obligation "
     "(4-5 %). Non couvert, l'actif défensif devient l'actif le plus risqué "
     "du portefeuille."],
    ["Actions internationales", "*30-50 %",
     "Le dollar s'apprécie quand les marchés paniquent. Le laisser "
     "partiellement nu, c'est une assurance gratuite contre les krachs."],
    ["Or", "*0 %",
     "Le couvrir annulerait sa fonction de réserve de valeur."],
    ["Actions émergentes", "*0 %",
     "Couverture coûteuse, et la devise participe au moteur de performance."],
], y=2.1, widths=[2.8, 1.6, 7.8], size=11.5)
quote(sl, "Vous nous avez dit être inquiet sur l'Europe ET sur les "
          "États-Unis.\n"
          "Cette remarque élimine la réponse paresseuse.\n\n"
          "Notre réponse n'est pas de choisir une devise contre l'autre — "
          "c'est\n"
          "de ne dépendre d'aucune des deux : franc suisse, yen, or, actifs "
          "réels.", y=4.5)

sl = slide("La crypto — notre réponse à votre fils",
           "Ce n'est pas une question d'allocation, c'est une question de "
           "gouvernance.")
bullets(sl, [
    ("Premièrement, le constat factuel.",
     "Le bitcoin a une volatilité d'environ 60 %, quatre fois celle des "
     "actions. Ses baisses historiques dépassent 70 %. Et en 2022, quand vous "
     "aviez besoin d'un actif décorrélé, il a chuté davantage que les actions. "
     "L'argument « or numérique » n'a pas résisté à son premier vrai test."),
    ("Deuxièmement, ce que votre contrainte impose.",
     "Nous l'avons chiffré sur votre portefeuille : une ligne de 2 % ajoute "
     "0,7 point à votre perte maximale ; à 5 %, elle en ajoute 1,6. La réponse "
     "à « combien » n'est donc pas une opinion sur la crypto — elle est "
     "déterminée par votre contrainte de risque."),
    ("Troisièmement, notre recommandation.",
     "Une enveloppe plafonnée à 2 %, logée dans la poche transmise à vos "
     "enfants — celle dont l'horizon est le plus long. Avec une règle écrite : "
     "jamais de renforcement après une hausse, et un rééquilibrage automatique "
     "qui prend les profits au-delà du plafond."),
], y=2.1)
callout(sl, "Cette réponse donne raison à votre fils sur le fond et à vous sur "
            "la prudence. Elle transforme un désaccord familial en règle "
            "écrite.", y=6.35)

# ---------------------------------------------------------------- 5
section("Risque et performance", "SECTION 5", [
    "Ce que vous auriez vécu dans les crises qui ont eu lieu",
    "La distribution complète des pertes",
    "Le comportement de la stratégie sur 21,8 ans"])

sl = slide("Les crises qui ont eu lieu",
           "Deux des quatre auraient dépassé votre contrainte de 15 %.")
chart(sl, "crises", x=1.15, y=2.0, w=11)
callout(sl, "2022 est moins profond que le COVID mais trois fois plus long à "
            "récupérer : en 2020 il y a eu un sauvetage monétaire, en 2022 la "
            "cause était la fin de ce sauvetage.", y=6.15, h=1.0)

sl = slide("Un client ne vit pas la profondeur d'une perte, il vit sa durée")
kpis(sl, [("En perte latente", "84,2 %", "du temps"),
          ("À plus de 10 %", "6,1 %", "du temps"),
          ("À plus de 15 %", "3,1 %", "du temps"),
          ("Épisode le plus long", "27,6", "mois sous l'eau")])
quote(sl, "Votre portefeuille passera 84 % du temps en dessous de son plus "
          "haut.\n"
          "C'est normal : c'est le cas de tout portefeuille investi.\n\n"
          "Ce qui compte n'est pas d'être sous l'eau, c'est de savoir à quelle\n"
          "profondeur et pour combien de temps.", y=4.3)

sl = slide("La distribution complète des pertes",
           "5 438 fenêtres de 12 mois observées sur 21,8 ans.")
chart(sl, "distribution", x=1.7, y=1.95, w=9.9)
callout(sl, "Probabilité de dépasser 15 % : 9,1 %, pour une tolérance de 10 %. "
            "La contrainte est respectée — sans marge confortable.", y=6.3)

sl = slide("Le comportement de la stratégie sur 21,8 ans",
           "Net de 0,85 % de frais et de fiscalité annuels.")
chart(sl, "backtest", x=1.0, y=2.0, w=11.3)
bullets(sl, [
    ("Le 60/40 rend 0,60 % de plus, avec 6 points de perte maximale en plus.",
     "Le Sharpe est identique. Le Calmar — rendement par unité de perte "
     "maximale — est légèrement meilleur pour notre stratégie. C'est la bonne "
     "mesure ici : votre contrainte est une perte, pas une volatilité."),
], y=5.35)
callout(sl, "Réserve : ce backtest couvre la fin d'un marché obligataire "
            "haussier de quarante ans, qui flatte le 60/40. Nos hypothèses "
            "disent que ce moteur est éteint.", y=6.55, color=RED)

sl = slide("Votre benchmark",
           "Il ne se choisit pas, il se déduit de l'allocation.")
chart(sl, "benchmark", x=1.9, y=1.9, w=9.5)
callout(sl, "Ses poids étant ceux de votre allocation, l'écart stratégique est "
            "nul par construction. Ce qu'il mesure, c'est notre exécution — "
            "et c'est bien ce que vous devez pouvoir juger.", y=6.35, h=1.0)

# ---------------------------------------------------------------- 6
section("Fiscalité et transmission", "SECTION 6", [
    "La friction annuelle, et où elle se trouve vraiment",
    "Ce qui arrive réellement à vos enfants",
    "Pourquoi ce dossier a une date limite"])

sl = slide("La friction fiscale annuelle",
           "Reconstruite à partir des rendements courants, de la rotation de "
           "rebalancement et du taux applicable — pas estimée à vue de nez.")
table(sl, ["Régime", "Friction annuelle", "Rendement brut requis", "Écart"], [
    ["Assurance-vie luxembourgeoise", "*0,25 %", "*4,80 %", "référence"],
    ["Compte-titres, supports capitalisants", "0,63 %", "5,18 %", "+38 pb"],
    ["Compte-titres, supports distribuants", "!1,23 %", "!5,78 %", "!+98 pb"],
], y=2.15, widths=[4.4, 2.4, 2.8, 2.6], size=12.5)
bullets(sl, [
    ("Soyons précis, c'est un endroit où notre profession raconte n'importe quoi.",
     "Entre une structure optimisée et un compte-titres CORRECTEMENT GÉRÉ, "
     "l'écart annuel est de 38 points de base. C'est réel, ce n'est pas "
     "spectaculaire. Si quelqu'un vous promet des points entiers de "
     "performance grâce à l'enveloppe, demandez-lui le calcul."),
    ("En revanche, l'absence de soin coûte 98 points de base par an.",
     "Des fonds qui distribuent des dividendes taxés chaque année au lieu de "
     "les réinvestir. Même actif, même performance brute : l'écart est du pur "
     "gaspillage, et il est gratuit à corriger."),
], y=4.1)
callout(sl, "Le vrai sujet fiscal n'est pas annuel, il est successoral. "
            "C'est la slide suivante.", y=6.45)

sl = slide("Ce qui arrive réellement à vos enfants",
           "Assiette 90 M€, horizon 25 ans, deux enfants.")
chart(sl, "transmission", x=3.47, y=1.88, w=6.4)
table(sl, ["Stratégie", "Brut", "Impôt", "Net aux enfants", "Taux effectif"], [
    ["Aucune structuration", "290 M€", "!130 M€", "160 M€", "!44,8 %"],
    ["*Recommandée — 30 % AV, 40 % nue-propriété, 30 % CTO", "*264 M€",
     "*62 M€", "*210 M€", "*22,7 %"],
    ["Maximale — 30 / 60 / 10", "251 M€", "38 M€", "225 M€", "14,4 %"],
], y=5.45, widths=[5.4, 1.7, 1.7, 2.1, 1.9], size=11.5)

sl = slide("Le patrimoine brut est le mauvais indicateur")
kpis(sl, [("Sans structuration", "160 M€", "net aux enfants"),
          ("Avec structuration", "210 M€", "net aux enfants"),
          ("Gain", "+50 M€", "soit +31 %"),
          ("Taux effectif", "22,7 %", "contre 44,8 % sans")])
quote(sl, "Regardez les deux patrimoines BRUTS : 290 millions sans "
          "structuration,\n"
          "264 avec. Le scénario structuré est plus pauvre — parce que les "
          "droits\n"
          "de donation sont payés dès le départ.\n\n"
          "Et pourtant il transmet 50 millions de plus à vos enfants.\n\n"
          "C'est la démonstration que nous ne mesurons pas la bonne chose "
          "quand\n"
          "nous regardons la valeur du portefeuille.", y=4.15)

sl = slide("La hiérarchie des leviers",
           "Ce que chaque décision rapporte à vos enfants sur 25 ans.")
chart(sl, "leviers", x=2.35, y=1.95, w=8.6)
callout(sl, "La structuration pèse NEUF FOIS le gain de toute l'optimisation "
            "d'allocation. Nous avons passé l'essentiel du temps sur le "
            "portefeuille ; l'essentiel de la valeur est ailleurs.", y=6.3,
        h=1.0)

sl = slide("Pourquoi ce dossier a une date limite",
           "Barème de l'article 669 du Code général des impôts.")
chart(sl, "anniversaire", x=2.0, y=1.9, w=9.3)
callout(sl, "Une donation en nue-propriété réalisée avant votre prochain "
            "anniversaire coûte 1,6 M€ de droits en moins. Sur la totalité du "
            "patrimoine, l'écart atteint 4,5 M€.", y=6.35, color=RED, h=1.0)

sl = slide("Le mécanisme, en clair")
quote(sl, "La pleine propriété d'un actif se décompose en deux droits :\n"
          "l'usufruit — le droit d'en percevoir les revenus — et la "
          "nue-propriété.\n\n"
          "Vous pouvez donner la nue-propriété à vos enfants en conservant\n"
          "l'usufruit : vous continuez de percevoir les revenus, votre train "
          "de vie\n"
          "ne change pas.\n\n"
          "L'intérêt est double. La base taxable n'est pas 100 % de l'actif "
          "mais\n"
          "la seule nue-propriété — 50 % à 60 ans. Et surtout : toute\n"
          "l'appréciation future appartient DÉJÀ à vos enfants.\n\n"
          "À votre décès, l'usufruit s'éteint. Sans aucun droit.", y=2.05)

sl = slide("Pourquoi nous ne recommandons pas la stratégie maximale",
           "Elle transmet 15 M€ de plus. Nous ne la retenons pas pour autant.")
bullets(sl, [
    ("Elle donne la nue-propriété de 60 % de votre patrimoine dès aujourd'hui.",
     "Vous conservez les revenus. Vous perdez le contrôle : vous ne pouvez "
     "plus arbitrer librement ce capital, ni le nantir, ni changer d'avis."),
    ("À 60 ans, avec deux enfants dont la maturité patrimoniale reste à "
     "observer, c'est une décision irréversible.",
     "Le gain fiscal seul ne la justifie pas. Nous préférons vous poser la "
     "question plutôt que la trancher à votre place."),
    ("Notre recommandation reste modulable.",
     "Le dispositif se construit par étapes : une première donation "
     "maintenant, une seconde au renouvellement des abattements dans quinze "
     "ans, selon ce que vous aurez observé entre-temps."),
], y=2.15)
callout(sl, "Nous vous proposons une stratégie, pas une porte qui se referme.",
        y=6.2)

# ---------------------------------------------------------------- 7
section("Mise en œuvre", "SECTION 7", [
    "Comment le portefeuille se pilote au quotidien",
    "Ce qui reste à valider avant signature",
    "Le calendrier"])

sl = slide("La gouvernance")
table(sl, ["Fréquence", "Objet"], [
    ["Mensuelle", "Reporting — performance, risque, suivi de la perte "
     "maximale face à votre contrainte de 15 %"],
    ["Trimestrielle", "Revue tactique, respect des bandes de ± 3 points, "
     "rebalancement si nécessaire"],
    ["Annuelle", "Révision du mandat, des hypothèses de marché, et du "
     "calendrier de transmission"],
    ["*Déclenchée", "*Si la perte atteint 10 % — deux tiers de votre budget de "
     "risque — nous vous appelons, que vous le demandiez ou non, avec un plan"],
], y=2.1, widths=[2.2, 10], size=12.5)
bullets(sl, [
    ("Rebalancement par bandes, pas par calendrier.",
     "Tant qu'une classe reste à plus ou moins trois points de sa cible, nous "
     "ne touchons à rien. Au-delà, nous ramenons à la cible. L'avantage : cela "
     "nous force mécaniquement à vendre ce qui a beaucoup monté et à acheter "
     "ce qui a baissé — la discipline que l'émotion rend difficile. Et cela "
     "réduit les frais et l'impôt par rapport à un rebalancement trimestriel "
     "systématique."),
], y=4.4)
callout(sl, "Nous ne vous appellerons pas seulement pour les bonnes nouvelles.",
        y=6.3)

sl = slide("Ce qui reste à valider avant signature",
           "Nous préférons vous montrer nos zones d'incertitude plutôt que de "
           "les taire.")
table(sl, ["Sujet", "Ce qui reste à faire", "Qui"], [
    ["Barème de l'article 669", "Confirmer les tranches d'âge et leur "
     "application à votre situation matrimoniale", "Votre notaire"],
    ["Régime matrimonial et conjoint", "Les droits du conjoint survivant "
     "réduisent la part des enfants — non modélisé ici", "Votre notaire"],
    ["Coût du filtre ESG", "Le mesurer sur les fiches officielles des indices, "
     "et non sur des prix d'ETF", "Nous"],
    ["Brique « suivi de tendance »", "Elle n'existe pas en ETF UCITS : soit on "
     "la retire, soit elle passe par un fonds logé dans le contrat", "Nous"],
    ["Calendrier de décaissement", "La ventilation exacte de vos 10 M€ sur "
     "deux ans, pour caler l'échelonnement", "Vous"],
    ["Préférence ESG", "ESG Screened, ou démarche plus large de type SRI ?",
     "Vous"],
], y=2.1, widths=[3, 7.2, 2], size=11.5)

sl = slide("En résumé")
kpis(sl, [("Rendement attendu", "5,79 %", "contre 4,80 % requis"),
          ("Perte P90", "13,8 %", "contrainte 15 %"),
          ("Croissance", "45 %", "des actifs"),
          ("Transmis en plus", "+50 M€", "à vos enfants")])
bullets(sl, [
    ("Votre objectif est atteignable, avec environ un point de marge annuelle "
     "— et il le reste dans les deux régimes d'inflation.",
     "Vous ne dépendez pas du fait que nous ayons raison sur l'inflation."),
    ("Mais à ce niveau de risque, une crise comme 2008 dépasserait votre "
     "contrainte.",
     "Nous vous le disons au moment où vous décidez, plutôt que le jour où "
     "cela se produit."),
    ("Et l'essentiel de la valeur n'est pas dans le portefeuille.",
     "Elle est dans la structuration de votre transmission — neuf fois le gain "
     "de toute l'optimisation d'allocation. C'est par là que nous aurions dû "
     "commencer, et c'est par là que nous vous proposons de commencer."),
], y=4.25)
callout(sl, "La plupart de nos concurrents vous parleront d'abord de fonds. "
            "Nous vous avons parlé d'abord de votre contrainte et de vos "
            "enfants.", y=6.65)

if APP_URL:
    sl = slide("L'outil est à votre disposition",
               "Tous les chiffres de cette présentation sont recalculables en "
               "direct.")
    table(sl, ["Onglet", "Ce que vous pouvez y faire"], [
        ["*Faisabilité", "*Faire varier l'inflation, nos frais, l'enveloppe "
         "fiscale — et voir immédiatement si votre objectif reste atteint"],
        ["*Transmission", "*Faire varier votre âge, l'horizon, la part donnée "
         "en nue-propriété — et voir ce qui arrive à vos enfants"],
        ["Allocation", "Le portefeuille, et ce que l'optimiseur proposait avant "
         "nos contraintes"],
        ["Risque", "Les crises qui ont eu lieu, la distribution complète des "
         "pertes, le temps passé sous l'eau"],
        ["Benchmark", "La composition de votre référence et ce qu'elle mesure"],
        ["Fiscalité", "La friction annuelle par enveloppe"],
        ["Univers", "Les supports retenus, et le contrôle qualité des données"],
        ["Concepts", "Le raisonnement derrière chaque décision"],
        ["Process", "D'où vient chaque chiffre : sources, traitements, "
         "arbitrages, et les corrections que nous avons faites"],
    ], y=2.1, widths=[2.4, 9.8], size=11.5)
    from pptx.enum.shapes import MSO_SHAPE
    btn = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.4),
                              Inches(6.05), Inches(4.5), Inches(0.62))
    btn.fill.solid(); btn.fill.fore_color.rgb = ACCENT
    btn.line.fill.background(); btn.shadow.inherit = False
    tfb = btn.text_frame
    pb = tfb.paragraphs[0]; pb.alignment = PP_ALIGN.CENTER
    rb = pb.add_run(); rb.text = APP_URL.replace("https://", "")
    rb.font.size, rb.font.bold = Pt(13), True
    rb.font.color.rgb = WHITE; rb.font.name = FONT
    rb.hyperlink.address = APP_URL

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f"{len(prs.slides.__iter__.__self__._sldIdLst)} slides")
print(f"-> {OUT}")
