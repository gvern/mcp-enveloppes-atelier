"""OAuth Google par utilisateur (scopes drive.file + spreadsheets).

L'app est un client OAuth (consent screen Interne → pas de vérif Google). Chaque user
consent une fois ; on stocke son refresh_token (Firestore) et on dérive des credentials
à la demande.

Variables d'environnement :
- GOOGLE_OAUTH_CLIENT_ID
- GOOGLE_OAUTH_CLIENT_SECRET
- OAUTH_REDIRECT_URI   (ex. http://localhost:8080/oauth/callback ou https://<run>/oauth/callback)
"""

import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _client_id() -> str:
    return os.environ["GOOGLE_OAUTH_CLIENT_ID"]


def _client_secret() -> str:
    return os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]


def _redirect_uri() -> str:
    return os.environ["OAUTH_REDIRECT_URI"]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": [_redirect_uri()],
        }
    }


def _flow() -> Flow:
    return Flow.from_client_config(_client_config(), scopes=SCOPES, redirect_uri=_redirect_uri())


def authorization_url(state: str) -> str:
    """URL de consentement. `state` = identifiant user (à valider au callback)."""
    url, _ = _flow().authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # force le renvoi d'un refresh_token
        state=state,
    )
    return url


def exchange_code(code: str) -> str:
    """Échange le code d'autorisation contre un refresh_token (renvoyé)."""
    flow = _flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    if not creds.refresh_token:
        raise RuntimeError("Pas de refresh_token renvoyé (déjà consenti ? forcer prompt=consent)")
    return creds.refresh_token


def credentials_from_refresh_token(refresh_token: str) -> Credentials:
    """Construit des credentials utilisables (rafraîchies) depuis un refresh_token."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=_client_id(),
        client_secret=_client_secret(),
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds
