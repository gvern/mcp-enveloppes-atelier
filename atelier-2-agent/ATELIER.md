# Atelier — Créer son premier agent

## L'idée à retenir (le pitch)

En atelier 1, tu as construit un **MCP** : une boîte à outils exposée à un LLM. Ici, tu
construis l'**agent** : celui qui **tient le LLM par la main**, boucle après boucle, entre
l'utilisateur et les outils.

|           | Le LLM (Anthropic)                                    | L'agent (toi, la boucle)                                    |
| --------- | ------------------------------------------------------ | ------------------------------------------------------------- |
| fait quoi | lit les tools disponibles, **décide** lesquels appeler et avec quels arguments | **exécute** l'appel sur le bon MCP, **renvoie** le résultat, **répète** |
| fiable ?  | non (peut boucler, se tromper d'outil)                 | oui (le code décide QUAND s'arrêter, QUOI faire d'une erreur) |

Le protocole MCP (comment un outil est exposé) a déjà été vu en atelier 1 — ici, on ne le
retouche pas. La difficulté de cet atelier est ailleurs : **structurer la boucle**, **écrire
un system prompt qui arbitre entre plusieurs outils**, et **brancher un deuxième outil sans
rien casser**.

---

## 🗺️ Le parcours — ce que tu vas faire, dans l'ordre

- [ ] **0 · Préparation** — `uv sync`, `check.py`, clé API *(à faire une fois, ~10 min)*
- [ ] **1 · Connexion à un MCP** — lire `demo_list_tools` *(rien à coder, juste comprendre)*
- [ ] **2 · Le system prompt** — écrire `SYSTEM_PROMPT` dans `atelier/config.py`
- [ ] **3 · La boucle agentique** — ⭐ **le cœur de l'atelier** (`run()`)
- [ ] **4 · Un deuxième MCP** — brancher le mini MCP météo (multi-outils)
- [ ] **🏁 Démo finale** — un message qui déclenche les DEUX MCP

> **Comment lire une fiche d'exercice :**
> 🎯 ce que tu construis · ✏️ ce que tu fais · 🧪 comment le tester · ✅ comment savoir que c'est bon · 💡 **Bloqué ?** = indices et réponse (clique pour dérouler).

---

## 0 · Préparation *(à faire une fois)*

### a. `uv` déjà installé ? (vu en atelier 1)

```bash
uv --version
```

Sinon : `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) ou
`brew install uv`.

### b. Le MCP de l'atelier 1 est-il prêt ?

Cet atelier **réutilise** `atelier-1-serveur-mcp/solution/server.py`. S'il n'est pas déjà
synchronisé :

```bash
cd ../atelier-1-serveur-mcp && uv sync && cd -
```

### c. Installer les dépendances de cet atelier + la clé API

**Toutes les commandes de cet atelier se lancent depuis `atelier-2-agent/`** :

```bash
uv sync                        # mcp, anthropic
export ANTHROPIC_API_KEY=sk-ant-...   # jamais dans le code, jamais commit
uv run python check.py         # pré-vol
```

✅ **C'est bon quand** `check.py` affiche **tout en ✅** (dépendances, clé API, MCP atelier 1
accessible).
❌ Sans clé API sous la main tout de suite : `check.py` te le dit clairement, et tu peux déjà
avancer sur les exercices 1, 2 et 4a (aucun n'appelle le modèle).

---

## La question centrale de tout l'atelier : **qui décide, et sur la base de quoi ?**

À chaque exercice, pose-toi cette question :

| Décision                                        | Qui la prend | Où c'est écrit               |
| ------------------------------------------------ | ------------ | ------------------------------ |
| « Quels outils existent, et à quoi ils servent »  | le MCP       | le schéma du tool (atelier 1) |
| « Quel outil appeler MAINTENANT, avec quoi »      | le **LLM**   | ta requête + le `SYSTEM_PROMPT` |
| « Quand s'arrêter, que faire d'une erreur d'outil »| l'**agent**  | la boucle `run()` (ton code)   |

Un agent mal structuré, c'est une décision au mauvais endroit (ex. un prompt qui essaie de
faire le travail du code, ou un code qui essaie de deviner ce que voulait dire l'utilisateur).

---

## 1 · Connexion à un MCP — `demo_list_tools` *(rien à coder)*

🎯 **Ce que tu comprends :** le geste de base d'un client MCP — ouvrir un sous-processus
stdio, s'annoncer (`initialize`), lister les tools, fermer.

✏️ **Ce que tu fais :** ouvre `atelier/agent.py`, lis la fonction `demo_list_tools()`. C'est
EXACTEMENT la même mécanique que `mcp dev` utilisait côté atelier 1 — sauf qu'ici, c'est TON
code Python qui joue le rôle du client (au lieu de l'Inspector ou de Claude Desktop).

🧪 **Teste :**

```bash
uv run python atelier/agent.py --list-tools
```

✅ **C'est bon quand :** tu vois les 5 tools du MCP atelier 1 s'afficher (`list_envelopes`,
`list_factures_a_classer`, `read_invoice`, `record_expense`, `get_balance`).

<details>
<summary>💡 Bloqué ? — ça ne se lance pas</summary>

Vérifie que `atelier-1-serveur-mcp/` existe bien à côté de ce dossier et qu'il a été
synchronisé (`cd ../atelier-1-serveur-mcp && uv sync`). Relance `uv run python check.py`
depuis `atelier-2-agent/` pour un diagnostic complet.

</details>

---

## 2 · Le system prompt — `atelier/config.py`

🎯 **Ce que tu construis :** le `SYSTEM_PROMPT`, le **seul** texte qui dit au modèle qui il
est et quand utiliser quel outil. C'est ta règle de gestion, écrite en français — le
strict équivalent du `hint` de l'atelier 1, mais côté agent.

✏️ **Ce que tu fais :** ouvre `atelier/config.py`, remplis `SYSTEM_PROMPT = ""`. Précise au
minimum : le rôle de l'agent, quand appeler les outils « enveloppes », et la règle non
négociable (ne jamais inventer prénom/nom).

🧪 **Teste :** pas d'exécution possible tant que l'exercice 3 n'est pas fait — relis-toi,
demande-toi « un collègue qui ne connaît pas le projet comprendrait-il quand utiliser quel
outil rien qu'en lisant ce texte ? ».

✅ **C'est bon quand :** `SYSTEM_PROMPT` n'est plus vide et couvre les deux points ci-dessus.

<details>
<summary>💡 Bloqué ? — un exemple de <code>SYSTEM_PROMPT</code></summary>

```python
SYSTEM_PROMPT = """\
Tu es l'assistant notes de frais d'AVISIA. Utilise les outils "enveloppes" pour classer
les factures déposées par l'utilisateur dans les enveloppes CE / APPRENTISSAGE.
Avant tout record_expense, demande le PRÉNOM et le NOM de l'utilisateur — ne les invente
jamais. Termine toujours par une réponse claire en français.
"""
```

Tu complèteras ce texte à l'exercice 4 pour y ajouter la consigne sur le nouvel outil météo.

</details>

---

## 3 · La boucle agentique — ⭐ le cœur de l'atelier

🎯 **Ce que tu construis :** la méthode `run()` de `MCPAgent` — le moteur qui fait dialoguer
le modèle et les outils jusqu'à une réponse finale. C'est LE morceau de code de tout
l'atelier.

✏️ **Ce que tu fais :** dans `atelier/agent.py`, remplace le `raise NotImplementedError(...)`
du TODO 3 par la boucle décrite juste au-dessus dans les commentaires :

1. appelle `self.anthropic.messages.create(...)` avec `tools=self.tools_schema` ;
2. ajoute la réponse à `messages` ;
3. si `response.stop_reason != "tool_use"` → renvoie le texte final ;
4. sinon, pour chaque bloc `tool_use` : appelle `self._call_tool(block.name, block.input)`
   (déjà écrit — route vers le bon MCP), construis un bloc `tool_result`, renvoie tout au
   modèle, boucle.

🧪 **Teste :**

```bash
uv run python atelier/agent.py "Salut, qui es-tu et que peux-tu faire pour moi ?"
```

Puis un vrai cas d'usage :

```bash
uv run python atelier/agent.py "Classe les factures de la boîte à classer de l'atelier 1"
```

✅ **C'est bon quand :** l'agent répond sans planter, et pour le 2ᵉ message, tu vois les
lignes `🛠️  appel ...` défiler (les tool_calls) avant la réponse finale `🤖 ...`.

<details>
<summary>💡 Bloqué ? — la boucle complète</summary>

```python
async def run(self, user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]
    while True:
        response = self.anthropic.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            tools=self.tools_schema,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                output = await self._call_tool(block.name, block.input)
            except Exception as e:
                output = f"Erreur lors de l'appel de {block.name} : {e}"
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": tool_results})
```

</details>

> 💡 **À discuter :** que se passerait-il si on oubliait de renvoyer le `tool_result` au
> modèle ? (Réponse : le modèle ne saurait jamais ce que l'outil a répondu — il ne peut pas
> "voir" l'exécution, seulement ce qu'on lui renvoie explicitement dans `messages`.)

---

## 4 · Un deuxième MCP — la gestion de plusieurs outils

🎯 **Ce que tu construis :** la connexion de l'agent à un **second** MCP (`mcp_meteo/`, un
mini serveur météo **fictif** fourni), sans toucher au protocole.

✏️ **Ce que tu fais — 2 étapes :**

- **4a** — dans `atelier/config.py`, décommente/ajoute l'entrée `"meteo"` dans
  `MCP_SERVERS` (inspire-toi de l'entrée `"enveloppes"` juste au-dessus).
- **4b** — reviens dans `SYSTEM_PROMPT` (exercice 2) et ajoute une consigne : quand utiliser
  `get_meteo`, et surtout **quand ne PAS l'utiliser** (ne pas mélanger avec les enveloppes).

Tu ne touches à **rien d'autre** : `connect_all()` (plomberie) boucle déjà sur
`config.MCP_SERVERS`, et `run()` (ton code de l'exercice 3) route déjà chaque appel vers le
bon serveur via `tool_to_server`. C'est la preuve qu'un agent bien structuré scale à
N outils sans réécrire le protocole — seule la **donnée de config** et le **prompt**
changent.

🧪 **Teste :**

```bash
uv run python atelier/agent.py "Quelle météo à Lyon ?"
```

✅ **C'est bon quand :** tu vois `🔌 connecté à « meteo » — 1 tool(s)` au démarrage, et
l'agent répond avec la météo (fictive) de Lyon sans toucher aux enveloppes.

<details>
<summary>💡 Bloqué ? — indice</summary>

Si l'agent essaie d'utiliser `get_meteo` pour une question de note de frais (ou l'inverse),
le problème n'est presque jamais dans `run()` : relis ton `SYSTEM_PROMPT`, c'est lui qui
arbitre.

</details>

---

## 🏁 Démo finale — les deux MCP dans la même conversation

```bash
uv run python atelier/agent.py "Classe les factures de la boîte à classer de l'atelier 1, et dis-moi aussi quelle météo il fait à Marseille."
```

Observe :

1. l'agent appelle les tools « enveloppes » (liste, lit, classe, archive) **et** `get_meteo`,
   dans le même tour de conversation ;
2. chaque appel est routé vers le **bon** sous-processus MCP (`tool_to_server`) ;
3. la réponse finale couvre les deux sujets.

**Réinitialiser pour rejouer :** relance simplement la commande — l'atelier 1 gère son
propre état (voir sa section « Réinitialiser » dans son `ATELIER.md`).

---

## 🆘 Ça ne marche pas ? — réflexes de dépannage

| Symptôme                                     | Cause la plus fréquente                     | Solution                                                        |
| --------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------- |
| `check.py` affiche un ❌ sur la clé API      | `ANTHROPIC_API_KEY` non exportée            | `export ANTHROPIC_API_KEY=sk-ant-...` dans le même terminal       |
| `check.py` ne trouve pas l'atelier 1          | dossiers pas voisins, ou atelier 1 pas sync | `cd ../atelier-1-serveur-mcp && uv sync`                          |
| L'agent boucle sans jamais répondre           | `stop_reason` mal testé, ou `tool_result` pas renvoyé | compare avec `solution/agent.py`                        |
| `KeyError` sur un nom de tool                 | `tool_to_server` pas à jour (2ᵉ MCP mal branché) | vérifie l'entrée `"meteo"` dans `MCP_SERVERS`                 |
| L'agent mélange enveloppes et météo           | `SYSTEM_PROMPT` pas assez précis            | relis l'exercice 4b — c'est le prompt qui arbitre                 |

> 💡 **Filet de sécurité :** `solution/` contient la version complète. En cas de blocage :
> `uv run python solution/agent.py "ton message"`.

---

## Pour l'animateur *(pas pour les participants)*

**Timing (~2 h, ~105 min occupées) :** 10 min pitch + tableau « qui décide » · 10 min
setup/`check.py` (dont vérif atelier 1) · 10 min exo 1 (connexion, lecture) · 10 min exo 2
(system prompt) · 35 min exo 3 ⭐ (boucle agentique — le plus long) · 20 min exo 4
(2ᵉ MCP + prompt) · 10 min démo finale + Q/R. ~15 min de marge pour les blocages.

**Pièges à éviter :**

- **Clé API** : distribue-la (ou fais créer un compte) AVANT la séance — c'est le seul
  prérequis qui peut bloquer un participant en cours de route. Les exercices 1, 2 et 4a ne
  la nécessitent pas : un participant sans clé peut avancer en attendant.
- **Atelier 1 obligatoire en amont** : `atelier-1-serveur-mcp/` doit être cloné et
  synchronisé (`uv sync`) avant de commencer cet atelier — c'est la cible MCP par défaut.
- **Aucune donnée réelle** : le MCP météo est un mock inventé (4 villes, pas d'appel
  réseau). Rappelle-le si la question se pose.

**Points de discussion à provoquer :**

- Exo 3 : que se passe-t-il si on ne renvoie jamais le `tool_result` ? *Le modèle ne "voit"
  que ce qu'on lui donne explicitement — pas d'exécution magique.*
- Exo 4 : brancher un 2ᵉ MCP ne touche ni au protocole ni à la boucle — seulement à
  `MCP_SERVERS` et au `SYSTEM_PROMPT`. *Un agent bien structuré scale par la donnée, pas
  par le code.*
- Le tableau « qui décide » : où mettrais-tu une règle de plafond (250 €) si tu devais la
  gérer côté agent plutôt que côté MCP ? *Nulle part — c'est justement le rôle du MCP
  (atelier 1), pas de l'agent : le prompt ne doit jamais porter une règle non négociable.*

**Solution de secours :** `solution/` contient la version complète.
`uv run python solution/agent.py "ton message"`.
