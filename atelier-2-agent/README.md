# Agent AVISIA — atelier de découverte

Un **agent** 100 % local qui pilote un ou plusieurs serveurs **MCP** via le tool-calling de
l'API Anthropic : tu lui parles en langage naturel, il décide **quel outil appeler, quand,
avec quels arguments**, exécute la boucle jusqu'à une réponse finale. Cible principale : le
serveur MCP de l'**atelier 1** (enveloppes AVISIA), plus un mini MCP météo **fictif** fourni
pour illustrer la gestion de plusieurs outils.

> Un **agent**, ce n'est pas le MCP : le MCP **expose** des capacités, l'agent **décide** et
> **enchaîne** les appels. Ici, l'agent est un client MCP (SDK officiel `mcp`) + une boucle
> de tool-calling Anthropic (SDK officiel `anthropic`). Rien d'autre.

## 🎓 Tu viens pour l'atelier ?

**→ Suis [`ATELIER.md`](ATELIER.md).** Tu construiras toi-même l'agent en complétant le
squelette `atelier/`, sans installer quoi que ce soit d'autre que `uv sync`.

Toutes les commandes ci-dessous se lancent **depuis ce dossier** (`atelier-2-agent/`) :

```bash
uv sync                       # mcp, anthropic
export ANTHROPIC_API_KEY=...  # ta clé (jamais dans le code, jamais commit)
uv run python check.py        # pré-vol : deps, clé API, MCP atelier 1 accessible
```

## Enchaînement avec l'atelier 1

Cet atelier **réutilise tel quel** le serveur MCP de
[`atelier-1-serveur-mcp/`](../atelier-1-serveur-mcp/) — précisément
`atelier-1-serveur-mcp/solution/server.py` (la version de référence, pas le squelette du
participant, pour ne pas dépendre d'un exercice éventuellement incomplet). Il doit donc
être **présent à côté de ce dossier** (`uv sync` déjà lancé dedans). Si ta disposition de
fichiers diffère, redéfinis `ATELIER1_DIR` en variable d'environnement.

## Structure du dépôt

| Dossier / fichier | Rôle |
| --- | --- |
| `atelier/` | **squelette à compléter** — tu n'écris que du métier (`# TODO`) |
| `solution/` | la version **complète et fonctionnelle** (référence / dépannage) |
| `mcp_meteo/` | mini MCP **fictif** fourni (données mockées) — 2ᵉ outil de l'exercice 4 |
| `check.py` | pré-vol : dépendances, clé API, MCP atelier 1 accessible |

`config.py` (modèle, chemins des MCP) = **plomberie fournie**, identique dans les deux
dossiers, sauf le `SYSTEM_PROMPT` et la liste `MCP_SERVERS` (le métier de l'atelier).

## La boucle agentique

```
utilisateur ──▶ agent.run(message)
                    │
                    ▼
        Anthropic.messages.create(tools=…)
                    │
        stop_reason == "tool_use" ? ──non──▶ réponse finale
                    │ oui
                    ▼
      pour chaque tool_use : agent._call_tool(name, args)
      → routé vers le BON serveur MCP (tool_to_server)
                    │
        résultats renvoyés au modèle (tool_result)
                    │
                    └──────────────▶ (retour en haut de boucle)
```

Chaque MCP (`config.MCP_SERVERS`) est lancé comme un **sous-processus stdio** par l'agent —
exactement le protocole vu côté serveur en atelier 1, mais ici côté **client**.

## Les deux MCP pilotés

| MCP | Outils | Données |
| --- | --- | --- |
| **enveloppes** (atelier 1) | `list_envelopes`, `list_factures_a_classer`, `read_invoice`, `record_expense`, `get_balance` | réel (local, `.xlsx`) |
| **meteo** (`mcp_meteo/`) | `get_meteo` | **100 % fictif / mocké**, aucun appel réseau |

> ⚠️ Aucune donnée réelle AVISIA n'est utilisée nulle part dans cet atelier. Le MCP météo
> est un jeu de données inventé (4 villes), fourni uniquement pour illustrer la gestion de
> plusieurs outils côté agent.

## Où est la clé API

`ANTHROPIC_API_KEY` est lue **uniquement** depuis la variable d'environnement (SDK
`anthropic`, lecture automatique). Elle n'apparaît **jamais** dans le code, n'est **jamais**
affichée par `check.py`, et ne doit **jamais** être committée.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Prérequis

- **[uv](https://docs.astral.sh/uv/)** — gère Python + dépendances.
- **Python ≥ 3.12** — installé par `uv` au besoin.
- **Une clé API Anthropic** — pour les exercices 3, 4 et la démo finale (les exercices 1,
  2 et 4a n'en ont pas besoin).
- **`atelier-1-serveur-mcp/` déjà prêt** (`uv sync` lancé dedans) — voir plus haut.
