# MCP Enveloppes AVISIA — atelier local

Atelier : **créer un serveur MCP de zéro et le brancher en local** sur Claude Desktop
(ou tout client MCP). Cas concret : classer une facture dans l'une des deux enveloppes
annuelles du cabinet et remplir le formulaire NDF correspondant.

100 % local : **aucun cloud, aucun compte Google, aucune clé**. Les formulaires sont de
vrais fichiers `.xlsx` écrits sur disque, ouvrables dans Excel / LibreOffice.

> Un **MCP** (Model Context Protocol) expose des *tools* à un LLM. Le LLM (Claude Desktop,
> Claude Code…) décide quand les appeler. Ici le LLM lit la facture (OCR), choisit la
> catégorie, et le MCP applique les règles + écrit le `.xlsx`.

## Les deux enveloppes

| Enveloppe | Taux remboursé | Plafond remboursé | Engageable | Exemples |
|---|---|---|---|---|
| **CE** | 50 % | 250 € | ≈ 500 € | cinéma, musée, spectacle, sport, salle de sport |
| **APPRENTISSAGE** | 100 % | 250 € | 250 € | formation, livre, conf, certif, abonnement IA |

Le plafond de 250 € porte sur le **montant remboursé**, pas l'engagé.

## Prérequis

- [uv](https://docs.astral.sh/uv/) (gestion env + deps Python)
- Python ≥ 3.12 (uv l'installe au besoin)

## Installation

```bash
uv sync
```

## Lancer le serveur

**stdio (défaut — pour Claude Desktop)** :

```bash
uv run python -m src.server
```

**HTTP (pour tester au navigateur / curl / Claude Code)** :

```bash
MCP_HTTP=1 uv run python -m src.server   # → http://localhost:8765/mcp
```

## Brancher dans Claude Desktop (stdio)

Éditer `claude_desktop_config.json` (Réglages → Développeur → Modifier la config) :

```json
{
  "mcpServers": {
    "enveloppes": {
      "command": "uv",
      "args": ["run", "--directory", "/CHEMIN/ABSOLU/atelier-mcp-enveloppes", "python", "-m", "src.server"]
    }
  }
}
```

Remplacer le chemin par celui du dossier cloné, puis **redémarrer Claude Desktop**. Les
tools `enveloppes` apparaissent (icône outils). Piloter en langage naturel :
*« classe cette facture »* en joignant le PDF/image.

## Brancher dans Claude Code (HTTP)

```bash
MCP_HTTP=1 uv run python -m src.server            # terminal 1
claude mcp add --transport http enveloppes http://localhost:8765/mcp   # terminal 2
```

## Les tools

| Tool | Rôle |
|---|---|
| `setup_user(user_id, nom, prenom)` | Crée les 2 formulaires NDF `.xlsx` locaux (idempotent). |
| `read_invoice(data_base64, mime_type)` | Renvoie la facture au modèle pour lecture (**OCR côté LLM**, pas côté MCP). |
| `classify(category, amount, user_id)` | → `CE` / `APPRENTISSAGE` / `ambiguous` + remboursé + reste + `fits`. |
| `record_expense(user_id, envelope, descriptif, amount, nom, prenom)` | Écrit la facture (1re ligne libre 15→28), renvoie le solde. |
| `get_balance(user_id, envelope)` | Engagé / remboursé / reste remboursable (vs 250 €). |
| `list_envelopes()` | Règles des deux enveloppes. |
| `ping(name)` | Vérifie que le MCP répond. |

Boucle agentique type :
`setup_user` → `read_invoice` (le LLM lit) → `classify` → `record_expense` → `get_balance`.

## Où sont les fichiers

`record_expense` écrit dans :

```
local_data/<user_id>/CE.xlsx
local_data/<user_id>/APPRENTISSAGE.xlsx
```

Copiés depuis `templates/`. Le descriptif va en colonne A, le montant en colonne B
(lignes 15→28) ; le total **B29** garde sa formule `SUBTOTAL`. Changer le dossier de
sortie : `LOCAL_XLSX_DIR=/autre/chemin`.

## Les règles

Tout est dans `src/config.py` :

- `ENVELOPES` : taux, plafond, catégories `eligible` par enveloppe.
- `ALIASES` : marchands mappés direct vers une enveloppe (`anthropic`/`claude` →
  APPRENTISSAGE, `basic-fit` → CE) sans passer par le LLM.

Le matching (`src/server.py:_match_envelope`) est tolérant aux accents, à la casse, aux
séparateurs et aux variantes ("licence sportive" → `sport`).

## Structure

```
src/
  server.py      # serveur MCP : tools + matching catégorie → enveloppe
  local_xlsx.py  # backend : copie template + écrit les .xlsx
  config.py      # règles enveloppes + disposition du formulaire
templates/
  CE.xlsx APPRENTISSAGE.xlsx   # formulaires NDF source
```

## TODO

- Confirmer les catégories éligibles **APPRENTISSAGE** dans `src/config.py`
  (CE = culture/sport déjà confirmé par le template).
