"""Point d'entrée HTTP du MCP enveloppes, avec authentification par clé API (SOLUTION).

Ce script ne modifie PAS le serveur de l'atelier 1 (solution/server.py, copié TEL QUEL dans
l'image Docker — voir Dockerfile) : il l'importe, récupère son application ASGI Streamable
HTTP, et l'enveloppe dans un middleware qui exige une clé API sur chaque requête.

Il pilote aussi l'adresse d'écoute (0.0.0.0, pas 127.0.0.1 — la valeur par défaut du serveur
de l'atelier 1) : c'est indispensable pour qu'un port Docker mappé (`-p 8765:8765`) soit
joignable depuis l'extérieur du conteneur. 127.0.0.1 à l'intérieur d'un conteneur n'est
visible que... depuis ce même conteneur.

Lancer en local (hors Docker), depuis atelier-3-orchestration/, avec atelier-1-serveur-mcp/
déjà synchronisé (`cd ../atelier-1-serveur-mcp && uv sync`) :
  MCP_API_KEY=une-cle-secrete uv run python solution/auth.py
"""

import hmac
import os
import sys
from pathlib import Path

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

# ⚙️ PLOMBERIE — importe le serveur MCP de l'atelier 1 TEL QUEL. En Docker, le Dockerfile
# copie atelier-1-serveur-mcp/solution/ sous ./solution ; en local, ATELIER1_DIR pointe vers
# le dossier voisin. On ajoute son dossier à sys.path pour que ses imports internes
# (`import config`, `import invoice`, `import local_xlsx`) fonctionnent comme un lancement
# direct (`python solution/server.py`), sans dupliquer ni modifier le fichier.
_HERE = Path(__file__).resolve().parent
_LOCAL_SOLUTION = _HERE / "solution"  # présent dans l'image Docker
if _LOCAL_SOLUTION.is_dir():
    SOLUTION_DIR = _LOCAL_SOLUTION
else:
    ATELIER1_DIR = Path(os.environ.get(
        "ATELIER1_DIR", str(_HERE.parent.parent / "atelier-1-serveur-mcp")
    )).resolve()
    SOLUTION_DIR = ATELIER1_DIR / "solution"
sys.path.insert(0, str(SOLUTION_DIR))
import server as mcp_server  # noqa: E402  (le serveur MCP enveloppes, importé tel quel)

# ⚙️ PLOMBERIE — Docker impose d'écouter sur 0.0.0.0 : on pilote ça ici plutôt que de
# modifier le fichier de l'atelier 1 (qui reste utilisable seul, en stdio, tel quel).
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))
mcp_server.mcp.settings.host = HOST
mcp_server.mcp.settings.port = PORT
# ⚙️ PLOMBERIE — le SDK MCP n'autorise par défaut que le Host `localhost`/`127.0.0.1` (protection
# DNS-rebinding, activée à la construction du serveur car l'atelier 1 écoute sur 127.0.0.1).
# Derrière Cloud Run, le Host est `*.run.app` → sans cette ligne : « 421 Invalid Host header ».
# Cette protection vise les serveurs locaux SANS authentification ; ici, la clé API est exigée.
mcp_server.mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False
)

mcp_app = mcp_server.mcp.streamable_http_app()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Exige un en-tête `X-API-Key` valide sur CHAQUE requête vers le MCP.

    Fail-closed par conception : si MCP_API_KEY n'est pas définie côté serveur, AUCUNE
    requête ne passe (on ne désactive jamais l'auth silencieusement).
    """

    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("MCP_API_KEY", "")
        provided = request.headers.get("X-API-Key", "")
        if not expected or not hmac.compare_digest(provided, expected):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


mcp_app.add_middleware(APIKeyMiddleware)


if __name__ == "__main__":
    if not os.environ.get("MCP_API_KEY"):
        print("⚠️  MCP_API_KEY n'est pas définie : TOUTES les requêtes seront rejetées "
              "(401) — c'est voulu (fail-closed), pas un bug. Définis-la avant de démarrer : "
              "MCP_API_KEY=une-cle-secrete (jamais une vraie valeur en dur dans le code).")
    print(f"🔐 MCP enveloppes (HTTP + clé API) sur http://{HOST}:{PORT}/mcp")
    uvicorn.run(mcp_app, host=HOST, port=PORT)
