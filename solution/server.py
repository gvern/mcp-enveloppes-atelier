"""MCP server — Enveloppes AVISIA (SOLUTION complète, SDK officiel `mcp`).

Transport :
  - défaut : stdio  → à brancher dans Claude Desktop
  - MCP_HTTP=1      → Streamable HTTP sur http://127.0.0.1:$PORT/mcp (défaut 8765)

Lancer en local :  uv run python solution/server.py
Inspecter :        uv run mcp dev solution/server.py
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

L'utilisateur dépose ses factures (PDF) dans une boîte à classer. Pour traiter TOUT le lot :
1. list_factures_a_classer() → liste les fichiers déposés (avec leur `path`) ;
2. demande UNE fois le PRÉNOM et le NOM de l'utilisateur (ne les invente jamais) ;
3. pour chaque fichier : read_invoice(path) renvoie le TEXTE — lis-le pour en tirer le
   descriptif et le montant, puis choisis l'enveloppe via les `hint` de list_envelopes ;
4. record_expense(prenom, nom, envelope, descriptif, amount, source_path=path) : écrit la
   ligne .xlsx ET archive automatiquement l'original (passe bien source_path).

APRÈS chaque record_expense : le champ `next_step` confirme l'archivage. Fais un récap final.
"""

# `dependencies` permet à `mcp dev` d'auto-installer ces paquets dans son env éphémère.
mcp = FastMCP(
    "enveloppes-avisia",
    instructions=INSTRUCTIONS,
    dependencies=["openpyxl", "pymupdf"],
)


# ───────────────────────────── tools ─────────────────────────────


@mcp.tool()
def list_envelopes() -> dict:
    """Les deux enveloppes : taux, plafond remboursé (250 €), et un `hint` pour classer."""
    return {
        key: {
            "label": env["label"],
            "cap_reimbursed": env["cap_reimbursed"],
            "reimbursement_rate": env["reimbursement_rate"],
            "currency": env["currency"],
            "hint": env["hint"],
        }
        for key, env in config.ENVELOPES.items()
    }


@mcp.tool()
def list_factures_a_classer() -> dict:
    """Liste les factures (PDF) déposées dans la boîte à classer ($INBOX_DIR).

    Renvoie `inbox_dir` (où l'utilisateur dépose) et `factures` (filename + path absolu).
    Appelle read_invoice(path) sur chacune pour en lire le contenu.
    """
    factures = backend.list_inbox()
    return {"inbox_dir": str(backend.INBOX_DIR), "count": len(factures), "factures": factures}


@mcp.tool()
def read_invoice(path: str) -> dict:
    """Lit une facture PDF sur le disque et renvoie son TEXTE exploitable (couche texte).

    Renvoie {filename, pages, text}. Lis `text` pour en tirer le descriptif et le montant.
    Donne un chemin absolu (celui renvoyé par list_factures_a_classer).
    """
    return invoice.read(path)


@mcp.tool()
def record_expense(
    prenom: str,
    nom: str,
    envelope: str,
    descriptif: str,
    amount: float,
    source_path: str | None = None,
) -> dict:
    """Enregistre une facture dans le formulaire .xlsx de l'enveloppe (CE ou APPRENTISSAGE).

    PRÉNOM et NOM sont OBLIGATOIRES → demande-les à l'utilisateur, ne les invente pas.
    Écrit l'identité (B10/B11) + le descriptif et le montant engagé sur la prochaine ligne
    libre (15→28). Si `source_path` est fourni (le fichier renvoyé par read_invoice), le MCP
    DÉPLACE l'original dans factures/ (archivage automatique). Renvoie le solde (`over_cap` =
    plafond 250 € dépassé) et un message `next_step` à transmettre.
    """
    row, _ = backend.record_line(prenom, nom, envelope, descriptif, amount)
    bal = backend.balance(envelope)
    bal["line_written"] = row
    # L'archivage est best-effort : la ligne est déjà écrite, donc il ne doit JAMAIS faire
    # échouer le tool (sinon le modèle croit que rien n'a été enregistré et ré-appelle →
    # ligne en double). Un source_path inaccessible (ex. pièce jointe du chat dans le sandbox
    # de Claude Desktop, /mnt/user-data/…) est traité comme "à déposer manuellement".
    archived_to = None
    if source_path:
        try:
            archived_to = backend.archive(envelope, source_path)
        except (FileNotFoundError, OSError):
            archived_to = None
    if archived_to:
        bal["archived_to"] = archived_to
        bal["next_step"] = f"Dépense enregistrée ✅ et facture archivée dans : {archived_to}"
    else:
        fdir = backend.factures_dir(envelope)
        bal["factures_dir"] = fdir
        bal["archived"] = False
        note = f"Dépense enregistrée ✅. Dépose le fichier original de la facture dans : {fdir}"
        if source_path:
            note += f" (l'original {source_path} n'est pas accessible côté serveur — dépose-le toi-même)"
        bal["next_step"] = note
    return bal


@mcp.tool()
def get_balance(envelope: str) -> dict:
    """Solde d'une enveloppe (LECTURE SEULE) : engagé, remboursé, reste (vs 250 €), over_cap."""
    return backend.balance(envelope)


# ─────────────────────────── resources ───────────────────────────
# Données READ-ONLY adressées par URI, attachées au contexte par l'utilisateur/le client.


@mcp.resource("enveloppes://guide", mime_type="text/markdown")
def guide() -> str:
    """Guide de classement des deux enveloppes (règles + exemples)."""
    out = [
        "# Enveloppes AVISIA — guide de classement",
        "",
        "Deux enveloppes annuelles, **plafond 250 € remboursés** chacune.",
        "",
    ]
    for key, env in config.ENVELOPES.items():
        taux = int(env["reimbursement_rate"] * 100)
        out += [
            f"## {key} — {env['label']}",
            f"- Remboursé à **{taux} %**, plafond **{env['cap_reimbursed']:.0f} €** remboursés.",
            f"- {env['hint']}",
            "",
        ]
    return "\n".join(out)


@mcp.resource("enveloppes://solde/{envelope}")
def solde(envelope: str) -> dict:
    """Solde courant d'une enveloppe (CE ou APPRENTISSAGE) — lecture seule, ne crée rien."""
    env = envelope.upper()
    if env not in config.ENVELOPES:
        return {"erreur": f"enveloppe inconnue : {envelope} (attendu CE ou APPRENTISSAGE)"}
    return backend.balance(env)


# ──────────────────────────── prompts ────────────────────────────
# Templates invoqués par l'UTILISATEUR (slash-command dans Claude Desktop).


@mcp.prompt()
def classer_facture() -> str:
    """Pilote le classement de TOUTES les factures déposées dans la boîte à classer."""
    return (
        "Tu vas classer dans les enveloppes AVISIA toutes les factures déposées dans la "
        "boîte à classer.\n"
        "1. Demande le PRÉNOM et le NOM de l'utilisateur (une seule fois, ne les invente pas).\n"
        "2. Appelle list_factures_a_classer() pour lister les fichiers à traiter.\n"
        "3. Pour CHAQUE fichier de la liste :\n"
        "   a. read_invoice(path) → lis le `text` (fournisseur, date, montant, nature) ;\n"
        "   b. choisis l'enveloppe (CE ou APPRENTISSAGE) via enveloppes://guide ou "
        "list_envelopes ;\n"
        "   c. record_expense(prenom, nom, envelope, descriptif, amount, source_path=path) "
        "— passe TOUJOURS source_path pour archiver l'original automatiquement.\n"
        "4. Récap final : pour chaque facture l'enveloppe choisie + le montant, le solde de "
        "chaque enveloppe, et préviens si `over_cap` est vrai (plafond 250 € dépassé)."
    )


# ───────────────────────────── run ─────────────────────────────

if __name__ == "__main__":
    if os.environ.get("MCP_HTTP") == "1":
        mcp.settings.host = "127.0.0.1"
        mcp.settings.port = int(os.environ.get("PORT", "8765"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()  # stdio (défaut) — pour Claude Desktop
