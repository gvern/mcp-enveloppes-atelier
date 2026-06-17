"""Backend DEMO in-memory — mêmes signatures publiques que src/gdrive.py.

Activé par DEMO_MODE=1. Aucune dépendance Google : simule le formulaire (lignes 15→28,
total = somme des montants) en mémoire, pour tester classify / record_expense /
get_balance sans Drive ni OAuth. État perdu au redémarrage du serveur.
"""

from src.config import ENVELOPES, FORM

# état : { user_id: { "nom":.., "prenom":.., "forms": { "CE":[(desc,montant)..], .. } } }
_STATE: dict = {}
MAX_LINES = FORM["last_line_row"] - FORM["first_line_row"] + 1  # 14


def _user(user_id: str) -> dict:
    return _STATE.setdefault(user_id, {"nom": "", "prenom": "", "forms": {}})


def setup_user(user_id: str, nom: str = "", prenom: str = "") -> dict:
    u = _user(user_id)
    for env in ENVELOPES:
        u["forms"].setdefault(env, [])
    if nom or prenom:
        u["nom"], u["prenom"] = nom, prenom
    return {
        "folder_id": f"demo-folder-{user_id}",
        "sheets": {env: {"id": f"demo-{env}-{user_id}"} for env in ENVELOPES},
        "demo": True,
    }


def set_identity(user_id: str, envelope: str, nom: str, prenom: str) -> None:
    u = _user(user_id)
    u["nom"], u["prenom"] = nom, prenom


def add_invoice_line(user_id: str, envelope: str, descriptif: str, montant: float) -> int:
    u = _user(user_id)
    lines = u["forms"].setdefault(envelope.upper(), [])
    if len(lines) >= MAX_LINES:
        raise RuntimeError(f"Formulaire {envelope} plein (14 lignes max)")
    lines.append((descriptif, float(montant)))
    return FORM["first_line_row"] + len(lines) - 1


def balance(user_id: str, envelope: str) -> dict:
    env = ENVELOPES[envelope.upper()]
    lines = _user(user_id)["forms"].get(envelope.upper(), [])
    engaged = sum(m for _, m in lines)
    rate, cap = env["reimbursement_rate"], env["cap_reimbursed"]
    reimbursed = engaged * rate
    remaining = max(0.0, cap - reimbursed)
    return {
        "envelope": envelope.upper(),
        "engaged": round(engaged, 2),
        "reimbursed": round(reimbursed, 2),
        "rate": rate,
        "cap_reimbursed": cap,
        "remaining_reimbursed": round(remaining, 2),
        "remaining_engageable": round(remaining / rate, 2) if rate else 0.0,
        "demo": True,
    }
