"""MCP server — Enveloppes AVISIA (version atelier, 100 % locale).

Aucune dépendance cloud : pas de Drive, OAuth, ni Firestore. Les formulaires NDF
(CE + Apprentissage) sont de vrais fichiers .xlsx écrits sur disque
(voir src/local_xlsx.py) — on peut les ouvrir dans Excel/LibreOffice.

Transport :
  - défaut : stdio  → à brancher dans Claude Desktop (claude_desktop_config.json)
  - MCP_HTTP=1      → Streamable HTTP sur http://localhost:$PORT/mcp (défaut 8765)

Boucle agentique type :
  setup_user -> read_invoice (le modèle lit) -> classify -> record_expense -> get_balance
"""

import base64
import os
import unicodedata

from fastmcp import FastMCP
from fastmcp.utilities.types import File, Image

from src import local_xlsx as backend
from src.config import ALIASES, ENVELOPES

mcp = FastMCP("enveloppes-avisia")


def _tokens(s: str) -> set[str]:
    """Normalise (minuscule, sans accents, séparateurs unifiés) → ensemble de mots."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    for sep in "-_/.,;:'":
        s = s.replace(sep, " ")
    return {t for t in s.split() if t}


def _tok_in(t: str, cat: set[str]) -> bool:
    """t couvert par un token de la catégorie (égalité ou préfixe ≥4 : sport↔sportive)."""
    return any(c == t or (len(t) >= 4 and len(c) >= 4 and (c.startswith(t) or t.startswith(c))) for c in cat)


def _covered(keyword: str, cat: set[str]) -> bool:
    """Tous les tokens du mot-clé sont couverts par la catégorie."""
    return all(_tok_in(t, cat) for t in _tokens(keyword))


def _match_envelope(category: str) -> list[str]:
    """Enveloppes correspondant à `category` (catégories éligibles + alias marchands).

    Tolérant aux accents/casse/séparateurs, aux mots en plus ("Abonnement salle de sport"
    → CE) et aux variantes morphologiques ("licence sportive" → 'sport'). Les alias
    mappent des marchands directement ("Claude"/"ChatGPT" → APPRENTISSAGE).
    """
    cat = _tokens(category)
    out = set()
    for key, env in ENVELOPES.items():
        if any(_covered(x, cat) for x in env["excludes"]):
            continue
        if any(_covered(e, cat) for e in env["eligible"]):
            out.add(key)
    for alias, env_key in ALIASES.items():
        if _covered(alias, cat):
            out.add(env_key)
    return sorted(out)


# ───────────────────────────── tools ─────────────────────────────


@mcp.tool
def ping(name: str = "AVISIA") -> str:
    """Tool de démo : vérifie que le MCP répond."""
    return f"MCP enveloppes en ligne — bonjour {name} !"


@mcp.tool
def list_envelopes() -> dict:
    """Les deux enveloppes : plafond remboursé (250 €), taux, catégories éligibles."""
    return {
        key: {
            "label": env["label"],
            "cap_reimbursed": env["cap_reimbursed"],
            "reimbursement_rate": env["reimbursement_rate"],
            "currency": env["currency"],
            "eligible": env["eligible"],
            "hint": env.get("hint", ""),
        }
        for key, env in ENVELOPES.items()
    }


@mcp.tool
def setup_user(user_id: str, nom: str = "", prenom: str = "") -> dict:
    """Crée (idempotent) les 2 formulaires NDF .xlsx locaux pour ce user."""
    return backend.setup_user(user_id, nom=nom, prenom=prenom)


@mcp.tool
def read_invoice(data_base64: str, mime_type: str):
    """Renvoie une facture (image/PDF, encodée base64) au modèle pour lecture.

    Le modèle connecté lit le contenu et en extrait fournisseur / date / montant /
    catégorie, puis appelle classify() et record_expense(). Le MCP ne fait pas l'OCR.
    """
    data = base64.b64decode(data_base64)
    if mime_type.startswith("image/"):
        return Image(data=data, format=mime_type.split("/", 1)[1])
    if mime_type == "application/pdf":
        return File(data=data, format="pdf")
    return File(data=data, format=mime_type.split("/")[-1] or "bin")


@mcp.tool
def classify(category: str, amount: float, user_id: str) -> dict:
    """Classe une dépense (montant ENGAGÉ) dans une enveloppe selon les règles.

    Renvoie {envelope: 'CE'|'APPRENTISSAGE'|'ambiguous', reason, reimbursed,
    remaining_reimbursed, fits}. reimbursed = amount × taux. fits = False si le
    remboursement dépasse le reste disponible (plafond 250 €).
    """
    matches = _match_envelope(category)
    if len(matches) != 1:
        reason = (
            "catégorie inconnue / non éligible"
            if not matches
            else f"catégorie éligible à plusieurs enveloppes ({', '.join(matches)})"
        )
        return {"envelope": "ambiguous", "reason": reason, "fits": False}

    envelope = matches[0]
    rate = ENVELOPES[envelope]["reimbursement_rate"]
    bal = backend.balance(user_id, envelope)
    reimbursed = round(amount * rate, 2)
    return {
        "envelope": envelope,
        "reason": f"catégorie '{category}' éligible à {envelope}",
        "reimbursed": reimbursed,
        "remaining_reimbursed": bal["remaining_reimbursed"],
        "fits": reimbursed <= bal["remaining_reimbursed"],
    }


@mcp.tool
def record_expense(
    user_id: str,
    envelope: str,
    descriptif: str,
    amount: float,
    nom: str = "",
    prenom: str = "",
) -> dict:
    """Inscrit une facture dans le formulaire .xlsx de l'enveloppe.

    Écrit descriptif + montant engagé sur la prochaine ligne libre (15→28) ; le total
    B29 (formule SUBTOTAL) reste intact. Renseigne NOM/PRÉNOM si fournis. Renvoie le
    solde. envelope : 'CE' ou 'APPRENTISSAGE'.
    """
    if nom or prenom:
        backend.set_identity(user_id, envelope, nom, prenom)
    row = backend.add_invoice_line(user_id, envelope, descriptif, amount)
    bal = backend.balance(user_id, envelope)
    bal["line_written"] = row
    return bal


@mcp.tool
def get_balance(user_id: str, envelope: str) -> dict:
    """Solde d'une enveloppe : engagé, remboursé, reste remboursable (vs 250 €)."""
    return backend.balance(user_id, envelope)


# ───────────────────────────── run ─────────────────────────────

if __name__ == "__main__":
    if os.environ.get("MCP_HTTP") == "1":
        port = int(os.environ.get("PORT", "8765"))
        mcp.run(transport="http", host="127.0.0.1", port=port)
    else:
        mcp.run()  # stdio (défaut) — pour Claude Desktop
