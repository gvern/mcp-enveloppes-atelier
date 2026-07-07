"""Mini MCP fictif — météo MOCKÉE (aucune donnée réelle, aucun appel réseau).

⚙️ PLOMBERIE fournie pour l'atelier 2 — sert de DEUXIÈME MCP pour l'exercice 4 (gestion de
plusieurs outils côté agent). Ne pas modifier pendant l'atelier : ce n'est pas l'objet de
l'exercice (le protocole MCP a déjà été vu en atelier 1).

Toutes les données ci-dessous sont INVENTÉES à but pédagogique — pas d'appel externe, pas
de donnée réelle AVISIA.

Lancer seul (debug) :  uv run mcp dev mcp_meteo/server.py
"""

from mcp.server.fastmcp import FastMCP

INSTRUCTIONS = """\
Serveur météo FICTIF — données mockées, aucun appel réseau réel. Donne la météo du jour
pour une ville d'un petit jeu de données inventé (Paris, Lyon, Marseille, Lille).
"""

mcp = FastMCP("meteo-fictive", instructions=INSTRUCTIONS)

# Jeu de données 100 % inventé — à but pédagogique uniquement.
_MOCK_METEO = {
    "paris": {"condition": "nuageux", "temperature_c": 17},
    "lyon": {"condition": "ensoleillé", "temperature_c": 22},
    "marseille": {"condition": "ensoleillé", "temperature_c": 26},
    "lille": {"condition": "pluie légère", "temperature_c": 14},
}


@mcp.tool()
def get_meteo(ville: str) -> dict:
    """Météo FICTIVE du jour pour une ville (données mockées, pas d'appel réseau réel).

    Villes disponibles dans le mock : Paris, Lyon, Marseille, Lille. Renvoie
    {ville, condition, temperature_c}, ou un message d'erreur si la ville ne fait pas
    partie du jeu de données mocké.
    """
    key = ville.strip().lower()
    if key not in _MOCK_METEO:
        return {
            "ville": ville,
            "erreur": "ville hors du jeu de données mocké (essaie : Paris, Lyon, Marseille, Lille)",
        }
    return {"ville": ville.strip().title(), **_MOCK_METEO[key]}


if __name__ == "__main__":
    mcp.run()  # stdio uniquement — ce MCP est piloté par l'agent, pas par Claude Desktop
