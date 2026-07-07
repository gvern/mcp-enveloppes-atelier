"""Configuration de l'agent — modèle Anthropic, system prompt, MCP pilotés.
   SQUELETTE D'ATELIER (à compléter).

⚙️ PLOMBERIE : chemins des MCP et nom du modèle déjà réglés — n'y touche pas. Les DEUX
TODO de ce fichier sont du pur métier : le system prompt (exercice 2) et la liste des MCP
pilotés par l'agent (exercice 4a).
"""

import os
from pathlib import Path

ATELIER_DIR = Path(__file__).resolve().parent.parent    # atelier-2-agent/
MONOREPO_ROOT = ATELIER_DIR.parent                        # racine du mono-repo

# Modèle Anthropic utilisé par l'agent (tool use). Redéfinissable via env.
MODEL = os.environ.get("AGENT_MODEL", "claude-3-5-sonnet-20241022")
MAX_TOKENS = 1024

# Dossier de l'atelier 1 (le MCP cible est réutilisé TEL QUEL, via solution/server.py).
ATELIER1_DIR = Path(os.environ.get(
    "ATELIER1_DIR", str(MONOREPO_ROOT / "atelier-1-serveur-mcp")
)).resolve()

# ════════════════════════════════════════════════════════════════════════════════
# EXERCICE 4a — connecter un DEUXIÈME MCP
#
# `connect_all()` (dans agent.py, déjà écrit — plomberie) boucle sur ce dictionnaire :
# chaque entrée devient un sous-processus MCP piloté par l'agent. Donner un nouvel outil
# à l'agent = ajouter une entrée ICI, rien à toucher côté protocole.
#
# TODO 4a — ajoute une entrée "formations" pour brancher le mini MCP catalogue formations
#           fourni (mcp_formations/server.py, dans ce dossier). Inspire-toi de l'entrée
#           "enveloppes".
# ════════════════════════════════════════════════════════════════════════════════
MCP_SERVERS = {
    "enveloppes": {
        "command": "uv",
        "args": ["run", "python", "solution/server.py"],
        "cwd": str(ATELIER1_DIR),
    },
    # TODO 4a — décommente et adapte :
    # "formations": {
    #     "command": "uv",
    #     "args": ["run", "python", "mcp_formations/server.py"],
    #     "cwd": str(ATELIER_DIR),
    # },
}

# ════════════════════════════════════════════════════════════════════════════════
# EXERCICE 2 — le system prompt de l'agent
#
# C'est le SEUL texte que le modèle lit pour savoir qui il est, QUAND utiliser QUEL
# outil, et comment se comporter. Pur métier — comme le `hint` de l'atelier 1.
#
# TODO 2 — écris le system prompt. Mentionne au moins :
#   • le rôle de l'agent (assistant notes de frais AVISIA) ;
#   • quand utiliser les outils "enveloppes" (classement de factures) ;
#   • la règle non négociable : ne jamais inventer prénom/nom.
#
# 💡 Reviens ici à l'exercice 4 pour ajouter une consigne sur les nouveaux outils formations
#    (pour éviter que l'agent l'appelle hors-sujet).
# ════════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = ""  # TODO 2
