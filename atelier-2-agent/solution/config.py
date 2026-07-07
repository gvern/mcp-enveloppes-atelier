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
    "formations": {
        "command": "uv",
        "args": ["run", "python", "mcp_formations/server.py"],
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
- les outils « formations » (list_formations, search_formations, get_formation) — un
  catalogue FICTIF de formations/certifications internes AVISIA, à but pédagogique.
  Appelle-les quand l'utilisateur cherche une formation ou une certification. Si la
  question porte aussi sur le financement, croise le `prix_ttc` de la formation avec le
  solde restant de l'enveloppe APPRENTISSAGE (get_balance("APPRENTISSAGE")) avant de
  recommander une inscription, et dis clairement si le budget suffit ou de combien il
  manque.

Règles non négociables :
- avant tout `record_expense`, demande le PRÉNOM et le NOM de l'utilisateur — ne les
  invente jamais ;
- ne mélange pas les familles d'outils dans une même intention si ce n'est pas demandé,
  sauf quand la question porte explicitement sur le financement d'une formation (auquel
  cas croiser formations + get_balance est justement attendu) ;
- termine toujours par une réponse claire et concise en français, jamais par un appel
  d'outil sans réponse finale.
"""
