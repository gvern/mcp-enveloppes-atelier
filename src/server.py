"""MCP server — Enveloppes AVISIA (modèle PROD : Drive perso par user via OAuth).

Transport : Streamable HTTP (Cloud Run). Sans état local : tokens + ids dans Firestore.
Chaque user consent une fois (drive.file + spreadsheets) ; le MCP crée et remplit ses
deux formulaires NDF (CE + Apprentissage) dans SON Drive.

Boucle agentique type :
  get_auth_url -> (user consent) -> setup_user -> read_invoice (le modèle lit) ->
  classify -> record_expense -> get_balance
"""

import base64
import os
import unicodedata

from fastmcp import FastMCP
from fastmcp.utilities.types import File, Image
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse

from src import auth, demo, gdrive, local_xlsx, store
from src.config import ALIASES, ENVELOPES

# DEMO_MODE=1   → backend in-memory (pas de Drive/OAuth), état perdu au redémarrage.
# LOCAL_XLSX=1  → backend fichiers .xlsx locaux (templates copiés, persistant sur disque).
# sinon         → backend Drive/Sheets par user via OAuth (prod).
DEMO = os.environ.get("DEMO_MODE") == "1"
LOCAL = os.environ.get("LOCAL_XLSX") == "1"
_be = local_xlsx if LOCAL else (demo if DEMO else gdrive)
NO_AUTH = DEMO or LOCAL

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
def get_auth_url(user_id: str) -> dict:
    """URL de consentement Google pour ce user (accès à son Drive, scope drive.file).

    Le user ouvre l'URL, consent une fois. Ensuite setup_user() devient possible.
    """
    if NO_AUTH:
        mode = "LOCAL_XLSX" if LOCAL else "DEMO_MODE"
        return {"authorized": True, "auth_url": None, "message": f"{mode} : pas de consentement requis"}
    authorized = store.get_refresh_token(user_id) is not None
    return {
        "authorized": authorized,
        "auth_url": None if authorized else auth.authorization_url(state=user_id),
        "message": "Déjà autorisé" if authorized else "Ouvrir auth_url pour autoriser l'accès Drive",
    }


@mcp.tool
def setup_user(user_id: str, nom: str = "", prenom: str = "") -> dict:
    """Crée (idempotent) le dossier + les 2 formulaires NDF dans le Drive du user."""
    return _be.setup_user(user_id, nom=nom, prenom=prenom)


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
    bal = _be.balance(user_id, envelope)
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
    """Inscrit une facture dans le formulaire de l'enveloppe (Drive du user).

    Écrit descriptif + montant engagé sur la prochaine ligne libre (15→28) ; le total
    B29 se recalcule. Renseigne NOM/PRÉNOM si fournis. Renvoie le solde.
    envelope : 'CE' ou 'APPRENTISSAGE'.
    """
    if nom or prenom:
        _be.set_identity(user_id, envelope, nom, prenom)
    row = _be.add_invoice_line(user_id, envelope, descriptif, amount)
    bal = _be.balance(user_id, envelope)
    bal["line_written"] = row
    return bal


@mcp.tool
def get_balance(user_id: str, envelope: str) -> dict:
    """Solde d'une enveloppe : engagé, remboursé, reste remboursable (vs 250 €)."""
    return _be.balance(user_id, envelope)


# ───────────────────────── routes HTTP ─────────────────────────


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@mcp.custom_route("/oauth/callback", methods=["GET"])
async def oauth_callback(request: Request) -> HTMLResponse:
    """Callback OAuth : échange le code, stocke le refresh_token (state = user_id)."""
    error = request.query_params.get("error")
    if error:
        return HTMLResponse(f"<h3>Autorisation refusée : {error}</h3>", status_code=400)
    code = request.query_params.get("code")
    user_id = request.query_params.get("state")
    if not code or not user_id:
        return HTMLResponse("<h3>Requête invalide (code/state manquant)</h3>", status_code=400)
    try:
        refresh_token = auth.exchange_code(code)
        store.save_refresh_token(user_id, refresh_token)
    except Exception as exc:  # noqa: BLE001
        return HTMLResponse(f"<h3>Échec de l'autorisation : {exc}</h3>", status_code=500)
    return HTMLResponse("<h3>✅ Accès autorisé. Vous pouvez retourner dans le chat.</h3>")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    mcp.run(transport="http", host="0.0.0.0", port=port)
