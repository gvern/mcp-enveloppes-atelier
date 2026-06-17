# Image MCP enveloppes — Python 3.12 + uv, sert le Streamable HTTP sur $PORT.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv (gestionnaire de paquets)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Dépendances d'abord (cache de build) — uv.lock pour des versions reproductibles
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code + templates NDF (uploadés/convertis dans le Drive du user)
COPY src/ ./src/
COPY templates/ ./templates/

# Cloud Run fournit $PORT (défaut 8080)
ENV PORT=8080
CMD ["uv", "run", "python", "-m", "src.server"]
