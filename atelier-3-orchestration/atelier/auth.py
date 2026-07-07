"""Point d'entrée HTTP du MCP enveloppes — SQUELETTE D'ATELIER (à compléter, exercice 3).

Exercices 1 et 2 : ce fichier fonctionne déjà TEL QUEL comme point d'entrée HTTP (import du
serveur de l'atelier 1, adresse d'écoute 0.0.0.0 pour Docker) — RIEN À CODER pour dockeriser
et vérifier le MCP en local. La clé API n'est PAS encore exigée (middleware pas branché).

Exercice 3 ⭐ (le cœur métier de cet atelier) : complète `APIKeyMiddleware.dispatch`, PUIS
décommente la ligne `mcp_app.add_middleware(...)` tout en bas pour activer l'authentification.
Si tu bloques, la version complète est dans solution/auth.py.
"""

import hmac
import os
import sys
from pathlib import Path

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# ⚙️ PLOMBERIE — importe le serveur MCP de l'atelier 1 TEL QUEL. En Docker, le Dockerfile
# copie atelier-1-serveur-mcp/solution/ sous ./solution ; en local, ATELIER1_DIR pointe vers
# le dossier voisin. On ajoute son dossier à sys.path pour que ses imports internes
# (`import config`, `import invoice`, `import local_xlsx`) fonctionnent comme un lancement
# direct (`python solution/server.py`), sans dupliquer ni modifier le fichier. Ne touche pas
# à ce bloc.
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

mcp_app = mcp_server.mcp.streamable_http_app()


# ══════════════════════════════════════════════════════════════════════════
# EXERCICE 3 ⭐ — LA COUCHE D'AUTHENTIFICATION (le cœur métier de cet atelier)
#
# Complète dispatch() :
#   1. lis la clé ATTENDUE dans la variable d'env MCP_API_KEY (jamais en dur dans le code) ;
#   2. lis la clé FOURNIE par le client dans l'en-tête `X-API-Key` de la requête
#      (`request.headers.get("X-API-Key", "")`) ;
#   3. si elles ne correspondent pas — ou si MCP_API_KEY n'est pas définie côté serveur —
#      renvoie `JSONResponse({"error": "unauthorized"}, status_code=401)`, SANS appeler
#      `call_next` (la requête ne doit JAMAIS atteindre le MCP). Utilise
#      `hmac.compare_digest(a, b)` plutôt que `a == b` pour comparer les clés (résiste aux
#      attaques par mesure de temps) ;
#   4. sinon → `return await call_next(request)`.
#
# Puis décommente la ligne `mcp_app.add_middleware(APIKeyMiddleware)` tout en bas : tant
# qu'elle reste commentée, le serveur répond SANS clé (comportement des exercices 1-2).
# ══════════════════════════════════════════════════════════════════════════
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        raise NotImplementedError("TODO 3 — vérifie X-API-Key (voir consignes ci-dessus)")


# mcp_app.add_middleware(APIKeyMiddleware)  # ← décommente une fois dispatch() complété


if __name__ == "__main__":
    if not os.environ.get("MCP_API_KEY"):
        print("ℹ️  MCP_API_KEY non définie — sans importance tant que le TODO 3 n'est pas "
              "activé (mcp_app.add_middleware(...) commenté ci-dessus).")
    print(f"🔓 MCP enveloppes (HTTP) sur http://{HOST}:{PORT}/mcp")
    uvicorn.run(mcp_app, host=HOST, port=PORT)
