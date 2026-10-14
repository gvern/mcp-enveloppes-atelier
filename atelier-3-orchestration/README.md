# Orchestration & déploiement — atelier de découverte

Un MCP en local (stdio) ne parle qu'à **une seule machine**. Ici, tu le fais sortir de ta
machine : **dockerisation**, **authentification**, **déploiement cloud**, et **connexion
depuis un client distant**. On ne parle PAS de système multi-agents (effleuré en atelier 2) —
« orchestration » veut dire ici l'architecture et la mise en production d'un outil agentique.

> Cet atelier est **autosuffisant** : tu n'as PAS besoin d'avoir suivi l'atelier 1 ou
> l'atelier 2. Il réutilise le serveur MCP de l'atelier 1 uniquement comme **objet à
> déployer**, fourni tel quel (`atelier-1-serveur-mcp/solution/`) — tu n'as ni à le
> comprendre en détail, ni à l'avoir construit toi-même.

## 🎓 Tu viens pour l'atelier ?

**→ Suis [`ATELIER.md`](ATELIER.md).** Tu compléteras `atelier/Dockerfile` et
`atelier/auth.py` ; `atelier/docker-compose.yml` est déjà prêt.

Toutes les commandes ci-dessous se lancent **depuis ce dossier** (`atelier-3-orchestration/`) :

```bash
uv sync                       # mcp, starlette, uvicorn (pour tester en local hors Docker)
uv run python check.py        # pré-vol : deps, fichiers, Docker/gcloud (soft-check)
```

## Ce qui est réutilisé de l'atelier 1

Le Dockerfile copie `atelier-1-serveur-mcp/solution/` (le serveur MCP complet) et
`atelier-1-serveur-mcp/templates/` **tels quels**, sans les modifier. Il doit donc être
**présent à côté de ce dossier** (mono-repo) — s'il n'a jamais été synchronisé :

```bash
cd ../atelier-1-serveur-mcp && uv sync && cd -
```

Aucun exercice de l'atelier 1 n'est requis : seul le fichier `solution/server.py` compte ici,
comme une boîte noire qu'on déploie.

## Structure du dépôt

| Dossier / fichier | Rôle |
| --- | --- |
| `atelier/` | **squelette à compléter** — `Dockerfile` (TODO 1) et `auth.py` (TODO 3) |
| `solution/` | la version **complète et fonctionnelle** (référence / dépannage) |
| `check.py` | pré-vol : dépendances, fichiers de l'atelier 1, Docker/gcloud (informatif) |

`docker-compose.yml` (build + lancement) est **plomberie fournie**, identique dans les deux
dossiers.

## Le chemin parcouru

```
stdio (atelier 1)  ──▶  HTTP local (Docker)  ──▶  HTTP + clé API  ──▶  déployé (Cloud Run)
                          exercice 1-2             exercice 3           exercice 4
                                                                              │
                                                                              ▼
                                                          client distant (exercice 5) :
                                                          URL HTTPS + en-tête X-API-Key
```

`auth.py` est le point d'entrée HTTP de cet atelier : il importe le serveur de l'atelier 1
**sans le modifier**, force l'écoute sur `0.0.0.0` (indispensable en conteneur — `127.0.0.1`
n'y est visible que depuis l'intérieur), et ajoute la couche d'authentification.

## Sécurité

- Aucune donnée réelle AVISIA : les factures/enveloppes viennent des templates fictifs de
  l'atelier 1.
- Aucune vraie clé/credential dans le repo : `MCP_API_KEY` (auth du MCP) et les
  identifiants cloud (`$PROJECT_ID`, `$REGION`, etc.) sont **toujours** des variables
  d'environnement ou des placeholders explicites, jamais des valeurs en dur.
- L'authentification est **fail-closed** : sans `MCP_API_KEY` définie côté serveur, toutes
  les requêtes sont rejetées (401), jamais laissées passer par défaut.

## Prérequis

- **[uv](https://docs.astral.sh/uv/)** — gère Python + dépendances.
- **Python ≥ 3.12** — installé par `uv` au besoin.
- **Docker** (Desktop ou Engine) — pour les exercices 1 à 3 en autonomie. Absent ? `check.py`
  le signale sans bloquer : tu peux lire/coder tout le TODO, la vérification `docker build`
  sera faite en binôme ou par l'animateur.
  Docker doit être **démarré** (pas seulement installé) : `docker info` doit répondre.
  Prévoir un premier build sur le réseau de la salle (téléchargement de `python:3.12-slim` et
  des dépendances, ~3 min au premier passage).
- **Node.js** (fournit `npx`) et **Claude Desktop** — optionnels, uniquement pour
  l'exercice 5 (connecter Claude Desktop à un MCP HTTP via le pont `mcp-remote`). Sans eux, suis
  l'exercice 5 avec le client Python.
- **gcloud CLI** — optionnel, uniquement pour suivre l'exercice 4 en détail (fait **en démo**
  par l'animateur, pas en autonomie).
- **`atelier-1-serveur-mcp/` déjà prêt** (`uv sync` lancé dedans) — voir plus haut.
