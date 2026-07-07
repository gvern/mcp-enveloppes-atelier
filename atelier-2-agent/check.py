"""Pré-vol de l'atelier — lance `uv run python check.py` AVANT de commencer.

Vérifie l'environnement (dépendances, clé API) et que le MCP de l'atelier 1 (réutilisé
comme cible via solution/server.py) est accessible en stdio. Aucun secret n'est stocké ni
affiché : ANTHROPIC_API_KEY est lue depuis l'environnement uniquement, jamais depuis le
code — si elle manque, ce script le signale proprement (pas de traceback).
"""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def check(label: str, cond: bool, hint: str = "") -> None:
    global ok
    mark = "✅" if cond else "❌"
    print(f"{mark} {label}" + ("" if cond else f"  → {hint}"))
    ok = ok and cond


# 1. dépendances
try:
    import mcp, anthropic  # noqa: F401
    check("Dépendances (mcp, anthropic)", True)
except Exception as e:  # noqa: BLE001
    check("Dépendances (mcp, anthropic)", False, f"{e} — lance `uv sync`")

# 2. clé API — on vérifie juste sa PRÉSENCE, jamais sa valeur (rien n'est affiché/loggé)
has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
check("Variable d'environnement ANTHROPIC_API_KEY définie", has_key,
      "export ANTHROPIC_API_KEY=sk-ant-... (jamais dans le code, jamais commit)")

# 3. le mini MCP météo fourni est bien en place
meteo_script = ROOT / "mcp_meteo" / "server.py"
check("mcp_meteo/server.py présent (2e MCP, exercice 4)", meteo_script.exists(),
      "fichier manquant — ne devrait pas arriver, réclone le dépôt")

# 4. atelier-1-serveur-mcp trouvable (voisin de ce dossier dans le mono-repo)
sys.path.insert(0, str(ROOT / "atelier"))
config = None
try:
    import config  # noqa: E402
    atelier1_server = config.ATELIER1_DIR / "solution" / "server.py"
    atelier1_ok = atelier1_server.exists()
    check(f"atelier-1-serveur-mcp trouvé ({config.ATELIER1_DIR.name}/)", atelier1_ok,
          f"introuvable : {atelier1_server} — clone/complète d'abord atelier-1-serveur-mcp/ "
          "(voisin de ce dossier), ou fixe ATELIER1_DIR")
except Exception as e:  # noqa: BLE001
    atelier1_ok = False
    check("atelier/config.py se charge", False, str(e))


async def _probe(command: str, args: list[str], cwd: str) -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=command, args=args, cwd=cwd)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return len(tools.tools)


# 5. connexion réelle au MCP atelier 1 en stdio (best-effort — ne fait JAMAIS planter le
#    pré-vol : un échec ici affiche juste un ❌ avec un message clair)
if atelier1_ok:
    try:
        n = asyncio.run(asyncio.wait_for(
            _probe("uv", ["run", "python", "solution/server.py"], str(config.ATELIER1_DIR)),
            timeout=30,
        ))
        check(f"MCP atelier 1 accessible en stdio ({n} tools)", n > 0)
    except Exception as e:  # noqa: BLE001
        check("MCP atelier 1 accessible en stdio", False,
              f"{e} — lance `cd ../atelier-1-serveur-mcp && uv sync` puis réessaie")
else:
    check("MCP atelier 1 accessible en stdio", False, "voir la ligne au-dessus")

print()
if ok:
    print("Tout est prêt. Suis ATELIER.md pour démarrer.")
else:
    print("⚠️  Corrige les ❌ ci-dessus quand tu peux.")
    print("   Pas de clé API sous la main ? Tu peux quand même avancer sur les exercices")
    print("   1, 2 et 4a (rien de tout ça n'appelle le modèle Anthropic).")
    sys.exit(1)
