"""Lecture d'une facture PDF sur disque → TEXTE exploitable par le LLM.

⚙️  PLOMBERIE — ne pas toucher pendant l'atelier.

Pourquoi du texte et pas une image ? Un tool-result *image* n'est pas réinjecté de façon
fiable dans la vision du modèle par Claude Desktop (il affiche seulement `[image]`). On
extrait donc la couche texte du PDF côté serveur, avec PyMuPDF — **zéro dépendance
système**. Un PDF scanné (sans couche texte) renvoie un message clair (hors périmètre).
"""

from pathlib import Path

import fitz  # PyMuPDF

_MIN_TEXT = 20  # en dessous → pas de vraie couche texte (PDF scanné)


def read(path: str) -> dict:
    """Renvoie {path, filename, pages, text} pour une facture PDF (couche texte)."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    if p.suffix.lower() != ".pdf":
        raise ValueError(f"Format non supporté : {p.suffix or '?'} — dépose un PDF numérique.")
    doc = fitz.open(p)
    text = "\n".join(page.get_text() for page in doc).strip()
    if len(text) < _MIN_TEXT:
        raise ValueError(
            f"{p.name} : aucune couche texte (PDF scanné ?). L'atelier attend un PDF numérique."
        )
    return {"path": str(p), "filename": p.name, "pages": doc.page_count, "text": text}
