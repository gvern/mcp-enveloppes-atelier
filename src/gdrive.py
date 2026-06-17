"""Opérations Drive / Sheets dans le Drive PERSONNEL du user (token OAuth drive.file).

Le service account ne touche jamais le Drive du user : tout passe par les credentials
OAuth de l'utilisateur. `setup_user` crée un dossier + uploade les templates .xlsx en
les convertissant en Google Sheets (l'app crée le fichier → drive.file peut l'éditer,
fidélité du formulaire préservée).
"""

from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src import auth, store
from src.config import ENVELOPES, FORM

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
FOLDER_NAME = "Enveloppes AVISIA 2026"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
GSHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _creds(user_id: str):
    rt = store.get_refresh_token(user_id)
    if not rt:
        raise PermissionError(f"User {user_id} non autorisé — appeler get_auth_url() d'abord")
    return auth.credentials_from_refresh_token(rt)


def _drive(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _sheets(creds):
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _ensure_folder(drive, user_id: str) -> str:
    u = store.get_user(user_id) or {}
    if u.get("folder_id"):
        return u["folder_id"]
    f = drive.files().create(
        body={"name": FOLDER_NAME, "mimeType": FOLDER_MIME}, fields="id"
    ).execute()
    store.set_fields(user_id, folder_id=f["id"])
    return f["id"]


def _upload_template(drive, envelope: str, folder_id: str) -> dict:
    path = TEMPLATES_DIR / f"{envelope}.xlsx"
    media = MediaFileUpload(str(path), mimetype=XLSX_MIME, resumable=False)
    return (
        drive.files()
        .create(
            body={
                "name": ENVELOPES[envelope]["title"],
                "parents": [folder_id],
                "mimeType": GSHEET_MIME,  # conversion xlsx -> Google Sheet
            },
            media_body=media,
            fields="id,webViewLink",
        )
        .execute()
    )


def setup_user(user_id: str, nom: str = "", prenom: str = "") -> dict:
    """Crée (si besoin) le dossier + les 2 formulaires dans le Drive du user.

    Idempotent : ne recrée pas ce qui existe déjà. Renvoie folder_id + ids/liens Sheets.
    """
    creds = _creds(user_id)
    drive = _drive(creds)
    folder_id = _ensure_folder(drive, user_id)
    existing = store.get_sheets(user_id)
    result = {"folder_id": folder_id, "sheets": {}}
    for env in ENVELOPES:
        if existing.get(env):
            result["sheets"][env] = {"id": existing[env]}
            continue
        f = _upload_template(drive, env, folder_id)
        store.set_sheet_id(user_id, env, f["id"])
        result["sheets"][env] = {"id": f["id"], "link": f.get("webViewLink", "")}
    if nom or prenom:
        for env in ENVELOPES:
            set_identity(user_id, env, nom, prenom)
        store.set_fields(user_id, nom=nom, prenom=prenom)
    return result


def _sheet_id(user_id: str, envelope: str) -> str:
    sid = store.get_sheets(user_id).get(envelope.upper())
    if not sid:
        raise RuntimeError(f"Formulaire {envelope} non créé — appeler setup_user() d'abord")
    return sid


def _set_cell(sheets, sheet_id: str, cell: str, value) -> None:
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{FORM['tab']}!{cell}",
        valueInputOption="USER_ENTERED",
        body={"values": [[value]]},
    ).execute()


def set_identity(user_id: str, envelope: str, nom: str, prenom: str) -> None:
    creds = _creds(user_id)
    sheets = _sheets(creds)
    sid = _sheet_id(user_id, envelope)
    _set_cell(sheets, sid, FORM["nom_cell"], nom)
    _set_cell(sheets, sid, FORM["prenom_cell"], prenom)


def _next_free_line(sheets, sheet_id: str) -> int | None:
    first, last, col = FORM["first_line_row"], FORM["last_line_row"], FORM["desc_col"]
    resp = (
        sheets.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=f"{FORM['tab']}!{col}{first}:{col}{last}")
        .execute()
    )
    rows = resp.get("values", [])
    for i in range(last - first + 1):
        if not (i < len(rows) and rows[i] and rows[i][0]):
            return first + i
    return None


def add_invoice_line(user_id: str, envelope: str, descriptif: str, montant: float) -> int:
    creds = _creds(user_id)
    sheets = _sheets(creds)
    sid = _sheet_id(user_id, envelope)
    row = _next_free_line(sheets, sid)
    if row is None:
        raise RuntimeError(f"Formulaire {envelope} plein (14 lignes max)")
    _set_cell(sheets, sid, f"{FORM['desc_col']}{row}", descriptif)
    _set_cell(sheets, sid, f"{FORM['amount_col']}{row}", montant)
    return row


def balance(user_id: str, envelope: str) -> dict:
    env = ENVELOPES[envelope.upper()]
    creds = _creds(user_id)
    sheets = _sheets(creds)
    sid = _sheet_id(user_id, envelope)
    resp = (
        sheets.spreadsheets()
        .values()
        .get(
            spreadsheetId=sid,
            range=f"{FORM['tab']}!{FORM['total_cell']}",
            valueRenderOption="UNFORMATTED_VALUE",
        )
        .execute()
    )
    rows = resp.get("values", [])
    engaged = 0.0
    if rows and rows[0]:
        try:
            engaged = float(rows[0][0])
        except (ValueError, TypeError):
            engaged = 0.0
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
    }
