"""MCP server — Enveloppes AVISIA  ·  SQUELETTE D'ATELIER (à compléter).

Tu vas transformer ce fichier en vrai serveur MCP en remplissant les TODO.
RÈGLE D'OR : tu n'écris QUE du métier. La plomberie (imports, backend .xlsx, lecture PDF)
est déjà faite — n'y touche pas. Si tu bloques, la version complète est dans solution/.

────────────────────────────────────────────────────────────────────────────────────
LES 3 PRIMITIVES MCP — à chaque TODO « décorateur », pose-toi LA question : qui déclenche ?

    @mcp.tool()                    → une ACTION que le MODÈLE déclenche (Claude décide).
    @mcp.resource("xxx://yyy")     → une DONNÉE que l'UTILISATEUR attache (lecture seule).
    @mcp.prompt()                  → une PROCÉDURE que l'UTILISATEUR lance (slash-command).
────────────────────────────────────────────────────────────────────────────────────

TESTER À TOUT MOMENT :   uv run mcp dev atelier/server.py
"""

import os

from mcp.server.fastmcp import FastMCP

import config
import invoice
import local_xlsx as backend

INSTRUCTIONS = """\
Serveur des enveloppes AVISIA — notes de frais, enveloppes CE / Apprentissage (.xlsx locaux).
Quand l'utilisateur parle d'« AVISIA », des « enveloppes » ou d'une « note de frais » à classer,
c'est CE serveur qu'il faut utiliser.
L'utilisateur dépose ses factures (PDF) dans une boîte à classer ; tu traites tout le lot :
liste les factures, lis chacune, choisis l'enveloppe, enregistre + archive l'original.
Demande UNE fois le prénom et le nom (ne les invente jamais).
"""

# ⚙️ PLOMBERIE — ne pas toucher. `dependencies` permet à `mcp dev` d'installer ces paquets.
mcp = FastMCP("enveloppes-avisia", instructions=INSTRUCTIONS, dependencies=["openpyxl", "pymupdf"])


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 2 — EXEMPLE RÉSOLU (lis-le, ne le modifie pas)
#
# « Lister les enveloppes » = une ACTION que Claude déclenche pour s'informer → un TOOL.
# Remarque le décorateur @mcp.tool() juste au-dessus de la fonction : c'est lui qui
# transforme une fonction Python ordinaire en capacité exposée au modèle.
# ══════════════════════════════════════════════════════════════════════════════════
@mcp.tool()
def list_envelopes() -> dict:
    """Les deux enveloppes : taux, plafond remboursé (250 €), et un `hint` pour classer."""
    return {
        key: {"label": e["label"], "cap_reimbursed": e["cap_reimbursed"],
              "reimbursement_rate": e["reimbursement_rate"], "currency": e["currency"],
              "hint": e["hint"]}
        for key, e in config.ENVELOPES.items()
    }


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 3 — à toi
#
# « Lister les factures déposées dans le dossier à classer » : est-ce une action que
# Claude déclenche, une donnée que l'utilisateur attache, ou une procédure ?
#
# TODO 3 — ajoute le BON décorateur sur la ligne au-dessus de la fonction.
# ══════════════════════════════════════════════════════════════════════════════════
# >>> ton décorateur ici
def list_factures_a_classer() -> dict:
    """Liste les factures (PDF) déposées dans la boîte à classer + leur chemin absolu."""
    factures = backend.list_inbox()
    return {"inbox_dir": str(backend.INBOX_DIR), "count": len(factures), "factures": factures}


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 4 — à toi
#
# « Lire le texte d'une facture PDF sur le disque ». Même question : quel décorateur ?
#
# TODO 4 — ajoute le bon décorateur.
# ══════════════════════════════════════════════════════════════════════════════════
# >>> ton décorateur ici
def read_invoice(path: str) -> dict:
    """Lit une facture PDF → {filename, pages, text}. Donne un chemin absolu."""
    return invoice.read(path)


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 5 — LE CŒUR MÉTIER (3 TODO)
#
# « Enregistrer une dépense dans le .xlsx + archiver la facture ».
#
# TODO 5a — quel décorateur ? (c'est une action à effet de bord : ça ÉCRIT un fichier)
#
# TODO 5b — AJOUTE deux paramètres OBLIGATOIRES en tête de la signature :
#               prenom: str, nom: str
#           En les rendant obligatoires (pas de valeur par défaut), tu FORCES Claude à
#           les demander à l'utilisateur — il ne peut pas les inventer. La règle est dans
#           le CONTRAT (le schéma), pas dans une consigne de politesse. C'est la leçon clé.
#           (Le corps ci-dessous utilise déjà `prenom` et `nom` : tant qu'ils ne sont pas
#            dans la signature, l'appel échouera — c'est normal, c'est le but du TODO.)
#
# TODO 5c — complète la docstring : Claude la LIT pour savoir quand/comment t'appeler.
#           Dis-lui que prénom + nom sont obligatoires et qu'il ne doit pas les inventer.
# ══════════════════════════════════════════════════════════════════════════════════
# >>> ton décorateur ici
def record_expense(envelope: str, descriptif: str, amount: float,
                   source_path: str | None = None) -> dict:
    """TODO 5c — décris ce tool pour Claude (et rappelle que prénom + nom sont requis)."""
    row, _ = backend.record_line(prenom, nom, envelope, descriptif, amount)
    bal = backend.balance(envelope)
    bal["line_written"] = row
    if source_path:
        bal["archived_to"] = backend.archive(envelope, source_path)
        bal["next_step"] = f"Dépense enregistrée ✅ et facture archivée dans : {bal['archived_to']}"
    else:
        fdir = backend.factures_dir(envelope)
        bal["next_step"] = f"Dépense enregistrée ✅. Dépose l'original dans : {fdir}"
    return bal


# get_balance — DONNÉ (exemple d'un 2e tool, en LECTURE SEULE). Ne pas modifier.
@mcp.tool()
def get_balance(envelope: str) -> dict:
    """Solde d'une enveloppe : engagé / remboursé / reste (vs 250 €) / over_cap."""
    return backend.balance(envelope)


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 6 — une AUTRE primitive
#
# « Le guide de classement » : ce n'est PAS une action que Claude déclenche, c'est une
# DONNÉE de référence que l'UTILISATEUR attache lui-même au chat. Quel décorateur ?
#
# TODO 6a — ajoute le bon décorateur. Indice : il prend une URI en argument.
#           URI suggérée : "enveloppes://guide"
# TODO 6b — écris le guide des 2 enveloppes en markdown (remplace le return).
# ══════════════════════════════════════════════════════════════════════════════════
# >>> ton décorateur ici (avec une URI)
def guide() -> str:
    """Guide de classement des deux enveloppes (règles + exemples)."""
    return "TODO 6b — écris ici le guide des 2 enveloppes en markdown."


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 7 — la PROCÉDURE complète
#
# « Classer TOUTES les factures du dossier » : une suite d'étapes que l'UTILISATEUR
# lance comme une commande. Quel décorateur correspond à « procédure lancée par l'user » ?
#
# TODO 7a — ajoute le bon décorateur.
# TODO 7b — écris la procédure en français : les étapes que Claude doit suivre
#           (demander prénom+nom une fois → lister → pour chaque : lire, choisir
#            l'enveloppe, record_expense avec source_path → récap final).
# ══════════════════════════════════════════════════════════════════════════════════
# >>> ton décorateur ici
def classer_facture() -> str:
    """Pilote le classement de toutes les factures déposées dans la boîte à classer."""
    return "TODO 7b — écris ici la procédure de classement du lot."


# ───────────────────────────── run ─────────────────────────────  ⚙️ PLOMBERIE
if __name__ == "__main__":
    if os.environ.get("MCP_HTTP") == "1":
        mcp.settings.host = "127.0.0.1"
        mcp.settings.port = int(os.environ.get("PORT", "8765"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()  # stdio (défaut) — pour Claude Desktop
