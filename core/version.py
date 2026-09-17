"""
Tampon de version, lu sans subprocess.

Raison d'etre : apres un `git push`, Streamlit Community Cloud redeploie tout
seul -- sauf quand il ne le fait pas. On a perdu du temps le 2026-09-17 a
chercher si une reecriture etait en ligne ou pas, faute de pouvoir lire la
version servie. L'application affiche desormais son propre commit.

Lecture directe des fichiers de .git : pas de `git` en sous-processus, qui
n'est pas garanti present dans le conteneur de deploiement.
"""
from __future__ import annotations

import datetime as dt
import pathlib

RACINE = pathlib.Path(__file__).resolve().parent.parent


def commit_court() -> str:
    """Les sept premiers caracteres du commit servi, ou '?' si illisible."""
    try:
        head = (RACINE / ".git" / "HEAD").read_text().strip()
        if head.startswith("ref: "):
            ref = RACINE / ".git" / head[5:]
            if ref.exists():
                return ref.read_text().strip()[:7]
            # Depot avec references empaquetees (git gc, ou clone frais).
            paquet = RACINE / ".git" / "packed-refs"
            if paquet.exists():
                cible = head[5:]
                for ligne in paquet.read_text().splitlines():
                    if ligne.endswith(" " + cible):
                        return ligne.split()[0][:7]
            return "?"
        return head[:7]                      # HEAD detachee
    except Exception:
        return "?"


def date_code() -> str:
    """Horodatage du code effectivement charge. Fonctionne meme sans .git."""
    try:
        ts = max(p.stat().st_mtime for p in RACINE.glob("*.py"))
        ts = max([ts] + [p.stat().st_mtime
                         for p in (RACINE / "tabs").glob("*.py")])
        return dt.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "?"


def tampon() -> str:
    return f"version {commit_court()} · code du {date_code()}"


if __name__ == "__main__":
    print(tampon())
