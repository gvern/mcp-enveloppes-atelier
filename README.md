# MCP Enveloppes AVISIA — atelier de découverte

Serveur **MCP** 100 % local : tu déposes tes factures PDF dans un dossier, Claude les lit
**toutes**, les classe dans une des deux enveloppes du cabinet (CE / Apprentissage), remplit
le formulaire NDF `.xlsx` et **archive automatiquement l'original**. À brancher sur
**Claude Desktop (plan gratuit suffit)**.

> Un **MCP** (Model Context Protocol) expose des capacités à un LLM. Le LLM décide quand les
> appeler : ici le MCP **extrait le texte** du PDF (PyMuPDF, zéro install), Claude choisit la
> catégorie, et le MCP applique les règles métier + écrit le `.xlsx` (déterministe, traçable).
> Construit avec le **SDK officiel `mcp`** (`mcp.server.fastmcp`).

## 🎓 Tu viens pour l'atelier ?

**→ Suis [`ATELIER.md`](ATELIER.md).** Tu construiras toi-même le serveur en complétant le
squelette `atelier/`, sans installer quoi que ce soit d'autre que `uv sync`.

```bash
uv sync                 # mcp, openpyxl, pymupdf
uv run python check.py  # pré-vol + crée 3 factures de test
```

## Structure du dépôt

| Dossier | Rôle |
| --- | --- |
| `atelier/` | **squelette à compléter** — tu n'écris que du métier (`# TODO`) |
| `solution/` | la version **complète et fonctionnelle** (référence / dépannage) |
| `templates/` | les vrais modèles `.xlsx` (CE, Apprentissage) |
| `factures_a_classer/` | la boîte de dépôt (générée par `check.py`) |

Backend (`local_xlsx.py`, `invoice.py`) et `config.py` (sauf les `hint`) = **plomberie
fournie**, identique dans les deux dossiers.

## Les deux enveloppes

| Enveloppe | Taux remboursé | Plafond remboursé | Exemples |
| --- | --- | --- | --- |
| **CE** | 50 % | 250 € | cinéma, musée, spectacle, sport, salle de sport |
| **APPRENTISSAGE** | 100 % | 250 € | formation, livre, conf, certif, abonnement IA |

Le plafond de 250 € porte sur le **montant remboursé**, pas l'engagé.

## Utiliser la version finie (hors atelier)

Brancher la **solution** dans Claude Desktop — Réglages → Développeur → Modifier la config :

```json
{
  "mcpServers": {
    "enveloppes": {
      "command": "uv",
      "args": ["run", "--directory", "/CHEMIN/ABSOLU/atelier-mcp-enveloppes", "python", "solution/server.py"]
    }
  }
}
```

Redémarre Claude Desktop (Cmd+Q). Dépose des PDF dans `factures_a_classer/`, lance le prompt
**`/classer_facture`**. Claude te demande prénom + nom (une fois), classe tout et archive les
originaux dans `notes_de_frais/<CE|ACADEMY>/factures/`.

> ℹ️ Le MCP lit la **couche texte** du PDF. Un PDF *scanné* (pur image) est hors périmètre :
> utilise des PDF numériques (FNAC, OpenAI, Udemy…).

## Inspecter le serveur (Inspector MCP)

```bash
uv run mcp dev solution/server.py     # ou atelier/server.py pendant l'atelier
```

UI web avec les onglets **Tools / Resources / Prompts** : déclenche chaque primitive à la
main, schémas visibles. (`mcp dev` recharge le code tout seul — pas besoin de redémarrer.)

## Les 3 primitives MCP

**Tools** — actions décidées par le **modèle** :

| Tool | Rôle |
| --- | --- |
| `list_factures_a_classer` | liste les factures PDF de `factures_a_classer/` |
| `read_invoice` | lit une facture PDF sur disque → **texte** (PyMuPDF) |
| `list_envelopes` | taux, plafond (250 €) et `hint` des 2 enveloppes |
| `record_expense` | prénom + nom requis → écrit la ligne, **archive l'original**, renvoie solde + `over_cap` |
| `get_balance` | lecture seule : engagé / remboursé / reste (vs 250 €) |

**Resources** — données **read-only** attachées par l'**utilisateur** :

| Resource | Contenu |
| --- | --- |
| `enveloppes://guide` | guide de classement (markdown) |
| `enveloppes://solde/{envelope}` | solde courant d'une enveloppe (template paramétré) |

**Prompts** — procédures invoquées par l'**utilisateur** :

| Prompt | Rôle |
| --- | --- |
| `/classer_facture` | pilote le lot complet : lister → lire → classer → archiver → récap |

## Où sont les fichiers

```
factures_a_classer/                  # ← dépôt ($INBOX_DIR)
notes_de_frais/                      # ← sortie ($NDF_DIR)
├─ CE/
│  ├─ aaaammjj_NOM_NDF_CE.xlsx        # formulaire CE rempli
│  └─ factures/                       # justificatifs CE (archivés automatiquement)
└─ ACADEMY/
   ├─ aaaammjj_NOM_NDF_RembApp.xlsx   # formulaire Apprentissage rempli
   └─ factures/                       # justificatifs Apprentissage (archivés automatiquement)
```

Ouvrables dans Excel / LibreOffice. Descriptif en colonne A, montant en colonne B (lignes
15→28) ; le total B29 garde sa formule `SUBTOTAL`. Règles métier dans `config.py`. Dossiers
configurables via `INBOX_DIR` et `NDF_DIR`.

## Prérequis

- **[uv](https://docs.astral.sh/uv/)** — gère Python + dépendances. Install :
  `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux), `brew install uv`,
  ou `pip install uv` (si Python déjà présent).
- **Python ≥ 3.12** — installé par `uv` au besoin.
- **Node.js** — uniquement pour l'Inspector (`mcp dev`), via `npx`.
- **Claude Desktop** — le **plan gratuit suffit**. → https://claude.ai/download
