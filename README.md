# MCP Enveloppes AVISIA

MCP qui classe des factures dans les deux enveloppes annuelles du cabinet (**CE** et
**Apprentissage**, plafond 250 € remboursés chacune) et remplit le formulaire NDF
(Google Sheet) correspondant **dans le Drive personnel de chaque utilisateur**.

Plafond = 250 € sur le **remboursé** : CE rembourse 50 % (≈ 500 € engageable),
Apprentissage 100 % (250 € engageable).

## Architecture (modèle PROD)

- **Transport** : Streamable HTTP (Cloud Run), endpoint `/mcp/`.
- **Auth user** : OAuth Google **par utilisateur** (scopes `drive.file` + `spreadsheets`).
  Chaque user consent une fois ; le MCP crée et remplit ses 2 formulaires dans SON Drive.
  Le service account ne touche jamais le Drive des users.
- **Sans état local** : refresh_tokens + ids de Sheets dans **Firestore**.
- **Templates** : les `.xlsx` de `templates/` sont **uploadés-convertis** en Google
  Sheets dans le Drive du user (l'app crée le fichier → `drive.file` suffit, fidélité
  du formulaire préservée — pas besoin de scope `drive` complet).

Boucle agentique : `get_auth_url` → (consent) → `setup_user` → `read_invoice`
(le modèle lit) → `classify` → `record_expense` → `get_balance`.

## Prérequis GCP (one-time, projet `avisia-training`)

1. **APIs** : `drive`, `sheets`, `firestore`, `run`, `cloudbuild`, `artifactregistry`,
   `secretmanager`.
2. **Firestore** : base en mode Native (région `europe-west`). Le SA runtime (default
   compute `1062626335546-compute@developer.gserviceaccount.com`) doit avoir
   `roles/datastore.user`.
3. **OAuth** :
   - Écran de consentement **User Type = Internal** (pas de vérif Google).
   - Client OAuth **type Web** → `CLIENT_ID` + `CLIENT_SECRET`.
   - Redirect URI = `<URL_DU_SERVICE>/oauth/callback` (local :
     `http://localhost:8080/oauth/callback`).
   - Scopes : `drive.file`, `spreadsheets`.
4. **Secret** : `gcloud secrets create enveloppes-oauth-client-secret --data-file=-`
   (coller le client secret). Le SA runtime : `roles/secretmanager.secretAccessor`.

## Test local sans Google (DEMO_MODE)

Pour valider toute la logique (classify / record_expense / balance / plafond) sans Drive,
OAuth ni Firestore — backend in-memory (`src/demo.py`) :

```bash
uv sync
DEMO_MODE=1 uv run python -m src.server   # http://localhost:8080/mcp/
# autre terminal :
claude mcp add --transport http enveloppes http://localhost:8080/mcp/
# puis redémarrer Claude Code (les MCP se chargent au démarrage) et piloter en langage naturel
```

En DEMO, `get_auth_url`/`setup_user` ne touchent rien et l'état vit en mémoire (perdu au
redémarrage). C'est Claude Code (ou tout client MCP) qui joue le LLM.

## Démarrage local avec Google (réel)

```bash
uv sync
cp .env.example .env        # remplir CLIENT_ID/SECRET, OAUTH_REDIRECT_URI, projet
gcloud auth application-default login   # ADC pour Firestore
uv run python -m src.server            # http://localhost:8080/mcp/
```

Connecter depuis Claude Code :

```bash
claude mcp add --transport http enveloppes http://localhost:8080/mcp/
```

Test : `get_auth_url("moi@avisia")` → ouvrir l'URL, consentir → `setup_user("moi@avisia",
nom="Dupont", prenom="Jean")` → vérifier le dossier + 2 Sheets dans votre Drive.

## Déployer sur Cloud Run

```bash
export GOOGLE_OAUTH_CLIENT_ID=...
export OAUTH_REDIRECT_URI=https://<service>-<hash>.europe-west1.run.app/oauth/callback
./deploy.sh
```

⚠️ 1er deploy pour obtenir l'URL → déclarer le redirect URI dans le client OAuth →
redéployer avec le bon `OAUTH_REDIRECT_URI`. Build en **deux étapes** (jamais
`--source .`, voir `deploy.sh`).

## Tools

| Tool | Rôle |
|---|---|
| `get_auth_url(user_id)` | URL de consentement Google (si pas déjà autorisé). |
| `setup_user(user_id, nom, prenom)` | Crée dossier + 2 formulaires NDF dans le Drive du user (idempotent). |
| `read_invoice(data_base64, mime_type)` | Renvoie la facture au modèle pour lecture (OCR côté modèle). |
| `classify(category, amount, user_id)` | → `CE` / `APPRENTISSAGE` / `ambiguous` + remboursé + reste. |
| `record_expense(user_id, envelope, descriptif, amount, nom, prenom)` | Écrit la facture (ligne 15→28), renvoie le solde. |
| `get_balance(user_id, envelope)` | Engagé / remboursé / reste remboursable (vs 250 €). |

## Fichiers

| Fichier | Rôle |
|---|---|
| `src/server.py` | Serveur MCP (tools) + routes `/oauth/callback`, `/healthz`. |
| `src/auth.py` | OAuth Google par user (consent, échange, refresh). |
| `src/store.py` | Firestore : tokens + ids par user. |
| `src/gdrive.py` | Drive/Sheets dans le Drive du user (upload template, remplissage). |
| `src/config.py` | Règles enveloppes + disposition du formulaire. |
| `templates/*.xlsx` | Formulaires NDF source (CE, Apprentissage). |
| `deploy.sh` / `Dockerfile` | Déploiement Cloud Run. |

## TODO

- Catégories éligibles **APPRENTISSAGE** dans `src/config.py` (CE = culture/sport confirmé).
- Sécurité prod : chiffrer le refresh_token, `state` OAuth signé/anti-CSRF, durcir
  l'accès (MCP privé derrière l'agent host Chat).
