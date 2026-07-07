# syntax=docker/dockerfile:1
#
# Dockerise le point d'entrée HTTP du MCP enveloppes (auth.py, qui importe TEL QUEL le
# serveur de l'atelier 1). Se construit depuis la RACINE du mono-repo — le contexte doit
# englober à la fois atelier-1-serveur-mcp/ ET atelier-3-orchestration/ :
#
#   docker build -f atelier-3-orchestration/solution/Dockerfile -t enveloppes-mcp:solution .
#
# En pratique, utilise plutôt `docker compose` (exercice 2) qui fixe déjà ce contexte pour
# toi : voir solution/docker-compose.yml.

FROM python:3.12-slim

# ⚙️ PLOMBERIE — uv (gestionnaire de paquets), copié depuis son image officielle.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# ⚙️ PLOMBERIE — dépendances du serveur MCP enveloppes (celles de l'atelier 1 : mcp[cli],
# openpyxl, pymupdf — starlette/uvicorn viennent avec mcp[cli], pas besoin de les rajouter).
COPY atelier-1-serveur-mcp/pyproject.toml atelier-1-serveur-mcp/uv.lock ./
RUN uv sync --frozen

# ⚙️ PLOMBERIE — code du serveur MCP, fourni TEL QUEL par l'atelier 1 (solution complète,
# pas le squelette du participant — on ne dépend pas d'un exercice éventuellement incomplet).
COPY atelier-1-serveur-mcp/solution ./solution
COPY atelier-1-serveur-mcp/templates ./templates

# ⚙️ PLOMBERIE — point d'entrée HTTP + authentification de CET atelier (voir auth.py).
COPY atelier-3-orchestration/solution/auth.py ./auth.py

ENV PORT=8765
EXPOSE 8765
CMD ["uv", "run", "python", "auth.py"]
