"""Agent — pilote un ou plusieurs serveurs MCP via tool-calling Gemini (SOLUTION).

Connexion : chaque MCP déclaré dans config.MCP_SERVERS est lancé en stdio (sous-processus),
comme `mcp dev` le fait côté atelier 1. Boucle : on envoie `contents` au modèle avec les
tools agrégés de tous les MCP connectés ; tant que le modèle répond par des function_calls,
on les exécute sur le BON serveur (via tool_to_server) et on renvoie les résultats ; on
s'arrête à la première réponse sans function_call.

Lancer :
  uv run python solution/agent.py "Classe les factures de la boîte à classer"
  uv run python solution/agent.py --list-tools   # exercice 1 : juste lister les tools
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
# EXERCICE 1 — EXEMPLE RÉSOLU (connexion à un seul MCP, pour comprendre le geste de base)
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
        """Route l'appel vers la BONNE session grâce à tool_to_server."""
        server = self.tool_to_server[name]
        result = await self.sessions[server].call_tool(name, arguments)
        return "\n".join(b.text for b in result.content if getattr(b, "text", None))

    async def run(self, user_message: str) -> str:
        """Boucle agentique : appelle le modèle, exécute ses function_calls, jusqu'à réponse finale."""
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message)])]
        gen_config = types.GenerateContentConfig(
            system_instruction=config.SYSTEM_PROMPT,
            max_output_tokens=config.MAX_TOKENS,
            tools=[types.Tool(function_declarations=self.tools_schema)],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        while True:
            response = self.client.models.generate_content(
                model=config.MODEL,
                contents=contents,
                config=gen_config,
            )
            contents.append(response.candidates[0].content)

            function_calls = response.function_calls
            if not function_calls:
                return response.text or ""

            response_parts = []
            for fc in function_calls:
                print(f"🛠️  appel {fc.name}({fc.args})")
                try:
                    output = await self._call_tool(fc.name, fc.args or {})
                    result = {"result": output}
                except Exception as e:  # noqa: BLE001
                    result = {"error": f"Erreur lors de l'appel de {fc.name} : {e}"}
                response_parts.append(types.Part.from_function_response(
                    name=fc.name, response=result,
                ))
            contents.append(types.Content(role="tool", parts=response_parts))

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
