# Atelier — Créer son premier MCP

## L'idée à retenir (le pitch)

Un MCP, c'est **exposer ta logique métier à un LLM sans lui en déléguer le contrôle**.

|           | Claude (le LLM)                             | Le serveur MCP (toi, le métier)                            |
| --------- | ------------------------------------------- | ----------------------------------------------------------- |
| fait quoi | lit, comprend,**décide** l'enveloppe | **applique** le taux, le plafond, écrit le `.xlsx` |
| fiable ?  | non (peut se tromper, inventer)             | oui (règles codées, testables, traçables)                |

Toute la question d'un projet IA métier : **où placer la frontière de confiance.** Cet atelier
la fait toucher du doigt.

---

## 🗺️ Le parcours — ce que tu vas faire, dans l'ordre

Tu avances de haut en bas. Coche au fur et à mesure. **Chaque exercice se teste avant de passer au suivant.**

- [ ] **0 · Préparation** — `uv sync`, `check.py`, brancher Claude Desktop *(à faire une fois, ~10 min)*
- [ ] **1 · La règle de classement** — écrire les `hint` dans `atelier/config.py`
- [ ] **2 · L'exemple résolu** — lire `list_envelopes` *(rien à coder, juste comprendre)*
- [ ] **3 · `list_factures_a_classer`** — choisir le bon décorateur
- [ ] **4 · `read_invoice`** — choisir le bon décorateur
- [ ] **5 · `record_expense`** — ⭐ **le cœur de l'atelier** (3 TODO)
- [ ] **6 · `enveloppes://guide`** — une *autre* primitive (une resource)
- [ ] **7 · `/classer_facture`** — la procédure complète (un prompt)
- [ ] **🏁 Démo finale** — lancer `/classer_facture` sur les 3 factures

> **Comment lire une fiche d'exercice :**
> 🎯 ce que tu construis · ✏️ ce que tu fais · 🧪 comment le tester · ✅ comment savoir que c'est bon · 💡 **Bloqué ?** = indices et réponse (clique pour dérouler).
>
> Les blocs **💡 Bloqué ?** sont repliés exprès : essaie d'abord, déroule seulement si tu cales.

---

## 0 · Préparation *(à faire une fois)*

### a. Installer `uv` (si tu ne l'as pas déjà)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# macOS Homebrew 
brew install uv
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Python déjà installé
pip install uv   (ou pipx install uv)
```

Vérifie : `uv --version`.

### b. Installer les dépendances et lancer le pré-vol

**Toutes les commandes de cet atelier se lancent depuis `atelier-1-serveur-mcp/`** (ce
sous-dossier du repo) :

```bash
cd atelier-1-serveur-mcp   # si tu n'y es pas déjà
uv sync                 # installe mcp, openpyxl, pymupdf (rien d'autre à installer)
uv run python check.py  # pré-vol : vérifie tout + crée 3 factures de test
```

✅ **C'est bon quand** `check.py` affiche **4 ✅** et dépose 3 factures dans `factures_a_classer/`.
❌ S'il affiche un ❌, le message te dit quoi corriger (en général : relancer `uv sync`).

### c. Brancher l'atelier sur Claude Desktop

Réglages → Développeur → Modifier la config, puis (remplace le chemin absolu par le tien) :

```json
{
  "mcpServers": {
    "enveloppes-atelier": {
      "command": "uv",
      "args": ["run", "--directory", "/CHEMIN/ABSOLU/atelier-mcp-enveloppes/atelier-1-serveur-mcp", "python", "atelier/server.py"]
    }
  }
}
```

Quitte Claude Desktop (**Cmd+Q**) et relance.

> ⚠️ **À retenir pour tout l'atelier :** à **chaque** fois que tu modifies le code, **quitte et
> relance Claude Desktop** — sinon l'ancien code continue de tourner.

### d. Tes deux outils de test

| Outil                               | Commande / accès                    | Pour quoi                                                                                                                            |
| ----------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Inspector** (boucle rapide) | `uv run mcp dev atelier/server.py` | voir tes tools apparaître + les appeler à la main,**sans Claude** — et il **recharge tout seul** à chaque sauvegarde |
| **Claude Desktop**            | le chat                              | voir Claude**se comporter** (réclamer le prénom, classer le lot)                                                             |

> 🔁 **La boucle de travail, à répéter à chaque exercice :**
> ① tu complètes un TODO → ② tu sauvegardes → ③ tu vérifies dans l'Inspector `mcp dev` → ④ exercice suivant.
> Tu ne rebranches Claude Desktop que pour les exercices 5 et 7 (là où on veut voir le *comportement*).

---

## La question centrale de tout l'atelier : **qui déclenche cette capacité ?**

À chaque exercice « choisis le décorateur », pose-toi cette seule question :

| Qui déclenche ?                                                    | Primitive             | Décorateur                    |
| ------------------------------------------------------------------- | --------------------- | ------------------------------ |
| une**ACTION** que *Claude* décide d'appeler                | un**tool**      | `@mcp.tool()`                |
| une**DONNÉE** de référence que *l'utilisateur* attache   | une**resource** | `@mcp.resource("uri://...")` |
| une**PROCÉDURE** que *l'utilisateur* lance (slash-command) | un**prompt**    | `@mcp.prompt()`              |

Tout l'atelier consiste à répondre à cette question, encore et encore. Garde ce tableau sous les yeux.

---

## 1 · La règle de classement — `atelier/config.py`

🎯 **Ce que tu construis :** le `hint`, le **seul** texte que Claude lit pour décider de l'enveloppe.
C'est ta règle de gestion, écrite en français. Pur métier.

✏️ **Ce que tu fais :** ouvre `atelier/config.py`, remplis les deux `hint: ""`. Pour chacun, donne
des **types de dépenses** + quelques **marchands** typiques (ça aide énormément Claude).

🧪 **Teste :** `uv run mcp dev atelier/server.py` → onglet **Tools** → `list_envelopes` → tu vois tes deux règles.

✅ **C'est bon quand :** les deux `hint` ne sont plus vides et s'affichent dans `list_envelopes`.

<details>
<summary>💡 Bloqué ? — un exemple de <code>hint</code></summary>

```python
# CE :
"hint": "Dépenses culturelles et sportives : cinéma, musée, spectacle, sport, salle de "
        "sport, livre culturel. Marchands type : UGC, FNAC, Basic-Fit, Decathlon.",

# APPRENTISSAGE :
"hint": "Montée en compétences : formation, certification, livre technique, conférence, "
        "abonnement IA (ChatGPT, Claude, Gemini). Marchands : OpenAI, Anthropic, Udemy, Coursera.",
```

Le taux (50 % / 100 %) et le plafond (250 €) sont déjà remplis : on les fige pour que rien ne plante.

</details>

---

## 2 · L'exemple résolu — `list_envelopes` *(rien à coder)*

🎯 **Ce que tu comprends :** comment une fonction Python devient une capacité MCP.

✏️ **Ce que tu fais :** dans `atelier/server.py`, repère le **`@mcp.tool()`** juste au-dessus de
`list_envelopes`. C'est **ce décorateur** qui expose la fonction à Claude. C'est ton modèle pour la suite.

> « Lister les enveloppes » = une **action** que Claude déclenche pour s'informer → un **tool**. Logique.

✅ **C'est bon quand :** tu sais répondre à « pourquoi `list_envelopes` est-il un tool et pas autre chose ? »

---

## 3 · `list_factures_a_classer` — choisis le décorateur

🎯 **Ce que tu construis :** la capacité de lister les factures déposées dans la boîte à classer.

❓ **La question :** lister les factures, c'est une **action que Claude déclenche**, une **donnée que
l'utilisateur attache**, ou une **procédure** ? → ajoute le bon décorateur au-dessus de la fonction (TODO 3).

🧪 **Teste :** dans `mcp dev`, `list_factures_a_classer` apparaît dans **Tools** et renvoie tes 3 factures.

✅ **C'est bon quand :** l'appel renvoie `count: 3` et la liste de tes factures.

<details>
<summary>💡 Bloqué ? — indice</summary>

C'est **Claude** qui doit pouvoir appeler cette fonction quand il en a besoin (pas l'utilisateur qui
« attache » quelque chose). Quelle ligne du tableau « qui déclenche ? » ça décrit ?

</details>

<details>
<summary>✅ La réponse</summary>

Une **action déclenchée par Claude → un tool** :

```python
@mcp.tool()
def list_factures_a_classer() -> dict:
    ...
```

</details>

---

## 4 · `read_invoice` — choisis le décorateur

🎯 **Ce que tu construis :** la capacité de lire le texte d'une facture PDF sur le disque.

❓ **La question :** même réflexe — qui déclenche ? Ajoute le bon décorateur (TODO 4).

🧪 **Teste :** `mcp dev` → `read_invoice` → colle le chemin d'une facture (celui renvoyé à l'exo 3) → tu vois le texte extrait.

✅ **C'est bon quand :** tu récupères `{filename, pages, text}` avec le contenu lisible de la facture.

<details>
<summary>💡 Bloqué ? — indice + réponse</summary>

Lire un fichier à la demande de Claude = encore une **action déclenchée par Claude → un tool**.

```python
@mcp.tool()
def read_invoice(path: str) -> dict:
    ...
```

</details>

---

## 5 · `record_expense` — ⭐ le cœur métier (3 TODO)

🎯 **Ce que tu construis :** l'écriture dans le `.xlsx` **et** une règle non négociable —
*impossible d'enregistrer sans prénom + nom*. C'est le moment clé de l'atelier.

✏️ **Ce que tu fais — 3 TODO :**

- **5a · le décorateur** — ça écrit un fichier (effet de bord), c'est Claude qui le déclenche.
- **5b · les paramètres obligatoires** — ajoute `prenom: str, nom: str` **en tête** de la signature,
  **sans valeur par défaut**. C'est *ça* qui force Claude à les demander.
- **5c · la docstring** — explique à quoi sert le tool, et précise que prénom + nom sont **obligatoires
  et ne doivent pas être inventés**. Claude lit la docstring.

🧪 **Teste (le moment à ne pas rater) :** **relance Claude Desktop**, puis demande
*« enregistre la facture UGC dans CE »*.

✅ **C'est bon quand :** **Claude te réclame ton prénom et ton nom** au lieu de les inventer.
→ La règle est dans le **contrat** (le schéma du tool), pas dans une consigne polie.

<details>
<summary>💡 Bloqué ? — la signature complète</summary>

```python
@mcp.tool()
def record_expense(prenom: str, nom: str, envelope: str, descriptif: str, amount: float,
                   source_path: str | None = None) -> dict:
    """Enregistre une facture dans le .xlsx de l'enveloppe (CE ou APPRENTISSAGE).

    PRÉNOM et NOM sont OBLIGATOIRES : demande-les à l'utilisateur, ne les invente jamais.
    Si source_path est fourni, le MCP archive automatiquement l'original.
    """
    ...
```

`prenom` et `nom` **en premier**, **sans `= ...`** → ils deviennent obligatoires dans le schéma.
Le corps de la fonction les utilise déjà : tant qu'ils ne sont pas dans la signature, l'appel échoue (c'est normal).

</details>

> 💡 **À discuter :** enlève les deux paramètres, recommence → Claude n'a plus rien à demander et peut
> inventer une identité. **Le schéma *est* le garde-fou**, pas la politesse de la consigne.

---

## 6 · `enveloppes://guide` — une *autre* primitive

🎯 **Ce que tu construis :** le guide de classement. Ce n'est **pas** une action de Claude : c'est une
**donnée de référence** que *l'utilisateur* attache lui-même au chat.

❓ **La question :** quel décorateur pour « une donnée attachée par l'utilisateur » ? (TODO 6a — indice : il prend une **URI**.)
Puis écris le guide des 2 enveloppes en markdown (TODO 6b).

🧪 **Teste :** dans Claude Desktop, bouton **« + »** → serveur `enveloppes-atelier` → tu peux **attacher**
`enveloppes://guide`. (Un tool, lui, ne s'attache pas : c'est Claude qui l'appelle.)

✅ **C'est bon quand :** `enveloppes://guide` apparaît dans l'onglet **Resources** de `mcp dev`, et tu peux l'attacher dans Claude Desktop.

<details>
<summary>💡 Bloqué ? — indice</summary>

Une donnée fournie par l'humain, adressée par une URI → ce n'est ni un tool ni un prompt.
Regarde la 2ᵉ ligne du tableau « qui déclenche ? ».

</details>

<details>
<summary>✅ La réponse</summary>

Une **resource** (elle prend une URI) :

```python
@mcp.resource("enveloppes://guide", mime_type="text/markdown")
def guide() -> str:
    return (
        "# Enveloppes AVISIA\n\n"
        "## CE — culturel & sportif (remboursé 50 %, plafond 250 €)\n"
        "Cinéma, musée, sport, salle de sport, livre culturel.\n\n"
        "## APPRENTISSAGE — montée en compétences (remboursé 100 %, plafond 250 €)\n"
        "Formation, certification, livre technique, abonnement IA.\n"
    )
```

</details>

> 💡 **À discuter :** si tu mets `@mcp.tool()` ici, « ça marche » aussi… mais c'est sémantiquement faux :
> une resource est *fournie par l'humain*, un tool est *appelé par le modèle*. La distinction = **qui a la main**.

---

## 7 · `/classer_facture` — la procédure complète

🎯 **Ce que tu construis :** la procédure qui enchaîne « lister → lire → classer → archiver » pour tout le lot.

❓ **La question :** une suite d'étapes que l'**utilisateur lance** comme une commande → quel décorateur ? (TODO 7a)
Puis écris la procédure en français (TODO 7b).

🧪 **Teste :** **relance Claude Desktop** → bouton **« + »** → `classer_facture`. Lance-le.

✅ **C'est bon quand :** `/classer_facture` apparaît dans la liste des prompts et démarre la procédure.

<details>
<summary>💡 Bloqué ? — décorateur + procédure</summary>

Une procédure lancée par l'utilisateur → un **prompt** (slash-command) :

```python
@mcp.prompt()
def classer_facture() -> str:
    return (
        "Classe toutes les factures de la boîte à classer dans les enveloppes AVISIA.\n"
        "1. Demande le prénom et le nom (une seule fois, ne les invente pas).\n"
        "2. Appelle list_factures_a_classer().\n"
        "3. Pour CHAQUE fichier : read_invoice(path), choisis l'enveloppe via le guide, puis "
        "record_expense(prenom, nom, envelope, descriptif, amount, source_path=path).\n"
        "4. Récap : enveloppe + montant par facture, solde par enveloppe, alerte si over_cap."
    )
```

</details>

---

## 🏁 Démo finale — tout s'enchaîne

Avec les 3 factures de test en place, lance **`/classer_facture`** dans Claude Desktop. Claude :

1. te demande **prénom + nom** (une fois),
2. lit chaque facture, choisit CE (UGC, Decathlon) ou APPRENTISSAGE (ChatGPT),
3. écrit les `.xlsx` et **déplace** chaque PDF dans `notes_de_frais/<…>/factures/`,
4. te fait un récap (montants, soldes, plafond 250 €).

Ouvre un `.xlsx` produit dans Excel : identité en B10/B11, lignes en colonnes A/B. **Livrable
auditable** — leur quotidien.

**Réinitialiser pour rejouer :**

```bash
uv run python check.py        # recrée les 3 factures de test
# ou, pour tout remettre à zéro :
rm -rf notes_de_frais factures_a_classer && uv run python check.py
```

---

## 🆘 Ça ne marche pas ? — réflexes de dépannage

| Symptôme                                | Cause la plus fréquente                | Solution                                                                   |
| ---------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------- |
| `check.py` affiche un ❌               | dépendances pas installées            | relance`uv sync`                                                         |
| Mon tool n'apparaît pas dans`mcp dev` | décorateur manquant ou faute de frappe | vérifie le`@mcp.xxx()` juste **au-dessus** de la fonction         |
| Claude ignore mon changement             | l'ancien code tourne encore             | **quitte (Cmd+Q) et relance** Claude Desktop                         |
| Le serveur ne se lance pas               | erreur Python                           | lis le message dans le terminal de`mcp dev` ; compare avec `solution/` |
| Claude n'invente plus / je suis perdu    | —                                      | ouvre la version de référence :`uv run mcp dev solution/server.py`     |

> 💡 **Filet de sécurité :** le dossier `solution/` contient la version complète et fonctionnelle.
> En cas de blocage, compare ton fichier avec `solution/server.py` (ou `solution/config.py`).

---

## Pour l'animateur *(pas pour les participants)*

**Timing (~2 h, ~102 min occupées) :** 15 min pitch + tableau « qui déclenche quoi » ·
10 min setup/`check.py` · 5 min exo 1 (rédaction des `hint`) · 3 min exo 2 (lecture, rien à
coder) · 12 min exo 3 · 12 min exo 4 · 15 min exo 5 (le sommet) · 10 min exo 6 · 10 min exo 7 ·
10 min démo finale + Q/R. ~18 min de marge pour les blocages.

**Pièges à éviter :**

- **Un seul prérequis** : `uv` (cf. §0). Une fois installé, tout passe par `uv sync` — Python et deps
  gérés par uv, rien d'autre à installer. Si quelqu'un bloque, `check.py` le dit.
- **Relancer Claude Desktop** après chaque modif (sinon l'ancien code tourne). Pour la boucle rapide,
  préfère `mcp dev` qui recharge tout seul.
- **PDF numériques uniquement** (couche texte). Les factures de test conviennent.

**Points de discussion à provoquer :**

- Exo 5 : retirer prénom/nom → Claude invente. *Le schéma est le garde-fou.*
- Exo 6 : `guide` en tool « marche » mais casse la sémantique. *Qui a la main : modèle ou user ?*
- Plafond 250 € : Claude ne calcule rien, le serveur tranche (`over_cap`). *Règle non négociable.*
- Le `hint` (exo 1) : changer le texte = changer le comportement **sans réentraîner**.

**Solution de secours :** `solution/` contient la version complète. Pour la montrer ou dépanner :
`uv run mcp dev solution/server.py`.
