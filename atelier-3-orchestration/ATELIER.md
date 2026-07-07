# Atelier — Orchestration & déploiement

## L'idée à retenir (le pitch)

Un MCP en **stdio** (comme celui de l'atelier 1) ne vit que le temps d'un sous-processus,
lancé par UN client sur UNE machine. Pour qu'un autre outil, une autre machine, ou un
collègue puisse s'y connecter, il faut le faire sortir de son terminal : **HTTP**,
**authentification**, **hébergement**.

| Étape                     | Question à laquelle elle répond                  | Où c'est écrit           |
| ------------------------- | -------------------------------------------------- | -------------------------- |
| Dockerisation              | « Comment j'emballe le process pour le faire tourner ailleurs que sur ma machine ? » | `Dockerfile` |
| Écoute réseau (`0.0.0.0`) | « Comment je le rends *joignable* depuis l'extérieur du conteneur ? »               | `auth.py` (host/port)      |
| Authentification           | « Qui a le droit d'appeler ce MCP ? »              | `auth.py` (middleware)     |
| Déploiement cloud          | « Où il tourne 24/7, sans ma machine ? »           | Cloud Run (démo animateur) |
| Connexion client           | « Comment un agent s'y connecte, à distance ? »    | URL + en-tête `X-API-Key`  |

> **Pas de multi-agents ici** — un seul MCP, mais qui passe du local à l'accessible. Le
> multi-outils/multi-agents a été effleuré en atelier 2 ; ici, c'est l'architecture et la
> mise en production qui comptent.

---

## 🗺️ Le parcours — ce que tu vas faire, dans l'ordre

- [ ] **0 · Préparation** — `uv sync`, `check.py` *(à faire une fois, ~10 min)*
- [ ] **1 · Dockeriser** — MCP en HTTP dans un conteneur (`atelier/Dockerfile`)
- [ ] **2 · Lancer et vérifier** — `docker compose up`, un client Python s'y connecte
- [ ] **3 · Authentifier** — ⭐ **le cœur de l'atelier** (`atelier/auth.py`)
- [ ] **4 · Déployer** — Cloud Run, *démo animateur*
- [ ] **5 · Se connecter depuis un client distant** — Claude Desktop / un agent, via HTTPS
- [ ] **🏁 Démo finale** — un agent externe classe une facture via le MCP déployé

> **Comment lire une fiche d'exercice :**
> 🎯 ce que tu construis · ✏️ ce que tu fais · 🧪 comment le tester · ✅ comment savoir que c'est bon · 💡 **Bloqué ?** = indices et réponse (clique pour dérouler).

---

## 0 · Préparation *(à faire une fois)*

### a. `uv` et Docker

```bash
uv --version
docker --version   # optionnel — voir plus bas si absent
```

Pas de `uv` ? `curl -LsSf https://astral.sh/uv/install.sh | sh`. Pas de Docker ? Pas
bloquant : `check.py` te le signalera sans planter — tu peux avancer sur la lecture et le
code des exercices 1 et 3, et binômer pour le `docker build`/`run` réel.

### b. Le MCP à déployer (fourni par l'atelier 1)

Cet atelier réutilise **tel quel** `atelier-1-serveur-mcp/solution/server.py` — tu n'as PAS
besoin d'avoir fait l'atelier 1, juste que le dossier soit présent (mono-repo) et synchronisé :

```bash
cd ../atelier-1-serveur-mcp && uv sync && cd -
```

### c. Dépendances de cet atelier

**Toutes les commandes ci-dessous se lancent depuis `atelier-3-orchestration/`** :

```bash
uv sync                # mcp, starlette, uvicorn, httpx
uv run python check.py # pré-vol : fichiers + Docker/gcloud (informatif, jamais bloquant)
```

✅ **C'est bon quand** les lignes fichiers/dépendances sont ✅. Docker/gcloud en ⚠️ ne
t'empêchent pas de commencer.

---

## 1 · Dockeriser le MCP en HTTP

🎯 **Ce que tu construis :** une image Docker qui lance le MCP enveloppes en HTTP, joignable
depuis l'extérieur du conteneur.

✏️ **Ce que tu fais :** ouvre `atelier/Dockerfile`, lis-le en entier (tout est déjà expliqué
en commentaires). Le point d'entrée `auth.py` est déjà fourni et FONCTIONNE tel quel — ton
seul TODO ici est de compléter les 2 dernières lignes :

```dockerfile
# EXPOSE 8765
# CMD ["uv", "run", "python", "auth.py"]
```

(décommente-les, sans rien changer d'autre.)

> 💡 **Pourquoi `auth.py` et pas `solution/server.py` directement ?** Le serveur de
> l'atelier 1 écoute par défaut sur `127.0.0.1`, qui n'est visible que **depuis l'intérieur**
> d'un conteneur. `auth.py` force l'écoute sur `0.0.0.0` (sans modifier le fichier de
> l'atelier 1) — sinon le port mappé par Docker (`-p 8765:8765`) ne répondrait jamais.

🧪 **Teste (depuis `atelier-3-orchestration/`, avec Docker) :**

```bash
docker build -f atelier/Dockerfile -t enveloppes-mcp:atelier ..
```

✅ **C'est bon quand :** le build se termine par `naming to docker.io/library/enveloppes-mcp:atelier`,
sans erreur — même si tu n'as pas encore touché `auth.py` (exercice 3), l'image doit déjà
se construire.

<details>
<summary>💡 Bloqué ? — erreurs fréquentes</summary>

- **`failed to solve: ... atelier-1-serveur-mcp/uv.lock: not found`** → tu as lancé la
  commande depuis le mauvais dossier, ou avec le mauvais contexte (`..`, pas `.`) : le
  contexte doit englober à la fois `atelier-1-serveur-mcp/` et `atelier-3-orchestration/`.
- **`uv sync --frozen` échoue dans l'image** → le `uv.lock` de l'atelier 1 n'est pas à jour ;
  relance `cd ../atelier-1-serveur-mcp && uv sync` puis reconstruis.

</details>

---

## 2 · Lancer et vérifier

🎯 **Ce que tu vérifies :** le MCP répond bien en HTTP, depuis l'extérieur du conteneur.

✏️ **Ce que tu fais :** lance le conteneur avec `docker compose` (déjà configuré, rien à
modifier) :

```bash
docker compose -f atelier/docker-compose.yml up --build
```

🧪 **Teste, dans un AUTRE terminal**, avec un petit client MCP officiel (SDK `mcp`, celui
que tu utiliserais dans un vrai agent) :

```bash
uv run python -c "
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client('http://127.0.0.1:8765/mcp') as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print('tools:', [t.name for t in tools.tools])

asyncio.run(main())
"
```

> 💡 Tu préfères une UI ? Si Node.js est installé : `npx @modelcontextprotocol/inspector`,
> puis choisis le transport **Streamable HTTP** et colle `http://127.0.0.1:8765/mcp`.

✅ **C'est bon quand :** tu vois les 5 tools de l'atelier 1 s'afficher — **sans** en-tête
d'authentification (normal, le TODO 3 n'est pas encore fait).

<details>
<summary>💡 Bloqué ? — `curl: (7) Failed to connect` ou pareil en Python</summary>

Vérifie que le conteneur est bien démarré (logs `docker compose` : tu dois voir `Uvicorn
running on http://0.0.0.0:8765`) et que le TODO 1 (EXPOSE/CMD) est bien décommenté — sans
CMD, le conteneur démarre mais ne lance rien.

</details>

---

## 3 · Authentifier — ⭐ le cœur de l'atelier

🎯 **Ce que tu construis :** un middleware qui exige une clé API sur CHAQUE requête HTTP
vers le MCP — sans quoi n'importe qui connaissant l'URL pourrait classer des factures ou lire
des soldes.

✏️ **Ce que tu fais :** dans `atelier/auth.py`, complète `APIKeyMiddleware.dispatch` (les
commentaires juste au-dessus détaillent les 4 étapes), PUIS décommente la ligne
`mcp_app.add_middleware(APIKeyMiddleware)` en bas du fichier.

🧪 **Teste :**

```bash
MCP_API_KEY=une-cle-secrete docker compose -f atelier/docker-compose.yml up --build
```

Dans un autre terminal :

```bash
# sans clé → doit échouer
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8765/mcp \
  -H "Accept: application/json, text/event-stream" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}'

# avec la bonne clé → doit réussir
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8765/mcp \
  -H "X-API-Key: une-cle-secrete" \
  -H "Accept: application/json, text/event-stream" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}'
```

✅ **C'est bon quand :** la 1ʳᵉ commande renvoie `401`, la 2ᵉ renvoie `200`.

<details>
<summary>💡 Bloqué ? — la solution complète</summary>

```python
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("MCP_API_KEY", "")
        provided = request.headers.get("X-API-Key", "")
        if not expected or not hmac.compare_digest(provided, expected):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


mcp_app.add_middleware(APIKeyMiddleware)
```

</details>

> 💡 **À discuter :** que se passe-t-il si `MCP_API_KEY` n'est PAS définie côté serveur ?
> Avec ce code, `expected` vaut `""` → la condition `not expected` est vraie → **tout le
> monde est rejeté**. C'est voulu : *fail-closed*. L'alternative (laisser passer si aucune
> clé n'est configurée) est un piège de sécurité classique — ne jamais désactiver l'auth
> silencieusement.

---

## 4 · Déployer — *démo animateur*

> ⚠️ Cette étape est présentée **en démo** par l'animateur, pas en exercice individuel :
> tout le monde n'a pas de compte GCP/Cloud Avisia en salle. Suis, pose des questions, mais
> ne bloque pas dessus.

🎯 **Ce que tu observes :** comment l'image construite en local part sur une plateforme qui
la fait tourner en continu, avec une URL HTTPS publique.

Principe (Cloud Run GCP, ou équivalent Cloud Avisia) — **placeholders explicites, jamais de
vraies valeurs** :

```bash
# 1. Construire et pousser l'image vers un registre
docker build -f solution/Dockerfile -t "$REGION-docker.pkg.dev/$PROJECT_ID/mcp/enveloppes:1.0" ..
docker push "$REGION-docker.pkg.dev/$PROJECT_ID/mcp/enveloppes:1.0"

# 2. Déployer sur Cloud Run
gcloud run deploy enveloppes-mcp \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/mcp/enveloppes:1.0" \
  --region "$REGION" \
  --set-env-vars "MCP_API_KEY=$MCP_API_KEY" \
  --allow-unauthenticated   # l'auth est gérée par NOTRE middleware, pas par Cloud Run
```

`$PROJECT_ID`, `$REGION`, `$MCP_API_KEY` : variables d'environnement définies au moment du
déploiement, **jamais commitées**. `--allow-unauthenticated` peut surprendre : c'est
volontaire, l'accès est déjà contrôlé par `X-API-Key` au niveau applicatif (exercice 3) —
sur un vrai environnement de prod AVISIA, on ajouterait EN PLUS l'authentification IAM de la
plateforme cloud (double couche), hors périmètre de cet atelier.

✅ **Tu dois pouvoir répondre à :** pourquoi l'image doit-elle écouter sur `$PORT` fourni par
Cloud Run (et pas un port fixe) ? *(Cloud Run assigne le port dynamiquement via la variable
d'env `PORT` — c'est déjà géré par `auth.py`, qui lit `PORT` depuis l'environnement.)*

---

## 5 · Connexion depuis un environnement client

🎯 **Ce que tu construis :** la configuration côté client (Claude Desktop, ou un agent comme
celui de l'atelier 2) pour parler au MCP **déployé**, à la place du stdio local.

✏️ **Claude Desktop** ne sait nativement lancer que des MCP en stdio. Pour du HTTP distant,
utilise un pont `mcp-remote` dans sa config (`claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "enveloppes-distant": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://ENVELOPPES-MCP-URL.run.app/mcp",
        "--header", "X-API-Key:${MCP_API_KEY}"
      ]
    }
  }
}
```

✏️ **Un agent Python** (comme celui de l'atelier 2) — même mécanique que l'exercice 2, avec
l'URL distante et l'en-tête en plus :

```python
async with streamablehttp_client(
    "https://ENVELOPPES-MCP-URL.run.app/mcp",
    headers={"X-API-Key": mcp_api_key},
) as (read, write, _):
    ...
```

✅ **C'est bon quand :** tu identifies la SEULE différence avec la connexion stdio de
l'atelier 2 : une URL + un en-tête, au lieu d'une commande + un sous-processus. Le reste du
protocole (initialize, list_tools, call_tool) ne change pas — **c'est tout l'intérêt de MCP :
le transport change, pas le contrat.**

---

## 🏁 Démo finale

Avec le MCP déployé (ou en local via `docker compose`) et une clé API définie :

1. lance un client (le snippet de l'exercice 2/5, ou l'agent de l'atelier 2 reconfiguré avec
   `MCP_SERVERS["enveloppes"]` pointant vers l'URL HTTP + l'en-tête `X-API-Key`) ;
2. fais-lui lister les tools, puis appeler `list_envelopes` ;
3. vérifie qu'une requête SANS la clé échoue toujours (`401`).

**Réinitialiser pour rejouer :** `docker compose down -v` (le `-v` supprime le volume de
persistance des `.xlsx` créé à l'exercice 2).

---

## 🆘 Ça ne marche pas ? — réflexes de dépannage

| Symptôme                                        | Cause la plus fréquente                          | Solution                                                          |
| ------------------------------------------------ | --------------------------------------------------- | -------------------------------------------------------------------- |
| `docker build` : fichier atelier-1 introuvable   | mauvais contexte de build                           | contexte = racine du mono-repo (`..` depuis `atelier-3-orchestration/`) |
| Le conteneur démarre mais rien ne répond          | TODO 1 (EXPOSE/CMD) pas décommenté                  | relis `atelier/Dockerfile`                                            |
| `curl`/client Python : connexion refusée          | serveur qui écoute sur `127.0.0.1` au lieu de `0.0.0.0` | ne PAS lancer `solution/server.py` directement dans le conteneur — utilise `auth.py` |
| Toutes les requêtes en `401`, même avec la clé    | `MCP_API_KEY` différente entre client et serveur, ou pas propagée au conteneur | vérifie `docker compose ... -e` / la variable d'env exportée |
| `check.py` affiche des ⚠️ sur Docker/gcloud       | outils non installés — **normal, pas bloquant**    | avance quand même sur la lecture/le code, teste en binôme            |

> 💡 **Filet de sécurité :** `solution/` contient la version complète. En cas de blocage :
> `docker compose -f solution/docker-compose.yml up --build`.

---

## Pour l'animateur *(pas pour les participants)*

**Timing (~2 h, ~110 min occupées) :** 10 min pitch + tableau des couches · 10 min
setup/`check.py` · 20 min exo 1 (Dockerfile) · 15 min exo 2 (run + vérif client) · 30 min
exo 3 ⭐ (auth — le plus long, prévoir un point de synchronisation collectif à mi-parcours) ·
**15 min exo 4 — DÉMO ANIMATEUR** (pas un exercice individuel, ne pas la compter dans le temps
« autonomie ») · 10 min exo 5 + démo finale. ~10 min de marge pour les blocages Docker.

**Pièges à éviter :**

- **Docker absent en salle** : c'est le risque n°1 de cet atelier (contrairement aux
  ateliers 1/2, l'outillage externe n'est pas garanti). `check.py` avertit sans bloquer —
  prévoir un mode binôme (un poste avec Docker pour deux) si besoin.
- **`gcloud`/compte GCP** : l'exercice 4 est une démo animateur précisément pour cette
  raison — ne JAMAIS transformer ce point en exercice individuel sans avoir vérifié en amont
  que tout le monde a un compte/projet GCP valide.
- **Confusion `127.0.0.1` vs `0.0.0.0`** : c'est LE piège réseau classique de la
  dockerisation. Si un participant lance `solution/server.py` directement dans son
  Dockerfile (au lieu de `auth.py`), le port mappé ne répondra jamais — bon prétexte pour
  insister sur le point de discussion ci-dessous.

**Points de discussion à provoquer :**

- Exo 1 : pourquoi le build réussit-il même sans EXPOSE/CMD ? *EXPOSE est documentaire (ne
  bloque rien), CMD est juste la commande par défaut au `run` — aucun des deux n'affecte la
  construction de l'image.*
- Exo 3 : pourquoi `hmac.compare_digest` plutôt que `==` ? *Comparer des chaînes avec `==`
  s'arrête au premier caractère différent — un attaquant peut mesurer le temps de réponse
  pour deviner la clé caractère par caractère (timing attack). `compare_digest` compare en
  temps constant.*
- Exo 5 : qu'est-ce qui NE change PAS entre un agent qui parle en stdio (atelier 2) et un
  agent qui parle en HTTP+clé (ici) ? *Le protocole MCP lui-même (initialize, tools,
  call_tool) — seul le transport et l'authentification changent. C'est le message central de
  tout l'atelier.*

**Solution de secours :** `solution/` contient la version complète.
`docker compose -f solution/docker-compose.yml up --build`.
