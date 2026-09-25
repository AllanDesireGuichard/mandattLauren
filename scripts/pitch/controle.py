"""
Contrôle géométrique du deck généré -> rien à l'écran si tout va bien.

Lancer :  python3 scripts/pitch/controle.py [chemin.pptx]

POURQUOI. Sans LibreOffice, on ne peut pas rendre le pptx en images, et une
collision ne se voit pas dans le code : deux blocs peuvent se chevaucher
alors que chaque appel pris isolément est correct. Ce contrôle relit le
fichier produit avec python-pptx et vérifie trois choses :

  1. AUCUN CHEVAUCHEMENT entre les blocs « durs » — tableaux, images, cartes
     et formes. Les zones de texte sont exclues du contrôle deux à deux :
     elles se superposent légitimement aux cartes qui leur servent de fond.
  2. RIEN SOUS LA LIGNE DE PIED. Le pied de page (source à gauche, numéro à
     droite) est posé à y = 7,02 sur une diapositive de 7,5 de haut. Tout
     bloc qui descend en dessous de 7,0 chevauche la source.
  3. RIEN HORS CADRE, ni à droite (13,333) ni en bas (7,5).

Il a déjà trouvé deux problèmes réels invisibles autrement (slides 14 et 35
le 2026-09-17). Il est versionné depuis le 2026-09-25, parce qu'il doit être
relancé à chaque régénération du deck et qu'il avait été perdu.

LIMITE CONNUE : la hauteur d'une zone de texte est celle DÉCLARÉE, pas celle
du texte rendu. Un paragraphe trop long déborde sans être détecté ici — d'où
la relecture des notes et des textes longs à l'œil, en plus de ce contrôle.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

RACINE = Path(__file__).resolve().parents[2]
DEFAUT = RACINE / "outputs" / "Mandat_Lauren_pitch_genere.pptx"

LARGEUR, HAUTEUR = 13.333, 7.5
PIED = 7.0                      # la ligne de source et le numéro de page
MARGE = 0.02                    # tolérance : deux blocs qui se touchent vont


def po(v) -> float:
    return Emu(v).inches if v is not None else 0.0


def boite(sh) -> tuple[float, float, float, float]:
    x, y = po(sh.left), po(sh.top)
    return x, y, x + po(sh.width), y + po(sh.height)


def dur(sh) -> bool:
    """Un bloc dont le chevauchement est un vrai défaut."""
    t = str(sh.shape_type)
    if sh.has_text_frame and sh.text_frame.text.strip():
        return False            # le texte se pose légitimement sur une carte
    return "TABLE" in t or "PICTURE" in t or "AUTO_SHAPE" in t


def main() -> int:
    chemin = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAUT
    prs = Presentation(chemin)
    soucis: list[str] = []

    for n, sl in enumerate(prs.slides, 1):
        blocs = [(sh, boite(sh)) for sh in sl.shapes]

        for sh, (x1, y1, x2, y2) in blocs:
            if y2 > PIED + MARGE and po(sh.top) < PIED:
                soucis.append(f"  slide {n:2d} · descend à {y2:.2f} sous la "
                              f"ligne de pied ({PIED}) — {resume(sh)}")
            if x2 > LARGEUR + MARGE or y2 > HAUTEUR + MARGE:
                soucis.append(f"  slide {n:2d} · sort du cadre "
                              f"({x2:.2f} × {y2:.2f}) — {resume(sh)}")

        durs = [(sh, b) for sh, b in blocs if dur(sh)]
        for i, (a, ba) in enumerate(durs):
            for b, bb in durs[i + 1:]:
                if chevauche(ba, bb):
                    soucis.append(f"  slide {n:2d} · chevauchement "
                                  f"{resume(a)} / {resume(b)}")

    print(f"{chemin.name} — {len(prs.slides)} slides")
    if soucis:
        print(f"\n{len(soucis)} problème(s) :")
        print("\n".join(soucis))
        return 1
    print("géométrie : aucun chevauchement, rien sous le pied, rien hors cadre")
    return 0


def contient(a, b) -> bool:
    """a contient entièrement b — une pastille posée dans une carte."""
    return (a[0] <= b[0] + MARGE and a[1] <= b[1] + MARGE
            and a[2] >= b[2] - MARGE and a[3] >= b[3] - MARGE)


def chevauche(a, b) -> bool:
    # Une inclusion complète est un parti pris de mise en page (pastille sur
    # carte, filet dans un cartouche), pas une collision. Seul le
    # recouvrement PARTIEL est un défaut.
    if contient(a, b) or contient(b, a):
        return False
    return (a[0] < b[2] - MARGE and b[0] < a[2] - MARGE
            and a[1] < b[3] - MARGE and b[1] < a[3] - MARGE)


def resume(sh) -> str:
    x, y, x2, y2 = boite(sh)
    t = sh.text_frame.text[:28].replace("\n", " ") if sh.has_text_frame else ""
    return f"{str(sh.shape_type).split(' ')[0]} [{x:.2f},{y:.2f}→{x2:.2f},{y2:.2f}] {t}"


if __name__ == "__main__":
    raise SystemExit(main())
