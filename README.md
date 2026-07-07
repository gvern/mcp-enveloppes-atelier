# Parcours de certification IA — 3 ateliers

Mono-repo regroupant les **3 ateliers** du parcours de certification interne AVISIA sur les
usages IA en entreprise : construire un **serveur MCP**, l'exposer via un **agent**, puis
**orchestrer et déployer** le tout. Chaque atelier dure ~2 h et se suit dans l'ordre.

| # | Atelier | Thème | Durée | Prérequis | Dossier |
| --- | --- | --- | --- | --- | --- |
| 1 | Créer son premier MCP | Serveur MCP local (classement de factures, formulaires `.xlsx`) | 2 h | `uv` installé | [`atelier-1-serveur-mcp/`](atelier-1-serveur-mcp/README.md) |
| 2 | Créer son premier agent | Agent qui consomme le MCP de l'atelier 1 | 2 h | Atelier 1 terminé | [`atelier-2-agent/`](atelier-2-agent/README.md) |
| 3 | Orchestration & déploiement | Du MCP en local (stdio) au MCP déployé : Docker, authentification, cloud | 2 h | `uv` installé (+ Docker recommandé) | [`atelier-3-orchestration/`](atelier-3-orchestration/README.md) |

## Enchaînement des ateliers

- **Atelier 1 → Atelier 2 :** ils s'enchaînent. Le serveur MCP que tu construis en atelier 1
  (dossier `solution/` ou ton propre `atelier/` complété) sert de **brique** à l'agent que tu
  construis en atelier 2 — tu le rebrancheras tel quel.
- **Atelier 3 :** **autosuffisant** — il ne demande pas d'avoir suivi les ateliers 1 ou 2.
  Il réutilise le serveur MCP de l'atelier 1 uniquement comme **objet à déployer** (fourni
  tel quel), pour le faire passer du stdio local au HTTP authentifié et déployé.

En dehors de cet enchaînement 1→2, chaque atelier est **autosuffisant** : son propre
`README.md` et son propre guide (`ATELIER.md` ou équivalent) suffisent pour le suivre.

## Prérequis commun

- **[uv](https://docs.astral.sh/uv/)** — gère Python + dépendances pour tous les ateliers.
  Install : `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux),
  `brew install uv`, ou `pip install uv` (si Python déjà présent). Détails dans la section
  **Prérequis** de [`atelier-1-serveur-mcp/README.md`](atelier-1-serveur-mcp/README.md#prérequis).

Chaque atelier est un projet `uv` indépendant (son propre `pyproject.toml` / `uv.lock`) : les
commandes `uv sync`, `uv run ...` se lancent **depuis le dossier de l'atelier concerné**, pas
depuis la racine du mono-repo.
