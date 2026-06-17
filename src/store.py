"""Stockage par utilisateur dans Firestore.

Un document par user (clé = identifiant Chat / e-mail) :
  refresh_token : str        — jeton OAuth long terme (drive.file + spreadsheets)
  nom, prenom   : str
  folder_id     : str        — dossier "Enveloppes AVISIA" dans le Drive du user
  sheets        : {CE: id, APPRENTISSAGE: id}

Auth Firestore = ADC. Sur Cloud Run, c'est le SA du service (rôle datastore.user).
⚠️ Le refresh_token est sensible : en prod, chiffrer avant écriture (clé Secret Manager)
ou s'appuyer sur le chiffrement at-rest de Firestore + IAM strict.
"""

import os
from functools import cache

from google.cloud import firestore

COLLECTION = "enveloppes_users"


@cache
def _db() -> firestore.Client:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    return firestore.Client(project=project) if project else firestore.Client()


def _doc(user_id: str):
    return _db().collection(COLLECTION).document(user_id)


def get_user(user_id: str) -> dict | None:
    snap = _doc(user_id).get()
    return snap.to_dict() if snap.exists else None


def set_fields(user_id: str, **fields) -> None:
    """Merge des champs dans le document user (création si absent)."""
    _doc(user_id).set(fields, merge=True)


def save_refresh_token(user_id: str, refresh_token: str) -> None:
    set_fields(user_id, refresh_token=refresh_token)


def get_refresh_token(user_id: str) -> str | None:
    u = get_user(user_id)
    return u.get("refresh_token") if u else None


def get_sheets(user_id: str) -> dict:
    u = get_user(user_id)
    return (u or {}).get("sheets", {})


def set_sheet_id(user_id: str, envelope: str, sheet_id: str) -> None:
    _doc(user_id).set({"sheets": {envelope.upper(): sheet_id}}, merge=True)
