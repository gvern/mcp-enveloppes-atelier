"""Agent — pilote un ou plusieurs serveurs MCP via tool-calling Gemini.
   SQUELETTE D'ATELIER (à compléter).

Tu vas transformer ce fichier en agent fonctionnel en remplissant le TODO. La connexion
aux MCP (protocole, sous-processus stdio, agrégation des tools) est déjà écrite — RÈGLE
D'OR : tu n'écris QUE la boucle agentique (le métier de cet atelier). Si tu bloques, la
version complète est dans solution/.

TESTER À TOUT MOMENT :
  uv run python atelier/agent.py --list-tools         # exercice 1 (rien à coder)
  uv run python atelier/agent.py "ton message ici"     # exercices 3 et 4
"""

import asyncio
import sys
from contextlib import AsyncExitStack

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import config


# ══════════════════════════════════════════════════════════════════════════════════
# EXERCICE 1 — EXEMPLE RÉSOLU (lis-le, ne le modifie pas)
#
# Connexion en stdio au MCP de l'atelier 1, de la façon la plus simple possible : UN
# seul serveur, on liste ses tools, on ferme. C'est le geste de base que `connect_all()`
# (plus bas, déjà écrit) généralise à plusieurs serveurs.
# ══════════════════════════════════════════════════════════════════════════════════
async def demo_list_tools() -> None:
    """Se connecte au MCP de l'atelier 1 et affiche ses tools (aucune écriture)."""
    params = StdioServerParameters(
        command="uv", args=["run", "python", "solution/server.py"],
        cwd=str(config.ATELIER1_DIR),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"MCP atelier 1 — {len(tools.tools)} tool(s) :")
            for t in tools.tools:
                print(f"  • {t.name} — {t.description}")


# ─────────────────────────────── plomberie ───────────────────────────────  ⚙️
# Connexion à TOUS les MCP déclarés dans config.MCP_SERVERS (1 aujourd'hui, 2 après
# l'exercice 4a). Ne pas toucher : c'est le protocole MCP, déjà vu en atelier 1. Le
# `tool_to_server` construit ici permet de router chaque appel vers le bon serveur —
# utilise-le dans le TODO 3 ci-dessous, tu n'as pas besoin de le reconstruire.
class MCPAgent:
    """Un agent Gemini qui pilote N serveurs MCP connectés en stdio."""

    def __init__(self) -> None:
        self.client = genai.Client()  # lit GEMINI_API_KEY dans l'environnement
        self._stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.tool_to_server: dict[str, str] = {}
        self.tools_schema: list[types.FunctionDeclaration] = []

    async def connect_all(self) -> None:
        """Lance chaque MCP de config.MCP_SERVERS (stdio) et agrège leurs tools."""
        for name, spec in config.MCP_SERVERS.items():
            params = StdioServerParameters(
                command=spec["command"], args=spec["args"], cwd=spec.get("cwd"),
            )
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[name] = session
            listed = await session.list_tools()
            for t in listed.tools:
                self.tool_to_server[t.name] = name
                self.tools_schema.append(types.FunctionDeclaration(
                    name=t.name,
                    description=t.description or "",
                    parameters_json_schema=t.inputSchema,
                ))
            print(f"🔌 connecté à « {name} » — {len(listed.tools)} tool(s)")

    async def _call_tool(self, name: str, arguments: dict) -> str:
        """Route l'appel vers la BONNE session grâce à tool_to_server. Ne pas toucher."""
        server = self.tool_to_server[name]
        result = await self.sessions[server].call_tool(name, arguments)
        return "\n".join(b.text for b in result.content if getattr(b, "text", None))

    # ══════════════════════════════════════════════════════════════════════════
    # EXERCICE 3 — ⭐ LA BOUCLE AGENTIQUE (le cœur de l'atelier)
    #
    # Le principe (le même, que 1 ou 2 MCP soient connectés) :
    #   1. envoie `contents` au modèle (self.client.models.generate_content) avec
    #      model=config.MODEL, contents=contents, et un `config=types.GenerateContentConfig(
    #      system_instruction=config.SYSTEM_PROMPT, max_output_tokens=config.MAX_TOKENS,
    #      tools=[types.Tool(function_declarations=self.tools_schema)],
    #      automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))` ;
    #   2. ajoute la réponse à `contents` (`response.candidates[0].content`) ;
    #   3. si `response.function_calls` est vide : c'est la réponse finale — renvoie
    #      `response.text` ;
    #   4. sinon : pour CHAQUE `fc` de `response.function_calls`, appelle
    #      `await self._call_tool(fc.name, fc.args or {})`, et construis un
    #      `types.Part.from_function_response(name=fc.name, response={"result": <résultat>})` ;
    #      regroupe ces parts dans un SEUL `types.Content(role="tool", parts=[...])`, ajoute-le
    #      à `contents` ;
    #   5. retourne à l'étape 1 (boucle `while True`).
    #
    # TODO 3 — remplace le `raise` ci-dessous par cette boucle.
    # ══════════════════════════════════════════════════════════════════════════
    async def run(self, user_message: str) -> str:
        """Boucle agentique : appelle le modèle, exécute ses function_calls, jusqu'à réponse finale."""
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message)])]
        raise NotImplementedError("TODO 3 — écris la boucle agentique (voir consignes ci-dessus)")

    async def aclose(self) -> None:
        await self._stack.aclose()


async def _main() -> None:
    user_message = " ".join(sys.argv[1:]) or (
        "Classe les factures déposées dans la boîte à classer de l'atelier 1."
    )
    agent = MCPAgent()
    await agent.connect_all()
    try:
        reply = await agent.run(user_message)
        print("\n🤖", reply)
    finally:
        await agent.aclose()


if __name__ == "__main__":
    if "--list-tools" in sys.argv:
        asyncio.run(demo_list_tools())
    else:
        asyncio.run(_main())
