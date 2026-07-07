"""Configuration de l'agent — modèle Anthropic, system prompt, MCP pilotés (SOLUTION).

⚙️ PLOMBERIE : chemins des MCP et nom du modèle sont déjà réglés pour que rien ne plante.
Le texte MÉTIER de cet atelier, c'est le SYSTEM_PROMPT (exercice 2) et la liste des MCP
pilotés par l'agent (exercice 4).
"""

import os
from pathlib import Path

ATELIER_DIR = Path(__file__).resolve().parent.parent    # atelier-2-agent/
MONOREPO_ROOT = ATELIER_DIR.parent                        # racine du mono-repo

# Modèle Anthropic utilisé par l'agent (tool use). Redéfinissable via env, sans toucher
# au code, si un autre modèle est disponible sur ton compte.
MODEL = os.environ.get("AGENT_MODEL", "claude-3-5-sonnet-20241022")
MAX_TOKENS = 1024

# Dossier de l'atelier 1 (le MCP cible est réutilisé TEL QUEL, via solution/server.py —
# jamais via le atelier/server.py du participant, potentiellement incomplet). Redéfinissable
# via ATELIER1_DIR si ton clone a une autre disposition.
ATELIER1_DIR = Path(os.environ.get(
    "ATELIER1_DIR", str(MONOREPO_ROOT / "atelier-1-serveur-mcp")
)).resolve()

# ── MCP pilotés par l'agent ────────────────────────────────────────────────────────
# nom logique -> {command, args, cwd}. `connect_all()` (agent.py) boucle dessus : chaque
# entrée devient un sous-processus MCP en stdio. Ajouter un outil à l'agent = ajouter une
# entrée ICI — rien à toucher côté protocole.
MCP_SERVERS = {
    "enveloppes": {
        "command": "uv",
        "args": ["run", "python", "solution/server.py"],
        "cwd": str(ATELIER1_DIR),
    },
    "meteo": {
        "command": "uv",
        "args": ["run", "python", "mcp_meteo/server.py"],
        "cwd": str(ATELIER_DIR),
    },
}

# ════════════════════════════════════════════════════════════════════════════════
# EXERCICE 2 — le system prompt de l'agent
#
# C'est le SEUL texte que le modèle lit pour savoir : qui il est, QUAND utiliser QUEL
# outil, et comment se comporter. Pur métier — comme le `hint` de l'atelier 1.
# ════════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """\
Tu es l'assistant notes de frais d'AVISIA. Tu pilotes deux familles d'outils :

- les outils « enveloppes » (list_envelopes, list_factures_a_classer, read_invoice,
  record_expense, get_balance) pour classer les factures déposées par l'utilisateur dans
  les enveloppes CE / APPRENTISSAGE ;
- l'outil météo « get_meteo » (données FICTIVES, mockées, à but pédagogique) : appelle-le
  UNIQUEMENT si l'utilisateur te parle explicitement de météo ou de conditions pour un
  déplacement. Ne l'utilise jamais pour une question de note de frais.

Règles non négociables :
- avant tout `record_expense`, demande le PRÉNOM et le NOM de l'utilisateur — ne les
  invente jamais ;
- ne mélange pas les deux familles d'outils dans une même intention si ce n'est pas
  demandé ;
- termine toujours par une réponse claire et concise en français, jamais par un appel
  d'outil sans réponse finale.
"""
